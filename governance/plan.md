# Plan

1. Freeze provenance and candidate research question; challenge novelty in parallel.
2. Run upstream tests; reproduce scoped counterexamples without changing vendor code.
3. Implement strict descriptor snapshots and binding lifecycle in src/binding_gate.
4. Implement adapters, declarative cases and independent dispatch oracle in experiments.
5. Freeze cases, run all methods and benign controls, preserve raw JSONL and metadata.
6. Review implementation and counterexamples independently; retain failure evidence.
7. Run local performance measurement, produce tables/figures and claims ledger.
8. Write a focused workshop manuscript with explicit prior-art overlap and limits.
9. Compile with the built-in LaTeX editor; validate artifact reproduction and package.

Ownership: coordinator owns governance, core, integration, manuscript and final claims.
Specialists initially own research/literature.md + sources.json,
research/baseline-audit.md, and research/evaluation-plan.md respectively.
Later work receives exclusive paths before dispatch.

Risks: known prior art may narrow novelty; one author-owned library is not ecosystem
prevalence; adapters can create artificial disadvantages; a synthetic suite cannot
show real-agent semantic robustness; global invalidation can reject benign calls.
These become explicit controls and limitations, not hidden exceptions.

Proof: upstream tests, independent local safety oracle, behavioral tests, held-out
verification, exact record counts and hashes, regenerable figures, source-to-claim
ledger, manuscript compiler diagnostics. No external live attacks.
