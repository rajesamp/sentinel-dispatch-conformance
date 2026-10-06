# Independent final evidence audit

Reviewed 2026-10-06 by the independent adversarial-review agent. Final evidence
roots: `results/python312-final/` and `results/python312-final-repeat/`. Both root
`reproduction.json` records reported `completed` before their raw checks began.
The earlier `results/python312-primary/` was also fully audited, exposed a
comparison defect, and remains preserved. This reviewer changed only this report.
The coordinator repaired the defect and produced fresh final directories; no
archived raw results were rewritten. The manuscript was still being prepared and
is outside this audit.

## Verdict

Completed raw checks found no discrepancy between saved trials, independently
reconstructed outcomes, and generated summaries. Both designed and enumerated
runs have complete case-by-method coverage, no duplicate trials, no failed
executions, valid saved hashes, and matching regenerated reports. In each final
run, all 1,770 arm-case trials and all 596 local enqueue receipts were checked,
not merely a sample. The two final runs have identical safety and completion
outcomes. The designed and enumerated suites remain separate denominators.

The initial audit found that the `global_epoch` arm rejected a fresh selection
because an unrelated server was published before that selection. The coordinator
fixed selection-time epoch capture in commit
`4e20ddda10b2f3a0dd5e1ec8fd25bfa1cd9e1389` and added a regression test. Independent
checks of the final raw records confirm the correction. Exactly one designed
arm-case outcome changed; all enumerated outcomes and the per-binding gate versus
strong snapshot equivalence are unchanged. The historical defect is documented
below rather than hidden by replacement evidence.

## Independently recalculated counts

Designed suite in each final run: 36 cases × 6 methods = 216 trials; 142 actual receipts. Of the
36 cases, 11 are labeled benign; 7 have no authored reapproval and 4 contain a
fresh-approval path. Every method completed its runner execution. These are local
enqueue outcomes, not remote execution success.

| Method | Unsafe traces / 36 | Unsafe receipts / receipts | Fully satisfied / 36 | Benign first / 7 | Benign final / 11 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `naive_host` | 23 | 23/35 | 13 | 6 | 10 |
| `scoped_upstream` | 9 | 9/30 | 27 | 7 | 11 |
| `snapshot_hash` | 4 | 4/25 | 32 | 7 | 11 |
| `snapshot_revocation` | 0 | 0/21 | 36 | 7 | 11 |
| `binding_gate` | 0 | 0/21 | 36 | 7 | 11 |
| `global_epoch` | 0 | 0/10 | 25 | 2 | 6 |

Enumerated suite in each final run: 259 words × 6 methods = 1,554 trials; 454 actual receipts.
The 259 cases are all labeled `challenge`, so the generated benign denominator
is zero. Independently, the declared alphabet gives 40 operation-preserving
words and 219 revoking words. These preserving words must not be confused with
the separate designed suite's 11 explicitly labeled benign cases.

| Method | Unsafe traces / 259 | Unsafe receipts / receipts | Fully satisfied / 259 | Safe enqueues | Safe rejections |
| --- | ---: | ---: | ---: | ---: | ---: |
| `naive_host` | 210 | 210/218 | 49 | 8 | 41 |
| `scoped_upstream` | 36 | 36/76 | 223 | 40 | 183 |
| `snapshot_hash` | 36 | 36/76 | 223 | 40 | 183 |
| `snapshot_revocation` | 0 | 0/40 | 259 | 40 | 219 |
| `binding_gate` | 0 | 0/40 | 259 | 40 | 219 |
| `global_epoch` | 0 | 0/4 | 223 | 4 | 255 |

The strongest comparison is exact equality of the per-binding gate and the
revocation-aware snapshot arm on both declared suites. A method that blocks an
expected enqueue remains safe but fails the completion policy. Thus the global
variant's zero unsafe receipts does not conceal its extra rejections.

## Verification method

Checks used an independent standard-library script executed in this review. It
did not import `report_results`, `run_study`, the receipt oracle, the adapters,
the gate, or the scenario generators. Inputs were saved JSON/JSONL and the
reviewed source text. Assertions covered:

1. Root and per-suite completion statuses; recorded artifact SHA-256 hashes;
   independently serialized manifest, environment, and source-map digests; and
   agreement of every source-map entry with current source bytes at audit time.
2. Exact manifest-case × declared-method products, unique trial keys, per-case
   hashes and labels, and consistent record provenance. Counts were 216/216
   and 1,554/1,554 in each final run, with no missing, duplicate, or
   out-of-manifest records.
3. Every operation's declared revocation flag, using a separate logical catalogue
   model with latest-requested-wins refresh revisions, independent of adapter
   acceptance. Initial catalogue values were copied, source mutations did not
   silently publish, stale completions did not revoke, and relevant descriptor,
   connection, or removal changes did revoke.
4. Manifest stage order against each raw event sequence; matching start/completion
   operation indices; preserved approval history; independent reconstruction of
   proposed argument changes; and approval request/descriptor bytes corresponding
   to the selected snapshot and proposed operation at each preparation.
5. Every enqueue event against its receipt record, then-current approval,
   revocation flag, and event sequence number. Base64 envelopes were decoded to
   actual bytes. A separate typed structural comparison recomputed identity,
   descriptor, request, revocation, replay, declared-target, and dispatch-count
   outcomes. These agreed with every saved violation and outcome issue.
6. Independently recomputed trial, receipt, violation, policy, full-completion,
   benign-completion, safe-enqueue, and safe-rejection counts against method,
   split, and family summaries. Generated summary JSON, Markdown, and LaTeX files
   were byte-identical to the separately regenerated copies.
7. The exact enumerated word set against an independently constructed Cartesian
   product for lengths 0 through 3. Every policy label also matched the separate
   predicate “contains `publish_changed`, `withdraw`, or `reconnect`.” This gives
   219 deny labels and 40 allow labels without consulting gate decisions.

The independent script's terminal conclusion was
`ALL INDEPENDENT RAW CHECKS PASSED`. This is a post-run verification statement,
not a new prior registration or a claim of blinding. Source-reading and prior
regression fixes were known to the reviewer.

## Runner circularity and event order

The runner's order is initial publication → selection → after-select operations
→ preparation → after-prepare operations → default execute → after-execute
operations. It captures the selected descriptor outside the adapter and captures
the proposed request before passing mutable arguments into `prepare`. Each
actual writer call records its bytes and external approval/revocation snapshot.
Returned allow/deny status does not substitute for a sink receipt.

The successful preparation predicate does determine whether an external approval
is active, but this does not make completion tautological: manifest-derived
expected dispatch counts and targets are separate. A method that refuses every
preparation fails all cases requiring an enqueue. A method returning a mismatched
selected origin cannot redefine the manifest's expected target. Independently
recomputed raw outcomes confirm these distinctions in the completed runs.

Revocation flags come from declared events, not the tested method's acceptance.
The audit separately validated those flags against catalogue state. A reapproval
only resets revocation when a fresh token exists. Each receipt retains its
then-active state, so a post-enqueue refresh does not retroactively invalidate
the earlier enqueue. Replay uses the consumed token, rather than manufacturing a
second approval. No outcome here depends on epoch equality in the oracle.

This is nevertheless selection/approval/local-enqueue evidence. The runner does
not retain a separately instrumented scanner-completion record or an actual
model/UI presentation record for every descriptor. It cannot establish the
broader prospective evaluation plan's entire scan-to-presentation audit chain.

## Representative controls and failures

These observations were read directly from raw trials after all-record checks:

- `dev-normal`: all six arms enqueue once and fully satisfy the case. The sink
  is exercised; safety is not achieved by suppressing all dispatches.
- `dev-server-namespace`: the naive host enqueues the wrong server; the strong
  snapshot and per-binding gate enqueue the intended server. The corrected global
  arm also enqueues the intended server. In the preserved initial run it produced
  no token; see the defect history below.
- `dev-title-refresh`: naive and scoped-upstream arms enqueue a changed descriptor
  after relevant revocation. Full-descriptor equality and both stronger arms
  reject. This concerns the declared full-descriptor host surface, not upstream
  semantic-detector accuracy.
- `dev-description-aba` and `verify-selection-aba`: naive, scoped, and full-byte
  equality arms enqueue after revocation despite restored bytes; strong snapshot
  and per-binding arms reject.
- `dev-outoforder-refresh`: naive dispatches a descriptor from the obsolete
  completion. Strong snapshot and per-binding arms preserve the approved request.
- `verify-newer-change-stale-restore`: the naive arm dispatches after relevant
  revocation; strong snapshot and per-binding arms reject.
- `dev-clean-recovery`: every arm completes the explicit fresh-approval path.
  These are authored reapproval operations, not measured retries after a failed
  dispatch.
- `dev-single-use`: each arm has exactly one receipt despite a replay attempt.
- `verify-after-enqueue-refresh`: all arms retain a valid earlier receipt after
  a later relevant update. The oracle does not retroactively revoke it.

## Global-epoch defect and verified correction

The pre-fix source stored `Selection.catalog_epoch` when a binding was published.
`select` returned that existing object; global mode subsequently required its
stored epoch to equal the current global epoch. In the preserved primary run's
raw `dev-server-namespace`, the event order was:

1. Publish server A at the first global epoch.
2. Publish server B at the second global epoch.
3. Select A's unchanged tool.
4. Preparation returns no token although `revoked=false`.
5. Execute returns “unknown or consumed permit”; no enqueue occurs.

There was no operation between selection and preparation. The coordinator changed
global-mode `select` to return a fresh selection stamped with the current epoch,
while retaining the selected descriptor, connection, and per-binding generation.
Subsequent global publication still invalidates that selection. The regression
test checks both successful fresh selection after earlier unrelated publication
and rejection after a later unrelated publication.

In both final runs this case now records a valid external approval and exactly
one correct enqueue. Comparing every primary outcome with the final outcome
showed only `('dev-server-namespace', 'global_epoch')` changed: global designed
completion rises from 24/36 with 9 receipts to 25/36 with 10 receipts. The original
and final reports are preserved separately. The 259-word experiment starts from
one server and has no outcome changes; its global variant still intentionally
invalidates unchanged or unrelated post-approval publications.

## Timing verification and interpretation

Each final designed run contains 6,820 complete timing records: 620 warmup batches and
6,200 measured batches. There are 31 operation/method groups, each with 20 warmup
and 200 measured batches of 16 operations. That is 99,200 measured operations,
including 3,200 shared-scanner operations. The enumerated run has an empty timing
file as declared. The two final process sessions were verified separately, for
13,640 checked timing batches in total. Repeated sessions do not add unique
security scenarios or change the scenario denominators.

The audit independently checked every elapsed-nanoseconds/batch-size conversion,
paired empty-harness calculation, un-clamped adjusted value, and raw/empty/adjusted
summary median, nearest-rank p95, minimum and maximum. Each of 1,100 six-method
pairs has exactly the recorded common method permutation and correct order indices.
Warmup and measured repeat sets have no omissions or duplicates. All generated
timing quantiles agree with raw samples.

Selected descriptive medians of batch means, in microseconds per operation:

| Boundary | Strong snapshot, final / repeat | Per-binding gate, final / repeat |
| --- | ---: | ---: |
| Prepare | 26.126 / 26.108 | 36.331 / 37.158 |
| Execute through local sink | 1.868 / 1.821 | 2.227 / 2.139 |
| Publication through local enqueue | 125.793 / 123.827 | 111.522 / 109.134 |

These results do not support a blanket faster/slower claim. The implementations
perform different internal work: the snapshot adapter constructs an upstream
registry and fingerprint during publication; the gate's admission callback uses
the scanner directly. The `snapshot_hash` internal name refers to full canonical
descriptor-byte equality at validation; it does not compute a descriptor
cryptographic hash there. Manuscript method names should describe the implemented
operations accurately.

These are two successive process sessions of sequential, valid-path local microbenchmarks. Quantiles
are of batch averages, not individual network-request tail latency. Background
load, power state, and affinity were uncontrolled. No independent-session
uncertainty interval, rejection-path distribution, deployment scalability, or
causal attribution of timing differences was established.

## Immutable evidence references and remaining scope

Recorded source-map aggregate for both suites in both final runs:
`0efa1c626ccef8b326c629b3e34155a6c8fbe2ec55c0c15d296e5890bb86a823`.
The preserved primary run used
`05099a9e8f9003cb2453e94456c9f70e4520136fe974b55d4837a61a489f1272`.

| Evidence | SHA-256 |
| --- | --- |
| Final designed raw trials | `0e08ad0ad8d5d2b4b54c2042e8e14bdb4aa9f0a572530ea4f3d2c808d220e4a2` |
| Final designed raw timings | `416845ceeae157ff254d28c3a5a0115e6775d9896f02bfd7c7479ca8c6442464` |
| Final enumerated raw trials | `152ae09025c36bea83d63a2d8e6860300e14fbb6ab454202f8a59f170f3e5651` |
| Repeat designed raw trials | `eb9e51e665c7f43857fa74a0879d917b1d1c5fafe26639c1e7dbf48f267669ac` |
| Repeat designed raw timings | `abb903844cbddd2c32702f1b432c2df0d5e0c5c22d1c41b695623079e0316938` |
| Repeat enumerated raw trials | `f2b745bb364c76dad44a62687f77651a209c51de8aaa775cd5a6e77266c04aac` |
| Runner source | `3e0ae3e4e2c793e36860455da10ae6da9896bc25e20493ff8bf4275a79756ae3` |
| Report-generator source | `c0875c1630116a785adba800b66c790b46bcbb4a29bce73d59dc42160a3999f2` |

The final saved test logs separately report 75 authored tests and 17 original
upstream tests passing (the primary run had 74 authored tests before the added
regression). This audit checked recorded successful outputs and root command
return codes; it did not independently rerun those test processes.

Completed scope: raw denominator and summary verification, all recorded receipt
outcomes, chronology/approval checks, catalogue-policy label validation, finite
enumeration completeness within its declared alphabet, representative controls,
raw timing arithmetic, report regeneration equality, and recorded provenance.

Blockers: none for raw verification; the discovered global-epoch defect was
corrected and the new evidence independently verified. This report does not audit
future manuscript numbers, other run directories,
unmeasured MCP/LLM behavior, real network dispatch, universal concurrency,
authorization-policy revocation beyond catalogue changes, or publication readiness.

Decision record: use raw receipts and independently reconstructed state rather
than trusting summary counters; retain strong-baseline equivalence rather than
promoting weaker-arm failures into novelty; flag global-arm implementation
behavior rather than silently generalizing it; retain separate suite denominators
and post-development labels rather than pooling correlated traces or inventing
blind preregistration.
