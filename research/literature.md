# Literature challenge and study boundary

Review date: 2026-10-06. Intended author: Rajeshkumar Sampathrajan, Independent Researcher. This document evaluates the study's contribution; it reports no experimental results. Numerical results from an earlier manuscript are not evidence for the new implementation. The selected genre is a full conference empirical conformance paper; see `venue-fit.md`.

## Judgment

The broad contribution “a runtime binding guard plus an invariant benchmark for MCP” is already occupied. Identity binding, descriptor integrity, capability-change detection, pre-effect authorization, and agent TOCTOU have direct prior art. A small reference implementation, naive and practice-informed baselines, ablations, and local overhead measurements also closely resemble the Handle-Capability Protocol (HCP) artifact design. Renaming these elements would not establish novelty.

A narrower, conditional contribution is credible: **a controlled empirical study of descriptor-to-dispatch continuity across catalog refreshes and model-facing client adapters**. The question is whether a client preserves its own checked snapshot through representation changes and concurrent dispatch, and what availability cost its consistency policy imposes. The contribution would be measured failures, a precise trace oracle, reproducible adapter experiments, and evidence about existing engineering remedies. It would not be a new cryptographic primitive or the discovery of TOCTOU.

Suggested provisional title: **When Tool Catalogs Change: Testing Descriptor-to-Dispatch Continuity in MCP Clients**. Retain this framing only if experiments substantiate it. If a conventional immutable snapshot and atomic dispatch baseline eliminates every failure without meaningful cost, report a replication/conformance study; do not manufacture a “novel guard” claim.

## Closest primary sources

The table covers eight principal texts whose relevant methods, evaluation descriptions, or normative rules were inspected. Existence and version metadata are verified; peer-reviewed publication metadata is not established for the arXiv papers. An Internet-Draft is an individual proposal, not an endorsed IETF standard. Source identifiers resolve in `sources.json`.

| Source | Verified overlap | Consequence for this study |
| --- | --- | --- |
| S1, [ETDI](https://arxiv.org/abs/2506.01333v1), 2025-06-02 | Sections IV-A/B bind tool definitions to signatures and versions, verify before LLM exposure, and require renewed approval when hashes or versions change. IV-D adds runtime policy evaluation. | Checked-definition continuity and reapproval are established ideas. The inspected method does not supply a systematic refresh/dispatch schedule experiment; that is a possible evaluation extension, not proof that ETDI implementations are vulnerable. |
| S2, [Governing Dynamic Capabilities](https://arxiv.org/abs/2603.14332v2), 2026-03-19 | Section 3.2 binds a canonical capability manifest to identity. Section 7.4 includes tool addition and implementation replacement among structural tests. Section 8.5 distinguishes observable descriptor integrity from hidden remote implementation changes. | Dynamic capability changes and manifest hashing are direct prior art. A differently named hash or registry epoch is insufficient novelty. No claim about this implementation's race behavior is justified without running it. |
| S3, [HCP invariant benchmark](https://arxiv.org/abs/2606.29073v1), 2026-06-27 | Eight invariants, ten listed cases, naive/practice-informed/reference-runtime comparison, ablations, generated result artifacts, and a local microbenchmark. Table 3 covers metadata poisoning, confused deputy, broad approval, data flow, and protocol state. | This is the strongest overlap in contribution shape. The listed cases do not include catalog refresh/dispatch interleavings. Section 9 limits the reference runtime and does not establish ecosystem vulnerability prevalence. |
| S4, [MCP Security Bench](https://arxiv.org/abs/2510.15994v2), 2026-03-24 | Sections 4 and 6 cover name collision, preference manipulation, injection, tool-response manipulation, mixed attacks, and utility effects of blocking. | Collision and tool-selection attacks are established categories. Distinguish deterministic routing continuity from model persuasion, and measure benign acceptance as well as unsafe dispatch. |
| S5, [MCPS draft revision 01](https://datatracker.ietf.org/doc/html/draft-sharif-mcps-secure-mcp-01), 2026-08-21 | Sections 6.2–6.5 specify origin checking and pins keyed by server origin and tool name. Although the abstract says full tool object, the concrete §6.3 signing object lists `author_origin`, `description`, `inputSchema`, and `name`. | Server-scoped pinning is prior art. Do not describe the draft as unambiguously covering every descriptor field: its text has a material scope discrepancy. No implementation defect or atomicity guarantee is established by this reading. |
| S6, [Semantic Attacks on Tool-Augmented LLMs](https://arxiv.org/abs/2512.06556v2), 2026-05-21 | Descriptor manipulation, poisoning/shadowing/rug-pull distinctions, integrity checks, auxiliary vetting, runtime guardrails, and simulated evaluation with validity limitations. | General lifecycle integrity and runtime defense are occupied. Separate semantic manipulation from the proposed client's snapshot property. Use the current version's title when citing v2. |
| S7, [Mind the Gap](https://arxiv.org/abs/2508.17155v1), 2025-08-23 | Sections 3–4 study changes in external state between successive agent tool calls, a 66-task benchmark, state monitoring, prompt changes, and tool fusion intended to narrow exposure. | General agent TOCTOU, benchmark construction, and shrinking a check/use gap are direct prior art. A single-call client routing pipeline is a narrower unit of analysis, but that distinction alone does not establish a publishable contribution. |
| S8, [Security Principal and Verifier Binding](https://datatracker.ietf.org/doc/html/draft-bu-agentproto-security-principal-binding-07), revision 07 | Sections 9–10 and 23–26 specify claim/verifier bindings, freshness, accepted-result identity, action evidence, and negative cases including mismatched digests, encodings, stale dependencies, and post-effect evidence. | Broad binding matrices and mismatch tests are also established. Position a new artifact as empirical operational coverage, not invention of these correctness obligations. No IETF endorsement is implied. |

Absence of a term or scenario in the inspected sections is not a proof of absence from all versions, repositories, or related work. The review did not execute any prior-art implementation.

## Protocol and ecosystem grounding

The [MCP tools specification dated 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) explicitly scopes name uniqueness to a server, discusses cross-server collisions, and warns that `serverInfo.name` is not unique. Its call example names a tool and supplies arguments; it is not evidence of an implementation's complete internal authorization scheme. Pin a protocol version, since the [2025-11-25 tools specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) differs from the current version.

The [2026-07-28 caching specification](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching) describes TTL as a hint, notification invalidation, authorization-sensitive private caches, and independently cached pages. It explicitly provides no cross-page consistency guarantee. A mixed-page observation is therefore not, by itself, an MCP violation. Tests must distinguish protocol-permitted catalog observations from violations of a stronger client-owned snapshot promise.

The current tools page also requires per-request `_meta`, and describes retry parameters `inputResponses`/`requestState` and `x-mcp-header` projections. A local fixture carrying only method, name, and arguments is not full 2026 wire conformance. Pin the tested protocol version and request subset; describe completeness only over fields actually admitted by the supported adapter contract.

Two concrete reports motivate availability controls: [Hermes issue 87112](https://github.com/NousResearch/hermes-agent/issues/87112) describes normalized-name collisions involving a generated utility; [IronClaw issue 2766](https://github.com/nearai/ironclaw/issues/2766) describes model-provider name limits and proposes separate model-facing names and registry keys. These are reporter observations/proposals, not independently reproduced vulnerabilities. Official [TypeScript SDK migration documentation](https://ts.sdk.modelcontextprotocol.io/v2/migration/upgrade-to-v2) also documents schema representation changes. None of these sources establishes exploitability in a pinned release.

Concurrency correctness has a much older foundation: [Herlihy and Wing's linearizability paper](https://www.cs.cmu.edu/~wing/publications/HerlihyWing90.pdf). If the new study uses “linearizable,” define the operation and its allowed instant of effect, and check histories against that definition. An epoch comparison alone is not a proof of linearizability.

## Questions worth answering

1. Under an explicit client consistency policy, which adapter transformations and refresh/dispatch schedules produce a dispatch inconsistent with the checked, model-visible selection?
2. Which conventional consistency mechanisms eliminate these failures, and when do they unnecessarily reject operations that remain valid under the policy?
3. Which results persist in pinned, real adapter paths rather than only a deliberately mutable simulator?

The third question determines external validity. A simulator can validate the oracle and isolate causes; it cannot establish vulnerability prevalence or behavior of a product it does not execute. A strong workshop paper can report a carefully bounded negative result, but a weakness planted in a toy baseline is not evidence against the ecosystem.

## Proposed trace contract

This is a proposed experimental contract, not a claim that MCP requires these fields or that prior work lacks them.

Record the server/session identity, raw tool name, descriptor bytes and canonical form, model-facing descriptor and alias, transformation/version identifier, authorization context, catalog snapshot generation, selected entry, bound route or dispatcher, authorization decision, and dispatched operation. Record event order and refresh start/completion independently. Hashes are evidence summaries; retain enough structure to inspect a counterexample.

Define the permissible projection from a checked descriptor to the model-facing schema. A normalized name need not equal a raw name, but the inverse mapping must be unambiguous in its snapshot. Do not classify every schema rewrite as malicious: determine whether it changes the policy-relevant contract. JSON object key order can be ignored under an explicit canonicalization rule; descriptions, argument constraints, array semantics, and routing identity must not be casually normalized away.

Define update semantics before labeling outcomes. A descriptor refresh, removal/re-addition, explicit revocation, and unrelated-tool update need not have the same cancellation rule. An immutable old snapshot may be acceptable for a benign update yet unacceptable after revocation. A “safe dispatch” label is meaningless without this choice.

Authorization must bind the actual selected dispatch target. Checking one object and then resolving a mutable name again creates a new gap. Specify the linearization point for selection/authorization/dispatch, including whether update and revocation can intervene. A client can establish what it selected and sent; it cannot establish that a remote server's hidden implementation or physical effects stayed faithful to the descriptor.

## Scenario families and controls

| Schedule or transformation | Paired control and expected evidence |
| --- | --- |
| Refresh after checking but before model exposure | Unchanged canonical descriptor under key/catalog reorder; compare the actually exposed projection. |
| Refresh after exposure or selection but before authorization | Unrelated-tool update; show whether a global epoch causes avoidable denial under the declared policy. |
| Refresh after authorization but before dispatch | No intervening update; bind and inspect the dispatched route rather than only a successful guard return. |
| Two refreshes finish out of order | Completion in request order; record refresh generation and committed catalog, not wall-clock latency alone. |
| Same raw name on two servers or normalization collisions | Distinct aliases and injective reverse mapping; include generated client utility names. |
| Removal and re-addition with the same visible name (ABA) | Stable entry; distinguish same descriptor from new route/session or an explicit revocation event. |
| Descriptor projection changes across adapter/schema versions | An explicitly allowed equivalent projection; show which policy-relevant fields reached the model. |
| Pagination/cache invalidation mixes observations | Stable pages and a full re-fetch; report allowed protocol observations separately from claimed atomic-client behavior. |

These are proposed cases, not confirmed vulnerabilities. Their number is not an attack-success denominator. Report unique semantic families, unique base traces, schedules executed, and repeated trials separately.

## Baselines and acceptance criteria

Use conventional remedies as serious baselines: server-scoped immutable entries; deterministic injective alias mapping; explicit projection validation; a global-epoch fail-closed guard; and per-entry binding with atomic dispatch/commit and defined revocation semantics. Test the last baseline as strongly as the proposed guard. Do not label an approximation “ETDI,” “MCPS,” or “HCP” unless their actual implementation/specification is reproduced faithfully; label it an inspired control with documented omissions.

Count unsafe dispatches against the independent trace oracle and benign acceptance against a predeclared policy. Also report rejection reasons, wrong-server/wrong-entry dispatches, stale authorized selections, and overhead under identical workloads. Latency is secondary; run counts and machine conditions must be recorded. A fixed schedule repeated many times does not create many independent attack examples. An LLM is unnecessary for a deterministic routing test; claims about model selection or semantic attack success require separate evidence.

Before submission, preserve pinned versions, source hashes, exact test configuration, raw event traces, all exclusions, and scripts that regenerate tables. Include counterexample traces for every failed family, a clean baseline, and a check that the oracle can detect an intentionally introduced error. If actual adapter integration is absent, title and abstract must clearly call the artifact a model or reference harness.

## Claim boundary and remaining uncertainty

Permissible now: the literature motivates a narrow study; the proposed cases and baselines are hypotheses for evaluation. Permissible after measurement: a stated implementation under stated schedules violated a stated policy, or a guard restored that property with a measured acceptance cost.

Not supported: “first runtime MCP defense,” “first dynamic binding,” “first TOCTOU benchmark,” a protocol-wide vulnerability, production exploitability, comprehensive prior-art superiority, prevention of hidden remote code changes, or any old attack-success numbers. Do not claim complete security from passing a bounded trace suite.

The initial review inspected eight principal method/normative texts. The follow-up below upgrades Attested Tool-Server Admission from abstract-only coverage, adds two close sources, verifies bibliographic metadata, and logs targeted searches. This remains a targeted review, not a systematic or exhaustive one. No prior-art performance result was reproduced. Source pages are not byte-archived; the conference template alone was fetched and hashed directly.

## Follow-up novelty challenge: approval and use are already linked in prior work

The full-conference framing must take account of three additional close sources:

| Source | Inspected method and overlap | Residual study boundary |
| --- | --- | --- |
| L1, [Attested Tool-Server Admission](https://arxiv.org/html/2605.24248v1), §§4–7 | Metere binds endpoint admission to signed clearance, locks the local trust root, checks a per-server closed tool allowlist, and reruns clearance checks at invocation. The hermetic harness observes transport writes directly and includes permitted calls as controls. | Neither pre-dispatch enforcement nor a network-observing conformance harness is new here. The inspected admission algorithm does not specify a complete approved-descriptor/request snapshot or an out-of-order catalog-refresh experiment. Its code was not executed. |
| S9, [Execution-Finality draft -02](https://datatracker.ietf.org/doc/html/draft-das-hardware-enforced-execution-finality-02), §§4–6, 14 | Das proposes act and argument digests, MCP server and sink identities, policy/revocation epochs, use-time verification, and atomic consume/effectuation. Section 14 describes a local software reference implementation, negative tests, and timing. | Exact-action binding, current revocation and atomic use are explicitly occupied concepts, even though the hardware-rooted proposal and this trusted-process harness have different assumptions. The draft is individual work in progress; no IETF endorsement, hardware guarantee, code reproduction, or superiority finding follows. |
| S10, [Approved Too Late](https://arxiv.org/html/2608.26306v1), §§III–VI | Shraga, Eshel, and Gorelik hold proposed actions fixed while relabeling later simulator states; distinguish approval expiry from judge error; and test a heuristic freshness gate with utility/overblocking controls. The method explicitly limits replay's causal interpretation. | Approval freshness and safety/utility reporting are already research subjects. This study instead tests discrete identity/request/catalog transitions under a declared host contract; it does not estimate a plant-dependent validity horizon. |

These additions strengthen the negative novelty judgment. A contribution claiming invention of complete-action binding, revocation checks at use, atomic dispatch, or benign-preservation measurement is not defensible. An original result would have to be **the supported implementation evidence and measured tradeoffs**, with faithful comparators and a reusable, independently checked testing artifact.

## Mechanism comparison without unsupported absence claims

“Not specified in inspected method” below is a coverage statement, not proof that an implementation lacks a defense. These sources use different trust models and are not experimental arms in this study.

| Mechanism/property | What the sources actually establish | What this study must still measure |
| --- | --- | --- |
| Complete descriptor binding | ETDI signs versioned definitions. Dynamic Capabilities commits to its declared skill-manifest representation. MCPS has the four-field signing-object discrepancy above. | Whether every field actually presented by the adapter is bound, including extension fields; avoid a selected-field baseline disguised as full coverage. |
| Complete outbound request | HCP makes principal/resource/capability authorization runtime objects. S9 explicitly binds an act/arguments digest to a sink. | Whether the actual method, route, and arguments equal the approved request at enqueue. Hashing a descriptor alone is insufficient. |
| Identity | ETDI has provider identity; MCPS has server-origin pinning; L1 has endpoint/bridge allowlists; S9 has server and sink identity. | Host registration and connection-generation continuity, including same-named tools and identical metadata from distinct registrations. |
| ABA and revocation | Dynamic Capabilities checks revoked credentials; HCP implements grant/handle revocation; S9 specifies current revocation epochs. | Whether remove/re-add or revoke/reapprove can resurrect an earlier approval when visible bytes return to their former value. A content hash cannot encode the intervening history by itself. |
| Stale refresh completion | The inspected methods do not establish a request-generation policy for concurrent `tools/list` responses. MCP cache pagination supplies no atomic multi-page snapshot promise. | Start/commit ordering, rejection of older completion generations, and whether the policy is the client's own stronger contract rather than a protocol requirement. |
| Benign preservation | L1 has successful controls; MSB studies utility; S10 distinguishes overblocking and fallback utility. | First-pass completion, eventual completion, and unnecessary invalidation for equivalent refresh, unrelated updates, and valid reapproval. A global epoch can be conservative without being more useful. |

## Author's existing software and scope attribution

The GitHub connector search `user:rajesamp sentinel` returned three public Sentinel repositories. Read their READMEs; this is not a code audit of all three.

- [sentinel-tpd at the pinned revision](https://github.com/rajesamp/sentinel-tpd/tree/5ce5d56e57a0acd092435fca5d89b78d0b39ee7b): a deterministic metadata scanner and call-time fingerprint check over `name`, `description`, and `inputSchema`; plain-dictionary API, no native MCP client. It is the actual pinned software comparator, not a promise of host routing/argument atomicity. README blob `da7910764f3503fa14418e0089052e459ed3d583` matches the local vendor manifest.
- [sentinel-guardrail](https://github.com/rajesamp/sentinel-guardrail): a related tool-registration/tool-attempt guardrail, with local logging and planned deployment hardening. The README does not establish complete request snapshots or atomic catalog integration. It was not an evaluated arm.
- [sentinel-mem](https://github.com/rajesamp/sentinel-mem): integrity/provenance gating for cross-session memory and transitive revocation. It explicitly attributes its integrity model to earlier work. Memory-origin propagation is a different boundary and does not constitute evidence for the MCP gate.

Discuss these as the author's related artifacts and cite them in third person for anonymous review. Do not imply independent third-party validation because their code is public. No release DOI was observed; cite exact revisions when experimentally used, and retain README blob identities for the unpinned companion reads.

## Bibliographic and search audit

Versioned arXiv landing pages confirm titles, authors, dates, and listed arXiv DOIs. ArXiv DOIs are repository identifiers, not proof of peer-reviewed publication. MSB's page reports ICLR 2026 acceptance and Approved Too Late reports ACSOS 2026 acceptance; this pass did not independently verify proceedings records, so `references.bib` cites the inspected preprint versions. Approved Too Late's DOI is explicitly marked pending registration on its page. The principal-binding draft author is **Songbo Bu**, dated **15 September 2026**. The execution-finality draft author is **Sangam Das**, dated **9 September 2026**.

Exact search strings, URLs, read scope, errors, and budget expansion are preserved in `sources.json`. Newly found but unreviewed follow-ups include [Temporal UI State Inconsistency](https://arxiv.org/abs/2604.18860), [A Secure, Manifest-Based Framework for Delegated Privilege Promotion](https://arxiv.org/abs/2605.28991), and [The Balkanization of Execution-Security Research](https://arxiv.org/abs/2607.05743). They are discovery leads only, not evidence supporting paper claims. The last is a possible bibliography-discovery aid; technical claims should return to its primary sources.

The sharpest unresolved question is external validity: a frozen finite suite can establish exact outcomes in its universe but cannot establish that real MCP clients fail. No assertion of firstness, exhaustive prior-art coverage, an unbounded proof, or ecosystem prevalence is supported by this review.
