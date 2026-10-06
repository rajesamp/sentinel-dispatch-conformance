# Scenario and independent-oracle contract

This document defines a prospective synthetic challenge suite. Its cases are not empirical results, independently collected attacks, an exhaustive trace universe, or independent statistical samples. A specialist agent authored this suite separately from the core implementation. The agent inspected the core API to make the runner interface usable; this is interface-aware verification, not a blinded external audit.

## Freeze and partitions

`experiments/scenarios.py` is the authoritative declarative generator. `data/scenario_manifest.json` is its saved machine-readable output. Development cases cover isolated invariants and ordinary benign controls. Verification cases use disjoint composition labels and combinations of transitions, timing, identity, nested values, and recovery. Their primitive operations necessarily overlap: the holdout concerns compositions, not novel protocol operations or independent statistical sampling.

Before the first scored verification run, save the core, baseline, runner, scenario, and oracle revisions/hashes. The coordinator must record whether verification labels were read while implementing. A file that is merely named verification is not a blind holdout. If failures trigger fixes, retain the original run and label later runs regression-informed verification. Do not imply untouched first-pass holdout performance after tuning on those cases.

The manifest is finite and intentionally selected. Report its exact denominators by family and split, but call it a challenge suite. It is not exhaustive enumeration of the protocol proposed in `evaluation-plan.md`. If a bounded trace enumerator is later implemented, archive and report it separately.

## Runner schema and action order

Each case contains `id`, `family`, `split`, `kind`, `initial_catalogs`, `selection`, `arguments`, `operations`, `expected_policy`, `expected_receipt`, `expected_dispatch_count`, and `notes`. Initial catalogues are published in array order with explicit host server/connection IDs. Copy fixture structures per arm; an arm must not mutate another arm's inputs.

The runner performs initial publications, `select`, after-select operations, `prepare`, after-prepare operations, one default `execute`, and after-execute operations. Preserve operation order within each stage. A failed selection/prepare means no valid current approval/token. An explicit `execute_again` reuses the exact previously used token, not a freshly prepared permit. A `reapprove` reselects the original server/name, prepares with the current argument dictionary, and replaces the operation's approval/token; it resets prior relevant revocation only if a new valid approval actually exists.

Actions are `refresh(server, tools, connection)`; `begin_refresh(server, tag)`; `complete_refresh(server, tag, tools, connection)`; `mutate_args(path, value)`; `mutate_source(catalog_index, tool_index, path, value)`; `reapprove`; and `execute_again`. Begin/complete tags map to the revision returned by the adapter. Mutation actions modify caller-owned fixture values without a catalogue refresh. The source mutation target is the exact dictionary passed from the initial catalogue into the adapter, so the test can expose retained mutable aliases. `apply_mutation` provides the common fixture mutation helper.

The request envelope is local fixture JSON-RPC with `id=1`; concurrent live request ID management is outside this suite. The default connection is explicitly `c1`, rather than relying on the adapter's default value.

## Oracle contract and explicit revocation

`experiments/oracle.py` imports no gate code and consults no generation or epoch. `check_receipt(approval, receipt, revoked=...)` compares externally recorded approved server identity, connection identity, complete descriptor structure, and complete request structure with the actual writer/sink receipt. Object key order is immaterial; array order and scalar types are preserved. It rejects duplicate-key raw JSON. The runner captures actual bytes in `request`/`descriptor` or `request_bytes`/`descriptor_bytes`; gate return status is not evidence that a receipt did or did not occur.

Each operation declares `revokes_approval` from the written policy, independently of whether an arm notices it. Descriptor change, connection change, and selected-tool removal revoke the old approval. Restoration of identical values does not restore that old approval. An unrelated server/tool change, identical refresh, or object/catalogue reordering does not revoke it. This is relevant selected-operation revocation, not global epoch equality.

Out-of-order refresh policy is latest-requested-wins. A stale older completion is not an accepted publication and cannot independently revoke or restore an approval. The scenario's stale completion therefore has `revokes_approval=false`, even if its attempted descriptor differs. A successful newer descriptor change has `true`. The runner evaluates the intended publication ordering from declared events, not by asking the tested arm whether its own publication was valid.

Capture relevant revocation **at each actual enqueue**. A refresh after enqueue must not retroactively change that receipt's expected status. Receipts may include immutable `approval` and `revoked_at_dispatch` snapshots; `evaluate_receipts` uses them in preference to final-state defaults. The externally recorded approval should include the actual selected immutable record and proposed request at the approval boundary, rather than a mutable reference or an implementation generation.

`evaluate_receipts` returns separate `safe`, `policy_satisfied`, `violations`, `outcome_issues`, and `dispatch_count`. Missing benign dispatch is an availability/outcome failure, not a safety success worth claiming as useful protection. More than one receipt for these one-operation cases violates single-use authorization. Current cases contain one final intended operation; a general multi-approval trace needs a per-approval cardinality contract rather than this convenience rule.

Compare each valid receipt with both the external actual approval and `expected_receipt`. This prevents a wrong initial selection from redefining the expected target. A baseline that selects server B when the declared selection requested server A must fail the scenario's target correspondence even if its later request matches its own mistaken selection. Root runner may expose these expected-target failures separately from post-approval invariant failures, but must not call that scenario fully protected.

## Baselines and claim limits

These fixtures do not presume that the proposed gate beats an immutable complete-request baseline. A strong baseline with complete state snapshots, relevant revocation, single-use permits, and sound synchronization should satisfy this contract. Comparative equivalence is an acceptable and important outcome. Removing epoch equality must not automatically fail the oracle.

The suite covers caller aliasing, metadata completeness, server namespaces, connection replacement, stale selections, explicit withdrawal, ABA, refresh ordering, request snapshots, single-use authorization, and benign recovery. It does not by itself exercise a real inter-thread validation-to-enqueue race. Add independently instrumented scheduling-barrier tests before making an atomicity claim. It does not test semantic detector quality, malicious remote implementation with unchanged metadata, live LLM behavior, production transport authentication, exhaustive JSON Schema validation, or global unbounded concurrent correctness.

The test file validates fixture integrity and includes oracle negative controls for server/connection/request/descriptor mismatches, explicit revocation despite unchanged bytes, replay, absent approvals, and status/receipt disagreement. These checks validate the verifier mechanics. They are not defense efficacy results.
