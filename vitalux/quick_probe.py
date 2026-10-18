"""Short isolated GPU + Qt Quick startup test, including a live resize."""
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication


def main():
    app = QApplication([])
    from PySide6.QtGui import QOffscreenSurface, QOpenGLContext
    surface = QOffscreenSurface()
    surface.create()
    if not surface.isValid():
        return 2
    context = QOpenGLContext()
    if not context.create() or not context.makeCurrent(surface):
        return 2
    context.doneCurrent()
    from PySide6.QtQuickWidgets import QQuickWidget
    from .quick_scene import QuickAmbientScene
    scene = QuickAmbientScene()
    if scene.status() != QQuickWidget.Ready or scene.rootObject() is None:
        return 3
    scene.resize(800, 560)
    scene.show()
    def check():
        if scene.status() != QQuickWidget.Ready or scene.rootObject() is None:
            app.exit(4)
            return
        scene.resize(880, 610)
        scene.sync_background()
        QTimer.singleShot(
            350, lambda: app.exit(0 if scene.status() == QQuickWidget.Ready else 5))
    QTimer.singleShot(450, check)
    QTimer.singleShot(4000, lambda: app.exit(7))
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
