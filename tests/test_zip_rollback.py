"""Regression: ZIP updater preserves one complete rollback snapshot."""
from pathlib import Path
import json
import tempfile
import sys
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vitalux import updater


def check_zip_restore():
    with tempfile.TemporaryDirectory(prefix="vitalux-zip-rollback-") as temp:
        root = Path(temp)
        (root/"vitalux").mkdir()
        (root/"vitalux"/"__main__.py").write_text("version='bad-current'\n")
        (root/"run.sh").write_text("new-launcher\n")
        (root/"assets").mkdir()
        (root/"assets"/"logo.txt").write_text("new")
        backup = root/".backup"
        (backup/"vitalux").mkdir(parents=True)
        (backup/"vitalux"/"__main__.py").write_text("version='stable-previous'\n")
        (backup/"root_files"/"assets").mkdir(parents=True)
        (backup/"root_files"/"run.sh").write_text("old-launcher\n")
        (backup/"root_files"/"assets"/"logo.txt").write_text("old")
        (backup/"metadata.json").write_text(json.dumps({
            "version":"0.9.3.51","root_files":["run.sh","assets"],
            "settings_saved":False}))
        assert updater.backup_available(str(root))
        updater.restore_previous(str(root), restore_settings=False)
        assert "stable-previous" in (root/"vitalux"/"__main__.py").read_text()
        assert (root/"run.sh").read_text() == "old-launcher\n"
        assert (root/"assets"/"logo.txt").read_text() == "old"
        assert updater.backup_available(str(root)), "A healthy restore must not automatically destroy recovery assets"
        assert not (root/".backup.old").exists()
        print("ZIP rollback restores application, launcher, and assets: PASS")


def check_zip_permissions():
    with tempfile.TemporaryDirectory(prefix='vitalux-zip-modes-') as directory:
        root = Path(directory)/'installed'
        (root/'vitalux').mkdir(parents=True)
        (root/'vitalux/__main__.py').write_text('old=True\n')
        archive = Path(directory)/'release.zip'
        with ZipFile(archive, 'w') as zipped:
            for name, content, mode in (
                    ('vitalux/__main__.py', 'new=True\n', 0o644),
                    ('run.sh', '#!/bin/sh\nexit 0\n', 0o755),
                    ('runtime/bin/python3.12', 'test interpreter', 0o4755)):
                item = ZipInfo('Vitalux-test/'+name)
                item.external_attr = mode << 16
                zipped.writestr(item, content)
        def download(url, output, *args, **kwargs):
            import shutil
            shutil.copyfile(archive, output)
        with patch.object(updater, '_download_verified', download), patch.dict('os.environ', {}, clear=False):
            import os
            os.environ.pop('APPIMAGE', None)
            updater.install('https://example.invalid/verified.zip', root=str(root), sha256='0'*64)
        assert (root/'run.sh').stat().st_mode & 0o7777 == 0o755
        assert (root/'runtime/bin/python3.12').stat().st_mode & 0o7777 == 0o755
        print('ZIP executable modes restored; special permission bits removed: PASS')


if __name__ == "__main__":
    check_zip_restore()
    check_zip_permissions()
