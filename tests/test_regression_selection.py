"""Selection follows transitive imports and keeps uncertain/critical work safe."""
import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from regression_selection import select
with tempfile.TemporaryDirectory() as folder:
    root=Path(folder)
    for name,text in {
        'vitalux/__init__.py':'', 'vitalux/sensor.py':'value=1',
        'vitalux/widget.py':'from . import sensor', 'vitalux/other.py':'value=2',
        'tests/test_screen.py':'from vitalux import widget',
        'tests/test_other.py':'from vitalux import other',
        'tests/test_dynamic.py':"import importlib\nname='sensor'\nimportlib.import_module('vitalux.'+name)",
        'tests/test_core_behaviors.py':'pass',
    }.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    result=select(root,['vitalux/sensor.py'])
    assert set(result['selected'])=={'test_screen.py','test_dynamic.py','test_core_behaviors.py'}
    assert result['skipped']==['test_other.py'] and not result['full']
    assert select(root,['portable-runtime/SHA256SUMS'])['full']
    assert select(root,['unknown-input'])['full']
    assert select(root,['README.md'])['selected']==['test_core_behaviors.py']
    assert 'test_other.py' in select(root,['tests/test_other.py'])['selected']
print('Transitive dependencies, dynamic-import safety, critical-input fallback and documentation-only selection PASS')
