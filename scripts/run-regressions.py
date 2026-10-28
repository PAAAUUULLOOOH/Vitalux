#!/usr/bin/env python3
"""Run Vitalux's standalone regression scripts in isolated Qt processes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time

# These scripts assert real-time Qt animation/relaunch behavior. Let them own
# the test runner's CPU budget instead of competing with other GUI processes.
EXCLUSIVE={'test_framed_navigation.py','test_settings_search_reset.py',
           'test_restart_profile_flow.py','test_startup_pipeline.py'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--output', type=Path, default=Path('build/regressions'))
    parser.add_argument('--only',nargs='+',help='Explicit scripts for focused local verification')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    tests = sorted((root/'tests').glob('test_*.py'))
    if args.only:
        requested=set(args.only)
        unknown=requested-{test.name for test in tests}
        if unknown:parser.error('Unknown test scripts: '+', '.join(sorted(unknown)))
        tests=[test for test in tests if test.name in requested]
    if not tests:
        raise SystemExit('No test scripts found')

    def run(test):
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix='vitalux-test-') as directory:
            env = os.environ.copy()
            env.pop('VITALUX_LOCAL_PREVIEW', None)
            env['QT_QPA_PLATFORM'] = 'offscreen'
            env['VITALUX_SPEC_OFFLINE'] = '1'
            env['PYTHONPATH'] = str(root)
            for var, suffix in (
                    ('XDG_CONFIG_HOME', 'config'), ('XDG_STATE_HOME', 'state'),
                    ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache'),
                    ('XDG_RUNTIME_DIR', 'runtime')):
                target = Path(directory)/suffix
                target.mkdir(mode=0o700)
                env[var] = str(target)
            try:
                process = subprocess.Popen([sys.executable,str(test)],cwd=root,env=env,
                                           stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                           text=True,start_new_session=True)
                try:
                    stdout,stderr=process.communicate(timeout=150)
                    code,log=process.returncode,stdout+stderr
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL)
                    stdout,stderr=process.communicate()
                    code,log=124,stdout+stderr+'\nTIMEOUT: script exceeded 150 seconds\n'
                finally:
                    # A relaunching shell may have exited before its Qt child.
                    # No child from a failed test may load the next test's CPU.
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
            except OSError as exc:
                code,log=125,str(exc)
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
        records = list(pool.map(run, [test for test in tests if test.name not in EXCLUSIVE]))
    records += [run(test) for test in tests if test.name in EXCLUSIVE]
    summary = {'passed': sum(r['exit_code'] == 0 for r in records),
               'failed': sum(r['exit_code'] != 0 for r in records), 'scripts': records}
    (output/'results.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(f'{summary["passed"]}/{len(records)} scripts passed; {summary["failed"]} failed', flush=True)
    return int(bool(summary['failed']))


if __name__ == '__main__':
    raise SystemExit(main())
