# Reproducible offline runner protocol

This protocol documents local synthetic replay and local timing. It is an internal
pre-run record, not a public preregistration. Verification labels were visible to
the implementation team. Development checks and scored frozen runs must use
different directories and truthful labels; these are not blind holdout claims.

## Replay and approvals

Run `python3 -m experiments.run_study` from the package root. Its default manifest
is the 36 designed cases (24 development and 12 verification) in
`experiments/scenarios.py`. `--manifest FILE` accepts an independently frozen
schema-version-1 manifest with the same case format. Keep any separately bounded
enumeration in its own run and report its own declared universe; never pool its
denominator with the designed challenge suite. All six entries in `METHODS` run
unless selected explicitly. Every arm receives a fresh deep copy of the same case.

Initial source dictionaries are passed directly to each adapter and retained for
the specified caller-mutation actions. This exposes a retained alias rather than
silently repairing it in the harness. The action order is initial publication,
selection, after-select actions, prepare, after-prepare actions, default execute,
then after-execute actions. Within a stage, manifest order is preserved. Explicit
refresh completions reuse their tagged begin result; replay reuses the same token.

The runner snapshots the selected server, connection and entire descriptor outside
the method. It serializes the proposed request independently before passing the
caller-owned arguments to prepare. A successful preparation retains a frozen
external approval with immutable bytes and a per-case serial. An absent selection
or failed preparation has no active valid approval. After-select revocations remain
applicable to the old selected record even if an arm nevertheless permits prepare.
A declared reapproval reselects and prepares the current arguments; only an actual
new valid approval resets relevant revocation. Old approval records are preserved.

Revocation follows the manifest's declared policy, not the tested adapter's
publication or validity verdict. The latest-requested-wins trace policy makes
stale completions nonrevoking. Every real sink call records exact request and
descriptor bytes, actual server/connection, the then-active approval and the
revocation state at that enqueue. Later updates cannot retroactively revoke a
past receipt. The sink is a local in-memory append; no remote tool is executed.

The independent oracle compares these receipts against both the active immutable
approval and the declared expected target. Safety, scenario policy/target
satisfaction, and benign completion are separate fields. A method status cannot
hide an emitted receipt. Crashes remain execution errors; an empty receipt list
from a failed execution is never credited as prevention. Unknown actions, unknown
refresh tags, invalid stages, duplicate case IDs and unreachable mutation paths
fail loudly. Valid but unsupported method behavior remains a scored outcome.

Each case represents one intended operation. Explicit fresh-approval paths do not
invent a second intended dispatch or an automatic retry. First-pass benign
completion uses only benign cases without an authored reapproval; final benign
completion includes all benign cases. These are enqueue outcomes. They do not
establish remote execution success or measure recovery after an observed failed
dispatch unless that sequence is explicitly present in a future manifest.

## Timing boundary

Timing is separate from scenario replay and uses only the unchanged admitted base
tool, base argument dictionary, host registration `server-a`, connection `c1`, and
JSON-RPC request ID 1. This intentionally measures valid paths. It does not measure
challenge rejection latency or claim a realistic workload distribution.

Defaults are 20 warmup pairs then 200 measured pairs per operation, batch size 16,
seed 20261006, one sequential process session, and no request-rate pacing. Every
pair randomly permutes all requested methods using a local seeded generator. All
methods receive identical fixture values in that pair. Warmup samples are saved
with a separate label and excluded from summary quantiles. Pair IDs and method
orders are retained. Repeat independent CLI invocations for multiple process
sessions; the current report never treats within-process batches as independent
experimental sessions.

For each batch, build fresh adapters and method-specific callable closures before
starting `perf_counter_ns`. Precondition publication, selection or preparation is
also outside timing where specified below. One method action runs on each prepared
adapter, bounding pending permits and audit growth. Timed operations are:

| Operation | Timed work | Untimed setup |
|---|---|---|
| `refresh_unchanged` | `refresh` of equivalent selected-tool catalogue, including scanner, copies/canonicalization, publication and method logging | Adapter construction and initial publication |
| `select` | Server/name lookup and method synchronization | Construction and initial publication |
| `prepare` | Complete prepare, including request capture, validation, permit allocation/random token and method logging | Construction, publication and selection |
| `execute` | Complete execute through synchronous local sink append, including validation, consumption, synchronization and logging | Construction, publication, selection and preparation |
| `integration` | Publication, selection, preparation and execution through local sink | Construction and fixture allocation |
| `scanner_only` | Vendored default `scan_tool_metadata(tool).allowed` via common admission function | Fixture allocation; measured once as a shared operation |

The batch timer includes the Python loop, callable invocation and assignment into
a preallocated result list. Timer calls define the interval. Setup, random method
ordering, result validation, JSONL writing and report aggregation are outside it.
Allocation inside a method, including permit randomness, remains included. The
execution sink appends immutable bytes without performing oracle comparisons.
Shared scanner measurement is reported separately; it is not subtracted from
integration totals. `refresh_unchanged` and `integration` include scanner work.

Each method batch has a paired empty-call batch with the same loop/result storage;
its order before/after the method batch is randomized outside the timer. Raw and
un-clamped harness-adjusted measurements are saved. Primary tables report raw
elapsed nanoseconds divided by batch size, displayed in microseconds. The p50 is
the sample median of batch means; p95 is nearest-rank `ceil(0.95*n)`. These are
quantiles of batch averages, not individual-request tail latency. No confidence
intervals, memory claims or percentage-overhead claims are generated. The runtime,
timer resolution, OS/machine, CPU count, available load average and installed
package versions are recorded. Power state, affinity and background load are not
controlled. This is not a network, LLM, multi-thread throughput or production test.
Interpreter and manifest paths omit the user's absolute workspace path; vendored
imports are recorded relative to the package. The vendor revision is recorded and
its declared file hashes are checked before a run.

## Frozen evidence and reproduction

`--output` must name a new directory. Files are opened exclusively, never
overwritten. Each run saves the exact manifest, initial metadata, trial JSONL,
timing JSONL (including warmups and failures), completion state, generated summary
JSON/Markdown and LaTeX table data. Byte fields use explicit base64 envelopes to
preserve exact transport bytes in JSON. Raw records carry hashes for the entire
manifest, source-file hash map and captured environment. Every trial also carries
its case hash. Source files and the three protocol documents are hashed before
and after; changes make the run fail while preserving its evidence. This is
tamper-evident hashing, not WORM storage or external attestation.

The completion file hashes all pre-report artifacts. Regeneration checks those
hashes, the actual manifest/environment/source-map digests, per-case hashes and
labels, and exact selected-case-by-method coverage for completed runs before
producing a new report destination. Retain failed directories rather than editing away failures. Table
numbers are calculated from the raw records and never hard-coded from expected
method rankings. A completed experiment can include unsafe outcomes; `completed`
means execution succeeded, not that a method satisfied every invariant.

Development check (not a headline run):

```sh
python3 -m unittest discover -s tests -p test_runner.py -v
python3 -m experiments.run_study --output runs/development-001 --split development --no-timing --label development
```

After integration and freezing the package, a coordinator can run:

```sh
python3 -m experiments.run_study --manifest data/scenario_manifest.json --output runs/designed-frozen-001 --label frozen-visible-verification
python3 -m experiments.report_results runs/designed-frozen-001 --output runs/designed-frozen-001-reproduced
```

Use a different directory for every rerun. If a verification failure prompts code
changes, retain the original and label the subsequent run regression-informed.
The optional enumerated manifest is passed with the same `--manifest` flag into a
separate run. The report preserves split and family breakdowns, actual dispatch
denominators, execution failures, safe rejection counts and benign availability.
