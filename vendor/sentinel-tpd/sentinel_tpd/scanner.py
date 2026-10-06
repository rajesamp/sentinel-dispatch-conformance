"""Content-level scanner for MCP tool metadata.

scan_tool_metadata() takes a plain tool dict (name, description, inputSchema)
and returns a Verdict. The whole metadata tree — including every nested
schema `description` — is treated as untrusted text and matched against the
deterministic signal catalog.

Fail-closed: malformed metadata (non-dict, non-string name, unparseable
schema) is denied, not skipped.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field as dc_field
from typing import Any, Iterator

from .signals import DENY_AT, SCANNED_FIELDS, SIGNALS, Signal


@dataclass(frozen=True)
class Finding:
    """A single signal hit inside one metadata field."""

    signal_id: str
    severity: int
    field_path: str
    excerpt: str
    rationale: str


@dataclass(frozen=True)
class Verdict:
    """Outcome of scanning one tool's metadata."""

    tool_name: str
    allowed: bool
    max_severity: int
    findings: tuple[Finding, ...] = dc_field(default_factory=tuple)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "allowed": self.allowed,
            "max_severity": self.max_severity,
            "reason": self.reason,
            "findings": [
                {
                    "signal_id": f.signal_id,
                    "severity": f.severity,
                    "field_path": f.field_path,
                    "excerpt": f.excerpt,
                    "rationale": f.rationale,
                }
                for f in self.findings
            ],
        }


def _iter_text_fields(tool: dict[str, Any]) -> Iterator[tuple[str, str]]:
    """Yield (field_path, text) for every scannable string in the tool dict.

    Covers top-level fields plus every `description` (and `title`) nested
    anywhere inside the input schema — parameter-level descriptions are the
    primary poisoning carrier.
    """
    for f in SCANNED_FIELDS:
        value = tool.get(f)
        if isinstance(value, str):
            yield f, value

    schema = tool.get("inputSchema") or tool.get("input_schema") or {}

    def walk(node: Any, path: str) -> Iterator[tuple[str, str]]:
        if isinstance(node, dict):
            for key, value in node.items():
                child = f"{path}.{key}"
                if key in ("description", "title") and isinstance(value, str):
                    yield child, value
                else:
                    yield from walk(value, child)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                yield from walk(item, f"{path}[{i}]")

    yield from walk(schema, "inputSchema")


def _excerpt(text: str, start: int, end: int, radius: int = 40) -> str:
    lo = max(0, start - radius)
    hi = min(len(text), end + radius)
    return text[lo:hi].replace("\n", " ")


def canonical_metadata(tool: dict[str, Any]) -> str:
    """Deterministic JSON serialization of the fields that steer the model.

    Used by the registry to fingerprint metadata; sorted keys make the hash
    stable across dict ordering.
    """
    subset = {
        "name": tool.get("name"),
        "description": tool.get("description"),
        "inputSchema": tool.get("inputSchema") or tool.get("input_schema"),
    }
    return json.dumps(subset, sort_keys=True, ensure_ascii=True, default=str)


def scan_tool_metadata(
    tool: Any,
    *,
    deny_at: int = DENY_AT,
    signals: tuple[Signal, ...] = SIGNALS,
) -> Verdict:
    """Scan one tool's metadata. Deny at severity >= deny_at. Fail closed."""
    if not isinstance(tool, dict):
        return Verdict(
            tool_name="<invalid>",
            allowed=False,
            max_severity=4,
            reason="fail-closed: tool metadata is not a dict",
        )

    name = tool.get("name")
    if not isinstance(name, str) or not name.strip():
        return Verdict(
            tool_name="<unnamed>",
            allowed=False,
            max_severity=4,
            reason="fail-closed: missing or non-string tool name",
        )

    findings: list[Finding] = []
    for field_path, text in _iter_text_fields(tool):
        for sig in signals:
            for m in sig.pattern.finditer(text):
                findings.append(
                    Finding(
                        signal_id=sig.signal_id,
                        severity=sig.severity,
                        field_path=field_path,
                        excerpt=_excerpt(text, m.start(), m.end()),
                        rationale=sig.rationale,
                    )
                )

    max_sev = max((f.severity for f in findings), default=0)
    allowed = max_sev < deny_at
    reason = (
        "clean"
        if not findings
        else f"max severity M{max_sev} "
        + ("< deny threshold" if allowed else f">= M{deny_at}: DENY")
    )
    return Verdict(
        tool_name=name,
        allowed=allowed,
        max_severity=max_sev,
        findings=tuple(findings),
        reason=reason,
    )
