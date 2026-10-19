#!/usr/bin/env python3
"""Run Vitalux's standalone regression scripts in isolated Qt processes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--output', type=Path, default=Path('build/regressions'))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    tests = sorted((root/'tests').glob('test_*.py'))
    if not tests:
        raise SystemExit('No test scripts found')

    def run(test):
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix='vitalux-test-') as directory:
            env = os.environ.copy()
            env.pop('VITALUX_LOCAL_PREVIEW', None)
            env['QT_QPA_PLATFORM'] = 'offscreen'
            env['PYTHONPATH'] = str(root)
            for var, suffix in (
                    ('XDG_CONFIG_HOME', 'config'), ('XDG_STATE_HOME', 'state'),
                    ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache'),
                    ('XDG_RUNTIME_DIR', 'runtime')):
                target = Path(directory)/suffix
                target.mkdir(mode=0o700)
                env[var] = str(target)
            try:
                result = subprocess.run([sys.executable, str(test)], cwd=root,
                                        env=env, capture_output=True, text=True, timeout=150)
                code, log = result.returncode, result.stdout+result.stderr
            except subprocess.TimeoutExpired as exc:
                code = 124
                log = (exc.stdout or b'') + (exc.stderr or b'')
                if isinstance(log, bytes):
                    log = log.decode(errors='replace')
                log += '\nTIMEOUT: script exceeded 150 seconds\n'
            (output/(test.stem+'.log')).write_text(log)
            print(('PASS ' if code == 0 else 'FAIL ')+test.name, flush=True)
            if code:
                print(log[-8000:], flush=True)
                if os.environ.get('GITHUB_ACTIONS') == 'true':
                    detail = log[-12000:].replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
                    print(f'::error title={test.name}::{detail}', flush=True)
            return {'script': test.name, 'exit_code': code,
                    'seconds': round(time.monotonic()-started, 2)}

    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        records = list(pool.map(run, tests))
    summary = {'passed': sum(r['exit_code'] == 0 for r in records),
               'failed': sum(r['exit_code'] != 0 for r in records), 'scripts': records}
    (output/'results.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(f'{summary["passed"]}/{len(records)} scripts passed; {summary["failed"]} failed', flush=True)
    return int(bool(summary['failed']))


if __name__ == '__main__':
    raise SystemExit(main())
