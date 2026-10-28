#!/usr/bin/env python3
"""Prefer desktop/driver interfaces from the host; supply absent ones offline."""
import ctypes
import os
from pathlib import Path
import sys

INTERFACES=('libwayland-client.so.0','libwayland-cursor.so.0','libdrm.so.2')


def library_path(root):
    parts=[value for value in os.environ.get('LD_LIBRARY_PATH','').split(os.pathsep) if value]
    root=Path(root)
    for name in INTERFACES:
        try:
            # The private copy lives outside lib/: modern Mesa may need API
            # added after the baseline ABI used to build the portable fallback.
            ctypes.CDLL(name)
        except OSError:
            folder=root/'fallback-libraries'/name
            if (folder/name).is_file():
                ctypes.CDLL(str(folder/name))
                parts.append(str(folder))
    return os.pathsep.join(dict.fromkeys(parts))


if __name__=='__main__':print(library_path(Path(sys.argv[1])))
