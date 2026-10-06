"""Build standalone venue-format TeX from verified raw-run summaries.

The official class is embedded for the native single-document compiler; a normal
LaTeX engine writes that exact class using filecontents. No experiments run here.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.report_results import build_summary

LABELS = {'naive_host':'Naive host', 'scoped_upstream':'Scoped upstream',
          'snapshot_hash':'Snapshot equality', 'snapshot_revocation':'Snapshot revocation',
          'binding_gate':'Binding gate', 'global_epoch':'Global epoch'}


def escape(text):
    return ''.join({'&':r'\&','%':r'\%','_':r'\_','#':r'\#','$':r'\$',
                    '~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in text)


def bibliography(body):
    entries = {}
    text = (ROOT/'manuscript/references.bib').read_text()
    for block in re.split(r'(?=@\w+\{)', text):
        match = re.match(r'@\w+\{([^,]+),',block)
        if not match:
            continue
        fields = dict(re.findall(r'^\s*(\w+)\s*=\s*\{(.*)\},?\s*$',block,re.M))
        for key,value in fields.items():
            while value.startswith('{') and value.endswith('}'):
                value=value[1:-1]
            fields[key]=value
        entries[match.group(1)] = fields
    used = []
    for group in re.findall(r'\\cite\{([^}]+)\}', body):
        for key in group.split(','):
            if key not in used:
                used.append(key)
    output = [r'\begin{thebibliography}{99}']
    for key in used:
        item = entries[key]
        authors = item['author'].replace(' and ', ', ')
        bits = [escape(authors), '``'+escape(item['title'])+'\x27\x27']
        if item.get('journal'):
            bits.append(r'\emph{'+escape(item['journal'])+'}')
            bits.append('vol. '+item['volume']+', no. '+item['number']+', pp. '+item['pages'])
        if item.get('howpublished'):
            bits.append(escape(item['howpublished']))
        if item.get('eprint'):
            bits.append('arXiv:'+item['eprint'])
        if item.get('year'):
            bits.append(item['year'])
        if item.get('note'):
            bits.append(escape(item['note']))
        output.append(r'\bibitem{'+key+'} '+', '.join(bits)+'. '+r'\url{'+item['url']+'}.')
    output.append(r'\end{thebibliography}')
    return '\n'.join(output)


def main():
    designed = build_summary(ROOT/'results/python312-final/designed')
    enumerated = build_summary(ROOT/'results/python312-final/enumerated')
    for s in (designed,enumerated):
        assert s['run_status']=='completed' and s['source_unchanged']
    methods = list(LABELS)
    primary = designed['by_method']
    finite = enumerated['by_method']
    gate = primary['binding_gate']; strong=primary['snapshot_revocation']
    abstract = (f"Both the revocation-aware snapshot control and the per-binding generation gate "
                f"satisfy all {gate['trials']} targeted scenarios and all {finite['binding_gate']['trials']} finite traces. "
                f"A global-invalidation ablation emits no unsafe receipt in these suites, but completes "
                f"only {primary['global_epoch']['benign_final_completed']} of {gate['benign_trials']} benign targeted cases. "
                f"A complete-descriptor equality control violates the historical-revocation contract "
                f"in {primary['snapshot_hash']['trials_with_invariant_violations']} targeted cases and "
                f"{finite['snapshot_hash']['trials_with_invariant_violations']} finite traces.")
    results = [r'\subsection{Targeted conformance and completion}',
               f"The saved primary run contains {designed['actual_trials']} targeted arm-case executions "
               f"({designed['selected_case_count']} cases across six methods) and {enumerated['actual_trials']} "
               "separate finite-model executions. Every execution completed without a harness error; "
               "this status means the experiment ran, not that an arm satisfied the contract. "
               r"Table~\ref{tab:outcomes} reports the actual unsafe-case and completion counts.",
               r'\begin{table*}[t]\centering\small',
               r'\caption{Measured conformance counts. Unsafe cases contain at least one violating sink receipt. Full completion requires both safety and the declared outcome. Denominators are designed cases, not independent attacks.}\label{tab:outcomes}',
               r'\begin{tabular}{lrrrrr}\hline',
               r'& \multicolumn{3}{c}{36 targeted scenarios} & \multicolumn{2}{c}{259 finite traces} \\',
               r'Arm & Unsafe & Full completion & Benign completion & Unsafe & Full completion \\\hline']
    for m in methods:
        a,b=primary[m],finite[m]
        results.append(f"{LABELS[m]} & {a['trials_with_invariant_violations']}/36 & {a['fully_satisfied_trials']}/36 & {a['benign_final_completed']}/{a['benign_trials']} & {b['trials_with_invariant_violations']}/259 & {b['fully_satisfied_trials']}/259" + r" \\")
    results += [r'\hline\end{tabular}\end{table*}',
        "The naive integration control violates correspondence or revocation in 23 of 36 "
        "targeted cases. Server scoping and copied requests remove several failures, but the "
        "scoped upstream-projection adapter still violates nine cases. Complete-descriptor equality "
        "reduces this count to four; its remaining violations are restoration after relevant "
        "revocation. These are observed behaviors of the authored wrappers under the stated policy.",
        "Both revocation-aware implementations complete every targeted case: 21 safe dispatches "
        "and 15 correct rejections each. Their 11 benign controls all complete. Global invalidation "
        "also has zero unsafe targeted cases, but completes only 25 of 36 declared outcomes, "
        "including six of 11 benign controls. It makes 26 safe rejections where the strong "
        "selected-binding implementations make 15. Safety-only reporting would hide those 11 "
        "additional completion failures.",
        r'\subsection{Finite coverage and representative counterexamples}',
        "Of the 259 event words, 40 preserve the original approved operation and 219 revoke it. "
        "Both strong arms emit exactly 40 valid receipts and correctly reject the other 219. "
        "The equality-only and scoped-projection arms each produce 36 unsafe traces. This alphabet "
        "has no descriptor-extension event, so their equal finite-model outcomes do not contradict "
        "their different targeted-scenario outcomes. The global-epoch arm emits four valid receipts "
        "and rejects 255 traces, unnecessarily suppressing 36 of the 40 preserving traces.",
        "For example, publication of a changed descriptor followed by publication of the original "
        "restores byte equality but not the revoked approval. The equality-only adapter enqueues the "
        "old request after this sequence; the revocation-aware arms reject it. Conversely, a refresh "
        "on another server followed by caller argument mutation should enqueue the original frozen "
        "request under this policy. A global epoch suppresses that otherwise valid request. "
        "The artifact preserves the event order, detached approval and actual receipt for each case.",
        "The upstream-only observation program separately records 18 source-contract observations, "
        "including positive controls and explicitly conditional integration cases. All match the "
        "predicted observations. They are not counted as 18 attack families or pooled with either "
        "conformance denominator. The primary run also passes 75 authored tests and 17 upstream "
        "tests. Test counts establish the performed checks, not a probability of security.",
        r'\subsection{Local cost}',
        r'Table~\ref{tab:timing} reports primary-session quantiles of batch means in microseconds. '
        'The strong snapshot control has lower measured dispatch cost than the reference gate in '
        'this session, while their complete integration paths order differently. Different copy, '
        'validation, registry and logging work contributes to these values; the experiment does '
        'not isolate a universal cost of generations or establish statistical superiority.',
        r'\begin{table}[t]\centering\small',
        r'\caption{Primary-session local costs in microseconds. Quantiles are over 200 batch means (16 operations per batch), not individual-request tail latency.}\label{tab:timing}',
        r'\begin{tabular}{lrrrr}\hline',
        r'&\multicolumn{2}{c}{Execute}&\multicolumn{2}{c}{Integration}\\',
        r'Arm & p50 & p95 & p50 & p95\\\hline']
    for m in methods:
        times=[]
        for op in ('execute','integration'):
            times += [designed['timing'][op][m]['ns_per_operation'][q]/1000 for q in ('p50','p95')]
        results.append(LABELS[m]+' & '+' & '.join(f'{v:.2f}' for v in times)+r' \\')
    results += [r'\hline\end{tabular}\end{table}',
                'Raw warmups, empty-harness controls, method orders and all timing samples are retained. '
                'They allow different summaries without reconstructing measurements from rounded table cells.']
    repeat_path=ROOT/'results/python312-final-repeat/designed'
    if (repeat_path/'completion.json').exists():
        repeated=build_summary(repeat_path)
        for m in methods:
            assert repeated['by_method'][m] == primary[m]
        g2=repeated['timing']['integration']['binding_gate']['ns_per_operation']['p50']/1000
        s2=repeated['timing']['integration']['snapshot_revocation']['ns_per_operation']['p50']/1000
        results.append(f"A separate process session on the same interpreter reproduces every deterministic "
                       f"targeted result. Its integration medians are {g2:.2f} microseconds for the generation "
                       f"gate and {s2:.2f} microseconds for the revocation-aware snapshot. The sessions are "
                       "reported separately and are not treated as a broad sample of deployment conditions.")
    cross=ROOT/'results/python314-reproduction/reproduction.json'
    if cross.exists():
        assert json.loads(cross.read_text())['status']=='completed'
        results.append("A fresh replay under Python 3.14.8 also reproduces every stored deterministic "
                       "outcome for both suites. Timing tables remain restricted to the Python 3.12.14 sessions.")
    protocol = ("The primary run uses CPython 3.12.14 on an Intel Core i9-9880H MacBookPro16,1 "
                "with 16 GiB installed memory. Each of five method operations uses 20 warmup pairs "
                "and 200 measured pairs, with 16 operations per batch. A seed of 20261006 "
                "randomizes the six method orders within each pair. Adapter construction and "
                "precondition setup occur outside timing; method work and the in-memory sink append "
                "remain inside. The five boundaries are unchanged refresh, selection, preparation, "
                "execute-through-enqueue and complete refresh/select/prepare/execute integration. "
                "A shared-scanner measurement is separate. The run contains 6,820 timing rows, "
                "including warmups, and 99,200 measured method/scanner operations. Median and "
                "nearest-rank 95th percentiles summarize batch means, not single-request tails. "
                "OS, interpreter, timer details and the source-file hashes are saved with each run.")
    original=(ROOT/'manuscript/paper-body.tex.in').read_text()
    shared = original.replace('@@ABSTRACT_RESULTS@@',abstract).replace('@@TIMING_PROTOCOL@@',protocol)
    shared=shared.replace('@@RESULTS@@','\n\n'.join(results))
    shared=shared.replace('@@BIBLIOGRAPHY@@',bibliography(shared))
    header=(r'\RequirePackage[T1]{fontenc}'+'\n'+r'\documentclass[compsoc,conference,a4paper,10pt,times]{IEEEtran}'+'\n'+
            r'\usepackage{cite,amsmath,amssymb,graphicx,textcomp}'+'\n'+
            r'\usepackage[colorlinks=true,urlcolor=black,citecolor=black,linkcolor=black]{hyperref}'+'\n'+
            r'\begin{document}'+'\n')
    cls=(ROOT/'manuscript/IEEEtran.cls').read_text()
    preamble=(r'\begin{filecontents*}[overwrite]{IEEEtran.cls}'+'\n'+cls+'\n'+r'\end{filecontents*}'+'\n')
    for name,author in [('paper',r'\author{\IEEEauthorblockN{Rajeshkumar Sampathrajan}\IEEEauthorblockA{\textit{Independent Researcher}}}'),
                         ('paper-anonymous',r'\author{}')]:
        text=shared.replace('@@AUTHOR@@',author)
        availability=("The reviewer package is supplied as an offline supplementary archive; a public "
                      "author repository is not required to reproduce the experiments. The package "
                      "has no dependency on an unpublished external dataset or model service.")
        text=text.replace('@@ARTIFACT_STATEMENT@@',availability)
        if name=='paper-anonymous':
            text=text.replace("its author is\nalso the author of this study.","it is the software baseline assessed here. The results are not independent third-party validation.")
            text=text.replace("The baseline library shares human authorship with the study.",
                              "Investigator selection of the baseline and comparison design can introduce bias.")
        assert '@@' not in text
        (ROOT/f'manuscript/{name}.tex').write_text(preamble+header+text+'\n'+r'\end{document}'+'\n')
    print('Generated authored and anonymous standalone TeX with source-derived tables.')


if __name__ == '__main__':
    main()
