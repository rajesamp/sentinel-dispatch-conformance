# Sentinel Dispatch Conformance

[Paper and artifact release](https://github.com/rajesamp/sentinel-dispatch-conformance/releases/tag/v0.1.0)
| [Submission handoff](submission/SUBMISSION.md)
| [Verification record](submission/verification.json)

Reproducible, offline conformance experiments for approval-to-dispatch binding in
authored MCP-style host adapters. This is a research artifact, not a production
MCP client, semantic attack detector, sandbox or remote attestation service.

The study asks whether a host enqueues the server, connection, descriptor and call
it approved, and whether relevant catalogue changes revoke stale approvals without
unnecessarily blocking unrelated work. It does **not** claim invention of action
binding, capabilities, use-time checks or reference monitors.

## Reproduce

Python 3.10+ and its standard library are sufficient. No package installation,
API key, model account, external dataset or experiment network is required.

```sh
python3 reproduce.py --quick --output /tmp/sentinel-replay
```

Use a new output directory each time. The command verifies all 12 vendored upstream
files, runs 84 authored and 17 upstream tests, records upstream observations and
six child-process transport checks, executes both suites
against six arms, regenerates reports, and compares deterministic outcomes with
the stored reference. It fails on mismatches and never overwrites a prior run.
The quick run omits timing. For full paired local measurements:

```sh
python3 reproduce.py --output /tmp/sentinel-full-run
```

The full run uses 20 warmup and 200 measured pairs, batch size 16. Timing depends
on host/interpreter/background load; compare deterministic outcomes exactly and
timings descriptively. Recorded sessions use Python 3.12.14 on an Intel i9 Mac.

## Measured findings

| Authored adapter | Unsafe targeted cases /36 | Full targeted completion /36 | Unsafe finite traces /259 | Full finite completion /259 |
|---|---:|---:|---:|---:|
| Naive host | 23 | 13 | 210 | 49 |
| Server-scoped upstream projection | 9 | 27 | 36 | 223 |
| Full descriptor equality | 4 | 32 | 36 | 223 |
| Revocation-aware snapshots | 0 | 36 | 0 | 259 |
| Per-binding generations | 0 | 36 | 0 | 259 |
| Global epoch | 0 | 25 | 0 | 223 |

The two strong approaches match on these bounded suites. Generations are not
uniquely necessary. Global invalidation has no unsafe receipt here but completes
only 6/11 benign targeted cases; the two strong selected-binding approaches
complete all 11. The 259 traces comprise 40 preserving and 219 revoking words.
These denominators are designed tests, not independent sampled attacks. No
attack-detection percentage, ecosystem vulnerability rate or universal safety
guarantee follows.

## What to inspect

- `manuscript/paper.tex`: standalone authored paper in the supplied EuroS&P 2027 class.
- `manuscript/paper-anonymous.tex`: anonymous manuscript variant; verify submission
  metadata and reviewer hosting separately before uploading to a venue.
- `manuscript/references.bib` and `research/sources.json`: verified working references
  and a dated targeted search log, including prior art that limits mechanism novelty.
- `research/run-protocol.md`, `finite-model.md`, `holdout-plan.md`: exact units,
  expected policy, timing boundary and specification-aware evaluation disclosure.
- `src/binding_gate/core.py`: reference implementation.
- `experiments/adapters.py`: authored comparison arms. Internal `snapshot_hash`
  means full descriptor byte equality; it performs no descriptor hashing.
- `experiments/oracle.py`: separately implemented receipt/approval comparison.
- `data/`: immutable input manifests and measured expected outcomes.
- `results/python312-final/` and `results/python312-final-repeat/`: authoritative
  recorded runs, raw receipts, samples, environment and byte-identical regenerated reports.
- `research/adversarial-review.md`, `final-evidence-audit.md`: reproduced defects,
  repairs, independent raw evidence checks, controls and remaining limitations.
- `submission/`: venue requirements, provenance and export materials.

Both paper variants are eight-page A4 PDFs in the supplied conference class.
The anonymous artifact was replayed from a fresh extracted folder without package
installation. Its export audit compares every observation, source file and hash
mapping with the original evidence. The final typography-only update preserves
all executable code and data from that replay; exact archive hashes and the
preserved replay evidence are in `submission/verification.json`.

Earlier `python312-primary` and `python312-repeat` runs are retained as pre-fix
evidence. An independent audit found that global epoch was captured at publication
instead of fresh selection; the corrected arm improves exactly one targeted
outcome. The old findings are not silently overwritten or used as headline results.

## Scope, rights and attribution

Tool/server identity is assigned by the trusted host. The writer must enqueue the
provided bytes directly under the documented serialized boundary. This fixture
uses the basic 2025-11-25 `tools/call` name/arguments shape, not every later MCP
field or a complete protocol stack. No live LLM or third-party service is tested.
The study shares human authorship with the pinned SENTINEL-TPD baseline, so the
artifact does not provide independent third-party validation of that library.

Original code and inert fixtures are MIT licensed. The vendored baseline retains
its MIT notice; the official conference class retains its original notices.
See `NOTICE.md` for AI assistance and provenance. No external attack corpus is
bundled. Human author: Rajeshkumar Sampathrajan, Independent Researcher.

The full conference manuscript is a submission candidate. Venue acceptance,
scientific significance and external validity are not certified by successful
artifact reproduction. The author must review the generated work and complete
the venue's authorship, conflict, originality and submission declarations.
