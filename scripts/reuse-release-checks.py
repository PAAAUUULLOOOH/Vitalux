#!/usr/bin/env python3
"""Reuse completed expensive checks only for a reviewed packaging-only retry.

Application/runtime bytes must be unchanged, and every named prior check must
have succeeded on an ancestor from this repository's Stable workflow. Basic
regressions, assembly, runtime and final package/update checks always run again.
"""
import argparse,json,os,re,subprocess
from pathlib import Path

CHECKS=(
 'Check bundled OpenGL and Vulkan game recording in both architectures',
 'Check bundled overlay inside a real Flatpak sandbox',
 "Check the overlay inside Valve's Steam runtime",
 'Check wide Steam capsules and offline reuse',
 'Check native header search, translucent dock and interrupted appearance transitions',
 'Check resource budgets, endurance and reference rendering',
 'Check real component pictures and offline reuse',
 'Check real manufacturer datasheets and offline reuse',
 'Check real DE/EN datasheet translation and offline reuse',
 'Check kernel traffic accounting and session blocks in the disposable runner VM',
 'Check CPU and X11 rendering in isolated compositor sessions',
 'Verify source ZIP startup without system Python',
 'Check fractional-scale settings layouts',
)
ALLOWED={'.github/workflows/publish.yml','packaging/build-appimage.sh',
 'scripts/prepare-release.py','scripts/check-distribution.py','scripts/distribution_tools.py',
 'scripts/reuse-release-checks.py','tests/test_package_permissions.py'}

def command(*args):return subprocess.check_output(args,text=True).strip()
def proof(run_id,repo):
 if not re.fullmatch(r'[0-9]+',run_id):raise ValueError('Expected a numeric validation run')
 run=json.loads(command('gh','api',f'repos/{repo}/actions/runs/{run_id}'))
 if (run['head_branch']!='main' or run['path']!='.github/workflows/publish.yml'
     or run['repository']['full_name']!=repo or run['status']!='completed'):
  raise ValueError('Validation must be a completed Stable workflow from this repository')
 previous=run['head_sha']
 if not re.fullmatch(r'[0-9a-f]{40}',previous):raise ValueError('Invalid source commit')
 subprocess.run(['git','merge-base','--is-ancestor',previous,'HEAD'],check=True)
 changed=command('git','diff','--name-only','--no-renames',previous,'HEAD').splitlines()
 if not set(changed)<=ALLOWED:raise ValueError('Application or unrelated files changed: '+', '.join(sorted(set(changed)-ALLOWED)))
 jobs=json.loads(command('gh','api',f'repos/{repo}/actions/runs/{run_id}/jobs?per_page=100'))['jobs']
 successful={step['name'] for job in jobs if job['name']=='build-and-release'
             for step in job['steps'] if step['conclusion']=='success'}
 if not set(CHECKS)<=successful:raise ValueError('Prior checks incomplete: '+', '.join(sorted(set(CHECKS)-successful)))
 return dict(reuse=True,run_id=run_id,url=run['html_url'],validated_commit=previous,
             current_commit=command('git','rev-parse','HEAD'),packaging_only_changes=changed,reused_steps=CHECKS)

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--run',default='');parser.add_argument('--github-output',type=Path)
 args=parser.parse_args()
 result=proof(args.run,os.environ.get('GITHUB_REPOSITORY','PAAAUUULLOOOH/Vitalux')) if args.run else dict(reuse=False)
 path=Path('build/validation-reuse.json');path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(result,indent=2)+'\n')
 if args.github_output:
  with args.github_output.open('a') as stream:stream.write('reuse='+str(result['reuse']).lower()+'\n')
 print(json.dumps(result,indent=2))
