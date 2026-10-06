# Final manuscript reviewer assessment

Reviewed 2026-10-06 by the source-and-novelty AI review agent. This is a critical internal review, **not independent human peer review**, a program-committee decision, or submission certification. No source or result files were edited.

Reviewed generated `manuscript/paper.tex`, from its final title through the bibliography, and `manuscript/paper-body.tex.in`; compared claims with the previously inspected primary sources, final evidence audit, finite-model contract, transport-check description, run protocol, and claims ledger. No new literature search was performed. The review snapshot hashes were:

- `paper.tex`: `9ba4c359e1f5f687cf11fd5bdc90b1cdaa90bc5d40397eb66896af294e159ea7`
- `paper-body.tex.in`: `93771bb2812c6584890ef24eb782d26cb182a5309d3d24546ba3afb8ac1a6f8c`

Line references below refer to those snapshots. Compilation and anonymous packaging were still being completed and were not verified in this review.

## Judgment

The manuscript now supports a carefully bounded empirical conformance claim. It fairly reports that the strong conventional snapshot control matches the generation gate, that a global invalidation policy sacrifices completion under the declared contract, and that the weak-arm failures belong to authored adapters. Its source attribution and limitations are substantially more defensible than a claim of a new MCP security mechanism.

The principal full-conference risk is **research significance**, rather than a remaining missing denominator or fabricated success rate. The contribution presently demonstrates well-known identity, copying, revocation-history, and synchronization obligations in a new executable local fixture. A EuroS&P reviewer could reasonably find this useful engineering and a reproducible artifact while remaining unconvinced that the new knowledge is sufficiently consequential for a full conference paper. That concern is a judgment about contribution; it is not a finding that the measured narrow results are invalid or that synthetic experiments are inherently inappropriate.

## Fixable inaccuracies and precision issues

1. **Correct the equality control's name.** Generated `paper.tex:6744` says “A hash-only adapter enqueues the old request.” The final evidence audit confirms that the historical internal name `snapshot_hash` uses complete serialized descriptor equality, not a cryptographic hash at validation. Replace with **“The equality-only adapter enqueues the old request.”** This text comes from the result generator rather than the body template. It is the clearest remaining factual error.

2. **Do not promise an unreported paired comparison.** `paper-body.tex.in:345` / `paper.tex:6700` says “We report absolute microseconds and paired method differences.” The manuscript reports absolute quantiles; the inspected summary stores paired empty-harness adjustments, which are different from between-method paired effect estimates. Replace with **“We report absolute batch-mean quantiles and retain paired samples for reanalysis.”** Alternatively, actually report a defined between-method paired statistic, but that is not necessary for the current descriptive cost claim. Subtracting two displayed medians would not establish that statistic.

3. **Remove an ambiguous independence claim.** The arm table at `paper-body.tex.in:227` / `paper.tex:6582` calls snapshot revocation a “Strong independently authored control.” Use **“Strong separately implemented control.”** The later shared-authorship disclosure is good, but the local table should not suggest independent human authorship or blind development.

4. **Name the collided identifier accurately.** The abstract at `paper-body.tex.in:7` / `paper.tex:6362` says “server-name collisions.” The explained and evaluated case concerns identical tool names across distinct host-assigned servers. Use **“cross-server tool-name collisions.”** The distinction matters because server identity and tool-name scope are separately modeled.

5. **Minor protocol precision.** At `paper-body.tex.in:85` / `paper.tex:6440`, describing descriptors as including “a name, description and argument schema” could suggest that the description is required. Use **“a name and argument schema, with an optional description and further metadata.”** This does not change the experiment.

These changes need wording/regeneration only; they do not call the saved security outcomes into question. They were reported to the coordinating agent before this report was saved.

## What is already adequately addressed

- The abstract identifies authored local adapters. The paper pins a basic 2025 call envelope and expressly excludes full current MCP wire conformance or SDK interoperability.
- The study has 36 targeted cases, all 259 serial words within its declared six-event/depth-three universe, six comparison arms including a strong revocation-aware snapshot control, 18 separate source-contract observations, two timing sessions, six supplementary subprocess checks, and a Python 3.14 reproduction. None of these are treated as independent attack samples or pooled into an invented success denominator.
- The reported count tables agree with the completed final evidence audit. This review cross-checked that audit and the generated prose; it did not independently repeat its all-record reconstruction.
- Equal full completion by the strong snapshot and generation arms is retained. The global policy's zero unsafe receipts is accompanied by its lost completion. Benign controls and valid reapproval prevent a deny-all implementation from appearing fully successful.
- The oracle observes actual sink receipts, and errors and uncertain transport outcomes are not silently credited as safe denials. Separate implementation and negative controls are documented without claiming independent human review.
- HCP is correctly expanded as **Handle-Capability Protocol**. MCPS's abstract-versus-enumerated-fields discrepancy remains qualified. Freshness studies are distinguished from individual exact-action/sink-binding drafts. The inspected preprint versions and Internet-Draft status are accurately represented; no proceedings status or standards endorsement is invented.
- Timing quantiles are explicitly batch means from valid local paths, not network request tails or deployment throughput. The paper does not infer universal performance superiority from the ordering.

## Substantive full-conference risks and useful responses

### 1. The closest related-work comparison remains compressed

HCP already presents an invariant-oriented runtime, comparison arms, ablations and local measurement. Attested Tool-Server Admission already observes effects in a hermetic harness with positive controls. The execution-finality draft already specifies exact action/arguments, identities, current revocation and atomic use. The current related-work section acknowledges these overlaps but does not sharply explain the incremental knowledge from this artifact.

**Useful revision now:** add a small mechanism/evaluation comparison or a focused paragraph distinguishing this paper's serial restoration cases, stale-refresh policy, representation-neutral receipt oracle, and selected-operation completion comparison. Use “not specified in the inspected method” where appropriate, never infer an implementation vulnerability or claim comprehensive absence. The existing `research/literature.md` supports this revision. This improves evaluability; it does not itself create novelty.

### 2. The strongest results are expected under the declared contract

History-free equality cannot encode intervening revocation; a global invalidator rejects unrelated changes; correctly synchronized immutable views can match counters. The paper demonstrates these points with executable evidence, but a reviewer may see them as direct consequences of the constructions rather than surprising findings. The 259 words completely exercise a small model; their numerical count does not increase the number of independent conceptual discoveries.

**Response:** keep the honest conformance/artifact framing and make the reusable testing contribution concrete: what error the receipt oracle detects that a returned-status test misses, which adapter assumptions the contract forces into the open, and how a different implementation can be plugged in without sharing gate logic. Additional development tests alone do not resolve the significance concern. A genuinely independent implementation application or consequential external finding would strengthen it, but is future research rather than a mandatory repair to the present narrow claims.

### 3. The pinned-library evidence is under-explained in the paper

The 18 observations are summarized in one paragraph. The artifact distinguishes ordinary recovery, malformed-schema admission, omitted metadata fields and conditional integration behavior, but readers of the paper cannot readily tell which observations concern actual pinned code and which require host assumptions.

**Useful revision now:** summarize two or three representative source observations with their controls and preconditions, preferably in a compact table. Preserve the distinction between documented clean-refresh recovery, a source-contract discrepancy, and an authored host failure. This gives the actual-library component evidential weight without misrepresenting it as an independent ecosystem survey or inflating the attack count.

### 4. External validity remains narrow despite real subprocess receipts

The six subprocess checks improve evidence about delivered bytes and zero-frame denials. They are meaningful integration checks, but both endpoints and wrappers remain authored fixtures and omit a general MCP stack. The Python-version replay establishes repeatability across two interpreter versions, not a new deployment population. Shared authorship, specification-aware cases and one selected revocation policy remain legitimate reviewer concerns, already disclosed.

**Response:** retain these qualifications. Neither an autonomous model nor a live target is required to answer the deterministic local contract question. An external adapter study would address a different and broader claim; do not imply that the current supplement has already done it.

### 5. Local timing is supporting evidence, not the main contribution

The differing registry, copying and validation work prevents attribution of the observed cost differences solely to counters versus immutable views. The manuscript correctly says so. Two sessions reduce the chance that one process session dominates the descriptive report, but do not characterize workload scaling or rejection paths.

**Response:** keep the timing claims descriptive and subordinate to conformance. Do not add an overhead percentage or superiority assertion. No extra benchmark is needed merely to support the current limited wording.

## Remaining completion gates and coverage gaps

This review does not certify the final PDF, page count, anonymous author/self-citation treatment, artifact archive contents, anonymous delivery mechanism, license packaging, or venue declarations. Those are separate completion checks already in progress, not newly discovered scientific blockers. In particular, “the reviewer package is supplied” should describe the final packaged state before submission.

No new source fabrication, unsupported ecosystem-vulnerability claim, hidden detector-accuracy percentage, or unbounded correctness claim was found. Acceptance cannot be inferred from compilation, checklist completion, or the amount of testing. Human source/code/result review remains necessary, and the author must decide whether the bounded contribution meets the selected venue's expectations.

## Authoring resolution appended 2026-10-06

At the coordinator's request, this same AI agent edited only `manuscript/paper-body.tex.in` and appended this resolution. The body now includes a concise comparison with HCP, Attested Tool-Server Admission and the execution-finality draft. It identifies the measured local scope and explicitly declines comparative-effectiveness or missing-defense claims about those prior systems. It does not claim new authority-binding primitives.

A new representative pinned-library table gives the observed outcomes, controls and host preconditions for schema-shape validation, top-level title projection, registration scan/fingerprint ordering, and a shared-registry namespace collision. The table was checked against `experiments/upstream_counterexamples.py` and the completed `results/python312-final/upstream-observations.json`, not inferred from the main adapter outcomes. The five malformed-schema records, title/covered-description controls, shared/copy registration pair, and shared/per-server registry pair all have `matches_expected: true` in that saved file. Documented clean-refresh recovery remains labeled intended behavior. No observation is promoted into remote execution, SDK acceptance or an additional conformance-case denominator.

The four body-template wording fixes above are applied: accurate cross-server tool-name terminology, optional descriptions, separately implemented control, and absolute quantiles with paired samples retained for reanalysis. The coordinator owns the remaining equality-control wording in the result generator. The pinned commit now has a discretionary LaTeX line break after its twentieth character; its exact 40 characters remain unchanged.

Targeted source checks confirmed the expected replacements, preserved build placeholders, paired table environments and unique new table label. No experiment, code, result, generator, bibliography or PDF was changed by this revision. Compilation and final visual/anonymous-package checks remain with the coordinator.

Resolution evidence:

- Revised body SHA-256: `5692392b5b6e024e81b29558ca9afec623daf80ac1a7119325f6bb0cd2ee3b98`.
- Observation JSON SHA-256: `e1509c58079e8fd90c2adf9078d6e8b52a9848ec7ad355574c76592afac1f2cc`.

These revisions address the specific presentation weaknesses identified in this review. The substantive significance/external-validity assessment remains; this resolution is not independent human review or an acceptance judgment.
