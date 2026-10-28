"""Release selection retains full checks for shared, unknown and baseline changes."""
from pathlib import Path
import subprocess
import sys
import tempfile
import json

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validation_plan import select,GROUPS

assert not any(select(['README.md','CHANGELOG.md','vitalux/__init__.py'])['groups'].values())
for path in ('vitalux/theme.py','vitalux/settings.py','assets/new.svg','packaging/AppRun',
             'unknown/new-runtime.bin','scripts/new-check.py'):
    assert all(select([path])['groups'].values()),path
assert select(['vitalux/game_profiles.py'])['groups']['overlay']
assert select(['vitalux/product_images.py'])['groups']['hardware_network']
assert select(['vitalux/network_traffic.py'])['groups']['kernel']
assert select(['vitalux/nav_icons.py'])['groups']['navigation']
assert all(select([],complete=True)['groups'].values())
with tempfile.TemporaryDirectory() as folder:
    output=Path(folder)/'plan.json';gha=Path(folder)/'outputs'
    subprocess.run([sys.executable,'scripts/validation_plan.py','--base','missing-baseline',
                    '--output',str(output),'--github-output',str(gha)],check=True,capture_output=True)
    assert all(json.loads(output.read_text())['groups'].values())
    assert set(gha.read_text().splitlines())=={group+'=true' for group in GROUPS}
print('Change-selected checks, shared/unknown full matrix and missing-baseline fallback PASS')
