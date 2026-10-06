# Independent baseline audit: descriptor-to-dispatch binding

Task `research-build/baseline-audit`; reviewed 2026-10-06. Baseline: `rajesamp/sentinel-tpd` commit `5ce5d56e57a0acd092435fca5d89b78d0b39ee7b`. This is a static derivation and proposed test plan, **not an executed experiment**. Original source was not changed or executed. The reference guard implementation was not inspected, preserving independence.

## Finding and scope

The strongest unconditional source counterexample is admission of malformed input-schema values despite documented fail-closed handling. Binding-related counterexamples mostly require explicit host integration or concurrency preconditions. The baseline deliberately implements metadata classification plus a per-name fingerprint registry; it does not claim to supply a complete MCP host or dispatch capability. A fair paper must distinguish a baseline defect from a stronger integration contract the new guard introduces.

Reject the suggestion that a clean refresh lifting quarantine is itself a vulnerability. This is documented and tested recovery behavior. Likewise, submitting changed covered metadata at invocation is caught; stale registration alone is not a successful bypass when the current descriptor is checked.

## Primary sources and exact locations

All code links below are immutable at the baseline commit:

- [scanner.py 61–87](https://github.com/rajesamp/sentinel-tpd/blob/5ce5d56e57a0acd092435fca5d89b78d0b39ee7b/sentinel_tpd/scanner.py#L61-L87): scanned text consists of configured top-level fields, then nested `description`/`title` inside input schema; non-dict/list schema nodes are silently skipped.
- [scanner.py 96–107](https://github.com/rajesamp/sentinel-tpd/blob/5ce5d56e57a0acd092435fca5d89b78d0b39ee7b/sentinel_tpd/scanner.py#L96-L107): canonical subset includes only name, description, and inputSchema/input_schema; JSON serialization permits `default=str`.
- [scanner.py 110–162](https://github.com/rajesamp/sentinel-tpd/blob/5ce5d56e57a0acd092435fca5d89b78d0b39ee7b/sentinel_tpd/scanner.py#L110-L162): explicit validation checks only dict type and nonblank string name, then allows when no pattern crosses the severity threshold.
- [scanner.py 8–9](https://github.com/rajesamp/sentinel-tpd/blob/5ce5d56e57a0acd092435fca5d89b78d0b39ee7b/sentinel_tpd/scanner.py#L8-L9): documentation promises fail-closed handling of unparseable schemas.
- [signals.py 152–156](https://github.com/rajesamp/sentinel-tpd/blob/5ce5d56e57a0acd092435fca5d89b78d0b39ee7b/sentinel_tpd/signals.py#L152-L156): top-level scan fields are name and description; default denial threshold is 3.
- [registry.py 26–60](https://github.com/rajesamp/sentinel-tpd/blob/5ce5d56e57a0acd092435fca5d89b78d0b39ee7b/sentinel_tpd/registry.py#L26-L60): decision records contain name, Boolean and reason; state keyed only by name; registration scans, writes an audit event, then fingerprints the original mutable object if allowed.
- [registry.py 65–114](https://github.com/rajesamp/sentinel-tpd/blob/5ce5d56e57a0acd092435fca5d89b78d0b39ee7b/sentinel_tpd/registry.py#L65-L114): invocation checks current name/quarantine/fingerprint and returns a decision, with no dispatch function or bound target.
- [registry.py 118–136](https://github.com/rajesamp/sentinel-tpd/blob/5ce5d56e57a0acd092435fca5d89b78d0b39ee7b/sentinel_tpd/registry.py#L118-L136): refresh clears the fingerprint map, registers each item in order, and lifts quarantine after a clean scan.
- [tests/test_sentinel_tpd.py 101–120](https://github.com/rajesamp/sentinel-tpd/blob/5ce5d56e57a0acd092435fca5d89b78d0b39ee7b/tests/test_sentinel_tpd.py#L101-L120): mutation is denied and clean refresh recovery is intentional.
- [README 78–98](https://github.com/rajesamp/sentinel-tpd/blob/5ce5d56e57a0acd092435fca5d89b78d0b39ee7b/README.md#L78-L98): plain-dict, framework-independent interface; host wiring required; fingerprint fields and unchanged-metadata behavior limitation explicitly documented.

Protocol context is fixed to [MCP specification 2025-11-25, Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools), consulted 2026-10-06. This edition lists title, outputSchema and annotations as tool fields, requires an input-schema object, treats annotations from untrusted servers as untrusted, and recommends names unique within a server. Discovery is paginated and refresh notification prompts another listing. Invocation sends name and arguments to a selected server. These facts motivate the proposed test preconditions; they do not impose the new guard's entire security contract on the baseline. No claim is made that this is the latest protocol edition.

## Narrow threat model and proposed invariants

The trusted host owns connection identities, the tool catalogue, model-exposure projection, policy, and dispatch. An adversarial connected server controls its own advertised descriptors and update timing, including names colliding with another server. It cannot forge a trusted connection identity, alter host policy, edit guard internals, or execute arbitrary host callbacks. Deterministic scheduler hooks may model legal host interleavings; they are test instrumentation, not new adversary powers.

Bounded objective: every accepted dispatch must correspond to an allowed descriptor snapshot, on the same trusted server/connection and tool name, under the policy/catalogue generation actually checked. Any host-visible descriptor surface included in that decision must match the checked snapshot at the dispatch boundary. Legitimate other-server tools and explicitly approved fresh snapshots must remain callable. This contract does not establish that tool code behaves honestly, that semantic prompt injection is solved, or that unchanged-metadata attacks are detectable.

The host must declare exactly which descriptor fields reach its model/UI or affect policy. A title or output-schema mutation is security relevant only if that field is consumed. Hashing all JSON fields is one conservative design; a documented canonical projection is also defensible. Network origin identity comes from the trusted transport binding, not an untrusted `server_id` field embedded in tool metadata.

## Disjoint proposed cases

Expected baseline outcomes below follow from the source and remain to be executed. Use a clean seed descriptor `name="lookup"`, `description="Return a value."`, `inputSchema={"type":"object"}`. Use a controlled marker such as `<IMPORTANT>test marker</IMPORTANT>` where a known denial-pattern hit is needed; no harmful real tool execution is necessary. Every test gets a fresh registry and records raw events, returned decisions, and any fake dispatch target.

### D1 — malformed schema admission: direct contract mismatch

Precondition: raw deserialized dictionaries reach the library without an upstream MCP validator. Separately substitute null, a string, a number, or a list for inputSchema; also test missing inputSchema. Register then check exactly the same descriptor. Expected source behavior: no findings, admission succeeds, matching invocation succeeds. Scanner performs no schema-shape validation. Do not imply any real SDK accepts these descriptors: an SDK schema gate may reject them before this layer. Report as malformed metadata acceptance, not successful harmful execution. A valid empty-parameter object is the benign paired control. Avoid calling every unknown JSON-Schema keyword invalid; that is a separate standards question.

### S1 — exposed-field mutation outside baseline projection: deliberate scope extension

Precondition: a host actually uses the specified field. Register a descriptor with a benign top-level title, then change only that title before check. Repeat independently for `annotations.title` and an `outputSchema` description. Expected baseline: fingerprint unchanged, invocation allowed; the added text is not scanned on refresh either. Each case isolates a different omitted field; do not bundle them. Paired control: change only the covered description, which must deny. This demonstrates insufficient coverage for the declared host projection, not violation of the README's explicitly limited fingerprint scope. If the host drops the field, there is no exposure counterexample.

### I1 — cross-server same-name catalogue overwrite: integration contract gap

Precondition: one registry is shared across multiple trusted connections without server namespacing. Register clean A/lookup, then clean B/lookup with a different description. Expected baseline: both registrations allow; B overwrites the sole fingerprint. Checking B allows. Checking A detects a mismatch and quarantines the shared name, after which B is denied too. This is a deterministic cross-server collision/availability failure of that adapter. It is not itself proof that B was selected maliciously. Paired control: separate registries for A and B avoid the collision.

### I2 — identical descriptors, substituted dispatch origin: integration contract gap

Precondition: the host can select one origin for checking and another origin for dispatch; A and B advertise identical descriptors. Check the registered A descriptor, then route the test dispatch to B. Baseline returns a Boolean decision with no origin binding; a naive adapter may send to B. Oracle is equality of checked and dispatched trusted origins, not a claim that B's code exfiltrated anything. This trace tests the adapter, because baseline has no server parameter or dispatcher. A correct host independently retaining A's transport route must pass. Do not present a purposefully miswired adapter as universal baseline behavior.

### I3 — mutation after invocation decision, before use: host check/use gap

Precondition: asynchronous host code stores a decision, then reads a shared descriptor or route again after an adversarial catalogue update. Obtain an allowed invocation decision, update the shared description or target, then have the fake dispatch/model-exposure step consume the new object. The decision cannot revoke itself and carries no checked fingerprint/generation. Record the mismatch between the captured checked snapshot and actual consumption. Paired controls: current metadata mutated before check denies; a copied descriptor and serialized check-to-dispatch path succeeds safely. Classify as adapter lifecycle gap unless the new API expressly owns dispatch.

### C1 — mutation between registration scan and fingerprint: conditional concurrency gap

Precondition: a trusted host catalogue stores mutable dictionaries and may update the same object concurrently with register. Registration order is scan → audit append → fingerprint; the last operation reads the original object again. Use a deterministic scheduling hook at the audit boundary to pause registration, let the normal catalogue-update worker replace only description with the denial marker, then resume. Expected: clean verdict from the original content, fingerprint of the poisoned content, subsequent check of poisoned content allowed. The hook is not a malicious AuditChain implementation; it models an interleaving. Compare with a benign no-interleaving control and with mutation after register returns (which should deny). Report thread/shared-reference precondition because thread safety is not promised by the baseline.

### R1 — denied re-registration retains old admission: observable state, conditional policy conflict

Precondition: caller uses register, not rescan_on_refresh, to process replacement metadata. Register clean A; register same-name poisoned A2 and receive denial; check the old A descriptor. Expected: old A still allowed because denial does not remove its fingerprint. Check A2 separately in a fresh equivalent sequence: it mismatches, quarantines and denies. Thus denial is not a bypass for checking current A2. Old-A acceptance conflicts only with a defined policy that replacement admission revokes all earlier authorization. If policy permits continued use of the last good immutable descriptor, this is acceptable. State that contract before scoring the test.

### R2 — partial refresh visibility: conditional atomicity test

Precondition: calls can occur concurrently with refresh. Refresh clears existing fingerprints and registers items sequentially. Pause after first candidate is admitted but before remaining candidates are processed; observe calls. Source predicts a partially published catalogue and temporary denial of not-yet-reinserted legitimate tools. This is not automatically an unsafe allow: each published item passed its own scan. Test only a predeclared atomic-snapshot invariant, and report availability separately from security. A sequential caller cannot observe intermediate state through normal return. A source-level exception case using cyclic Python objects is not a valid wire-format attack; exclude it from the core MCP threat model.

## Rejected or qualified candidates

- Clean refresh after quarantined mutation is **intended recovery**, not quarantine bypass. Keep as a required positive control. An operator-approval requirement would be a new policy, not a recovered baseline requirement.
- A poisoned refresh of an already quarantined name does not lift quarantine: the removal condition requires allowed=true. Test this negative control.
- Mutating an ordinary covered descriptor after register returns is caught at invocation. It is not a bypass.
- A denied new descriptor does not pass check_invocation merely because an older same-name entry exists; the differing fingerprint causes denial. The stale-entry finding requires checking the old descriptor or another integration assumption.
- Unknown nonblank names are denied if absent from the registry. Malformed *schemas* should not be conflated with unknown tools.
- A server changes its actual code/behavior while preserving metadata: explicitly outside the baseline and proposed binding model. A matching fingerprint cannot attest code semantics.
- Freshly re-registering changed clean metadata replaces its fingerprint by design. Generation invalidation can be a stricter reference policy but should not be counted as attack prevention without a stale-use threat trace.
- Partial refresh after an exception primarily concerns state consistency/availability. JSON-invalid Python cycles, custom objects or malicious audit callbacks do not represent a remote JSON-speaking attacker under this threat model.

## Fair comparison and measurement

Evaluate at least (a) direct baseline behavior within documented single-server/sequential scope, (b) a plainly disclosed naive shared-registry adapter, and (c) a strengthened adapter with a registry per trusted server, immutable descriptor copies and serialized check/dispatch. If the strengthened adapter satisfies the same binding invariants, report that result; the contribution may be an explicit API/contract and reproducible conformance suite rather than a novel detection algorithm.

Keep direct defects, scope extensions, concurrency cases and adapter gaps in separate result groups. Do not pool them into an attack-detection percentage. Use per-case invariant satisfaction, unexpected dispatch count, legitimate-call preservation, and reproducible event traces. Distinct perturbations of one invariant are variants, not independent attack families. Freeze expected outcomes and host preconditions before executing the reference implementation. Include order permutations and paired benign controls without treating repetitions as new security cases.

## Handoff

- Result: one direct malformed-schema validation mismatch; several conditional binding/snapshot gaps with explicit integration requirements; clean recovery and covered-metadata mutation handling must be positive controls.
- Decisions: source logic over broad marketing claims; strongest appropriate baseline adapter over strawman host integration; predeclared invariants over retroactive attack labels; no execution until root vendors the original source.
- Uncertainty: no proposed outcome has been empirically run in this audit; real host exposure projections, SDK validation and synchronization may eliminate cases; callback scheduling instrumentation requires careful attribution.
- Coverage gaps: no semantic attack-quality evaluation, network deployment, adaptive attack generation, MCP SDK survey, reference implementation reading, performance measurement or novelty assessment. The separate novelty reviewer owns directly competing work.

## Executable follow-up supplied for root verification

Following explicit local implementation authorization, `experiments/upstream_counterexamples.py` and `tests/test_upstream_counterexamples.py` were added without changing the vendor. The script verifies Git blob hashes for all five imported baseline modules before loading them under a private package namespace. It uses inert metadata, in-memory audit objects, no actual tool dispatch, no network requests, and no file writes. JSON goes to stdout and includes pinned source provenance, observed/expected Boolean values, support classes, preconditions and interpretations.

The script implements 18 records: five ordinary/recovery controls, five malformed-schema variants, one denied-replacement observation, three omitted-field variants, one controlled registration interleaving and its copied-snapshot control, and a shared-registry collision with its per-server adapter control. These are not 18 independent attack families. Eleven unittest methods cover observations, controls and export/provenance. The race uses two barriers; only a separate catalogue-update actor mutates the shared descriptor. The audit subclass only waits at the scan-to-fingerprint boundary.

At handoff, both new files passed Python syntax parsing. Root owns execution and measurement results. From the project directory:

```sh
python3 -m unittest discover -s tests -p test_upstream_counterexamples.py -v
python3 experiments/upstream_counterexamples.py
```

To preserve the emitted record after a successful run, the caller can redirect the second command into its chosen results file. No performance or novelty claim is implied by these source-contract reproductions.
