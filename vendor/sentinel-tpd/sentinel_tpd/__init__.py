"""SENTINEL-TPD — content-level trust gate for MCP tool metadata.

Tool descriptions and schemas are untrusted input. Scan at TOOL_REGISTERED,
fingerprint what was admitted, and deny at call time if the metadata mutated.
"""

from .audit import AuditChain
from .registry import InvocationDecision, ToolRegistry, fingerprint
from .scanner import Finding, Verdict, scan_tool_metadata
from .signals import DENY_AT, SIGNALS, Signal

__version__ = "2026.8.0"

__all__ = [
    "AuditChain",
    "DENY_AT",
    "Finding",
    "InvocationDecision",
    "SIGNALS",
    "Signal",
    "ToolRegistry",
    "Verdict",
    "fingerprint",
    "scan_tool_metadata",
    "__version__",
]
