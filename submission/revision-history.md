# Evidence and revision history

All work is on the isolated research branch, not the RadicalGraph product.

- Upstream baseline: `5ce5d56e57a0acd092435fca5d89b78d0b39ee7b`, verified by the
  12-file vendor manifest. Original source remains unchanged.
- Local initial implementation: `e5a4152`.
- Study freeze: `943f16d`, includes independently reviewed receipt oracle, source
  counterexamples, 36 targeted cases, 259 finite traces and paired timing runner.
- Pre-fix recorded evidence: `results/python312-primary` and `python312-repeat`.
  All files are retained. Raw audit found a global-epoch baseline fairness issue.
- Correction: `4e20ddd`, sampling global epoch at fresh selection rather than
  reusing the selected tool's publication epoch. New regression test prevents
  unrelated pre-selection publication from denying a newly selected tool.
- Final evidence: `results/python312-final` and `python312-final-repeat`. The only
  deterministic outcome changed by the correction is `dev-server-namespace` for
  `global_epoch`, improving full targeted completion from 24 to 25 of 36. Both
  strong arms remain 36/36 and 259/259; all original failed comparisons remain.

The code map and exact document/data hashes are recorded within each run. Later
manuscript and packaging edits do not retroactively change those maps. Newly
added transport checks are supplemental evidence, not hidden additions to the
36/259 denominators. All evaluated cases were visible during development; no
blind holdout or public preregistration is claimed.
