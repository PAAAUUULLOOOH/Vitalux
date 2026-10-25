"""The inactive test channel reuses Stable bytes and retains legacy return proof."""
import contextlib,importlib.util,io,json,os,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from vitalux import updater

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
baseline='0.9.6.3';test='0.9.6.3-unstable.25'
manifest=dict(schema=1,version=test,commit='last-test',has_test_changes=False,stable_version=baseline,stable_contains_test=True,baseline_version=baseline)
with patch.object(updater,'_get_unstable_release',return_value=dict(tag_name='unstable',prerelease=True,body='Baseline')),patch.object(updater,'_unstable_manifest',return_value=manifest):
 result=updater.check('unstable',stable_result=dict(ok=True,latest=baseline,notes='Stable notes'))
 assert result['latest']==baseline and result['covered_test_version']==test
 assert not result['eligible'] and not result['url'] and result['notes']=='Stable notes'

refresh=module('baseline_refresh','scripts/refresh-unstable-channel.py');calls=[];uploaded={}
names=['Vitalux-v'+baseline+suffix for suffix in ('-linux-x86_64.zip','-x86_64.AppImage','-SHA256SUMS.txt','-ThirdPartySources.zip')]
def gh(*args,**kwargs):
 calls.append(args)
 if args[:2]==('release','view'):
  assets=([dict(name='obsolete-test.zip'),dict(name='Vitalux-unstable-channel.json')] if args[2]=='unstable' else [dict(name=n) for n in names])
  return SimpleNamespace(returncode=0,stdout=json.dumps(dict(assets=assets)))
 if args[:2]==('release','download'):
  name=args[args.index('--pattern')+1];folder=Path(args[args.index('--dir')+1])
  (folder/name).write_bytes(json.dumps(manifest).encode() if name.endswith('channel.json') else ('verified Stable '+name).encode())
 if args[:2]==('release','upload'):uploaded[Path(args[3]).name]=Path(args[3]).read_bytes()
 return SimpleNamespace(returncode=0,stdout='')
with patch.object(refresh,'gh',gh),patch.object(refresh,'describe',return_value=dict(stable_version=baseline,stable_commit='stable-head',stable_contains_test=True,same_as_stable=False,has_test_changes=False)),contextlib.redirect_stdout(io.StringIO()):refresh.refresh()
new=json.loads(uploaded['Vitalux-unstable-channel.json'])
assert new['version']==test and new['baseline_version']==baseline and new['baseline_commit']=='stable-head'
assert new['commit']=='last-test' and not new['has_test_changes']
assert all(uploaded[n]==('verified Stable '+n).encode() for n in names)
manifest_upload=next(i for i,a in enumerate(calls) if a[:2]==('release','upload') and a[3].endswith('channel.json'))
assert all(i>manifest_upload for i,a in enumerate(calls) if a[:2]==('release','delete-asset'))
assert not any(a[:2]==('workflow','run') for a in calls)
prepare=module('prepare_next_test','scripts/prepare-unstable-build.py')
assert prepare.next_test_version(baseline,baseline)=='0.9.6.4-unstable.1'
print('Stable baseline bytes, legacy return proof, disabled equal-version offer, safe asset replacement and next real test numbering PASS')
