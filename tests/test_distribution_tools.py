"""Shared archive extraction preserves launchers and rejects escaping members."""
from pathlib import Path
import stat
import sys
import tempfile
from zipfile import ZipFile, ZipInfo
import runpy
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from distribution_tools import extract_release_zip


with tempfile.TemporaryDirectory(prefix='vitalux-distribution-') as folder:
    root = Path(folder)
    archive = root / 'package.zip'
    launcher = ZipInfo('Vitalux/run.sh')
    launcher.create_system = 3
    launcher.external_attr = (stat.S_IFREG | 0o755) << 16
    with ZipFile(archive, 'w') as zipped:
        zipped.writestr(launcher, '#!/bin/sh\nexit 0\n')
    target = root / 'normal'
    extract_release_zip(archive, target)
    assert (target / 'Vitalux/run.sh').read_text().endswith('exit 0\n')
    assert (target / 'Vitalux/run.sh').stat().st_mode & 0o111

    for name, symlink in (('../escaped.txt', False), ('/absolute.txt', False),
                          ('Vitalux/link', True)):
        item = ZipInfo(name)
        item.create_system = 3
        item.external_attr = ((stat.S_IFLNK if symlink else stat.S_IFREG) | 0o644) << 16
        with ZipFile(archive, 'w') as zipped:
            zipped.writestr(item, 'outside')
        try:
            extract_release_zip(archive, root / 'rejected')
        except RuntimeError:
            pass
        else:
            raise AssertionError('Unsafe release member accepted: ' + name)
    assert not (root / 'escaped.txt').exists()

    # Notice collection excludes example code but follows attribution license
    # references, even when the legal text lives in a source header.
    collector=runpy.run_path(str(Path(__file__).resolve().parents[1]/'scripts/collect-license-notices.py'))
    source=root/'notices.zip'
    with ZipFile(source,'w') as zipped:
        for name in ('LICENSE','COPYING.libsample','COPYING3','LGPL2.txt','GPLv2.TXT',
                     'licenseRule.json','LICENSES/MIT.txt','src/bufferprocs_py37.h'):
            zipped.writestr('project/'+name,'Verbatim license fixture')
        zipped.writestr('project/src/qt_attribution.json',json.dumps({'LicenseFile':'bufferprocs_py37.h'}))
        zipped.writestr('project/examples/licensewizard/licensewizard.py','example')
        zipped.writestr('project/examples/licensewizard/licensewizard.png','image')
        zipped.writestr('project/tools/license_check.py','tool')
    notices=root/'notices'
    collector['collect']([dict(filename=source.name,name='qt')],root,notices)
    assert (notices/'qt/src/bufferprocs_py37.h').read_text()=='Verbatim license fixture'
    assert (notices/'qt/COPYING.libsample').is_file()
    assert all((notices/'qt'/name).is_file() for name in ('COPYING3','LGPL2.txt','GPLv2.TXT','licenseRule.json'))
    assert not any('licensewizard' in p.name or p.name=='license_check.py' for p in notices.rglob('*'))

print('Release extraction: executable launcher retained; path traversal, absolute paths and symlinks rejected PASS')
