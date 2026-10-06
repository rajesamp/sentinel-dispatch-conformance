"""Signal definitions for tool-metadata scanning.

Tool descriptions and schemas are Layer-4 UNTRUSTED input the moment they are
registered (Huang et al., arXiv MCP threat modeling: tool poisoning DREAD
46.5/50, highest client-side threat). Each signal is a deterministic,
auditable pattern — no model in the loop.

Severity tiers (M0-M4):
    M0  informational
    M1  low        — style smell, log only
    M2  medium     — suspicious, log + warn
    M3  high       — default-deny
    M4  critical   — deny, never overridable
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Signal:
    """One detection pattern applied to tool metadata text."""

    signal_id: str
    severity: int  # 0..4 == M0..M4
    rationale: str
    pattern: re.Pattern = field(repr=False)


def _s(signal_id: str, severity: int, rationale: str, regex: str) -> Signal:
    return Signal(
        signal_id=signal_id,
        severity=severity,
        rationale=rationale,
        pattern=re.compile(regex, re.IGNORECASE | re.DOTALL),
    )


# ---------------------------------------------------------------------------
# Signal catalog
#
# Grouped by the tool-poisoning tactics observed in the wild and in the
# Huang et al. threat model. Patterns intentionally favor precision over
# recall for M3/M4 (a deny must be explainable); M1/M2 may be noisier.
# ---------------------------------------------------------------------------

SIGNALS: tuple[Signal, ...] = (
    # -- Imperative instruction markup smuggled into descriptions -----------
    _s(
        "TPD-IMPERATIVE-TAG",
        4,
        "Instruction-style markup (<IMPORTANT>, <system>, [INST]) inside tool "
        "metadata: classic tool-poisoning carrier addressing the model, not "
        "the human.",
        r"<\s*(important|system|instructions?|inst|admin|hidden)\b[^>]*>"
        r"|\[\s*(inst|system)\s*\]",
    ),
    _s(
        "TPD-DIRECT-MODEL-ADDRESS",
        3,
        "Metadata directly addresses the assistant/model with an imperative "
        "(e.g. 'you must', 'the assistant should', 'ignore previous').",
        r"\b(you\s+(must|should|will|are\s+required)|the\s+(assistant|model|ai)"
        r"\s+(must|should|will)|ignore\s+(all\s+)?(previous|prior|above))\b",
    ),
    # -- Concealment / secrecy instructions ---------------------------------
    _s(
        "TPD-CONCEALMENT",
        4,
        "Instructs the model to hide behavior from the user ('do not tell', "
        "'do not mention', 'without informing'). Legitimate tool docs never "
        "need secrecy from the operator.",
        r"\b(do\s*n[o']t\s+(tell|mention|inform|reveal|show|disclose)|"
        r"without\s+(telling|informing|notifying|alerting)|"
        r"keep\s+(this|it)\s+(secret|hidden)|never\s+(mention|reveal|disclose))\b",
    ),
    # -- Priority / hierarchy claims -----------------------------------------
    _s(
        "TPD-PRIORITY-CLAIM",
        3,
        "Claims elevated priority over system/user instructions ('overrides "
        "all other instructions', 'highest priority', 'takes precedence').",
        r"\b(overrides?\s+(all|any|other|previous)|highest\s+priority|"
        r"takes?\s+precedence|supersedes?\s+(all|any)|"
        r"before\s+(doing|using)\s+anything\s+else)\b",
    ),
    # -- Sensitive path / secret references ----------------------------------
    _s(
        "TPD-SENSITIVE-PATH",
        3,
        "References credential stores or secret material a tool description "
        "has no business naming (~/.ssh, id_rsa, .env, .aws/credentials, "
        "private keys, API keys, seed phrases).",
        r"(~?/?\.(ssh|aws|env|netrc|gnupg)\b|id_rsa|id_ed25519|"
        r"\b(private\s+key|api[_\s-]?key|access\s+token|seed\s+phrase|"
        r"mnemonic|credentials?\s+file)\b)",
    ),
    # -- Cross-tool behavior steering ----------------------------------------
    _s(
        "TPD-CROSS-TOOL-STEER",
        3,
        "Attempts to modify how OTHER tools are used ('when using any other "
        "tool', 'for every subsequent call', 'all future requests') — "
        "cross-tool shadowing attack.",
        r"\b(when\s+(you\s+)?(use|call|invoke)\s+(any\s+)?other\s+tools?|"
        r"(for|in|on)\s+(every|all)\s+(subsequent|future|other)\s+"
        r"(calls?|requests?|messages?|responses?))\b",
    ),
    # -- Parameter smuggling --------------------------------------------------
    _s(
        "TPD-PARAM-SMUGGLE",
        3,
        "Schema parameter description instructs the model to populate the "
        "field with data from elsewhere in the conversation/context rather "
        "than a value the task requires.",
        r"\b(pass|include|copy|insert|put)\s+(the\s+)?(entire|full|whole|all)?"
        r"\s*(conversation|chat\s+history|context|system\s+prompt|previous\s+"
        r"messages?)\b",
    ),
    # -- Exfiltration verbs paired with external destinations -----------------
    _s(
        "TPD-EXFIL-DEST",
        4,
        "Instructs sending data to an embedded external destination "
        "(send/post/forward + URL or email inside metadata).",
        r"\b(send|post|forward|upload|transmit|email)\b[^.\n]{0,80}"
        r"(https?://|[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})",
    ),
    # -- Encoded payload smells ----------------------------------------------
    _s(
        "TPD-ENCODED-BLOB",
        2,
        "Long base64-like blob embedded in metadata: possible encoded "
        "instruction payload. Medium severity — legitimate tools rarely need "
        "this, but false positives exist (e.g. embedded examples).",
        r"[A-Za-z0-9+/]{120,}={0,2}",
    ),
    # -- Urgency / social pressure -------------------------------------------
    _s(
        "TPD-URGENCY",
        1,
        "Urgency or consequence framing aimed at the model ('immediately or "
        "the user will be harmed', 'critical: failure to comply'). Weak "
        "signal alone; escalates real attacks when combined.",
        r"\b(failure\s+to\s+comply|or\s+the\s+user\s+will|immediately\s+or|"
        r"consequences\s+will\s+be\s+severe)\b",
    ),
)

# Fields of a tool definition that are scanned as untrusted text.
SCANNED_FIELDS: tuple[str, ...] = ("name", "description")

# Default enforcement threshold: severity >= DENY_AT is denied.
DENY_AT: int = 3
