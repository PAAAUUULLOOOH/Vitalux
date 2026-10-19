"""Portable archives accept reproducible epoch dates without losing execute bits."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile


def run():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        current, previous, output = folder/'Vitalux-v0.9.5.6', folder/'Vitalux-v0.9.5.5', folder/'out'
        current.mkdir()
        previous.mkdir()
        binary = current/'run.sh'
        binary.write_text('#!/bin/sh\nexit 0\n')
        binary.chmod(0o755)
        os.utime(binary, (0, 0))
        (previous/'obsolete.txt').write_text('previous')
        subprocess.run([sys.executable, str(root/'scripts/create-release-archives.py'),
                        str(current), str(previous), str(output), '0.9.5.5'], check=True)
        with ZipFile(output/'Vitalux-v0.9.5.6-linux-x86_64.zip') as zipped:
            item = zipped.getinfo(current.name+'/run.sh')
            assert item.date_time == (1980, 1, 1, 0, 0, 0)
            assert item.external_attr >> 16 & 0o111
            assert zipped.read(item) == binary.read_bytes()
        with ZipFile(output/'Vitalux-v0.9.5.6-Update-von-v0.9.5.5.zip') as zipped:
            assert 'obsolete.txt' in zipped.read('ENTFERNTE-DATEIEN.txt').decode()
            assert zipped.testzip() is None
    print('Release archives: epoch timestamps, executable modes and removal list PASS')


if __name__ == '__main__':
    run()
