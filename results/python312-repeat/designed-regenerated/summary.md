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
| global_epoch | 0/36 | 0/36 | 0/9 | 24/36 | 24/36 | 2/7 | 6/11 |

## development

| Method | Failed executions | Unsafe traces | Unsafe receipts / receipts | Policy met | Fully met | Benign first pass | Benign final |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| naive_host | 0/24 | 15/24 | 15/23 | 9/24 | 9/24 | 5/6 | 7/8 |
| scoped_upstream | 0/24 | 6/24 | 6/19 | 18/24 | 18/24 | 6/6 | 8/8 |
| snapshot_hash | 0/24 | 2/24 | 2/15 | 22/24 | 22/24 | 6/6 | 8/8 |
| snapshot_revocation | 0/24 | 0/24 | 0/13 | 24/24 | 24/24 | 6/6 | 8/8 |
| binding_gate | 0/24 | 0/24 | 0/13 | 24/24 | 24/24 | 6/6 | 8/8 |
| global_epoch | 0/24 | 0/24 | 0/6 | 17/24 | 17/24 | 1/6 | 3/8 |

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
| execute | binding_gate | 200/200 | 3200 | 2.111 | 2.681 |
| execute | global_epoch | 200/200 | 3200 | 2.150 | 2.879 |
| execute | naive_host | 200/200 | 3200 | 27.208 | 32.537 |
| execute | scoped_upstream | 200/200 | 3200 | 42.668 | 52.474 |
| execute | snapshot_hash | 200/200 | 3200 | 1.777 | 2.107 |
| execute | snapshot_revocation | 200/200 | 3200 | 1.751 | 2.488 |
| integration | binding_gate | 200/200 | 3200 | 106.031 | 124.532 |
| integration | global_epoch | 200/200 | 3200 | 107.045 | 128.209 |
| integration | naive_host | 200/200 | 3200 | 130.672 | 150.060 |
| integration | scoped_upstream | 200/200 | 3200 | 202.294 | 231.101 |
| integration | snapshot_hash | 200/200 | 3200 | 120.151 | 144.391 |
| integration | snapshot_revocation | 200/200 | 3200 | 123.111 | 145.711 |
| prepare | binding_gate | 200/200 | 3200 | 34.679 | 42.330 |
| prepare | global_epoch | 200/200 | 3200 | 34.579 | 41.880 |
| prepare | naive_host | 200/200 | 3200 | 24.278 | 29.257 |
| prepare | scoped_upstream | 200/200 | 3200 | 69.840 | 81.576 |
| prepare | snapshot_hash | 200/200 | 3200 | 24.681 | 33.351 |
| prepare | snapshot_revocation | 200/200 | 3200 | 24.209 | 31.767 |
| refresh_unchanged | binding_gate | 200/200 | 3200 | 54.059 | 69.547 |
| refresh_unchanged | global_epoch | 200/200 | 3200 | 53.886 | 69.071 |
| refresh_unchanged | naive_host | 200/200 | 3200 | 40.092 | 52.434 |
| refresh_unchanged | scoped_upstream | 200/200 | 3200 | 70.814 | 92.057 |
| refresh_unchanged | snapshot_hash | 200/200 | 3200 | 79.069 | 92.972 |
| refresh_unchanged | snapshot_revocation | 200/200 | 3200 | 79.117 | 91.412 |
| scanner_only | shared_scanner | 200/200 | 3200 | 14.316 | 18.719 |
| select | binding_gate | 200/200 | 3200 | 0.562 | 0.647 |
| select | global_epoch | 200/200 | 3200 | 0.551 | 0.640 |
| select | naive_host | 200/200 | 3200 | 13.782 | 16.965 |
| select | scoped_upstream | 200/200 | 3200 | 0.554 | 0.640 |
| select | snapshot_hash | 200/200 | 3200 | 0.550 | 0.639 |
| select | snapshot_revocation | 200/200 | 3200 | 0.549 | 0.668 |

## Interpretation limits

- Designed cases are not independent attack samples; no scenario confidence intervals.
- Timing is one sequential local process session; no timing confidence intervals.
- No memory, network, LLM behavior, detector accuracy or production scalability measurement.
- Reapproval cases run the declared fresh-approval path; no automatic retries are invented.
- First-pass denominator excludes authored reapproval cases; final benign denominator includes them.

Raw evidence: `trials.jsonl`, `timings.jsonl`, `manifest.json`, `metadata.json`, and `completion.json`. All records carry scenario, source-tree, and environment hashes. Transport bytes use explicit base64 envelopes.
