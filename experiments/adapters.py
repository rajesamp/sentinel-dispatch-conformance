"""Explicit study adapters. Authored adapters are not external products.

All semantic decisions use the same pinned Sentinel TPD scan function.
Scored claims about wrappers must not be attributed to upstream alone.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import secrets
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "sentinel-tpd"))
sys.path.insert(0, str(ROOT / "src"))
from sentinel_tpd import ToolRegistry
from sentinel_tpd.scanner import scan_tool_metadata, canonical_metadata
from binding_gate.core import (BindingGate, RefreshResult, DispatchResult,
                               descriptor_bytes, freeze_json)


def semantic_admit(tool):
    return scan_tool_metadata(tool).allowed


@dataclass(frozen=True)
class View:
    server: str
    name: str
    connection: str
    descriptor: bytes


class SnapshotAdapter:
    """Conventional strong comparison implemented independently of BindingGate.

    covered: upstream fingerprint projection with per-server registry.
    full_hash: complete descriptor equality, but no observed-revocation memory.
    revoke: complete descriptor equality plus immutable view identity; replacing
    a view makes all old authorizations invalid even if bytes are later restored.
    """
    def __init__(self, mode="revoke"):
        self.mode = mode
        self.lock = threading.Lock()
        self.views = {}
        self.registries = {}
        self.issued = {}
        self.completed = {}
        self.pending = {}
        self.audit = []

    def begin_refresh(self, server):
        with self.lock:
            self.issued[server] = self.issued.get(server, 0) + 1
            return self.issued[server]

    def complete_refresh(self, server, revision, tools, connection="c1"):
        staged = {}
        registry = ToolRegistry()
        error = ""
        try:
            if type(tools) is not list:
                raise ValueError("catalog shape")
            for tool in tools:
                # covered keeps upstream's documented validation/projection scope.
                raw = (freeze_json(tool) if self.mode == "covered"
                       else descriptor_bytes(tool))
                detached = json.loads(raw)
                if not registry.register(detached).allowed:
                    raise ValueError("scanner denial")
                name = detached["name"]
                if name in staged:
                    raise ValueError("duplicate name")
                staged[name] = View(server, name, connection, raw)
        except Exception as exc:
            error = type(exc).__name__
        with self.lock:
            if (revision != self.issued.get(server)
                    or revision <= self.completed.get(server, 0)):
                return RefreshResult(False, "stale refresh", 0)
            self.completed[server] = revision
            if error:
                self.views = {k: v for k, v in self.views.items() if k[0] != server}
                self.registries.pop(server, None)
                return RefreshResult(False, error, 0)
            published = {k: v for k, v in self.views.items() if k[0] != server}
            for name, view in staged.items():
                old = self.views.get((server, name))
                # Preserve identity across semantically identical host snapshots.
                if old == view:
                    view = old
                published[(server, name)] = view
            self.views = published
            self.registries[server] = registry
            return RefreshResult(True, "published", len(staged))

    def refresh(self, server, tools, connection="c1"):
        return self.complete_refresh(server, self.begin_refresh(server), tools, connection)

    def select(self, server, name):
        with self.lock:
            return self.views.get((server, name))

    def valid(self, view):
        current = self.views.get((view.server, view.name))
        if current is None or current.connection != view.connection:
            return False
        if self.mode == "revoke":
            return current is view
        if self.mode == "full_hash":
            return current.descriptor == view.descriptor
        projection_same = (
            canonical_metadata(json.loads(current.descriptor)) ==
            canonical_metadata(json.loads(view.descriptor))
        )
        return projection_same and self.registries[view.server].check_invocation(
            json.loads(current.descriptor)).allowed

    def prepare(self, view, arguments):
        if view is None:
            return None
        try:
            raw = freeze_json({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                               "params": {"name": view.name, "arguments": arguments}})
            if type(json.loads(raw)["params"]["arguments"]) is not dict:
                return None
        except Exception:
            return None
        with self.lock:
            if not self.valid(view):
                return None
            token = secrets.token_hex(16)
            self.pending[token] = (view, raw)
            return token

    def execute(self, token, writer):
        with self.lock:
            pending = self.pending.pop(token, None) if type(token) is str else None
            if pending is None or not self.valid(pending[0]):
                return DispatchResult(False, "invalid or stale")
            view, request = pending
            current = self.views[(view.server, view.name)]
            try:
                receipt = writer(view.server, view.connection, request, current.descriptor)
            except Exception:
                return DispatchResult(False, "transport outcome unknown")
            return DispatchResult(True, "dispatched snapshot", receipt)


class NaiveAdapter:
    """Deliberately weak integration control, never claimed upstream native API."""
    def __init__(self):
        self.registry = ToolRegistry()
        self.catalogs = {}
        self.connections = {}
        self.route = {}
        self.pending = {}
        self.issued = {}
        self.audit = []

    def begin_refresh(self, server):
        self.issued[server] = self.issued.get(server, 0) + 1
        return self.issued[server]

    def complete_refresh(self, server, revision, tools, connection="c1"):
        self.catalogs[server] = tools
        self.connections[server] = connection
        self.route = {n: s for n, s in self.route.items() if s != server}
        try:
            for t in tools:
                if self.registry.register(t).allowed:
                    self.route[t["name"]] = server
            return RefreshResult(True, "incremental publication", len(tools))
        except Exception:
            return RefreshResult(False, "publication error", 0)

    def refresh(self, server, tools, connection="c1"):
        return self.complete_refresh(server, self.begin_refresh(server), tools, connection)

    def current(self, server, name):
        return next((x for x in self.catalogs.get(server, []) if x.get("name") == name), None)

    def select(self, server, name):
        tool = self.current(server, name)
        if tool is None:
            return None
        return View(server, name, self.connections[server], freeze_json(tool))

    def prepare(self, view, arguments):
        if view is None:
            return None
        tool = self.current(view.server, view.name)
        try:
            if not self.registry.check_invocation(tool).allowed:
                return None
        except Exception:
            return None
        token = secrets.token_hex(16)
        self.pending[token] = (view.name, arguments)
        return token

    def execute(self, token, writer):
        pending = self.pending.pop(token, None) if type(token) is str else None
        if pending is None:
            return DispatchResult(False, "missing permit")
        name, arguments = pending
        server = self.route.get(name)
        if server is None:
            return DispatchResult(False, "route missing")
        try:
            tool = self.current(server, name)
            request = freeze_json({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                   "params": {"name": name, "arguments": arguments}})
            receipt = writer(server, self.connections[server], request, freeze_json(tool))
        except Exception:
            return DispatchResult(False, "transport outcome unknown")
        return DispatchResult(True, "dispatched via mutable name route", receipt)


METHODS = {
    "naive_host": lambda: NaiveAdapter(),
    "scoped_upstream": lambda: SnapshotAdapter("covered"),
    "snapshot_hash": lambda: SnapshotAdapter("full_hash"),
    "snapshot_revocation": lambda: SnapshotAdapter("revoke"),
    "binding_gate": lambda: BindingGate(admit=semantic_admit),
    "global_epoch": lambda: BindingGate(admit=semantic_admit, global_epoch=True),
}
