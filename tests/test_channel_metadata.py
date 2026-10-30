"""Real Git trees: build labels/docs never masquerade as new test changes."""
from pathlib import Path
import importlib.util,subprocess,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from channel_metadata import describe
from importlib.machinery import SourceFileLoader
prepare=SourceFileLoader('prepare_unstable_test',str(Path(__file__).resolve().parents[1]/'scripts/prepare-unstable-build.py')).load_module()
assert prepare.next_test_version('0.9.6.1-unstable.2','0.9.6.1')=='0.9.6.2-unstable.1'
assert prepare.next_test_version('0.9.6.2-unstable.9','0.9.6.1')=='0.9.6.2-unstable.10'
spec=importlib.util.spec_from_file_location('sync_unstable',Path(__file__).resolve().parents[1]/'scripts/sync-unstable.py')
sync=importlib.util.module_from_spec(spec);spec.loader.exec_module(sync)

with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    def git(*args):return subprocess.run(['git',*args],cwd=root,check=True,capture_output=True,text=True).stdout.strip()
    git('init','-b','main');git('config','user.name','PAAAUUULLOOOH');git('config','user.email','PAAAUUULLOOOH@users.noreply.github.com')
    (root/'vitalux').mkdir();(root/'assets').mkdir()
    (root/'vitalux/__init__.py').write_text('__version__ = "0.9.6.0"\nDEFAULT_THEME="gold"\n')
    (root/'vitalux/app.py').write_text('appearance="glass"\n')
    git('add','.');git('commit','-m','stable');git('switch','-c','unstable')
    (root/'vitalux/__init__.py').write_text('__version__ = "0.9.6.1-unstable.20"\nDEFAULT_THEME="gold"\n')
    (root/'README.md').write_text('Updated instructions')
    (root/'assets/vitalux-readme-dark-animated.svg').write_text('readme-only art')
    git('add','.');git('commit','-m','build label and documentation')
    state=describe(main='main',root=root)
    assert not state['has_test_changes'] and state['same_as_stable']
    (root/'packaging').mkdir()
    (root/'packaging/restart-request.py').write_text('restart_protocol=2\n')
    git('add','.');git('commit','-m','launch handoff change')
    assert describe(main='main',root=root)['has_test_changes'],'Runtime-only changes were mistaken for Stable parity'
    (root/'vitalux/app.py').write_text('appearance="improved glass"\n')
    git('add','.');git('commit','-m','actual app change')
    assert describe(main='main',root=root)['has_test_changes']
    git('switch','main');(root/'vitalux/new.py').write_text('new_stable=True\n');git('add','.');git('commit','-m','new stable baseline')
    git('switch','unstable');assert not describe(main='main',root=root)['has_test_changes']
    git('merge','--no-edit','main');assert describe(main='main',root=root)['has_test_changes']
ours='# History\n\n## [v0.9.6.1-unstable.2] - 2026-10-21\n- Test notes\n\n## [v0.9.6.0] - 2026-10-20\n- Old notes\n'
theirs='# History\n\n## [v0.9.6.1] - 2026-10-21\n- Stable changes\n\n## [v0.9.6.0] - 2026-10-20\n- Old notes\n'
merged=sync.merge_changelog(ours,theirs)
assert merged.index('[v0.9.6.1]')<merged.index('[v0.9.6.1-unstable.2]')<merged.index('[v0.9.6.0]')
assert 'Test notes' in merged and 'Stable changes' in merged
try:sync.merge_changelog(ours,theirs.replace('Old notes','Conflicting old notes'))
except ValueError:pass
else:raise AssertionError('Discarded a conflicting published changelog')
print('Git content/ancestry gate, build-number/doc exclusion and lossless changelog merge PASS')
