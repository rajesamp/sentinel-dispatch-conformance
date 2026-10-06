# Registration content draft

Title: Binding Approval to Dispatch in Tool-Using Agents: A Reproducible Lifecycle Conformance Study

Author: Rajeshkumar Sampathrajan

Affiliation: Independent Researcher

Contact email and ORCID: not supplied; enter required contact details directly in the venue form.

Suggested topics (map to the actual form): agent/LLM systems security; access control; security testing and measurement.

## Abstract

An agent host can inspect a tool descriptor and still dispatch an operation that differs from the operation it approved. Catalogue updates, cross-server tool-name collisions, connection replacement and mutable call arguments create distinct opportunities for this divergence. We present a reproducible conformance study of this lifecycle boundary in authored local adapters modeling a Model Context Protocol style host. The artifact separates a pinned metadata scanner from six explicitly authored host adapters and evaluates actual sink receipts against a separately implemented structural oracle. It combines 36 targeted scenarios, all 259 event sequences of length at most three over a declared six-event model, deterministic concurrency checks and local paired timing samples. Both the revocation-aware snapshot control and the per-binding generation gate satisfy all 36 targeted scenarios and all 259 finite traces. A global-invalidation ablation emits no unsafe receipt in these suites, but completes only 6 of 11 benign targeted cases. A complete-descriptor equality control violates the historical-revocation contract in 4 targeted cases and 36 finite traces. The study contributes an executable contract, replayable counterexamples and controls that distinguish safety from useful completion. It establishes neither a new authorization primitive nor semantic attack-detection accuracy: the measured question is whether a local host preserves the operation it has already approved.

## Declarations

Conflicts, prior-submission overlap, authorship responsibility and exclusive-submission declarations require the author's factual confirmation. This draft makes no such attestation. Use the anonymous PDF and reviewer artifact from the submission handoff.
