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
| execute | binding_gate | 200/200 | 3200 | 2.139 | 2.459 |
| execute | global_epoch | 200/200 | 3200 | 2.266 | 2.929 |
| execute | naive_host | 200/200 | 3200 | 28.613 | 33.441 |
| execute | scoped_upstream | 200/200 | 3200 | 44.950 | 52.342 |
| execute | snapshot_hash | 200/200 | 3200 | 1.873 | 2.140 |
| execute | snapshot_revocation | 200/200 | 3200 | 1.821 | 2.583 |
| integration | binding_gate | 200/200 | 3200 | 109.134 | 128.387 |
| integration | global_epoch | 200/200 | 3200 | 109.477 | 125.093 |
| integration | naive_host | 200/200 | 3200 | 132.495 | 152.362 |
| integration | scoped_upstream | 200/200 | 3200 | 204.492 | 233.285 |
| integration | snapshot_hash | 200/200 | 3200 | 123.586 | 143.078 |
| integration | snapshot_revocation | 200/200 | 3200 | 123.827 | 141.036 |
| prepare | binding_gate | 200/200 | 3200 | 37.158 | 51.321 |
| prepare | global_epoch | 200/200 | 3200 | 37.207 | 47.317 |
| prepare | naive_host | 200/200 | 3200 | 25.848 | 39.217 |
| prepare | scoped_upstream | 200/200 | 3200 | 74.488 | 98.227 |
| prepare | snapshot_hash | 200/200 | 3200 | 26.558 | 34.422 |
| prepare | snapshot_revocation | 200/200 | 3200 | 26.108 | 33.511 |
| refresh_unchanged | binding_gate | 200/200 | 3200 | 55.439 | 63.532 |
| refresh_unchanged | global_epoch | 200/200 | 3200 | 55.145 | 63.899 |
| refresh_unchanged | naive_host | 200/200 | 3200 | 41.722 | 50.172 |
| refresh_unchanged | scoped_upstream | 200/200 | 3200 | 73.104 | 84.883 |
| refresh_unchanged | snapshot_hash | 200/200 | 3200 | 81.678 | 94.969 |
| refresh_unchanged | snapshot_revocation | 200/200 | 3200 | 80.709 | 94.470 |
| scanner_only | shared_scanner | 200/200 | 3200 | 13.657 | 19.410 |
| select | binding_gate | 200/200 | 3200 | 0.604 | 0.678 |
| select | global_epoch | 200/200 | 3200 | 1.607 | 2.636 |
| select | naive_host | 200/200 | 3200 | 14.598 | 17.885 |
| select | scoped_upstream | 200/200 | 3200 | 0.575 | 0.670 |
| select | snapshot_hash | 200/200 | 3200 | 0.570 | 0.670 |
| select | snapshot_revocation | 200/200 | 3200 | 0.572 | 0.685 |

## Interpretation limits

- Designed cases are not independent attack samples; no scenario confidence intervals.
- Timing is one sequential local process session; no timing confidence intervals.
- No memory, network, LLM behavior, detector accuracy or production scalability measurement.
- Reapproval cases run the declared fresh-approval path; no automatic retries are invented.
- First-pass denominator excludes authored reapproval cases; final benign denominator includes them.

Raw evidence: `trials.jsonl`, `timings.jsonl`, `manifest.json`, `metadata.json`, and `completion.json`. All records carry scenario, source-tree, and environment hashes. Transport bytes use explicit base64 envelopes.
