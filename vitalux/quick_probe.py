"""Isolated Qt Quick/RHI startup smoke test: catches native Qt/driver aborts."""
import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PySide6.QtQuick import QSGRendererInterface


def main():
    # QSG_RHI_BACKEND must be configured before creating the Quick surface.
    selected = os.environ.get('VITALUX_QUICK_API', 'opengl').lower()
    if selected not in ('opengl', 'vulkan'):
        return 8
    os.environ['QSG_RHI_BACKEND'] = selected
    app = QApplication([])
    from PySide6.QtQuickWidgets import QQuickWidget
    from .quick_scene import QuickAmbientScene
    scene = QuickAmbientScene()
    scene.resize(800, 560)
    # Simulate the actual mixed Qt Widget layout, not only an empty Quick view.
    layout = QVBoxLayout(scene)
    layout.addWidget(QLabel('Qt Widget overlay smoke test', scene))
    scene.show()
    expected = (QSGRendererInterface.Vulkan if selected == 'vulkan'
                else QSGRendererInterface.OpenGL)
    def check():
        if scene.status() != QQuickWidget.Ready or scene.rootObject() is None:
            app.exit(3)
            return
        actual = scene.quickWindow().rendererInterface().graphicsApi()
        if actual != expected:
            print(f'Unexpected RHI: {actual}; expected {expected}', file=sys.stderr)
            app.exit(4)
            return
        image = scene.grabFramebuffer()
        if image.isNull():
            app.exit(5)
            return
        scene.resize(880, 610)
        scene.sync_background()
        QTimer.singleShot(450, finish)
    def finish():
        if (scene.status() != QQuickWidget.Ready or
                scene.quickWindow().rendererInterface().graphicsApi() != expected or
                scene.grabFramebuffer().isNull()):
            app.exit(6)
        else:
            scene.close()
            app.exit(0)
    QTimer.singleShot(750, check)
    QTimer.singleShot(5500, lambda: app.exit(7))
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
