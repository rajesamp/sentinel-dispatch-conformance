# Claim-to-evidence ledger

All numerical manuscript claims are derived from the final runs. Earlier runs are
retained but excluded from headline tables. No values from the original similarity
report's manuscript are used.

| Claim | Reproduction/evidence |
|---|---|
| 36 designed scenarios, six arms, 216 executions | `data/scenario_manifest.json`; final `designed/metadata.json` and `trials.jsonl` |
| All 259 words over six events, depth 0..3 | `experiments/enumerate_traces.py`; `tests/test_enumeration.py`; `data/finite_trace_manifest.json` |
| Both strong arms fully satisfy 36/36 and 259/259 | Both final suite `summary.json` files, `by_method.{snapshot_revocation,binding_gate}.fully_satisfied_trials`; independently recomputed in `research/final-evidence-audit.md` |
| Global epoch benign completion 6/11, full targeted 25/36 | Final designed `by_method.global_epoch`; initial pre-fix value 24 is explicitly retired |
| Equality-only unsafe targeted 4/36 and finite 36/259 | Final `by_method.snapshot_hash.trials_with_invariant_violations`; internal name is historical, implementation compares bytes |
| Finite strong-arm 40 valid enqueues / 219 correct denials | Final enumerated `safe_dispatch_trials` and `safe_rejection_trials`; independent model audit |
| Actual receipt counting and per-enqueue revocation | `experiments/run_study.py`, `oracle.py`, raw base64 records, runner negative-control tests and final evidence audit |
| Primary 75 authored +17 upstream tests | `results/python312-final/{authored-tests,upstream-tests}.log` |
| Latest 84 authored +17 upstream tests; Python 3.14 reproduction | `results/python314-reproduction/`; nine added transport checks account for increase |
| 18 upstream observations | `results/python312-final/upstream-observations.json`; source pin checked inside runner; not an attack sample |
| 6,820 timing batches/session, 99,200 measured operations/session | 5 operations ×6 arms ×220 pairs +220 shared scanner rows; measured 31×200×16. Warmups are excluded from table quantiles |
| Local timing values | Final designed `timings.jsonl`, regenerated summaries; `submission/measurement-host.json`; two process sessions separate |
| Six subprocess checks all pass; child-side zero-frame controls | `results/transport-check.json`, `integration/`, `tests/test_transport.py`; supplementary, not part of designed/finite suite |
| No new binding/reference-monitor primitive claimed | `research/literature.md`, `sources.json`, manuscript related work and versioned references |
| Source/reference provenance | `vendor/manifest.json`, `manuscript/references.bib`, dated `research/sources.json` |

Unsupported claims deliberately excluded: firstness; universal agent security;
detector recall; independent real-world attack accuracy; ecosystem exploit
prevalence; unbounded concurrency proof; throughput/memory/production latency;
remote behavior attestation; full 2026 MCP wire conformance; blind holdout/public
preregistration; independently verified human peer review; guaranteed acceptance.
