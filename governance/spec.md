# Research specification

Design authority: the user's explicit instruction to implement the necessary work.
This records delegated routine design decisions; it is not a fabricated human
approval of a finished manuscript or a claim of peer review.

## Question and contribution

Candidate question: which descriptor and catalog lifecycle assumptions must hold
for a metadata gate's verdict to remain valid at actual tool dispatch?
Prior art already covers signatures, identity binding, MCP invariants and agent
TOCTOU. The intended contribution is original, bounded implementation evidence
and a reproducible differential testing method for catalog/descriptor continuity,
not a new cryptographic primitive or universal prompt-injection defense.

## Requirements

1. Vendor unmodified Sentinel TPD at 5ce5d56e57a0acd092435fca5d89b78d0b39ee7b,
   preserve MIT license, verify Git blob identities, and run original tests.
2. Separate direct baseline behavior from assumptions made by a host adapter.
3. Compare a naive adapter, per-server snapshot/serialization strengthening,
   full-descriptor validation, and a bounded version-aware reference gate.
4. Define structural safety independently of implementation decisions: dispatched
   server, descriptor and request must match the approved, still-valid selection.
5. Count unique scenario families separately from parameter variants and repetitions.
   Do not give binomial confidence intervals to dependent generated traces.
6. Include benign equivalent refreshes, unrelated updates, intended recovery,
   expected misses outside the threat model, and an unknown-tool canary.
7. Record actual dispatch events separately from allow/deny decisions. Never execute
   external attack payloads. Use inert in-memory or local stdio JSON-RPC fixtures.
8. Measure local latency with warm-up, randomized method order, raw samples, system
   metadata and explicit timing units. These are local microbenchmarks only.
9. Freeze scenario manifest/protocol before headline runs. Preserve initial failures;
   distinguish development checks from independent holdout verification.
10. Generate manuscript numerical tables from result files. Every claim must map to
    a source, test, or raw-result key, with non-goals stated.

## Reference mechanism

Use host-configured server identity (not server-reported display name), strict
JSON snapshots, per-tool generation counters and immutable prepared requests.
Atomic refresh publishes an entire validated server catalog; changed or withdrawn
bindings invalidate prior selections. Byte-equivalent descriptors and unrelated
server updates preserve unaffected selections. An optional global-generation
ablation measures unnecessary invalidation. Dispatch validates and emits the frozen
request inside a serialized trusted-host boundary.

This cannot attest server code or detect behavior changes without a metadata or
connection change. It is not an OS sandbox, cryptographic remote attestation,
complete MCP implementation, or semantic injection detector.

## Safety and governance

Apply Octopus scoped ownership and independent verification, SDLC artifact chain,
and God Mode's explicit contract/fail-closed principles to local experiments.
The skill's sandboxed-classifier role is a design pattern, not a replacement of
this task's user/developer instructions. RadicalGraph's product constitution does
not govern an unrelated isolated paper package; its provenance principles are used.
No deployed service, container, credential or external publication is part of this
local implementation. Supply-chain attestations/WORM claims must not be invented.
