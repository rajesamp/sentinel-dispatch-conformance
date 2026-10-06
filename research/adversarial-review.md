# Independent adversarial review

Task: `adversarial_review`; date: 2026-10-06. This is a bounded, local,
post-development review by a separate agent with no implementation ownership. It
is not a blinded external review, public preregistration, statistical attack
sample, or proof of production security. Only inert local inputs were used.

## Outcome and provenance

The review found and reproduced two narrow issues, both corrected by the
coordinator: a trusted admission callback could change the published name without
changing the frozen descriptor; and the independent receipt oracle accepted
non-finite overflow and a lone Unicode surrogate when both records contained the
same invalid value. Neither finding established a server-reachable dispatch
bypass in the tested adapter. The former requires a mutating trusted callback;
the latter is a verifier hardening defect outside the saved fixture alphabet.

At the tested revised hashes, all 20 reviewer tests passed. These include a
separate driver for both strong arms over the 259-word finite model: each arm
enqueued exactly 40 preserving traces and rejected all 219 traces containing a
revoking event. The actual receipt fields matched independently constructed
approvals. This is conformance to that explicit finite model, not evidence of
superiority over the strong snapshot baseline. The independent driver uses the
same generator but independently derives expected revocation from event-symbol
membership, rather than trusting its labels or either gate's decisions.

Initial HEAD was `e5a4152cbbb7eed858323f110b656a314368c25f`. Several research
files were untracked, so the HEAD alone does not identify the reviewed working
tree. SHA-256 values identify the exact inspected input revisions:

| File | Initial SHA-256 | Revised tested SHA-256 |
| --- | --- | --- |
| `src/binding_gate/core.py` | `87af227f91306220ec94b62aa7aeb0f093694e56a945a42c8632cff8cf872fe4` | `e3b27a4f5e0b6e5aa2b6036d45a293d993a312f26cffd4c2d8f03778d12cae5a` |
| `experiments/oracle.py` | `b3e9b5e712b6390621af8afc5725dbe06dc995c22248ba780293a45ddf55026a` | `6716fc80a252cff8dfbd585ccf6f660ab5f16d59310acd0d489606a93fa785b3` |
| `experiments/adapters.py` | `213c7316ee23c753ed3f2150125cdff81a65590b61396b374998cb4cb031220b` | unchanged |
| `experiments/scenarios.py` | `3b5a1cc28ad01d968e995c69cd32b27bc8a96cba874521c82d32782669d12c88` | unchanged |
| `experiments/enumerate_traces.py` | added during review | `66451d1b55666c3507d107adbd19e89c51e694a4c8ba77ca458027fe679322f5` |

Reviewer test file SHA-256:
`c83ecd1f54fae6bea0bfe593f86db2040ed1d944c7d35996ea1dac5ed271d8b9`.
Changes to these files require rerunning the checks. The reviewer edited only
`tests/test_adversarial_review.py` and this report; the coordinator implemented
the repairs. The first automated run of the review tests happened after those
repairs; the pre-fix evidence below comes from executed manual probes, not an
invented pre-fix unittest log.

## Preserved initial counterexamples

### A1: admission callback changes the published name

Initial `BindingGate.complete_refresh` froze a descriptor, decoded it into
`parsed`, passed `parsed` to a trusted callback, then used its possibly mutated
`name` as the publication key. The following local probe was executed:

```python
def mutate(descriptor):
    descriptor["name"] = "changed_by_host_callback"
    return True

gate = BindingGate(admit=mutate)
gate.refresh("s", [{"name": "read_file", "inputSchema": {"type": "object"}}], "c")
selection = gate.select("s", "changed_by_host_callback")
token = gate.prepare(selection, {})
receipts = []
gate.execute(token, lambda *values: receipts.append(values))
```

Observed: refresh accepted; request `params.name` was
`changed_by_host_callback`; saved descriptor `name` was `read_file`.
This broke internal name/descriptor correspondence. Minimal repair: retain the
validated original name before calling the callback. The coordinator made that
repair, and `test_callback_cannot_change_publication_name_away_from_frozen_descriptor`
now checks the correspondence.

Classification: trusted-host callback robustness. The shipped `semantic_admit`
does not perform this mutation, and a JSON-speaking server cannot install an
arbitrary callback under the declared threat model. Calling this a remote attack
would overstate the result. The repair does not make an arbitrary malicious
policy callback trustworthy; it only detaches publication identity from that
callback's local mutations.

### A2: invalid decoded JSON accepted by the independent oracle

For each of `b'{"n":1e999}'` and `b'{"s":"\\ud800"}'`, constructing approval
and receipt with the same raw descriptor and calling `check_receipt` returned
`[]`. The first value decodes to infinity in Python despite `parse_constant`
rejecting literal `Infinity`; the second decodes to a lone surrogate. The core's
strict snapshot function rejects both corresponding Python values.

Minimal repair: add independent recursive JSON-value validation after decoding,
including finite floats and strict UTF-8 encoding for strings. The coordinator
implemented it without importing core validation. The regression test
`test_oracle_rejects_overflowed_number_and_nonunicode_scalar` passes for both
cases. This is verifier hardening; no current finite trace contained those
values, and no false headline safety result was demonstrated.

## Attempted falsifications and observed boundaries

| Attempt | Observed result | Interpretation |
| --- | --- | --- |
| Unissued, other-instance, and wrong-type permits | No enqueue | Permits are scoped to the local pending store; this test does not estimate token-guessing probabilities. |
| Alter selected server, name, connection, descriptor, or generation | Preparation denied | Relevant selected fields are checked against host state. |
| Copy a legitimate `Selection` and prepare different arguments | Preparation accepted | Expected trusted-host authority: `prepare` is where a trusted caller requests approval; it does not authenticate human intent. |
| Eight callers concurrently replay one token | Exactly one enqueue in each strong arm | The bounded replay schedule preserves single use. |
| Pause inside writer before recording enqueue; concurrently attempt refresh | Enqueue precedes publication in both strong arms | Host lock covers this observed writer/enqueue boundary; it does not lock a remote server. |
| Publish revocation before execute | No enqueue in either strong arm | Before-enqueue revocation is honored. |
| Withdraw and restore identical bytes | Old selections and tokens rejected in both strong arms | Revocation survives ABA. |
| Same ABA against full-hash-only arm | One enqueue | Intended absence of revocation memory; a capability distinction, not evidence against the stronger baseline. |
| Stale malformed completion after a valid latest completion | Latest binding preserved; old approval can complete | Obsolete failed work cannot withdraw an accepted current snapshot. |
| Latest duplicate-name refresh | Whole target server withdrawn; unrelated server still usable | No prefix publication on failure; scope isolation preserved. |
| Pause scanner on second staged descriptor | First staged descriptor invisible; old snapshot still usable | Publication is atomic; pending scan does not itself revoke the old snapshot. |
| Writer records enqueue then raises | `transport outcome unknown`; token consumed; one receipt remains | A transport exception cannot be scored as a safe prevented dispatch solely from `allowed=false`. |
| Writer reenters `select` on its own gate | Disposable process times out at 0.5 s and is killed | Documented unsupported trusted-host callback; the ordinary lock is non-reentrant. This is an availability limitation, not a remote metadata exploit. |
| Raw duplicate-key JSON supplied directly to gate | Rejected as unsupported input | The gate expects Python JSON objects. Duplicate keys already discarded by a preceding parser cannot be detected here. |
| Infinity, NaN, surrogate, custom object, or cycle in descriptor | Rejected | Only the finite/Unicode cases are representable as relevant parser outputs; cycles/custom objects are host-only robustness cases. |

The callback reentry regression intentionally demonstrates the documented
restriction and bounds cleanup. It does not assert that hanging is desirable or
safe. A production host should enforce its non-reentrant writer contract or add
explicit reentry detection, rather than counting this timeout as protection.

## Conservative numeric invalidation

An additional probe found that an extension-field value `-0.0` and `+0.0` produce
different canonical bytes while the independent typed structural oracle considers
them equal. The coordinator explicitly chose structural numeric equality for
the safety oracle and conservative canonical-byte comparison in both strong
arms. The reviewer therefore rejected the alternative of changing the oracle to
mirror the implementation's byte policy.

`test_signed_zero_exposes_conservative_gate_invalidation` documents the tradeoff:
both strong arms reject a previously prepared request after a sign-of-zero
refresh. This is one independently added benign counterexample to any broad
claim of zero unnecessary invalidation over structurally equivalent metadata.
It is outside the frozen six-event alphabet and must be reported separately;
the 40 preserving finite-model traces contain no numeric variation. No claim of
general semantic JSON-Schema equivalence is supported.

## Oracle independence and comparison fairness

The receipt oracle imports no gate, canonicalizer, epoch, or generation logic.
It compares externally captured identities, complete structured descriptors,
requests, and relevant revocation-at-enqueue. The added invalid-JSON failure
shows why independence is useful: the verifier needed its own correction rather
than inheriting the gate's validation result. The trusted sink must preserve
real bytes and external approval snapshots; accepting a receipt generated only
from the gate's successful status would still invalidate the study.

`SnapshotAdapter("revoke")` is a meaningful strong comparison: full immutable
request, server/connection scope, current view identity retaining ABA history,
single-use token, and lock across validation/writer. The corresponding gate uses
generations to establish the same selected-operation property. On the reviewer's
259-case driver they match exactly. This supports equivalence on that model and
rejects any claimed necessity of generations or global epochs for those traces.

The full-hash baseline lacks revocation history by design; its ABA failure must
not substitute for comparison with the strong revocation-aware snapshot arm.
The deliberately naive host's mutable routing should remain a positive failure
control, not be attributed as the upstream scanner's universal behavior. Shared
descriptor validation/canonicalization between strong arms is neutral common
infrastructure, but means they are not wholly independent implementations; the
independent structural oracle and preserved original fixtures partly reduce,
but do not eliminate, that shared-error risk.

Gate-unit tests use its structure-only default callback where policy isolation
is the purpose. The finite driver uses descriptors accepted by the strong
scanner-backed baseline. Headline integration runs must still hold semantic
scanner configuration constant, as required by the evaluation plan; the reviewer
does not substitute unit-test totals for those integration results.

## Finite model and claim controls

The enumerator yields all words of length 0 through 3 over its six symbols:
`1 + 6 + 36 + 216 = 259`. No state-dependent transition precondition excludes a
word. The approval is revoked if a word contains `publish_changed`, `withdraw`,
or `reconnect`, and revocation is absorbing. The remaining three symbols yield
`1 + 3 + 9 + 27 = 40` preserving words; the other 219 require rejection. The
independent event-membership check agrees with every generated label, and the
independent two-arm driver obtains exactly those receipt counts.

This enumeration is exhaustive only within that serial word model. It excludes
within-scan mutation, pending/stale refresh completion, recovery/reapproval,
multiple approvals, variable request IDs, genuine transport reconnect identity,
and concurrent interleavings. Some are separately challenged by named cases or
barrier tests, but they do not thereby enter the enumerated universe. Repeated
no-op symbols and similar words remain correlated designed traces, not
independent attacks.

The reviewed plans accurately call the 36 scenarios a designed challenge suite
and the finite enumeration specification-aware conformance evidence. The
reviewer read implementations, the coordinator read findings and fixed code,
and all revised results are regression-informed. A later artifact freeze is a
reproducibility checkpoint; it cannot be described as prior public
preregistration or untouched blind holdout testing.

## Execution evidence and reproduction

From the package root:

```sh
PYTHONPATH=src:. python3 -m unittest discover -s tests -p test_adversarial_review.py -v
PYTHONPATH=src:. python3 -m unittest discover -s tests
```

Observed final review run: `Ran 20 tests in 0.781s`, `OK`. Observed combined
authored suite at that revision: `Ran 60 tests in 0.821s`, `OK`. Test-method
counts are not attack counts; the finite-driver method alone runs 259 cases for
each of two arms. These durations are ordinary test runtimes, not benchmark
measurements. The combined discovery does not include the vendored upstream's
separate original test directory. The pre-fix manual outcomes above remain
preserved even though the revised tests pass.

## Decisions, uncertainty, and coverage gaps

Decisions: classify callback mutation as host robustness instead of remote
exploit because the server cannot choose callbacks; retain the strong snapshot
baseline instead of crediting only weak-arm failures because it implements the
same required safety contract; retain structural numeric equality in the oracle
instead of making it copy byte policy because harmless invalidation is itself
an outcome to expose; describe post-fix checks as regression-informed rather
than blind because implementations and findings were exchanged.

Uncertainty: the audit found no supported server-reachable bypass in the tested
bounded schedules, but this does not imply none exists. Scheduler tests cover
selected real thread interleavings, not all interleavings or linearizability
proofs. Both strong implementations share Python serialization and some
validation helpers. A future runner must still establish independent sink
receipts, attribution, complete logs, and actual comparison denominators.

Coverage gaps: no network exploit, real credential, production MCP SDK, remote
server behavior/attestation, LLM selection, semantic injection detector quality,
authorization-policy revision API, host identity authentication, raw transport
parser, resource-exhaustion bound for total catalogue bytes, request-ID
multiplexing, performance benchmark, or final manuscript audit. The broad
evaluation plan contains some of those prospective items; this implementation
does not satisfy them merely because they are written there. Future paper claims
must be restricted to the experiments actually executed and their source hashes.
