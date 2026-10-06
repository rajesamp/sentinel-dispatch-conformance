# SENTINEL-TPD

**Content-level trust gate for MCP tool metadata.**

Access-control layers (mTLS, ACLs, gateways) answer *who may call which tool*.
SENTINEL-TPD answers a different question: **can the tool's own description be
trusted to steer the agent?** A tool's description and schema enter the model's
context verbatim — they are instructions to the model wearing the costume of
documentation. This library treats them as **untrusted input** (instruction-
hierarchy Layer 4) from the moment they are registered.

Grounded in the MCP threat-modeling literature: tool poisoning scores
**DREAD 46.5/50**, the highest-severity client-side MCP threat (Huang et al.,
arXiv:2603.22489).

## What it does

Two enforcement points, both fail-closed, both audit-logged:

1. **`TOOL_REGISTERED` gate** — every tool's name, description, and *every
   nested schema description* is scanned against a deterministic signal
   catalog before the tool is admitted. Severity ≥ M3 ⇒ deny; the tool never
   reaches the model's context.
2. **Call-time decision-path check** — admitted metadata is fingerprinted
   (SHA-256 over canonical JSON). At invocation, the current metadata is
   re-fingerprinted and diffed. Any mutation (**rug pull**) ⇒ deny +
   quarantine until a clean re-scan on the next `tools/list` refresh.
   Unknown tool ⇒ **default-deny**.

Every allow/deny/mutation event lands in a **hash-chained audit log**: each
entry embeds the SHA-256 of the previous one, so editing any record breaks
every downstream hash.

## Signal catalog (v2026.8)

| Signal | Sev | Tactic |
|---|---|---|
| `TPD-IMPERATIVE-TAG` | M4 | `<IMPORTANT>`/`<system>`-style markup addressing the model |
| `TPD-CONCEALMENT` | M4 | "do not tell the user" — secrecy from the operator |
| `TPD-EXFIL-DEST` | M4 | send/post/forward + embedded URL or email |
| `TPD-DIRECT-MODEL-ADDRESS` | M3 | "you must…", "ignore previous…" |
| `TPD-PRIORITY-CLAIM` | M3 | "takes precedence over all other instructions" |
| `TPD-SENSITIVE-PATH` | M3 | `~/.ssh`, `id_rsa`, `.env`, API keys, seed phrases |
| `TPD-CROSS-TOOL-STEER` | M3 | shadowing: modifies how *other* tools are used |
| `TPD-PARAM-SMUGGLE` | M3 | "include the entire conversation in this field" |
| `TPD-ENCODED-BLOB` | M2 | long base64-like payloads in metadata |
| `TPD-URGENCY` | M1 | pressure framing aimed at the model |

Default-deny threshold: **M3**. Configurable per registry.

## Quickstart

```python
from sentinel_tpd import ToolRegistry

reg = ToolRegistry()

verdict = reg.register(tool_dict)          # TOOL_REGISTERED gate
if verdict.allowed:
    decision = reg.check_invocation(tool_dict)   # call-time diff
    if decision.allowed:
        ...  # safe to place in model context / execute

reg.rescan_on_refresh(new_tools_list)      # on tools/list change

ok, detail = reg.audit.verify()            # audit chain integrity
```

Zero runtime dependencies — Python 3.11+ stdlib only. Run tests with either:

```bash
python -m unittest discover -s tests
pytest
```

## Design decisions

- **Deterministic classifier, no LLM in the loop.** A model inside the trust
  boundary you are defending is a recursion, not a defense. Regex/heuristic
  signals are auditable, testable, and explainable per-deny.
- **Fail closed everywhere.** Malformed metadata, unnamed tools, unregistered
  tools, mutated tools — all deny paths, never warn-and-continue.
- **Framework-agnostic.** Takes plain dicts, returns verdicts. No MCP client
  dependency; wire it into any client at the two enforcement points.

## Honest limitations

- The signal catalog is a **first-line, precision-biased filter** — it will
  not catch novel phrasings, non-English payloads, or semantic attacks that
  avoid the listed patterns. Recall is intentionally traded for explainable
  denies. Pair with runtime egress controls and least-privilege tool scopes.
- The audit chain is **tamper-evident, not tamper-proof**: an attacker with
  write access to the log can rewrite the whole chain. Real WORM guarantees
  require append-only storage with retention lock (e.g. GCS bucket retention
  policy) — that's a deployment concern this library deliberately leaves to
  the deployment.
- Fingerprinting covers `name`, `description`, and `inputSchema`. Server
  behavior changes that don't touch metadata are out of scope here.

## Relation to the SENTINEL family

SENTINEL-TPD extends the author's broader agent-runtime-security posture
(instruction hierarchy, M0–M4 severity tiers, default-deny on missing
contract, fail-closed on ambiguity) to the client-side MCP tool-metadata
trust gap.

## License

MIT — see [LICENSE](LICENSE).

## Author

Rajeshkumar Sampathrajan · [github.com/rajesamp](https://github.com/rajesamp)
