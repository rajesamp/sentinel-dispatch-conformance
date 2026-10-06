# Offline run enumerated

Run label: `bounded-model-reproduction`. Status: **completed**. Source unchanged during run: `True`.

259 selected cases from 259 manifest cases; 4 selected family labels; 1554/1554 expected arm-case executions.

all finite words over declared event alphabet

verification labels were visible during implementation; not blind.

Completion below means enqueue into the local sink. A safe rejection is distinct from a completed approved operation.

## All selected cases

| Method | Failed executions | Unsafe traces | Unsafe receipts / receipts | Policy met | Fully met | Benign first pass | Benign final |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| naive_host | 0/259 | 210/259 | 210/218 | 49/259 | 49/259 | — | — |
| scoped_upstream | 0/259 | 36/259 | 36/76 | 223/259 | 223/259 | — | — |
| snapshot_hash | 0/259 | 36/259 | 36/76 | 223/259 | 223/259 | — | — |
| snapshot_revocation | 0/259 | 0/259 | 0/40 | 259/259 | 259/259 | — | — |
| binding_gate | 0/259 | 0/259 | 0/40 | 259/259 | 259/259 | — | — |
| global_epoch | 0/259 | 0/259 | 0/4 | 223/259 | 223/259 | — | — |

## bounded_enumeration

| Method | Failed executions | Unsafe traces | Unsafe receipts / receipts | Policy met | Fully met | Benign first pass | Benign final |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| naive_host | 0/259 | 210/259 | 210/218 | 49/259 | 49/259 | — | — |
| scoped_upstream | 0/259 | 36/259 | 36/76 | 223/259 | 223/259 | — | — |
| snapshot_hash | 0/259 | 36/259 | 36/76 | 223/259 | 223/259 | — | — |
| snapshot_revocation | 0/259 | 0/259 | 0/40 | 259/259 | 259/259 | — | — |
| binding_gate | 0/259 | 0/259 | 0/40 | 259/259 | 259/259 | — | — |
| global_epoch | 0/259 | 0/259 | 0/4 | 223/259 | 223/259 | — | — |

First-pass denominator includes benign cases without a declared reapproval. Final benign completion includes authored recovery paths. Execution failures are retained and are never credited as prevention.

## Local timing

p50 is sample median; p95 is nearest-rank ceil(0.95*n); samples are batch means.

Values include the Python batch-loop/call cost and use microseconds per operation. No subtraction is applied here; paired empty-harness and un-clamped adjusted values remain in JSON and raw samples.

| Operation | Method | Batch samples | Timed operations | p50 µs | p95 µs |
|---|---|---:|---:|---:|---:|

## Interpretation limits

- Designed cases are not independent attack samples; no scenario confidence intervals.
- Timing is one sequential local process session; no timing confidence intervals.
- No memory, network, LLM behavior, detector accuracy or production scalability measurement.
- Reapproval cases run the declared fresh-approval path; no automatic retries are invented.
- First-pass denominator excludes authored reapproval cases; final benign denominator includes them.

Raw evidence: `trials.jsonl`, `timings.jsonl`, `manifest.json`, `metadata.json`, and `completion.json`. All records carry scenario, source-tree, and environment hashes. Transport bytes use explicit base64 envelopes.
