# Offline run designed

Run label: `specification-aware-reproduction`. Status: **completed**. Source unchanged during run: `True`.

36 selected cases from 36 manifest cases; 28 selected family labels; 216/216 expected arm-case executions.

declarative finite challenge suite; not exhaustive enumeration or independent statistical samples

verification labels were visible during implementation; not blind.

Completion below means enqueue into the local sink. A safe rejection is distinct from a completed approved operation.

## All selected cases

| Method | Failed executions | Unsafe traces | Unsafe receipts / receipts | Policy met | Fully met | Benign first pass | Benign final |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| naive_host | 0/36 | 23/36 | 23/35 | 13/36 | 13/36 | 6/7 | 10/11 |
| scoped_upstream | 0/36 | 9/36 | 9/30 | 27/36 | 27/36 | 7/7 | 11/11 |
| snapshot_hash | 0/36 | 4/36 | 4/25 | 32/36 | 32/36 | 7/7 | 11/11 |
| snapshot_revocation | 0/36 | 0/36 | 0/21 | 36/36 | 36/36 | 7/7 | 11/11 |
| binding_gate | 0/36 | 0/36 | 0/21 | 36/36 | 36/36 | 7/7 | 11/11 |
| global_epoch | 0/36 | 0/36 | 0/10 | 25/36 | 25/36 | 2/7 | 6/11 |

## development

| Method | Failed executions | Unsafe traces | Unsafe receipts / receipts | Policy met | Fully met | Benign first pass | Benign final |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| naive_host | 0/24 | 15/24 | 15/23 | 9/24 | 9/24 | 5/6 | 7/8 |
| scoped_upstream | 0/24 | 6/24 | 6/19 | 18/24 | 18/24 | 6/6 | 8/8 |
| snapshot_hash | 0/24 | 2/24 | 2/15 | 22/24 | 22/24 | 6/6 | 8/8 |
| snapshot_revocation | 0/24 | 0/24 | 0/13 | 24/24 | 24/24 | 6/6 | 8/8 |
| binding_gate | 0/24 | 0/24 | 0/13 | 24/24 | 24/24 | 6/6 | 8/8 |
| global_epoch | 0/24 | 0/24 | 0/7 | 18/24 | 18/24 | 1/6 | 3/8 |

## verification

| Method | Failed executions | Unsafe traces | Unsafe receipts / receipts | Policy met | Fully met | Benign first pass | Benign final |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| naive_host | 0/12 | 8/12 | 8/12 | 4/12 | 4/12 | 1/1 | 3/3 |
| scoped_upstream | 0/12 | 3/12 | 3/11 | 9/12 | 9/12 | 1/1 | 3/3 |
| snapshot_hash | 0/12 | 2/12 | 2/10 | 10/12 | 10/12 | 1/1 | 3/3 |
| snapshot_revocation | 0/12 | 0/12 | 0/8 | 12/12 | 12/12 | 1/1 | 3/3 |
| binding_gate | 0/12 | 0/12 | 0/8 | 12/12 | 12/12 | 1/1 | 3/3 |
| global_epoch | 0/12 | 0/12 | 0/3 | 7/12 | 7/12 | 1/1 | 3/3 |

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
