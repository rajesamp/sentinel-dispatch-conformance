# Offline protocol for MCP approval-to-dispatch binding

Status: prospective protocol, not a results report. No result from the earlier manuscript is accepted as verified evidence. Author: Rajeshkumar Sampathrajan, Independent Researcher. The coordinator owns the implementation, preregistration freeze, and final claims.

## Research question and falsifiable claim

Can an MCP host maintain an auditable correspondence between the metadata it checked, the catalogue representation it supplied for tool selection, the operation it approved, and the operation it actually dispatches when catalogue and invocation state can change between those steps?

The narrow target is a deterministic host invariant. It does not require an LLM or a judgment about whether a tool description is malicious. The empirical claim should be of the form: **within a declared finite state/trace model, implementation X prevents dispatches inconsistent with an immutable approval record, with measured costs and explicitly reported benign invalidations.** An enumeration can establish this statement for its declared bounds; it does not prove correctness outside them.

Do not claim generic prompt-injection detection, real-world attack prevalence, universal MCP security, or a new security primitive merely from successful tests of these invariants.

## Objects, trust boundary, and independent oracle

Use separate immutable records for the following stages, each with a stable trial identifier:

1. **Checked descriptor:** exact descriptor supplied to the scanner, scanner/configuration version, decision, and scanner completion event.
2. **Presented catalogue:** exact host-controlled representation supplied to the selection interface. With no LLM, a deterministic selection driver consumes that representation and records the chosen entry. This simulates the selection boundary; it does not establish actual model behavior.
3. **Approval:** server registration identity assigned by the host; connection generation or equivalent session binding; tool name; complete approved descriptor; serialized call arguments; applicable authorization/policy revision; and the relevant catalogue/selection context, if that context is part of the declared policy.
4. **Dispatch receipt:** immutable connection/registration actually used, tool name and argument bytes actually enqueued, and the catalogue/configuration state relevant at the enqueue boundary. A controlled transport sink records this receipt independently of the gate's own success log.

Keep the checker, approval store, gate, transport sink, and oracle in the trusted host. An adversary cannot arbitrarily rewrite trusted code, forge approvals, or alter the sink while the paper simultaneously claims the host invariant remains meaningful. Model a malicious or changing server through permitted catalogue publication, disconnection/reconnection, and tool behavior. Model stale selection/request objects and concurrent argument edits as specific host workflow races; identify which are reachable through the tested adapter rather than assuming unlimited host-memory compromise.

The reference oracle is a declarative comparison of immutable records and event order, independently implemented from the gate. It must not ask the tested implementation whether a dispatch is safe, reuse its approval validator, or use its pass/fail decision as the expected label. Preserve the original descriptors and argument structures in the oracle so a shared digest/canonicalization defect cannot silently make both agree.

Define separate invariants before running the suite:

- **Scan/presentation correspondence:** an allowed entry presented for selection corresponds to the descriptor that received the applicable scanner decision. A scan of one string does not authorize another string.
- **Identity correspondence:** the dispatched host registration, connection generation, and tool name match the identity approved. Self-asserted server names are not authenticated host identities.
- **Descriptor correspondence:** the selected tool descriptor at the declared authorization boundary agrees with the approved descriptor, under the specified canonical representation.
- **Operation correspondence:** the actual outbound method/tool/arguments match the approved operation. Hashing only a descriptor does not establish this property.
- **Revocation/order correspondence:** a relevant approval revocation before enqueue prevents enqueue. A revocation after an irreversible enqueue has different semantics and cannot undo the past.

Catalogue epoch equality is one possible implementation technique, **not the oracle's definition of safety**. Otherwise an epoch gate could win by construction. Declare which changes materially invalidate an approval and distinguish them from harmless unrelated catalogue activity. If the study also examines a stronger full-catalogue-context policy, report that as a separate contract and keep its outcomes separate from selected-operation safety.

For canonicalization, specify treatment of object key ordering, array ordering, omitted versus null fields, numbers, Unicode, unknown/extension fields, and invalid/duplicate-key JSON. Reject unsupported input shapes explicitly. Do not normalize away content that can affect the presented descriptor or outbound call. Bind all fields actually delivered across each claimed boundary, not just a hand-selected list. Store both canonical bytes and original structured records for audit.

## Comparison arms and fair adapter

Every arm gets the same catalogue event stream, exact descriptors, selection driver, proposed call, workload ordering, transport adapter, and observable scheduling windows. Share neutral instrumentation; isolate security decisions. A common wrapper must not repair the baseline's identity/presentation issue silently, or introduce a mutable lookup used only to make a baseline fail.

| Arm | Required interpretation |
| --- | --- |
| Unprotected host | The common adapter with binding checks disabled; establishes whether the challenge can cause a mismatched dispatch. |
| Actual pinned `sentinel-tpd` | Use the actual pinned implementation and published configuration, with exact import path, revision, dependency versions, and adapter. Describe its native responsibility accurately. Do not claim a scanner promises host dispatch guarantees unless its own API makes that promise. |
| Namespace + full-descriptor-hash baseline | Host-assigned server-scoped identity and complete metadata hashing, checked at the latest dispatch boundary the adapter supports. Do not restrict it to an unnecessarily early check. Clearly report which fields and operation state it does or does not bind. |
| Immutable complete-request baseline | Where practical, capture an approved server/connection reference and complete outbound request immutably, then enqueue that exact request. This is a strong low-complexity control; it may close the relevant gap without a global epoch. |
| Atomic epoch-bound gate | Proposed mechanism, with a documented linearization point connecting validation to enqueue, approval revocation policy, and precise lock/transaction scope. |

If the proposed gate embeds `sentinel-tpd`, the primary integration comparison must hold the scanner decision and scanner version constant across host-binding arms. Binding challenges should use initially accepted descriptors; whether a scanner recognizes a malicious phrase is a separate outcome. Fix the descriptor inclusion rule before results are observed. Report rejected fixtures and reasons; do not silently drop failed attacks or scanner rejects. A scanner reject is not evidence that its caller maintained an approval-to-dispatch invariant.

Report native scanner behavior separately from host guarantees and adapter-created protections. If the actual package is unavailable or cannot be pinned, mark that arm unavailable rather than substitute a mock and keep its name. Stubs are allowed only in clearly labeled gate-unit experiments that isolate scanner-independent properties.

If the immutable complete-request arm matches the proposed gate's safety and has lower overhead/less benign invalidation, that is a substantive negative result for the proposed mechanism. It must be retained.

## Trace model and exact finite denominator

Implement a small documented state machine with registration, scan, catalogue presentation, selection, approval, validation, enqueue, completion, revocation, and refresh events. Generate traces from state-machine transitions with explicit preconditions. Preserve a deterministic replay artifact for every generated trace.

Use named scheduling windows: before scan; between scan and presentation; between presentation and approval; between approval and validation; between validation and enqueue; and after enqueue. The gate's atomic region has a defined linearization point; the scheduler must not pretend an event occurred inside an indivisible region. It should schedule the event immediately before or after that region and evaluate the corresponding expected outcome. For a non-atomic implementation, an actual hook/barrier should expose the validation-to-enqueue window rather than merely relabel a serial sequence as a race.

Declare the finite universe before execution: fixture alphabet; allowed operations and mutation values; maximum trace length; maximum number of mutations/refreshes; number of server registrations and same-named tools; scheduling windows; and transition preconditions. These are protocol bounds, not empirically measured sample sizes. The generator emits the exact number of syntactically generated, semantically valid, deduplicated, executed, skipped, and failed-to-execute traces. Explain any symmetry reduction and retain a map from representatives to their equivalence classes.

Enumerate the **whole declared universe**. A chosen collection of examples should be called a challenge suite, not exhaustive enumeration. Synthetic variants and multiple scheduler positions are not independent samples from a real attack population. Do not attach binomial confidence intervals or significance claims that treat them as such. Report exact bounded counts and coverage by transition family.

Recommended challenge families:

| Family | Variation | Security property challenged |
| --- | --- | --- |
| Representation replacement | Descriptor changes between scan and selection representation; nested schema/annotation/extension-field changes | Scan/presentation and complete-field binding |
| Identity alias | Same tool name and identical descriptor registered by different host-scoped servers; registration order changes | Server identity binding |
| Connection replacement | Same registration label reconnects with a new generation before enqueue | Session binding and revocation |
| Selected-tool refresh | Approved descriptor changes before validation or enqueue | Descriptor binding and synchronization |
| Checked-call mutation | Arguments, tool name, or target reference change after approval or after validation | Exact operation binding |
| Approval revocation | Relevant policy/authorization changes before versus after enqueue | Ordering and revocation semantics |
| Compound transition | Two individually permitted mutations in different windows, including change-and-revert where allowed | Composition and stale-record handling |

Include negative controls proving the harness can detect an inconsistent dispatch. For example, an intentionally disabled gate must emit a mismatched transport receipt on at least one reachable challenge. An oracle that declares every trace safe or a sink that never receives any request cannot validate a security mechanism.

## Leakage-resistant suite partition

There is no model training here. The main leakage risk is implementation overfitting to visible fixtures and shared mistakes in generator, implementation, and oracle.

- **Development partition:** simple examples from each documented invariant, used while implementing and debugging.
- **Frozen evaluation partition:** fixture values and trace compositions held apart from development, generated by declared transformations after the policy and mechanism are frozen. Hold out composition patterns and boundary placements where feasible, not just random string spellings.
- **Independent challenge partition:** a reviewer/agent with no implementation file ownership constructs additional counterexamples from the written contract. Mark these as post-freeze challenge evidence, not as a random statistical sample. If a challenge causes a fix, record the old/new revisions and rerun all partitions; subsequent results are no longer an untouched first-pass holdout.
- **Regression partition:** every discovered failure receives a persistent trace. Regression cases are useful but cannot masquerade as unseen evaluation.

Record creation time, source provenance, generator revision, seed where randomness is used, fixture IDs, and content hashes. Prevent duplicate normalized traces or simple renamings from crossing partitions unnoticed. The headline denominators should distinguish unique transition structures from surface variants and repeated executions.

## Benign controls, supported controls, and exclusions

Benign controls must include normal unchanged calls; identical catalogue refresh; unrelated registration/removal; harmless descriptor key reordering; other explicitly equivalent encodings; authorized argument edits followed by fresh approval; legitimate selected-tool updates followed by rescan/reapproval; reconnect followed by fresh approval; concurrent calls to different tools; same-named legitimate tools on distinct servers; and a relevant update after enqueue.

Report immediate disposition and eventual completion separately. A conservative gate may reject a stale approval safely yet cause a temporary benign interruption. Count that interruption, then measure whether the documented rescan/reapproval/retry path completes. Do not call the first rejection either an attack blocked or a successful user workflow. Do not allow retries only for the proposed arm.

Maintain an applicability matrix for every challenge and comparator: supported target guarantee; outside native scanner scope but addressed by host integration; rejected/unsupported input; or out of the study's threat model. Every executed supported challenge remains in its arm's denominator. Out-of-scope controls appear in a separate table with the expected limitation, never as successful defenses.

Out-of-scope examples: malicious tool implementation retaining identical metadata; harmful behavior after a valid request is delivered; compromised trusted host/oracle; forged authentication outside the host's connection guarantees; semantic prompt injection contained in an otherwise consistently bound descriptor; harmful but explicitly approved arguments; network attackers beyond the transport model; effects occurring before detection; and actual LLM selection susceptibility. The gate must not be credited with solving these. A controlled example showing that unchanged malicious tool code still executes is a useful limitation demonstration.

## Metrics and reporting rules

For each arm and trace partition, report raw denominators alongside every fraction:

- **Invariant violations among dispatches:** actual receipts violating each oracle invariant divided by actual dispatch receipts; also report violating traces divided by eligible traces. No dispatch is distinct from a correct dispatch.
- **Unauthorized-dispatch prevention:** eligible challenge traces with no forbidden dispatch, together with the count that would produce a forbidden dispatch in the unprotected counterfactual. Separate safe successful dispatch, safe rejection, and execution failure. A crash or unsupported fixture is not silently counted as prevention.
- **Benign first-pass completion:** benign eligible traces completing the approved operation without rescan/reapproval/retry; report unnecessary rejections separately.
- **Benign eventual completion:** benign eligible traces completing under the same declared retry budget and retry algorithm for every applicable arm; report retries, rescans, and additional elapsed time.
- **Scope and coverage:** unique fixtures, unique transition structures, semantic attack families if any, supported/out-of-scope controls, generator exclusions, and exact bounded trace count. None represents real-world attack prevalence.
- **Audit correspondence:** receipts with complete recoverable links to checked descriptor, presented entry, approval, and decision. Also count missing, ambiguous, or contradictory records. Logging correctness is separate from prevention.
- **Performance:** operation-level gate latency, end-to-end local adapter latency, throughput under specified local concurrency, retry cost, and optional absolute memory change measured by an explicitly supported method.

Use a result table by invariant/family so a large number of trivial variants cannot swamp a failing rare transition. Report all counterexamples with minimal reproducible traces. Avoid combining semantic detector recall with binding-prevention metrics or calling deterministic state mismatches “tool-poisoning detection accuracy.”

## Counterfactual ablations

Change one enforcement component at a time while retaining the same adapter, complete trace universe, and policy unless the ablation itself requires a documented policy difference:

- Remove server namespace binding but retain the other fields.
- Replace complete metadata binding with the pinned comparator's actual partial representation, if it is partial; document the exact difference rather than invent a weak representation.
- Remove connection-generation binding.
- Remove argument/request binding while retaining descriptor binding.
- Remove atomic validation-to-enqueue while retaining the same checks and exposing the same actual scheduling hook.
- Remove global epoch binding while retaining immutable complete-request state and relevant revocation checks.

The final ablation is particularly important: if content/identity/request equality with proper synchronization suffices, a global catalogue epoch may offer no incremental safety and may reduce availability. Do not erase this possibility by defining the oracle to require epoch equality.

Interactions can matter. If all individual ablations remain safe because redundant checks cover them, report that honestly and test a small declared set of compound ablations. Do not claim each component is necessary merely because it appears in the design.

## Timing methodology

Timing is a separate experiment from trace enumeration. Freeze a representative distribution of supported benign and challenge operations; do not time only cases fast-rejected by one arm. Measure semantic scanner cost separately from gate-only cost, and include an integration total for arms using the same scanner.

Use a monotonic high-resolution timer on a documented machine/OS/runtime. Record power/load conditions and relevant dependency versions. Perform untimed initialization and a declared warm-up; distinguish cold-start and steady-state results. Run repeated independent process sessions, randomize or counterbalance arm order using a recorded seed, and pair arms on identical fixtures. Define each operation boundary, including whether canonicalization, hashing, locking, logging, allocation, rescan, and transport enqueue are included.

For very short gate operations, time batches large enough to exceed timer resolution and scheduler noise, report batch size, and retain an empty-harness control. Report raw times as well as any paired harness-adjusted estimate; do not conceal negative adjusted values or clamp them into a claimed zero overhead. Prevent dead-code elimination where applicable and avoid accumulating an unbounded log in one arm only.

Report medians and tail quantiles with the underlying repetition/unit definition. If confidence intervals are used for timing, resample independent process/session units, not correlated inner loop iterations. Provide raw measurements. Benchmark request rate and concurrency explicitly; increasing a total invocation count alone is not a load/scalability experiment.

Any percentage overhead uses a named paired baseline and shows both absolute times. Memory claims require an explicit measurement API, absolute units, baseline, measurement boundary, and repetitions. If reliable allocation or resident-memory measurement is unavailable, omit the memory claim. Offline local timing cannot establish network, remote-server, or LLM-agent production latency.

## Falsification and stop conditions

The proposed benefit is falsified or materially narrowed if any supported trace causes an oracle-violating receipt; if claimed safe behavior is only a logger/scheduler artifact; if a strong complete-request baseline provides the same safety with less complexity or fewer benign interruptions; if the proposed atomicity does not cover actual enqueue; if relevant revocation can race past it; or if the scanner/adapter boundary differs across arms enough to explain the result.

All-blocking behavior fails the usefulness claim even if no forbidden operation is dispatched. Failure to complete ordinary benign controls within the declared retry policy must be visible. If epoch checks improve only an artificially early-check baseline, the evidence supports a narrower observation about synchronization, not superiority over sound host designs.

A successful bounded study would demonstrate implemented host consistency properties and their local tradeoffs. It would still leave unproven: semantic maliciousness detection; real-world exploit frequency; security of server code; model behavior; broader protocol authentication; performance at deployment scale; unbounded concurrent correctness; and novelty relative to prior systems. Those limits belong in the paper's claim language and discussion, not only in a supplemental caveat.

## Minimum reproducibility package

Archive the pinned code and dependency manifests; host adapter contract; scanner configuration; canonicalization specification; frozen fixture/trace manifest; generator and independent oracle; all replayable traces and raw outcomes, including failures/exclusions; timing raw data; environment report; and the script producing manuscript tables from those artifacts. Include a concise command sequence for an offline reviewer run. A result number enters the manuscript only after it can be traced to a saved run and regenerated table.
