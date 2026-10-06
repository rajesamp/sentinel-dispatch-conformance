# Independent package export audit

Date: 2026-10-06. Scope: inspect `tools/export_artifact.py`, audit the completed
anonymous archive independently against the original local package, and assess
the author-export path before its final packaging. This review did not modify
implementation, exporter, source evidence, or either manuscript. The coordinator
owns PDF validation and the full extracted-package replay.

## Verified anonymous archive

Artifact: `output/packages/anonymous-review.zip`.

- Final SHA-256: `575048b350be636c51577581ac8e06f8f859a5fc765c523f97cb5b54242752c0`
- Final size: 1,305,766 bytes.
- ZIP members: 125; manifest entries: 124, excluding the hash manifest itself.
- Exporter reviewed SHA-256:
  `19d913f5dde6a192286fcc3ef8c50e330cf34fdc7014a25627e7fa39c51097ea`.

The full preservation audit below first checked the archive now preserved as
`output/packages/anonymous-review-layout-check.zip`, SHA-256
`85e29ceddf37984f2890fcd2ade7c0105068adcd0d7ce8877fc762a9a58ef1ef`,
size 1,305,779 bytes. A later differential audit verified the corrected final
archive named above; only manuscript layout files and their hash manifest changed.
Both ZIPs existed and were fully readable before their checks. Both CRC checks passed.
Every member has the expected `anonymous-review/` prefix; no duplicate names,
absolute paths, traversal components, symlinks, Git history, Python caches, or
temporary compilation outputs were found. The hash manifest covers every file
other than itself, with no missing or extra entries, and every recorded digest
matches the extracted bytes.

All 29 exported `.py` and `.toml` files are byte-identical to the corresponding
original local files. The anonymous export therefore did not alter executable
Python, the vendored implementation, tests, or package configuration. The isolated
smoke test described below used this exact archive, not its pre-ZIP staging tree.

## Observation preservation and provenance remapping

Six run suites are included: designed and enumerated results for
`python312-final`, `python312-final-repeat`, and `python314-reproduction`.
The independent comparison checked every original and exported JSONL record in
order after removing only its top-level `provenance` field:

| Checked material | Exact count | Result |
| --- | ---: | --- |
| Trial rows | 5,310 | All other fields unchanged |
| Timing rows | 13,640 | All measured values and other fields unchanged |
| Local enqueue receipts inside trial rows | 1,788 | Identity, request/descriptor bytes, approval snapshots, event order, and revocation state unchanged |
| Regenerated summary objects | 6 | Equal to originals except provenance |
| Generated LaTeX numerical tables | 6 | Byte-identical to originals |

These are preservation-check totals across repeated runs, not additional unique
security scenarios or pooled efficacy denominators. Base64 transport data was
preserved as exact strings inside the otherwise identical observations. No
outcome, expected label, timing sample, sample order, gate status, receipt,
approval, or recorded event was replaced by an expected value.

For each suite, the following also passed independent checks:

- The original recorded source hashes match the original source files.
- Exported source hashes match the exported files. Exactly two source-map entries
  change: `governance/spec.md` and `research/evaluation-plan.md`.
- Scenario and environment provenance digests are unchanged.
- Metadata fields other than source-file digests and provenance are unchanged.
- The manifest bytes are unchanged.
- Original and exported artifact hashes match both sides of `ANONYMIZATION.json`.
- Completion fields other than declared output hashes and ending source-map
  digest are unchanged; the recomputed ending digest matches exported metadata.
- Every remapped trial/timing provenance field matches the declared exported map.

The export map records 18 changed document/log files and six remapped run suites.
All listed original/exported file digests match the corresponding bytes. The
standalone subprocess transport evidence and all three upstream-observation
records are byte-identical to their originals.

The export is appropriately labeled a derived reviewer view, not a new run. The
changed provenance reflects redacted documents; it does not claim that a new
experiment produced the old measurements. Original provenance is retained in the
map, and source/scenario/evidence relationships remain checkable.

## Anonymity checks and preserved attribution

The initial static review found an unnecessary `RadicalGraph` project reference
in the exported governance specification. The coordinator added an export-only
redaction before creating the audited ZIP. The coordinator also added two
fail-closed checks: original source bytes must match each run's recorded source
map, and exported source-map changes are permitted only for the two declared
redacted documents. These assertions prevent an unrelated changed implementation
from being silently assigned new historical provenance.

The completed archive's UTF-8 text files contain no matches for the original
home-directory prefix, local username, source-project name, unique workspace
identifier, or known author email. Author names and repository handles remain
only in these source-attribution categories:

- Vendored repository manifest, license, README, and package author metadata.
- Immutable upstream-source URLs in the counterexample program and its recorded
  observation provenance.
- Bibliographic entries in the manuscript and reference database.

Those occurrences identify cited upstream software or bibliographic authors.
Removing them would alter third-party attribution or source provenance. They
are not an author block, contact field, home path, or undeclared author statement.
The root license uses the exported anonymous-contributor label, the prospective
plan's author sentence is removed, and supplementary command logs replace the
original checkout root with `.`.

This is a bounded explicit-identifier scan plus source inspection, not a guarantee
against inference from scholarly citations or publicly recognizable results.
PDF metadata, embedded PDF objects, and visual layout remain the coordinator's
separate validation responsibility; this audit does not imply that a text scan
of source files inspected all compressed PDF contents.

## Extracted-package independence

The reviewer extracted the exact ZIP into a newly created, separate temporary
directory and ran a smoke process with Python isolated mode (`-I`), bytecode
writing disabled, a minimal environment without `PYTHONPATH`, and a working
directory outside the original checkout. Only the extracted package was added
to the import path.

The process checked that the runner, adapters, oracle, scenarios, binding gate,
and vendored Sentinel module were loaded from files beneath the extracted
archive root. A normal per-binding-gate case produced one valid receipt, and the
naive-host namespace negative control produced one receipt with an invariant
violation. It printed:

```text
Isolated extracted-package imports and positive/negative controls passed
```

This establishes local import independence and meaningful positive/negative
execution from the preserved layout-check archive. Its code and data are identical
to the corrected final archive, as verified below. It is not a claim that the
reviewer independently replayed every test, timing batch, or transport check.

The coordinator's fresh deterministic replay is now complete. The reviewer
inspected `submission/fresh-replay-evidence.zip`, whose SHA-256 is
`12e6bb924017c2beda5d686c97f174ab6b5a8dfea7c4abe304d5fa66786e3c32`.
Its ZIP CRC check passes; the saved reproduction record reports Python 3.12.14,
`status=completed`, `mode=quick`, all eight stage return codes zero, and
`deterministic_outcomes_match_reference=true`. Saved logs report 84 authored
tests and 17 original upstream tests passing. This verifies the recorded replay
evidence; the reviewer did not launch that complete replay independently.
Quick mode reruns deterministic cases and tests, not timing measurements.

The independent check's machine-readable result is saved locally at
`/private/tmp/sentinel-independent-package-audit-xe4qf0yn/audit-result.json`.
That temporary path is audit output, not a dependency of the distributed package.

## Corrected-layout differential check

The coordinator removed a duplicate terminal period from five paragraph-heading
labels and regenerated the PDF. The independent differential check verified:

- The preserved layout-check ZIP has the original audited hash above.
- The corrected final ZIP has the final hash and size listed at the start.
- Both archives have exactly the same 125 member names.
- Exactly three members have changed bytes: `manuscript/paper.tex`,
  `output/pdf/paper.pdf`, and `SHA256SUMS.json` beneath the common archive prefix.
- The TeX changes are exactly five removals of `.` immediately before the closing
  brace in `\paragraph{...}` labels; no other source line changes occur.
- All 124 entries in the corrected manifest match the corrected archived bytes.
- Every other archived byte is unchanged, including all executable code, tests,
  raw observations, metadata, export maps, and regenerated result tables.
- The changed TeX source has no new match for the checked home, author-email,
  username, workspace, or unrelated-project identifiers.

The final archive therefore retains the code/data preservation and isolated-replay
evidence established on the previous layout version. The independently saved
differential record is
`/private/tmp/sentinel-independent-package-audit-xe4qf0yn/layout-differential.json`.
PDF visual correctness remains the coordinator's separate validation; comparing
PDF bytes alone cannot establish page layout.

## Author archive and outstanding scope

The author-export branch was inspected statically. It copies the executable code
and selected evidence directly without anonymization or provenance rewriting;
adds the author documentation, manuscripts, PDF outputs, review reports, export
tools, and preserved earlier runs; excludes Git history and local caches; and
creates a complete per-file hash manifest followed by a ZIP opened exclusively.
It does not recursively include the output package directory.

The final `author-artifact.zip` did not yet exist when this report was written:
the coordinator will build it afterward so this audit report can be included.
Therefore no author-archive SHA-256, actual member count, or byte-level archive
verification is claimed here. The coordinator owns that final check and should
record its resulting outer digest separately. A report inside an archive cannot
usefully include the final digest of its own enclosing archive without changing
that digest.

No outstanding defect was found in the audited anonymous ZIP. The coordinator's
fresh deterministic replay is complete and its saved evidence was checked.
Outstanding independent verification scope is PDF internals and actual author-ZIP
membership/integrity after creation. A later change to the
anonymous ZIP or exporter invalidates the exact-hash conclusions above and
requires a fresh comparison.

Decision record: compare all observations after removing only declared provenance
rather than trusting export flags; preserve mandatory upstream/bibliographic
attribution rather than deleting cited author names; use the ZIP itself for
isolated import testing rather than trusting its staging directory; keep final
author-archive verification explicitly pending rather than claim an artifact
that did not yet exist was audited.
