"""Offline replay and paired local microbenchmarks; never invokes a remote tool.

Run from the package root: python3 -m experiments.run_study --help
Approvals and receipts are copied outside the tested adapter. Timing and replay
are separate experiments. See research/run-protocol.md for exact boundaries.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import random
import sys
import time
import traceback
from typing import Any

from experiments.adapters import METHODS, semantic_admit
from experiments.oracle import check_receipt, decode_json, evaluate_receipts
from experiments.scenarios import BASE_ARGUMENTS, BASE_TOOL, apply_mutation, manifest

ROOT = Path(__file__).resolve().parents[1]
STAGES = ("after_select", "after_prepare", "after_execute")
ACTIONS = {"refresh", "begin_refresh", "complete_refresh", "mutate_args",
           "mutate_source", "reapprove", "execute_again"}
OPERATIONS = ("refresh_unchanged", "select", "prepare", "execute", "integration")


class InvalidScenario(ValueError):
    """A malformed trace must not silently become a successful defense."""


def canonical(value: Any) -> bytes:
    """Independent serialization for evidence, never a gate validator."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"encoding": "base64", "data": base64.b64encode(value).decode("ascii")}
    if is_dataclass(value):
        return jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(v) for v in value]
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidScenario(message)


def validate_case(case: dict) -> None:
    _require(type(case) is dict, "case must be an object")
    required = {"id", "family", "split", "kind", "initial_catalogs", "selection",
                "arguments", "operations", "expected_policy", "expected_receipt",
                "expected_dispatch_count", "notes"}
    _require(required <= case.keys(), "case missing required fields")
    for key in ("id", "family", "split", "kind"):
        _require(type(case[key]) is str and bool(case[key]), f"invalid {key}")
    _require(case["kind"] in {"benign", "challenge"}, "invalid case kind")
    _require(case["expected_policy"] in {"allow", "deny", "allow_once"}, "invalid policy")
    count = case["expected_dispatch_count"]
    _require(type(count) is int and count == (0 if case["expected_policy"] == "deny" else 1),
             "policy and expected dispatch count disagree")
    _require((case["expected_receipt"] is None) == (count == 0), "invalid expected receipt")
    if count:
        expected = case["expected_receipt"]
        _require(type(expected) is dict and
                 {"server", "connection", "descriptor", "request"} <= expected.keys(),
                 "incomplete expected receipt")
    selected = case["selection"]
    _require(type(selected) is dict and {"server", "name"} <= selected.keys(), "invalid selection")
    _require(all(type(selected[k]) is str and selected[k] for k in ("server", "name")),
             "invalid selection identity")
    _require(type(case["arguments"]) is dict, "arguments must be an object")
    _require(type(case["initial_catalogs"]) is list and bool(case["initial_catalogs"]),
             "initial catalogues must be a nonempty array")
    for item in case["initial_catalogs"]:
        _require(type(item) is dict and {"server", "connection", "tools"} <= item.keys(),
                 "invalid catalogue")
        _require(type(item["tools"]) is list, "catalogue tools must be an array")
        _require(all(type(item[k]) is str and item[k] for k in ("server", "connection")),
                 "invalid catalogue identity")
    _require(type(case["operations"]) is list, "operations must be an array")
    tags: dict[str, str] = {}
    completed: set[str] = set()
    for op in case["operations"]:
        _require(type(op) is dict and {"at", "action", "revokes_approval"} <= op.keys(),
                 "invalid operation")
        _require(op["at"] in STAGES and op["action"] in ACTIONS, "unknown stage or action")
        _require(type(op["revokes_approval"]) is bool, "revocation must be explicit boolean")
    # Validation follows execution order, not accidental cross-stage list order.
    for stage in STAGES:
        for op in (x for x in case["operations"] if x["at"] == stage):
            action = op["action"]
            if action in {"refresh", "begin_refresh", "complete_refresh"}:
                _require(type(op.get("server")) is str and bool(op["server"]), "missing server")
            if action in {"refresh", "complete_refresh"}:
                _require(type(op.get("tools")) is list and type(op.get("connection")) is str
                         and bool(op["connection"]), "invalid refresh payload")
            if action in {"begin_refresh", "complete_refresh"}:
                tag = op.get("tag")
                _require(type(tag) is str and bool(tag), "invalid refresh tag")
                if action == "begin_refresh":
                    _require(tag not in tags, "duplicate refresh tag")
                    tags[tag] = op["server"]
                else:
                    _require(tags.get(tag) == op["server"] and tag not in completed,
                             "refresh completion without matching uncompleted begin")
                    completed.add(tag)
            if action in {"mutate_args", "mutate_source"}:
                _require(type(op.get("path")) is list and bool(op["path"]) and "value" in op,
                         "invalid mutation")
                _require(all(type(k) in {str, int} for k in op["path"]), "invalid path key")
            if action == "mutate_source":
                for field in ("catalog_index", "tool_index"):
                    _require(type(op.get(field)) is int and op[field] >= 0, "invalid source index")
            if action == "reapprove":
                _require(stage == "after_prepare" and op.get("resets_revocation") is True,
                         "reapprove must explicitly reset after prepare")
            if action == "execute_again":
                _require(stage == "after_execute", "replay must follow default execution")
            if action not in {"refresh", "complete_refresh"}:
                _require(not op["revokes_approval"], "unsupported revocation action")
    try:
        canonical(case)
    except (ValueError, TypeError, UnicodeError) as exc:
        raise InvalidScenario("case must contain finite plain JSON") from exc


def validate_manifest(value: dict) -> None:
    _require(type(value) is dict and type(value.get("schema_version")) is int
             and value["schema_version"] == 1,
             "unsupported manifest schema")
    _require(type(value.get("request_id", 1)) is int and value.get("request_id", 1) == 1,
             "this runner supports fixture request ID 1 only")
    _require(type(value.get("cases")) is list and bool(value["cases"]), "manifest has no cases")
    ids = set()
    for case in value["cases"]:
        validate_case(case)
        _require(case["id"] not in ids, "duplicate case id: " + case["id"])
        ids.add(case["id"])


@dataclass(frozen=True)
class ExternalApproval:
    server: str
    connection: str
    descriptor_bytes: bytes
    request_bytes: bytes
    serial: int

    def record(self) -> dict:
        return asdict(self)


def capture_selection(view: Any) -> dict | None:
    if view is None:
        return None
    # Decode then independently reserialize: no shared gate hash/canonicalizer.
    return {"server": view.server, "connection": view.connection, "name": view.name,
            "descriptor_bytes": canonical(decode_json(view.descriptor))}


def run_case(case: dict, method: str) -> dict:
    """Replay one fresh arm. Return failures with all events retained."""
    validate_case(case)
    if method not in METHODS:
        raise ValueError("unknown method: " + method)
    fixture = deepcopy(case)
    adapter = None
    events: list[dict] = []
    receipts: list[dict] = []
    approvals: list[dict] = []
    revoked = False
    approval: ExternalApproval | None = None
    view = None
    selected_snapshot = None
    token = None
    refresh_tags: dict[str, Any] = {}
    approval_serial = 0
    reapproval_attempts = 0
    status = "completed"
    failure = None

    def event(action: str, **fields: Any) -> None:
        events.append({"sequence": len(events), "action": action, **fields})

    def select() -> None:
        nonlocal view, selected_snapshot
        target = fixture["selection"]
        view = adapter.select(target["server"], target["name"])
        selected_snapshot = capture_selection(view)
        event("selected", declared_selection=deepcopy(target), actual_selection=selected_snapshot)

    def prepare(*, reapproval: bool = False) -> None:
        nonlocal token, approval, approval_serial, revoked
        # Snapshot before giving the mutable argument dictionary to an adapter.
        intended = canonical({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                              "params": {"name": fixture["selection"]["name"],
                                         "arguments": fixture["arguments"]}})
        candidate = None
        if selected_snapshot is not None:
            approval_serial += 1
            candidate = ExternalApproval(selected_snapshot["server"],
                                         selected_snapshot["connection"],
                                         selected_snapshot["descriptor_bytes"], intended,
                                         approval_serial)
        token = adapter.prepare(view, fixture["arguments"])
        approval = candidate if token is not None else None
        if approval is not None:
            approvals.append(approval.record())
            if reapproval:
                revoked = False
        event("prepared", has_token=token is not None,
              approval=None if approval is None else approval.record(),
              revoked=revoked, reapproval=reapproval)

    def sink(server: str, connection: str, request: bytes, descriptor: bytes) -> int:
        # The sink does not call the method's validity, status or audit APIs.
        receipt = {"server": deepcopy(server), "connection": deepcopy(connection),
                   "request_bytes": bytes(request), "descriptor_bytes": bytes(descriptor),
                   "approval": None if approval is None else approval.record(),
                   "revoked_at_dispatch": revoked, "enqueue_sequence": len(events)}
        receipts.append(receipt)
        event("enqueued", receipt=receipt)
        return len(receipts) - 1

    def execute(*, replay: bool = False) -> None:
        response = adapter.execute(token, sink)
        event("execute_returned", replay=replay, allowed=response.allowed,
              reason=response.reason, receipt=response.receipt)
        if response.reason == "transport outcome unknown":
            raise RuntimeError("method reported unknown transport outcome")

    def operations(stage: str) -> None:
        nonlocal revoked, reapproval_attempts
        for index, op in enumerate(fixture["operations"]):
            if op["at"] != stage:
                continue
            action = op["action"]
            event("operation_started", operation_index=index, operation=deepcopy(op))
            response = None
            if action == "refresh":
                response = adapter.refresh(op["server"], op["tools"], op["connection"])
            elif action == "begin_refresh":
                refresh_tags[op["tag"]] = adapter.begin_refresh(op["server"])
                response = refresh_tags[op["tag"]]
            elif action == "complete_refresh":
                response = adapter.complete_refresh(op["server"], refresh_tags[op["tag"]],
                                                    op["tools"], op["connection"])
            elif action == "mutate_args":
                try:
                    apply_mutation(fixture["arguments"], op["path"], op["value"])
                except (KeyError, IndexError, TypeError) as exc:
                    raise InvalidScenario("unreachable argument mutation path") from exc
            elif action == "mutate_source":
                try:
                    source = fixture["initial_catalogs"][op["catalog_index"]]["tools"][op["tool_index"]]
                    apply_mutation(source, op["path"], op["value"])
                except (KeyError, IndexError, TypeError) as exc:
                    raise InvalidScenario("unreachable source mutation path") from exc
            elif action == "reapprove":
                reapproval_attempts += 1
                select()
                prepare(reapproval=True)
            elif action == "execute_again":
                execute(replay=True)
            # This is declared external policy, never the adapter's verdict.
            if op["revokes_approval"]:
                revoked = True
            event("operation_completed", operation_index=index, response=jsonable(response),
                  revoked=revoked)

    try:
        adapter = METHODS[method]()
        for item in fixture["initial_catalogs"]:
            response = adapter.refresh(item["server"], item["tools"], item["connection"])
            event("initial_publication", server=item["server"], connection=item["connection"],
                  tools=deepcopy(item["tools"]), response=jsonable(response))
        select()
        operations("after_select")
        prepare()
        operations("after_prepare")
        execute()
        operations("after_execute")
    except Exception as exc:
        status = "invalid_scenario" if isinstance(exc, InvalidScenario) else "execution_error"
        failure = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        event("failed", failure=failure)
    outcome = evaluate_receipts(None if approval is None else approval.record(), receipts,
                                revoked=revoked, expected_policy=case["expected_policy"],
                                expected_receipt=case["expected_receipt"],
                                expected_dispatch_count=case["expected_dispatch_count"])
    completed = status == "completed" and outcome["safe"] and outcome["policy_satisfied"]
    benign = case["kind"] == "benign"
    return {"record_type": "trial", "case_id": case["id"], "family": case["family"],
            "split": case["split"], "kind": case["kind"], "method": method,
            "case_sha256": digest(canonical(case)), "expected_policy": case["expected_policy"],
            "status": status, "failure": failure, "events": events, "approvals": approvals,
            "receipts": receipts, "outcome": outcome, "fully_satisfied": completed,
            "reapproval_attempts": reapproval_attempts,
            "benign_first_pass_completed": (completed and not reapproval_attempts) if benign else None,
            "benign_final_completed": completed if benign else None,
            "completion_scope": "local enqueue only; no remote tool completion"}


def source_hashes() -> dict[str, str]:
    files: set[Path] = set()
    for directory in ("experiments", "src", "tests", "vendor/sentinel-tpd"):
        files.update(p for p in (ROOT / directory).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix in {".py", ".toml"})
    files.update(ROOT / p for p in ("governance/spec.md", "research/evaluation-plan.md",
                                   "research/holdout-plan.md", "research/run-protocol.md",
                                   "vendor/manifest.json", "vendor/sentinel-tpd/LICENSE",
                                   "vendor/sentinel-tpd/README.md"))
    return {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(files) if p.is_file()}


def environment() -> dict:
    distributions = sorted(({"name": d.metadata.get("Name", "unknown"), "version": d.version}
                            for d in importlib.metadata.distributions()),
                           key=lambda x: (x["name"].lower(), x["version"]))
    clock = time.get_clock_info("perf_counter")
    vendor_file = ROOT / "vendor/manifest.json"
    vendor = json.loads(vendor_file.read_text())
    vendor_matches = all(digest((ROOT / "vendor/sentinel-tpd" / item["path"]).read_bytes())
                         == item["sha256"] for item in vendor["files"])
    if not vendor_matches:
        raise RuntimeError("vendored comparator differs from its pinned provenance manifest")
    return {"python": sys.version, "executable": Path(sys.executable).name, "platform": platform.platform(),
            "machine": platform.machine(), "processor": platform.processor(),
            "cpu_count": os.cpu_count(), "load_average": list(os.getloadavg()) if hasattr(os, "getloadavg") else None,
            "clock": {"implementation": clock.implementation, "monotonic": clock.monotonic,
                      "adjustable": clock.adjustable, "resolution_seconds": clock.resolution},
            "packages": distributions, "power_state": "not measured", "cpu_affinity": "not controlled",
            "background_load": "not controlled", "network": "no experiment network activity",
            "upstream_import": "vendor/sentinel-tpd/sentinel_tpd",
            "upstream_revision": vendor["revision"], "vendor_manifest_sha256": digest(vendor_file.read_bytes()),
            "vendor_files_match_manifest": vendor_matches,
            "scanner_configuration": "vendored default scan_tool_metadata(tool)"}


def _fixture_batch(method: str, operation: str, batch_size: int) -> list:
    calls = []
    for _ in range(batch_size):
        adapter = METHODS[method]()
        tool = deepcopy(BASE_TOOL)
        arguments = deepcopy(BASE_ARGUMENTS)
        if operation != "integration":
            admitted = adapter.refresh("server-a", [tool], "c1")
            if not admitted.accepted:
                raise RuntimeError("timing setup publication rejected")
        view = adapter.select("server-a", "read_file") if operation in {"prepare", "execute"} else None
        token = adapter.prepare(view, arguments) if operation == "execute" else None
        # Appending raw immutable bytes models only a synchronous local enqueue.
        sink_records = []
        def sink(server, connection, request, descriptor, records=sink_records):
            records.append((server, connection, request, descriptor))
            return len(records)
        if operation == "refresh_unchanged":
            call = lambda a=adapter, t=tool: a.refresh("server-a", [t], "c1")
        elif operation == "select":
            call = lambda a=adapter: a.select("server-a", "read_file")
        elif operation == "prepare":
            call = lambda a=adapter, v=view, args=arguments: a.prepare(v, args)
        elif operation == "execute":
            if token is None:
                raise RuntimeError("timing setup prepare rejected")
            call = lambda a=adapter, tok=token, writer=sink: a.execute(tok, writer)
        else:
            def call(a=adapter, t=tool, args=arguments, writer=sink):
                publication = a.refresh("server-a", [t], "c1")
                selection = a.select("server-a", "read_file")
                permit = a.prepare(selection, args)
                result = a.execute(permit, writer)
                return publication, result
        call.sink_records = sink_records
        calls.append(call)
    return calls


def _time_batch(calls: list) -> tuple[int, list]:
    results = [None] * len(calls)
    start = time.perf_counter_ns()
    for index, call in enumerate(calls):
        results[index] = call()
    elapsed = time.perf_counter_ns() - start
    return elapsed, results


def _validate_timing_results(operation: str, values: list, calls: list) -> None:
    for value, call in zip(values, calls):
        if operation == "refresh_unchanged":
            okay = value.accepted
        elif operation in {"select", "prepare"}:
            okay = value is not None
        elif operation == "execute":
            okay = value.allowed
        else:
            okay = value[0].accepted and value[1].allowed
        if not okay:
            raise RuntimeError("timing operation failed: " + operation)
        if operation in {"execute", "integration"}:
            expected = {"server": "server-a", "connection": "c1", "descriptor": BASE_TOOL,
                        "request": {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                    "params": {"name": "read_file", "arguments": BASE_ARGUMENTS}}}
            if len(call.sink_records) != 1:
                raise RuntimeError("timing sink did not receive exactly one request")
            server, connection, request, descriptor = call.sink_records[0]
            if check_receipt(expected, {"server": server, "connection": connection,
                                        "request_bytes": request, "descriptor_bytes": descriptor}):
                raise RuntimeError("timing sink received an unexpected operation")


def benchmark(*, methods: list[str], seed: int, warmups: int, repeats: int,
              batch_size: int, emit) -> None:
    """Seed randomizes paired method order; fixture preparation is never timed."""
    rng = random.Random(seed)
    for operation in OPERATIONS:
        for repeat in range(-warmups, repeats):
            order = list(methods)
            rng.shuffle(order)
            phase = "warmup" if repeat < 0 else "measured"
            for order_index, method in enumerate(order):
                record = {"record_type": "timing", "operation": operation, "method": method,
                          "phase": phase, "repeat": repeat, "pair_id": f"{operation}:{repeat}",
                          "method_order": order, "order_index": order_index, "batch_size": batch_size}
                try:
                    calls = _fixture_batch(method, operation, batch_size)
                    # Same Python call/loop shape, no subtraction in primary tables.
                    empty_calls = [lambda: None for _ in range(batch_size)]
                    empty_first = rng.choice((True, False))
                    if empty_first:
                        empty_elapsed, _ = _time_batch(empty_calls)
                    elapsed, results = _time_batch(calls)
                    if not empty_first:
                        empty_elapsed, _ = _time_batch(empty_calls)
                    record.update(status="completed", elapsed_ns=elapsed,
                                  empty_harness_elapsed_ns=empty_elapsed, empty_harness_first=empty_first,
                                  ns_per_operation=elapsed / batch_size,
                                  empty_harness_ns_per_operation=empty_elapsed / batch_size,
                                  paired_harness_adjusted_ns_per_operation=(elapsed - empty_elapsed) / batch_size)
                    _validate_timing_results(operation, results, calls)
                except Exception as exc:
                    record.update(status="execution_error", failure={"type": type(exc).__name__,
                                  "message": str(exc), "traceback": traceback.format_exc()})
                    emit(record)
                    raise
                emit(record)
    # The default scanner is identical across arms; time it independently once.
    for repeat in range(-warmups, repeats):
        record = {"record_type": "timing", "operation": "scanner_only", "method": "shared_scanner",
                  "phase": "warmup" if repeat < 0 else "measured", "repeat": repeat,
                  "pair_id": f"scanner_only:{repeat}", "batch_size": batch_size}
        try:
            tools = [deepcopy(BASE_TOOL) for _ in range(batch_size)]
            calls = [lambda tool=tool: semantic_admit(tool) for tool in tools]
            elapsed, decisions = _time_batch(calls)
            record.update(elapsed_ns=elapsed, ns_per_operation=elapsed / batch_size,
                          status="completed")
            if not all(decisions):
                raise RuntimeError("scanner timing fixture rejected")
        except Exception as exc:
            record.update(status="execution_error", failure={"type": type(exc).__name__,
                          "message": str(exc), "traceback": traceback.format_exc()})
            emit(record)
            raise
        emit(record)


def _write_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(jsonable(value), stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def run_study(output: Path, *, suite: dict, splits: list[str] | None = None,
              methods: list[str] | None = None, seed: int = 20261006,
              warmups: int = 20, repeats: int = 200, batch_size: int = 16,
              timing: bool = True, label: str = "development", manifest_source: str = "generator") -> dict:
    """Create a new evidence directory; all outputs use exclusive creation."""
    validate_manifest(suite)
    methods = list(METHODS) if methods is None else list(methods)
    if not methods or len(set(methods)) != len(methods) or any(m not in METHODS for m in methods):
        raise ValueError("methods must be unique known methods")
    if warmups < 0 or repeats < 1 or batch_size < 1:
        raise ValueError("warmups >= 0, repeats >= 1 and batch size >= 1 required")
    available_splits = {c["split"] for c in suite["cases"]}
    if splits and not set(splits) <= available_splits:
        raise ValueError("unknown split")
    cases = [c for c in suite["cases"] if not splits or c["split"] in splits]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    source_path = Path(manifest_source)
    if source_path.is_absolute():
        try:
            manifest_source = str(source_path.resolve().relative_to(ROOT))
        except ValueError:
            manifest_source = source_path.name
    code = source_hashes()
    env = environment()
    provenance = {"scenario_sha256": digest(canonical(suite)), "code_sha256": digest(canonical(code)),
                  "environment_sha256": digest(canonical(env))}
    metadata = {"schema_version": 1, "run_id": output.name, "started_at": started, "label": label,
                "manifest_source": manifest_source, "provenance": provenance,
                "code_files": code, "environment": env, "methods": methods,
                "splits": sorted({c["split"] for c in cases}), "manifest_case_count": len(suite["cases"]),
                "selected_case_count": len(cases), "families": dict(Counter(c["family"] for c in cases)),
                "expected_trial_count": len(cases) * len(methods), "seed": seed,
                "timing": {"enabled": timing, "warmup_pairs_per_operation": warmups,
                           "measured_pairs_per_operation": repeats, "batch_size": batch_size,
                           "operations": list(OPERATIONS) + ["scanner_only"],
                           "unit": "nanoseconds per operation = elapsed batch nanoseconds / batch size",
                           "process_sessions": 1, "concurrency": 1, "request_rate": "unpaced sequential",
                           "workload": "valid unchanged synthetic tool and arguments"},
                "verification_disclosure": "verification labels were visible during implementation; not blind",
                "scope": suite.get("scope", "finite synthetic suite"),
                "claims": "descriptive local evidence only; no statistical attack accuracy, memory or network claims"}
    _write_json(output / "metadata.json", metadata)
    _write_json(output / "manifest.json", suite)
    failures = 0
    trials = 0
    fatal = None
    with (output / "trials.jsonl").open("x", encoding="utf-8") as trial_file, \
            (output / "timings.jsonl").open("x", encoding="utf-8") as timing_file:
        def emit(stream, record):
            record = {"run_id": output.name, "provenance": provenance, **record}
            stream.write(json.dumps(jsonable(record), sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
        try:
            for case in cases:
                for method in methods:
                    result = run_case(case, method)
                    emit(trial_file, result)
                    trials += 1
                    failures += result["status"] != "completed"
                    if result["status"] == "invalid_scenario":
                        raise InvalidScenario(result["failure"]["message"])
            if timing:
                benchmark(methods=methods, seed=seed, warmups=warmups, repeats=repeats,
                          batch_size=batch_size, emit=lambda row: emit(timing_file, row))
        except Exception as exc:
            fatal = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    end_hashes = source_hashes()
    complete = {"finished_at": datetime.now(timezone.utc).isoformat(), "trial_count": trials,
                "execution_failures": failures, "fatal_error": fatal,
                "source_unchanged": code == end_hashes, "ending_code_sha256": digest(canonical(end_hashes)),
                "status": "completed" if not fatal and not failures and code == end_hashes else "failed",
                "output_sha256": {p.name: digest(p.read_bytes()) for p in sorted(output.iterdir()) if p.is_file()}}
    _write_json(output / "completion.json", complete)
    from experiments.report_results import write_report
    write_report(output)
    if complete["status"] != "completed":
        raise RuntimeError(f"run failed; retained evidence in {output}")
    return complete


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new directory; existing path is rejected")
    parser.add_argument("--manifest", type=Path, help="frozen schema-v1 manifest; default generated suite")
    parser.add_argument("--split", action="append", help="include only this split; repeatable; default all")
    parser.add_argument("--method", action="append", choices=list(METHODS), help="default all six methods")
    parser.add_argument("--seed", type=int, default=20261006)
    parser.add_argument("--warmups", type=int, default=20)
    parser.add_argument("--repeats", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--no-timing", action="store_true")
    parser.add_argument("--label", default="development", help="honest provenance label; never implies blinding")
    args = parser.parse_args()
    suite = decode_json(args.manifest.read_bytes()) if args.manifest else manifest()
    run_study(args.output, suite=suite, splits=args.split, methods=args.method, seed=args.seed,
              warmups=args.warmups, repeats=args.repeats, batch_size=args.batch_size,
              timing=not args.no_timing, label=args.label,
              manifest_source=str(args.manifest.resolve()) if args.manifest else "experiments.scenarios.manifest")
    print(str(args.output.resolve()))


if __name__ == "__main__":
    main()
