"""Inert, authored JSON-RPC tools/call subprocess fixture; not an MCP server.

stdin/stdout carry newline-delimited JSON. EOF produces a compact audit record on
stderr, so the parent can independently check that a denied call sent no frame.
No supplied tool name or argument is executed or used for a filesystem/network
operation. Only the fixed read_file fixture name is accepted.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sys

MAX_FRAME_BYTES = 1_048_576


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _constant(value):
    raise ValueError("nonfinite number")


def response_for(payload: bytes) -> tuple[dict, bool]:
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError):
        return {"jsonrpc": "2.0", "id": None,
                "error": {"code": -32700, "message": "Invalid fixture JSON"}}, False
    identifier = value.get("id") if type(value) is dict else None
    if (type(value) is not dict or value.get("jsonrpc") != "2.0"
            or type(identifier) not in (int, str) or type(value.get("method")) is not str):
        return {"jsonrpc": "2.0", "id": None,
                "error": {"code": -32600, "message": "Unsupported request envelope"}}, False
    if value["method"] != "tools/call":
        return {"jsonrpc": "2.0", "id": identifier,
                "error": {"code": -32601, "message": "Only tools/call is supported"}}, False
    params = value.get("params")
    if (type(params) is not dict or params.get("name") != "read_file"
            or type(params.get("arguments")) is not dict):
        return {"jsonrpc": "2.0", "id": identifier,
                "error": {"code": -32602, "message": "Unsupported fixture parameters"}}, False
    return {"jsonrpc": "2.0", "id": identifier, "result": {
        "content": [{"type": "text", "text": "Inert local transport receipt."}],
        "structuredContent": {"received_object": value,
                              "received_payload_base64": base64.b64encode(payload).decode("ascii"),
                              "process_pid": os.getpid()}, "isError": False}}, True


def main() -> None:
    frames = 0
    calls = 0
    payload_hashes = []
    try:
        while True:
            line = sys.stdin.buffer.readline(MAX_FRAME_BYTES + 1)
            if not line:
                break
            frames += 1
            payload = line[:-1] if line.endswith(b"\n") else line
            payload_hashes.append(hashlib.sha256(payload).hexdigest())
            if len(line) > MAX_FRAME_BYTES or not line.endswith(b"\n"):
                response = {"jsonrpc": "2.0", "id": None,
                            "error": {"code": -32600, "message": "Invalid fixture frame"}}
                supported = False
            else:
                response, supported = response_for(payload)
            calls += supported
            sys.stdout.buffer.write(json.dumps(response, ensure_ascii=False, allow_nan=False,
                                                separators=(",", ":")).encode("utf-8") + b"\n")
            sys.stdout.buffer.flush()
            if len(line) > MAX_FRAME_BYTES:
                break
    finally:
        audit = {"fixture_event": "stdin_closed", "process_pid": os.getpid(),
                 "frames_received": frames, "supported_calls_received": calls,
                 "received_payload_sha256": payload_hashes}
        sys.stderr.write(json.dumps(audit, separators=(",", ":")) + "\n")
        sys.stderr.flush()


if __name__ == "__main__":
    main()
