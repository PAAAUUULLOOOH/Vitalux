"""Keep declared dependency versions and the actual shipped binaries aligned."""
import json,os,re,subprocess
from pathlib import Path


def expected(root):
    root=Path(root);records=json.loads((root/'third_party/sources.lock.json').read_text())
    sources={entry['name']:entry['version'] for entry in records}
    qt=sources['pyside-setup']
    if any(sources[name]!=qt for name in ('qtbase','qtdeclarative','qtsvg','qtwayland','qtimageformats')):
        raise ValueError('Qt and PySide source versions must match')
    requirements=root/'requirements-dev.txt'
    if requirements.exists():
        pins=dict(re.findall(r'^([A-Za-z0-9_-]+)==([^\s#]+)$',requirements.read_text(),re.M))
        if pins.get('PySide6-Essentials')!=qt or pins.get('psutil')!=sources['psutil']:
            raise ValueError('Python pins and corresponding-source locks disagree')
    if not sources['cpython'].startswith('3.12.'):
        raise ValueError('A Python minor-version change requires a separate compatibility update')
    return dict(python=sources['cpython'],PySide6=qt,Qt=qt,psutil=sources['psutil'])


def inspect(root):
    root=Path(root).resolve();python=root/'runtime/bin/python3.12'
    env=dict(os.environ,LD_LIBRARY_PATH=str(root/'lib'),PYTHONNOUSERSITE='1')
    for name in ('PYTHONHOME','PYTHONPATH','PYTHONUSERBASE','LD_PRELOAD'):env.pop(name,None)
    helper=root/'packaging/runtime-libraries.py'
    if helper.exists():env['LD_LIBRARY_PATH']=subprocess.check_output([str(python),str(helper),str(root)],env=env,text=True).strip()
    probe='import json,sys,PySide6,psutil;from PySide6.QtCore import qVersion;print(json.dumps(dict(python=".".join(map(str,sys.version_info[:3])),PySide6=PySide6.__version__,Qt=qVersion(),psutil=psutil.__version__)))'
    actual=json.loads(subprocess.check_output([str(python),'-c',probe],env=env,text=True,timeout=30))
    wanted=expected(root)
    if actual!=wanted:raise ValueError('Shipped runtime versions do not match their pins/source locks: '+repr(dict(expected=wanted,actual=actual)))
    return actual
