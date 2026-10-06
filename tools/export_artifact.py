"""Export reviewer or author archives without Git history or local caches.

Anonymous export is a declared derived view. It preserves executable code and
numeric/raw receipt data; authorship text/path redactions require recomputing the
document provenance hashes. Original run hashes are retained in its export map.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.report_results import write_report


def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
def write_json(path,value): path.write_text(json.dumps(value,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['author','anonymous'],required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    dest=args.output.resolve();dest.mkdir(parents=True,exist_ok=False)
    anon=args.mode=='anonymous'
    include=['src','experiments','integration','tests','data','vendor','reproduce.py','LICENSE',
             'governance/spec.md','research/evaluation-plan.md','research/holdout-plan.md',
             'research/run-protocol.md','research/finite-model.md','research/transport-check.md',
             'results/python312-final','results/python312-final-repeat',
             'results/python314-reproduction','results/transport-check.json',
             'submission/measurement-host.json','submission/template-provenance.json']
    if not anon:
        include+=['README.md','NOTICE.md','CITATION.cff','research','manuscript','tools',
                  'submission','output/pdf','results/python312-primary','results/python312-repeat',
                  '.github/workflows/reproduce.yml']
    changes=[]
    for item in include:
        source=ROOT/item
        if not source.exists():raise FileNotFoundError(source)
        paths=source.rglob('*') if source.is_dir() else [source]
        for file in paths:
            if not file.is_file() or '__pycache__' in file.parts or file.suffix in {'.pyc','.log','.aux','.out'}:
                # Test logs are scientific records and must be retained.
                if not(file.is_file() and file.suffix=='.log' and 'results' in file.parts):continue
            relative=file.relative_to(ROOT)
            if anon and (file.name in {'summary.json','summary.md','tables.tex'} or '-regenerated' in str(relative)):
                continue
            target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True)
            raw=file.read_bytes()
            if anon and relative==Path('LICENSE'):
                raw=raw.replace(b'Rajeshkumar Sampathrajan',b'Anonymous study contributors')
            if anon and relative==Path('research/evaluation-plan.md'):
                raw=raw.replace(b'Author: Rajeshkumar Sampathrajan, Independent Researcher. ',b'')
            if anon and relative==Path('governance/spec.md'):
                raw=raw.replace(b"RadicalGraph's product constitution",b"The unrelated source project's product constitution")
            if anon and (file.name=='reproduction.json' or file.suffix=='.log'):
                # This command log is supplementary metadata, not a trial record.
                raw=raw.replace(str(ROOT).encode(),b'.')
            target.write_bytes(raw)
            if raw!=file.read_bytes():changes.append({'file':str(relative),'original_sha256':sha(file.read_bytes()),'exported_sha256':sha(raw)})
    if anon:
        for name in ('paper-anonymous.tex','IEEEtran.cls','references.bib'):
            target=dest/'manuscript'/('paper.tex' if name=='paper-anonymous.tex' else name)
            target.parent.mkdir(exist_ok=True);shutil.copyfile(ROOT/'manuscript'/name,target)
        (dest/'output/pdf').mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/'output/pdf/paper-anonymous.pdf',dest/'output/pdf/paper.pdf')
        (dest/'README.md').write_text('''# Anonymous lifecycle conformance artifact

Run `python3 reproduce.py --quick --output /tmp/conformance-replay` from this
directory. Python 3.10+ standard library only; no network, installation, API key
or external dataset. A new output directory is required. Omit `--quick` for
local timing. See `research/run-protocol.md` and the included manuscript for the
supported contract and interpretation. The root license covers original code;
the vendored upstream notices remain unchanged and are third-party attribution.

This is an anonymous derived export of recorded evidence. Executable code and
measured data are unchanged. Identifying document text and local command paths
are redacted; affected provenance hashes are recomputed and mapped in
`ANONYMIZATION.json`. It is not a new experimental run. The article does not
claim independent human review, semantic detector accuracy, or a novel primitive.
OpenAI Codex assisted with sources, code, experiments and drafting; the human
author is responsible for final review and submission declarations.
''')
        for run in sorted((dest/'results').glob('*/*')):
            if not (run/'metadata.json').exists():continue
            metadata=json.loads((run/'metadata.json').read_text())
            original_prov=dict(metadata['provenance'])
            for path, recorded in metadata['code_files'].items():
                if sha((ROOT/path).read_bytes()) != recorded:
                    raise ValueError('Recorded source differs from export source: '+path)
            code={path:sha((dest/path).read_bytes()) for path in metadata['code_files']}
            for path, recorded in metadata['code_files'].items():
                if code[path] != recorded and path not in {'research/evaluation-plan.md','governance/spec.md'}:
                    raise ValueError('Undeclared source change in anonymous export: '+path)
            metadata['code_files']=code
            metadata['provenance']['code_sha256']=sha(canonical(code))
            write_json(run/'metadata.json',metadata)
            for filename in ('trials.jsonl','timings.jsonl'):
                path=run/filename;lines=[]
                for line in path.read_text().splitlines():
                    row=json.loads(line);row['provenance']=metadata['provenance']
                    lines.append(json.dumps(row,sort_keys=True,ensure_ascii=False,allow_nan=False))
                path.write_text('\n'.join(lines)+ ('\n' if lines else ''))
            complete=json.loads((run/'completion.json').read_text())
            original_hashes=dict(complete['output_sha256'])
            complete['ending_code_sha256']=metadata['provenance']['code_sha256']
            complete['output_sha256']={name:sha((run/name).read_bytes()) for name in original_hashes}
            write_json(run/'completion.json',complete)
            changes.append({'run':str(run.relative_to(dest)), 'original_provenance':original_prov,
                            'exported_provenance':metadata['provenance'],
                            'original_output_sha256':original_hashes,
                            'exported_output_sha256':complete['output_sha256']})
            write_report(run)
        write_json(dest/'ANONYMIZATION.json',{'mode':'derived reviewer view; not a new run',
                   'executable_code_changed':False,'observations_changed':False,'changes':changes})
    manifest={str(f.relative_to(dest)):sha(f.read_bytes()) for f in sorted(dest.rglob('*')) if f.is_file()}
    write_json(dest/'SHA256SUMS.json',manifest)
    with ZipFile(dest.with_suffix('.zip'),'x',ZIP_DEFLATED,compresslevel=9) as archive:
        for file in sorted(dest.rglob('*')):
            if file.is_file():archive.write(file,str(Path(dest.name)/file.relative_to(dest)))
    print(dest.with_suffix('.zip'))


if __name__=='__main__':main()
