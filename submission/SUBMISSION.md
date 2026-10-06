# Submission handoff

Prepared for **Rajeshkumar Sampathrajan, Independent Researcher**, 6 October 2026.
The preparation target is a full conference paper at **IEEE EuroS&P 2027**.
This package is a submission candidate, not a submitted or accepted article.

## Files to use

- `output/pdf/paper.pdf`: author version for review and research distribution.
- `output/pdf/paper-anonymous.pdf`: conference review version.
- `manuscript/paper.tex` and `paper-anonymous.tex`: editable standalone sources.
- `manuscript/paper-body.tex.in`: shared manuscript prose; regenerate the two
  standalone documents with `python3 manuscript/build_paper.py` after edits.
- `manuscript/references.bib`: 18 versioned working references; the manuscript
  prints the references it actually cites.
- `output/packages/anonymous-review.zip`: offline reviewer artifact.
- `output/packages/author-artifact.zip`: author archive with full evidence and
  development history. The export command excludes private Git configuration.
- `research/run-protocol.md`, `submission/claims-ledger.md`, and
  `research/final-evidence-audit.md`: measurement definitions and traceability.
- `submission/verification.json`: final build/package verification record.

## Scientific status

The study contributes a reusable, executable approval-to-dispatch contract,
replayable failure traces, and safety/completion comparisons. The implementation,
test manifests, raw receipts, exact source pins, regeneration scripts and negative
results are supplied. Both strong implementations pass the measured universe;
the manuscript does not claim a novel primitive or superior universal defense.

The original uploaded similarity-report manuscript is not the evidentiary source
for the new results. Its numerical claims were not carried into this paper.
This work was newly drafted around executed experiments and attributed primary
sources. No commercial plagiarism checker has certified it, and a low textual
similarity score would not establish research novelty.

The main remaining conference risk is significance and external validity:
authored local adapters and one author-owned pinned scanner do not establish
ecosystem prevalence. More test cases alone cannot remove that limitation.
See the candid internal `reviewer-assessment.md`; it is AI-assisted internal
review, not independent human peer review. No acceptance guarantee is made.

## Venue requirements checked

The [official CFP](https://eurosp2027.ieee-security.org/cfp.html), checked
6 October 2026, gives registration **25 November 2026** and submission
**2 December 2026**, both AoE. The supplied A4 IEEE template and 13-body-page
limit apply. The paper includes harms, data availability and specific AI-use
disclosure. See `research/venue-fit.md` and `template-provenance.json`.

Ordinary GitHub and Google Drive links are not anonymous artifact hosting for this
venue. Use the anonymous archive as a supplemental file if supported by the
submission system, or place its contents on a venue-accepted anonymous service.
Do not use the author repository URL as the reviewer artifact link. Upstream
citations and license notices remain in the review archive as third-party
attribution, with no claim of independent baseline authorship. The export map
records redactions without presenting them as a new experimental run.

## Actions only the author can attest to

1. Read the full text, references, code, and results; accept responsibility for
   generated material and the stated scope. AI assistance is disclosed in the
   paper and `NOTICE.md`.
2. Supply a contact email, account information and any required conflicts directly
   to the venue. No email, ORCID, institutional affiliation or conflict statement
   has been invented.
3. Confirm author list, originality/overlap, exclusive-submission status and any
   required venue declarations based on the author's actual circumstances.
4. Register by the deadline, upload the anonymous PDF and anonymous artifact,
   inspect the submission-system preview and confirm the final submission.

No conference account was created, no declaration was made on the author's
behalf, and no manuscript was submitted. Public artifact publication and venue
submission are different actions. This handoff makes the latter reviewable.
