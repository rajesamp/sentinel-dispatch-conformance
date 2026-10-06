"""Reference host boundary; not remote attestation or a semantic defense.

The trusted writer must use the supplied connection and request bytes directly.
It must not resolve tool names again or re-enter this gate. The lock spans the
writer call; production transports should enqueue under this lock and await a
response separately. No claim is made about undetected remote code changes.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
import secrets
import threading
from typing import Callable, Any


class InvalidDefinition(ValueError):
    pass


def freeze_json(value: Any, *, max_bytes: int = 262144) -> bytes:
    """Copy and validate in one traversal; serialize only the detached copy.

    This is a restricted Python JSON canonicalization, not RFC 8785 JCS.
    Python finite-number encoding is used consistently within this artifact.
    """
    active: set[int] = set()
    count = 0

    def copy(node: Any, depth: int = 0) -> Any:
        nonlocal count
        count += 1
        if depth > 32 or count > 20000:
            raise InvalidDefinition("JSON nesting/node limit")
        kind = type(node)
        if node is None or kind in (bool, int):
            return node
        if kind is str:
            try:
                node.encode("utf-8")
            except UnicodeError as exc:
                raise InvalidDefinition("invalid Unicode scalar") from exc
            return node
        if kind is float:
            if not math.isfinite(node):
                raise InvalidDefinition("non-finite number")
            return node
        if kind not in (dict, list):
            raise InvalidDefinition("not plain JSON")
        ident = id(node)
        if ident in active:
            raise InvalidDefinition("cyclic JSON")
        active.add(ident)
        try:
            if kind is list:
                return [copy(v, depth + 1) for v in node]
            if any(type(k) is not str for k in node):
                raise InvalidDefinition("non-string JSON key")
            return {copy(k, depth + 1): copy(v, depth + 1) for k, v in node.items()}
        finally:
            active.remove(ident)

    try:
        out = json.dumps(copy(value), sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (RuntimeError, TypeError, ValueError, OverflowError, UnicodeError) as exc:
        raise InvalidDefinition(str(exc)) from exc
    if len(out) > max_bytes:
        raise InvalidDefinition("JSON byte limit")
    return out


def descriptor_bytes(tool: Any) -> bytes:
    """Validate the fixed subset used by this study, preserving all JSON fields.

    Not a complete JSON Schema 2020-12 validator. The top-level name/schema
    requirements and shapes of common MCP metadata fields are checked.
    """
    raw = freeze_json(tool)
    data = json.loads(raw)
    if type(data) is not dict:
        raise InvalidDefinition("descriptor must be object")
    name = data.get("name")
    if type(name) is not str or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", name):
        raise InvalidDefinition("invalid tool name")
    schema = data.get("inputSchema")
    if type(schema) is not dict:
        raise InvalidDefinition("inputSchema must be object")
    if "input_schema" in data:
        raise InvalidDefinition("ambiguous non-protocol schema alias")
    if schema.get("type", "object") != "object":
        raise InvalidDefinition("input root type must be object")
    if "properties" in schema and type(schema["properties"]) is not dict:
        raise InvalidDefinition("properties must be object")
    if "required" in schema and (
        type(schema["required"]) is not list or
        any(type(x) is not str for x in schema["required"])
    ):
        raise InvalidDefinition("required must be string array")
    for key in ("description", "title"):
        if key in data and type(data[key]) is not str:
            raise InvalidDefinition(key + " must be string")
    for key in ("annotations", "outputSchema", "execution", "_meta"):
        if key in data and type(data[key]) is not dict:
            raise InvalidDefinition(key + " must be object")
    if "icons" in data and type(data["icons"]) is not list:
        raise InvalidDefinition("icons must be array")
    return raw


@dataclass(frozen=True)
class Selection:
    server: str
    name: str
    generation: int
    connection: str
    descriptor: bytes
    catalog_epoch: int


@dataclass(frozen=True)
class RefreshResult:
    accepted: bool
    reason: str
    count: int


@dataclass(frozen=True)
class DispatchResult:
    allowed: bool
    reason: str
    receipt: Any = None


@dataclass(frozen=True)
class _Prepared:
    selection: Selection
    request: bytes


class BindingGate:
    """Trusted-host reference gate with per-binding generations.

    Server and connection IDs are assigned by the host, not server metadata.
    Selection and prepare happen after the host's policy decision. The default
    admission callback validates structure only; it does not approve user intent.
    """
    def __init__(self, admit: Callable[[dict], bool] | None = None,
                 *, global_epoch: bool = False):
        self._lock = threading.Lock()
        self._bindings: dict[tuple[str, str], Selection] = {}
        self._versions: dict[tuple[str, str], int] = {}
        self._issued: dict[str, int] = {}
        self._completed: dict[str, int] = {}
        self._pending: dict[str, _Prepared] = {}
        self._epoch = 0
        self._admit = admit or (lambda tool: True)
        self._global_epoch = global_epoch
        self.audit: list[dict] = []

    def _log(self, action: str, **fields: Any) -> None:
        self.audit.append({"index": len(self.audit), "action": action, **fields})

    def begin_refresh(self, server: str) -> int:
        if type(server) is not str or not server:
            raise InvalidDefinition("host server ID required")
        with self._lock:
            revision = self._issued.get(server, 0) + 1
            self._issued[server] = revision
            self._log("refresh_requested", server=server, revision=revision)
            return revision

    def _withdraw(self, server: str) -> None:
        for key in list(self._bindings):
            if key[0] == server:
                self._versions[key] = self._versions.get(key, 0) + 1
                del self._bindings[key]

    def complete_refresh(self, server: str, revision: int, tools: Any,
                         connection: str = "connection-1") -> RefreshResult:
        staged: dict[str, bytes] = {}
        error = ""
        try:
            if type(connection) is not str or not connection:
                raise InvalidDefinition("host connection ID required")
            if type(tools) is not list or len(tools) > 10000:
                raise InvalidDefinition("catalog must be bounded array")
            for tool in tools:
                raw = descriptor_bytes(tool)
                parsed = json.loads(raw)
                name = parsed["name"]
                if name in staged:
                    raise InvalidDefinition("duplicate name within server")
                # The callback may inspect or mutate its detached input. Publish
                # the validated snapshot and its original identity in either case.
                if not self._admit(parsed):
                    raise InvalidDefinition("admission policy denied descriptor")
                staged[name] = raw
        except Exception as exc:
            error = type(exc).__name__ + ": " + str(exc)
        with self._lock:
            if (type(revision) is not int or revision != self._issued.get(server)
                    or revision <= self._completed.get(server, 0)):
                self._log("refresh_stale", server=server, revision=revision)
                return RefreshResult(False, "stale refresh completion", 0)
            self._completed[server] = revision
            self._epoch += 1
            if error:
                self._withdraw(server)
                self._log("refresh_denied", server=server, reason=error)
                return RefreshResult(False, error, 0)
            for key in list(self._bindings):
                if key[0] == server and key[1] not in staged:
                    self._versions[key] = self._versions.get(key, 0) + 1
                    del self._bindings[key]
            for name, raw in staged.items():
                key = (server, name)
                old = self._bindings.get(key)
                if old is None or old.descriptor != raw or old.connection != connection:
                    self._versions[key] = self._versions.get(key, 0) + 1
                self._bindings[key] = Selection(server, name, self._versions[key],
                                                connection, raw, self._epoch)
            self._log("refresh_published", server=server, revision=revision,
                      count=len(staged))
            return RefreshResult(True, "published", len(staged))

    def refresh(self, server: str, tools: Any,
                connection: str = "connection-1") -> RefreshResult:
        return self.complete_refresh(server, self.begin_refresh(server), tools, connection)

    def select(self, server: str, name: str) -> Selection | None:
        with self._lock:
            return self._bindings.get((server, name))

    def _valid(self, view: Selection) -> bool:
        current = self._bindings.get((view.server, view.name))
        if current is None:
            return False
        return (
            current.generation == view.generation and
            current.connection == view.connection and
            current.descriptor == view.descriptor and
            (not self._global_epoch or view.catalog_epoch == self._epoch)
        )

    def prepare(self, view: Selection, arguments: dict) -> str | None:
        if type(view) is not Selection:
            return None
        try:
            args = json.loads(freeze_json(arguments))
            if type(args) is not dict:
                raise InvalidDefinition("arguments must be object")
            request = freeze_json({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                   "params": {"name": view.name, "arguments": args}})
        except InvalidDefinition:
            return None
        with self._lock:
            if not self._valid(view):
                self._log("prepare_denied", server=view.server, name=view.name)
                return None
            token = secrets.token_hex(16)
            self._pending[token] = _Prepared(view, request)
            self._log("prepared", server=view.server, name=view.name,
                      request_sha256=hashlib.sha256(request).hexdigest())
            return token

    def execute(self, token: str, writer: Callable[[str, str, bytes, bytes], Any]
                ) -> DispatchResult:
        """Consume once, validate binding, send frozen bytes while serialized."""
        with self._lock:
            pending = self._pending.pop(token, None) if type(token) is str else None
            if pending is None:
                self._log("dispatch_denied", reason="unknown or consumed permit")
                return DispatchResult(False, "unknown or consumed permit")
            view = pending.selection
            if not self._valid(view):
                self._log("dispatch_denied", reason="binding changed", server=view.server)
                return DispatchResult(False, "binding changed")
            try:
                receipt = writer(view.server, view.connection,
                                 pending.request, view.descriptor)
            except Exception as exc:
                self._log("dispatch_error", reason=type(exc).__name__, server=view.server)
                # The writer may have sent before it failed: outcome is not a safe deny.
                return DispatchResult(False, "transport outcome unknown", None)
            self._log("dispatched", server=view.server, name=view.name)
            return DispatchResult(True, "dispatched frozen request", receipt)
