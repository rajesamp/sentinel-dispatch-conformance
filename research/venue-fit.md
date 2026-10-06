# Full conference preparation target

Checked 2026-10-06. The user selected a **full conference paper**, authored by **Rajeshkumar Sampathrajan, Independent Researcher**. Prepare a full-length empirical security/conformance paper. This is a preparation target, not an acceptance prediction or a submitted paper.

## EuroS&P 2027 requirements

The [official CFP](https://eurosp2027.ieee-security.org/cfp.html) gives these current requirements:

- Register by **25 November 2026**, submit by **2 December 2026**, both AoE. Include title, abstract, author details, conflicts, and topics at registration.
- Maximum **13 body pages**; references and appendices are additional. Core evidence must be in the body.
- Use the supplied LaTeX template, **A4**, and PDF output. Check grayscale readability.
- Submit anonymously: omit author/affiliation and identifying acknowledgments. Cite prior work in third person. Review artifacts need anonymous hosting; ordinary GitHub and Google Drive are explicitly excluded.
- Discuss potential harms in the body. Include a data-availability statement and plan reproducible, openly licensed artifacts.
- Disclose generated AI content in acknowledgments, naming the system, affected sections, and extent of use; that section is excluded from the submission page limit.
- Disclose overlap with prior work; no simultaneous substantially overlapping submission. Accepted papers require a talk and poster.

## Template verified directly

Read the [official archive](https://eurosp2027.ieee-security.org/eurosp2027-template.zip) in memory. It contains `IEEEtran.cls`, `IEEEtran_HOWTO.pdf`, `eurosp-template.pdf`, `eurosp-template.tex`, and `fig1.png`.

```latex
\documentclass[compsoc,conference,a4paper,10pt,times]{IEEEtran}
```

The supplied class is IEEEtran V1.8b (2015-08-26). Retain its options and geometry. Example packages include `cite`, AMS math, `algorithmic`, `graphicx`, `textcomp`, `bmpsize`, `xcolor`, and `hyperref`; `lipsum` is example filler, not a manuscript requirement. The local authored draft can use:

```latex
\author{\IEEEauthorblockN{Rajeshkumar Sampathrajan}
\IEEEauthorblockA{\textit{Independent Researcher}}}
```

No email, city, or institution beyond the supplied affiliation was invented. Remove this block for anonymous submission. The template retains stale 2025 contact links and generic acknowledgment-removal advice; apply the current 2027 CFP for dates and AI disclosure.

| File | SHA-256 |
| --- | --- |
| Archive | `5f07428502371be3475a959c49d1ca588706aa9723d317add7ada994f52d725d` |
| `eurosp-template.tex` | `94f14347514d58980ae35df781e0a9609b66dfd999d2da6afed4427ea2407214` |
| `IEEEtran.cls` | `c972aca108fda004c3514d63658e02816da2e54d9a1451e870b9bd970e003f55` |

The built-in document compiler accepts a standalone source. A locally previewed approximation is not enough to claim venue-template compliance: verify the supplied class is actually used (or its identical bundled equivalent), page size, and body-page count. If that cannot be established, label the preview a draft and retain the official-format source for a compatible compiler.

## Fit assessment and completion criteria

The appropriate genre is an original **empirical methods and conformance** paper. A full paper can devote space to the contract, oracle, independent failure discovery, comparisons, negative results, finite coverage, and limitations. Page length alone does not make a conference contribution.

The presently defensible object is the specified local adapter/reference harness plus an actual pinned scanner. A bounded word enumeration does not establish unbounded concurrent correctness, real-client prevalence, or production exploitability. A paper based only on deliberately weak adapters faces a substantial originality and external-validity risk. Strong immutable-request and synchronized per-entry baselines must be treated as contenders, including a result that they match or outperform the proposed gate. If no consequential finding survives those controls, retain the negative result and narrow the contribution.

Before submission, the coordinating author must verify all generated text, code, results, and references; reproduce artifact tables; resolve every acceptance-critical claim; choose anonymous artifact hosting; and check the final PDF against the actual venue rules. This task creates no registration, upload, or publication.

## Alternatives considered

[USENIX Security 2027](https://www.usenix.org/conference/usenixsecurity27/call-for-papers) is another full conference with Cycle 2 registration on 19 January 2027 and paper deadline on 26 January 2027. It permits 13 body pages, requires an Open Science Appendix and anonymous artifacts, and explicitly offers **no replication submissions**. It is not an easier fallback for a reproduction-only study.

[CSET 2026](https://cset26.isi.edu/cfp.html) fits experimental-methods work but is a workshop, and its 17 September 2026 deadline has passed. [AISec 2026](https://aisec.cc/) is also a workshop, with a closed 24 July 2026 deadline. Neither satisfies the user's selected full-conference genre.
