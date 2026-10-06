# Manuscript source review

Reviewed 2026-10-06: `manuscript/paper-body.tex.in`, SHA-256 `4434bc467006bb147484e44ec6e93b859d5b28208ba705b03bc1c411b7758772`. Scope: cited factual claims and evidence boundaries against the primary sources already inspected in `sources.json`. No extra web research, implementation audit, or result verification was performed. Result placeholders are intentional and were not scored as defects.

## Material corrections

1. **Abstract, lines 9–12: qualify the evaluated system immediately.** “In hosts using the Model Context Protocol” can suggest tests of functioning MCP clients. The body correctly explains that the experiment uses authored local adapters and a restricted 2025 request fixture, without a general protocol stack. Use “in authored local adapters modeling an MCP-style host boundary.” Prefer “separately implemented structural oracle” over “independent structural oracle” here: algorithmic separation is supported, independent human authorship is not. The later limitations are accurate but should not bear the entire abstract's scope qualification.

2. **Related work, lines 112–113: separate freshness studies from exact-action/sink proposals.** The combined sentence assigns a single overlap to four citations. *Mind the Gap* studies external-state changes between agent calls; *Approved Too Late* studies the lifetime of approvals using fixed-action replay and a heuristic validity horizon. Exact-action and sink binding is directly supported by the principal-binding and execution-finality drafts. Suggested split: “Agent TOCTOU and verdict-staleness studies examine validity at use time [mindgap, approvedtoolate]. Individual principal-binding and execution-finality drafts specify exact-action and sink-related authority bindings [principalbinding, executionfinality].” This preserves the distinction between empirical papers and individual work-in-progress proposals without claiming any IETF endorsement.

3. **Interpretation, second proposition: avoid claiming immutability is necessary.** “Immutable requests ... must reach the sink” promotes the tested representation into a universal prerequisite. The contract requires approved request contents and target identity to be preserved at enqueue; other correctly synchronized representations can establish that correspondence. Use “The approved request contents and unambiguous host identity must be preserved through enqueue.” The manuscript's strong-control discussion already makes this representation-neutral point correctly.

## Checks that passed

- HCP is correctly expanded as **Handle-Capability Protocol** in the manuscript. No incorrect expansion was present in `research/literature.md`; its first mention now states the correct expansion explicitly.
- The treatment of MCPS preserves its abstract-versus-four-field-algorithm discrepancy without inventing an implementation defect.
- The pinned SENTINEL-TPD responsibility is separated from authored host behavior, and shared human authorship is disclosed.
- The request-subset limitation, host-owned revocation contract, bounded serial enumeration, and absence of protocol certification or deployed-host prevalence claims are stated clearly.
- The manuscript does not claim a new primitive, claim that passing finite tests proves unbounded correctness, or label the composition cases a blinded holdout.
- AI assistance and the need for human review are disclosed. The current text does not falsely claim peer review or submission readiness.

## Remaining judgment

No fabricated source, incorrect author attribution, or remaining HCP expansion error was found. The three corrections above narrow wording; they do not require new experiments. Full-conference suitability remains a judgment about contribution and external validity, not something this source review establishes. Numerical results, artifact licenses, code behavior, anonymous packaging, and final venue-template compliance require their own checks before submission.
