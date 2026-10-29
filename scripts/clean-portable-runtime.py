#!/usr/bin/env python3
"""Remove unused optional Qt modules; retain all supported desktop renderers."""
from pathlib import Path
import shutil
import sys


def clean(root):
    qt = root/'runtime/lib/python3.12/site-packages/PySide6/Qt'
    removed = []
    for pattern in ('libQt6Lottie*.so*', 'libQt6QuickVector*.so*', 'libQt6QuickTimeline.so*',
                    'libQt6QuickShapes.so*', 'libQt6QmlCompiler.so*'):
        for path in (qt/'lib').glob(pattern):
            removed.append(str(path.relative_to(root)))
            path.unlink()
    for relative in ('../QtOpenGLWidgets.abi3.so', 'lib/libQt6OpenGLWidgets.so.6',
                     'plugins/wayland-graphics-integration-client/libvulkan-server.so', 'plugins/vectorimageformats', 'plugins/imageformats/libqpdf.so',
                     'plugins/platforminputcontexts/libqtvirtualkeyboardplugin.so'):
        path = qt/relative
        if path.exists():
            removed.append(str(path.relative_to(root)))
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    return removed


if __name__ == '__main__':
    removed = clean(Path(sys.argv[1]).resolve())
    print(f'Removed {len(removed)} unused optional Qt libraries/plugins')
