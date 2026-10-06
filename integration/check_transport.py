"""Six local process-boundary checks using the actual BindingGate.

This is an authored inert transport fixture, not MCP SDK interoperability or MCP
certification. Run: python3 -m integration.check_transport
"""
from __future__ import annotations

import argparse
import base64
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from binding_gate.core import BindingGate

TOOL = {"name": "read_file", "description": "Read inert transport fixture.",
        "inputSchema": {"type": "object", "properties": {}}}
ARGUMENTS = {"path": "fixture.txt", "options": {"fields": ["name", "size"]}}
CASE_NAMES = ("normal_and_mutated_arguments", "same_name_routing", "descriptor_replacement",
              "connection_replacement", "single_use", "legitimate_reapproval")


def encoded(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def expected_payload(arguments: dict) -> bytes:
    value = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "read_file", "arguments": deepcopy(arguments)}}
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


class LocalConnection:
    """Host-assigned process identity with bounded POSIX pipe writes and reads."""
    def __init__(self, server: str, connection: str, *, timeout: float = 3.0,
                 command: list[str] | None = None):
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.server = server
        self.connection = connection
        self.timeout = timeout
        self.responses = []
        self.requests_sent = 0
        self._buffer = b""
        self._finished = None
        self.process = subprocess.Popen(
            command or [sys.executable, "-I", "-u", str(ROOT / "integration/stdio_sink.py")],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)

    def _wait(self, descriptor: int, event: int, deadline: float) -> None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("local process pipe deadline exceeded")
        with selectors.DefaultSelector() as selector:
            selector.register(descriptor, event)
            if not selector.select(remaining):
                raise TimeoutError("local process pipe deadline exceeded")

    def _write(self, frame: bytes, deadline: float) -> None:
        remaining = memoryview(frame)
        descriptor = self.process.stdin.fileno()
        while remaining:
            self._wait(descriptor, selectors.EVENT_WRITE, deadline)
            try:
                written = os.write(descriptor, remaining)
            except BlockingIOError:
                continue
            if written <= 0:
                raise EOFError("local process stopped receiving")
            remaining = remaining[written:]

    def _read_line(self, deadline: float) -> bytes:
        descriptor = self.process.stdout.fileno()
        while b"\n" not in self._buffer:
            self._wait(descriptor, selectors.EVENT_READ, deadline)
            try:
                chunk = os.read(descriptor, 65536)
            except BlockingIOError:
                continue
            if not chunk:
                raise EOFError("local process ended before a complete receipt")
            self._buffer += chunk
            if len(self._buffer) > 4_194_304:
                raise ValueError("local process response exceeded fixture limit")
        line, self._buffer = self._buffer.split(b"\n", 1)
        return line

    def send(self, request: bytes) -> dict:
        if self._finished is not None:
            raise RuntimeError("connection already finished")
        if type(request) is not bytes or b"\n" in request or len(request) >= 1_048_576:
            raise ValueError("request must fit one bounded UTF-8 JSON line")
        deadline = time.monotonic() + self.timeout
        self._write(request + b"\n", deadline)
        self.requests_sent += 1
        response_line = self._read_line(deadline)
        record = {"trusted_server": self.server, "trusted_connection": self.connection,
                  "trusted_process_pid": self.process.pid,
                  "sent_payload_base64": encoded(request),
                  "received_response_base64": encoded(response_line), "response": None}
        self.responses.append(record)
        record["response"] = json.loads(response_line.decode("utf-8"))
        return record

    def finish(self) -> dict:
        """Close stdin, obtain independent EOF counts, then reap this child only."""
        if self._finished is not None:
            return self._finished
        result = {"trusted_server": self.server, "trusted_connection": self.connection,
                  "trusted_process_pid": self.process.pid, "requests_sent": self.requests_sent,
                  "responses": self.responses, "clean_exit": False, "audit": None}
        try:
            self.process.stdin.close()
            self.process.wait(timeout=self.timeout)
        except Exception as exc:
            result["lifecycle_error"] = type(exc).__name__ + ": " + str(exc)
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=0.5)
        finally:
            result["returncode"] = self.process.poll()
            stderr = self.process.stderr.read()
            trailing_stdout = self._buffer + (self.process.stdout.read() or b"")
            result["stderr_base64"] = encoded(stderr)
            result["unconsumed_stdout_base64"] = encoded(trailing_stdout)
            try:
                audit = json.loads(stderr.decode("utf-8"))
                if audit.get("fixture_event") == "stdin_closed" and audit.get("process_pid") == self.process.pid:
                    result["audit"] = audit
            except (ValueError, UnicodeError, AttributeError):
                pass
            result["clean_exit"] = (result["returncode"] == 0 and result["audit"] is not None
                                    and not trailing_stdout and "lifecycle_error" not in result)
            for pipe in (self.process.stdin, self.process.stdout, self.process.stderr):
                if not pipe.closed:
                    pipe.close()
            self._finished = result
        return result


def check_case(name: str, *, timeout: float = 3.0) -> dict:
    if name not in CASE_NAMES:
        raise ValueError("unknown transport check")
    connections = []
    receipts = []
    events = []
    assertions = []
    failure = None
    expected = []
    writer_calls = 0
    gate = BindingGate()

    def check(condition, label):
        assertions.append({"check": label, "passed": bool(condition)})
        if not condition:
            raise AssertionError(label)

    def publish(server="server-a", connection="c1", descriptor=None):
        result = gate.refresh(server, [deepcopy(TOOL if descriptor is None else descriptor)], connection)
        events.append({"action": "refresh", "server": server, "connection": connection,
                       "accepted": result.accepted, "reason": result.reason})
        check(result.accepted, "fixture publication accepted")

    def prepare(server="server-a", arguments=None):
        args = deepcopy(ARGUMENTS) if arguments is None else arguments
        selection = gate.select(server, "read_file")
        token = gate.prepare(selection, args)
        events.append({"action": "prepare", "server": server, "has_token": token is not None})
        check(token is not None, "preparation produced a permit")
        return token

    def writer(server, connection, request, descriptor):
        nonlocal writer_calls
        writer_calls += 1
        target = next(c for c in connections if (c.server, c.connection) == (server, connection))
        receipt = target.send(request)
        receipt["host_descriptor_base64"] = encoded(descriptor)
        receipts.append(receipt)
        return len(receipts) - 1

    def execute(token, allowed):
        result = gate.execute(token, writer)
        events.append({"action": "execute", "allowed": result.allowed, "reason": result.reason})
        check(result.reason != "transport outcome unknown", "transport outcome is known")
        check(result.allowed is allowed, "dispatch decision matches declared transport check")

    def expect(server, connection, arguments):
        expected.append({"server": server, "connection": connection,
                         "payload_base64": encoded(expected_payload(arguments))})

    try:
        identities = [("server-a", "c1"),
                      ("server-a", "c2") if name in {"connection_replacement", "legitimate_reapproval"}
                      else ("server-b", "c1")]
        for server, connection in identities:
            connections.append(LocalConnection(server, connection, timeout=timeout))
        check(connections[0].process.pid != connections[1].process.pid, "two distinct trusted child processes")
        publish()
        if name == "normal_and_mutated_arguments":
            expect("server-a", "c1", ARGUMENTS)
            execute(prepare(), True)
            mutable = deepcopy(ARGUMENTS)
            token = prepare(arguments=mutable)
            mutable["path"] = "caller-changed.txt"
            mutable["options"]["fields"][0] = "caller-changed"
            events.append({"action": "mutate_caller_arguments", "arguments": deepcopy(mutable)})
            expect("server-a", "c1", ARGUMENTS)
            execute(token, True)
        elif name == "same_name_routing":
            publish("server-b")
            for server in ("server-a", "server-b"):
                expect(server, "c1", ARGUMENTS)
                execute(prepare(server), True)
        elif name == "descriptor_replacement":
            token = prepare()
            changed = deepcopy(TOOL)
            changed["description"] = "Changed transport fixture descriptor."
            publish(descriptor=changed)
            execute(token, False)
        elif name == "connection_replacement":
            token = prepare()
            publish(connection="c2")
            execute(token, False)
        elif name == "single_use":
            token = prepare()
            expect("server-a", "c1", ARGUMENTS)
            execute(token, True)
            execute(token, False)
        else:
            stale = prepare()
            changed = deepcopy(TOOL)
            changed["description"] = "Authorized revised transport fixture."
            publish(connection="c2", descriptor=changed)
            execute(stale, False)
            authorized = {"path": "authorized-new.txt"}
            expect("server-a", "c2", authorized)
            execute(prepare(arguments=authorized), True)
        check(writer_calls == len(expected), "writer called only for intended dispatches")
        check(len(receipts) == len(expected), "exact number of process receipts")
        for index, (receipt, approval) in enumerate(zip(receipts, expected)):
            response = receipt["response"]
            check(response.get("jsonrpc") == "2.0" and response.get("id") == 1,
                  f"receipt {index} response envelope")
            body = response.get("result", {}).get("structuredContent", {})
            check(receipt["trusted_server"] == approval["server"]
                  and receipt["trusted_connection"] == approval["connection"],
                  f"receipt {index} reached selected trusted connection")
            check(body.get("process_pid") == receipt["trusted_process_pid"],
                  f"receipt {index} returned by selected actual child")
            check(receipt["sent_payload_base64"] == approval["payload_base64"]
                  == body.get("received_payload_base64"),
                  f"receipt {index} exact approved bytes crossed process boundary")
            check(body.get("received_object") == json.loads(base64.b64decode(approval["payload_base64"])),
                  f"receipt {index} exact approved request object echoed")
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc),
                   "traceback": traceback.format_exc().replace(str(ROOT), "<package>")}
    finally:
        lifecycle = [connection.finish() for connection in connections]
    # EOF audit comes from the child, independently of gate statuses and writer
    # counts. Missing audit/unknown transport is a failed check, never safe denial.
    try:
        check(len(lifecycle) == 2, "both intended child processes were created")
        for child in lifecycle:
            check(child["clean_exit"], "child closed cleanly with independent EOF audit")
            wanted = [x for x in expected if (x["server"], x["connection"])
                      == (child["trusted_server"], child["trusted_connection"])]
            audit = child["audit"]
            check(audit["frames_received"] == len(wanted) == audit["supported_calls_received"],
                  "child independently received exactly its intended frame count")
            check(audit["received_payload_sha256"] == [hashlib.sha256(base64.b64decode(x["payload_base64"])).hexdigest()
                                                        for x in wanted],
                  "child EOF payload hashes match intended requests")
    except Exception as exc:
        if failure is None:
            failure = {"type": type(exc).__name__, "message": str(exc)}
    return {"case": name, "status": "passed" if failure is None else "failed",
            "expected_dispatches": expected, "writer_calls": writer_calls, "events": events,
            "receipts": receipts, "processes": lifecycle, "assertions": assertions, "failure": failure}


def run_checks(names=None, *, timeout: float = 3.0) -> dict:
    cases = [check_case(name, timeout=timeout) for name in (CASE_NAMES if names is None else names)]
    files = ("integration/stdio_sink.py", "integration/check_transport.py", "src/binding_gate/core.py")
    return {"schema_version": 1, "scope": "authored inert local subprocess JSON-RPC tools/call subset",
            "python": sys.version, "interpreter": Path(sys.executable).name,
            "source_sha256": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in files},
            "status": "passed" if all(c["status"] == "passed" for c in cases) else "failed",
            "case_count": len(cases), "passed_count": sum(c["status"] == "passed" for c in cases),
            "cases": cases,
            "limits": ["Authored transport fixture, not a full MCP implementation, SDK benchmark or certification.",
                       "No initialize/capability negotiation, notifications, cancellation or concurrent request routing.",
                       "Synchronous request/receipt occurs inside the gate writer; no production latency claim.",
                       "Only local host-assigned process identities are tested; no remote authentication or server attestation.",
                       "Default structural admission is used; semantic scanner behavior is outside this check.",
                       "The sink executes no tool and performs no argument-directed filesystem or network effects."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", choices=CASE_NAMES)
    parser.add_argument("--timeout", type=float, default=3.0, help="seconds per request/lifecycle boundary")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    result = run_checks(args.case, timeout=args.timeout)
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    raise SystemExit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
