#!/usr/bin/env python3
"""Reproduce offline evidence using Python's standard library only.

Use --output NEW_DIRECTORY. No network, package install, secret, model account,
or external attack corpus is required. Existing evidence is never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def verify_vendor():
    data = json.loads((ROOT / 'vendor/manifest.json').read_text())
    for item in data['files']:
        raw = (ROOT / 'vendor/sentinel-tpd' / item['path']).read_bytes()
        blob = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
        if hashlib.sha256(raw).hexdigest() != item['sha256'] or blob != item['git_blob_sha1']:
            raise RuntimeError('upstream source mismatch: ' + item['path'])
    return len(data['files'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--quick', action='store_true', help='deterministic replay only; no timing')
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.error('Python 3.10 or newer required')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    env['PYTHONPATH'] = str(ROOT / 'src')
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    commands = []

    def run(command, name):
        with (output / name).open('x', encoding='utf-8') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, text=True)
        commands.append({'argv': [Path(command[0]).name, *command[1:]],
                         'log': name, 'returncode': result.returncode})
        if result.returncode:
            raise RuntimeError('reproduction stage failed; inspect ' + name)

    status = {'python': sys.version, 'mode': 'quick' if args.quick else 'full',
              'vendor_files_verified': verify_vendor(), 'commands': commands}
    try:
        run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], 'authored-tests.log')
        run([sys.executable, '-m', 'unittest', 'vendor/sentinel-tpd/tests/test_sentinel_tpd.py'], 'upstream-tests.log')
        run([sys.executable, 'experiments/upstream_counterexamples.py'], 'upstream-observations.json')
        common = [sys.executable, '-m', 'experiments.run_study']
        command = common + ['--manifest', 'data/scenario_manifest.json', '--output',
                            str(output / 'designed'), '--label', 'specification-aware-reproduction']
        if args.quick:
            command.append('--no-timing')
        run(command, 'designed-run.log')
        run(common + ['--manifest', 'data/finite_trace_manifest.json', '--output',
                      str(output / 'enumerated'), '--no-timing', '--label',
                      'bounded-model-reproduction'], 'enumerated-run.log')
        for name in ('designed', 'enumerated'):
            run([sys.executable, '-m', 'experiments.report_results', str(output / name),
                 '--output', str(output / (name + '-regenerated'))], name + '-report.log')
            for filename in ('summary.json', 'summary.md', 'tables.tex'):
                if (output / name / filename).read_bytes() != (output / (name + '-regenerated') / filename).read_bytes():
                    raise RuntimeError('report regeneration mismatch: ' + name + '/' + filename)
        reference = ROOT / 'data/expected_outcomes.json'
        if reference.exists():
            expected = json.loads(reference.read_text())
            for suite, methods in expected.items():
                actual = json.loads((output / suite / 'summary.json').read_text())['by_method']
                for method, metrics in methods.items():
                    for metric, value in metrics.items():
                        if actual[method][metric] != value:
                            raise RuntimeError(f'deterministic mismatch: {suite}/{method}/{metric}')
            status['deterministic_outcomes_match_reference'] = True
        status['status'] = 'completed'
    except Exception as exc:
        status['status'] = 'failed'
        status['error'] = str(exc)
        raise
    finally:
        # Keep local path details in local commands; exported anonymous artifacts
        # use a separate export view, preserving the raw run as the original.
        (output / 'reproduction.json').write_text(json.dumps(status, indent=2)+'\n')
    print('Reproduction completed:', output)


if __name__ == '__main__':
    main()
