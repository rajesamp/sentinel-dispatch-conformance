"""TOOL_REGISTERED gate and call-time decision-path check.

Two enforcement points:

1. register(tool)        — scan metadata BEFORE the tool enters the model's
                           context. Deny => tool never registered.
2. check_invocation(...) — at call time, re-fingerprint the tool's current
                           metadata and diff it against the registered
                           fingerprint. Any mutation (rug pull) => deny and
                           quarantine; unknown tool => deny (default-deny).

Both paths append to the audit chain. Fail-closed throughout.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .audit import AuditChain
from .scanner import Verdict, canonical_metadata, scan_tool_metadata
from .signals import DENY_AT


def fingerprint(tool: dict[str, Any]) -> str:
    """SHA-256 over the canonical serialization of steering-relevant fields."""
    return hashlib.sha256(canonical_metadata(tool).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class InvocationDecision:
    tool_name: str
    allowed: bool
    reason: str


class ToolRegistry:
    """Holds fingerprints of tools that passed the TOOL_REGISTERED gate."""

    def __init__(
        self,
        *,
        audit: AuditChain | None = None,
        deny_at: int = DENY_AT,
    ) -> None:
        self._fingerprints: dict[str, str] = {}
        self._quarantined: set[str] = set()
        self._audit = audit if audit is not None else AuditChain()
        self._deny_at = deny_at

    # -- gate 1: registration ------------------------------------------------

    def register(self, tool: dict[str, Any]) -> Verdict:
        """Scan and (only if clean) admit a tool. Returns the Verdict."""
        verdict = scan_tool_metadata(tool, deny_at=self._deny_at)
        event = "TOOL_REGISTERED" if verdict.allowed else "TOOL_DENIED"
        self._audit.append(event, verdict.to_dict())
        if verdict.allowed:
            self._fingerprints[verdict.tool_name] = fingerprint(tool)
        return verdict

    # -- gate 2: invocation --------------------------------------------------

    def check_invocation(self, tool: dict[str, Any]) -> InvocationDecision:
        """Call-time check: known tool, unmutated metadata, not quarantined."""
        name = tool.get("name") if isinstance(tool, dict) else None
        if not isinstance(name, str) or not name.strip():
            decision = InvocationDecision(
                "<unnamed>", False, "fail-closed: invalid tool at invocation"
            )
            self._audit.append("INVOCATION_DENIED", decision.__dict__)
            return decision

        if name in self._quarantined:
            decision = InvocationDecision(
                name, False, "denied: tool is quarantined after prior mutation"
            )
            self._audit.append("INVOCATION_DENIED", decision.__dict__)
            return decision

        registered = self._fingerprints.get(name)
        if registered is None:
            decision = InvocationDecision(
                name, False, "default-deny: tool was never registered"
            )
            self._audit.append("INVOCATION_DENIED", decision.__dict__)
            return decision

        current = fingerprint(tool)
        if current != registered:
            # Rug pull: metadata changed between registration and call.
            self._quarantined.add(name)
            del self._fingerprints[name]
            decision = InvocationDecision(
                name,
                False,
                "denied: metadata mutated since registration (rug pull); "
                "tool quarantined — must be re-scanned and re-registered",
            )
            self._audit.append(
                "TOOL_MUTATION_DETECTED",
                {
                    "tool_name": name,
                    "registered_fingerprint": registered,
                    "observed_fingerprint": current,
                },
            )
            self._audit.append("INVOCATION_DENIED", decision.__dict__)
            return decision

        decision = InvocationDecision(name, True, "allowed: fingerprint match")
        self._audit.append("INVOCATION_ALLOWED", decision.__dict__)
        return decision

    # -- refresh handling ----------------------------------------------------

    def rescan_on_refresh(self, tools: list[dict[str, Any]]) -> list[Verdict]:
        """Re-run the registration gate on a tools/list refresh.

        Tools absent from the new list are dropped (their fingerprints are
        removed). Quarantine survives refresh: a tool caught mutating must
        pass a clean scan to leave quarantine.
        """
        self._audit.append("TOOLS_LIST_REFRESH", {"count": len(tools)})
        self._fingerprints.clear()
        verdicts = []
        for tool in tools:
            v = self.register(tool)
            if v.allowed and v.tool_name in self._quarantined:
                self._quarantined.discard(v.tool_name)
                self._audit.append(
                    "QUARANTINE_LIFTED", {"tool_name": v.tool_name}
                )
            verdicts.append(v)
        return verdicts

    # -- introspection -------------------------------------------------------

    @property
    def audit(self) -> AuditChain:
        return self._audit

    def is_registered(self, name: str) -> bool:
        return name in self._fingerprints

    def is_quarantined(self, name: str) -> bool:
        return name in self._quarantined
