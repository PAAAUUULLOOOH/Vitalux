"""Holographic smoke/regression tests for the native Qt rendering paths."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.getcwd())

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from vitalux import theme
from vitalux.glass import AmbientScene, GlassSidebar, GlassSurface
from vitalux.holographic import scene_pixmap


def run():
    app = QApplication.instance() or QApplication([])
    theme.set_mode("holographic")
    theme.set_accent("#4f8cff")
    assert theme.mode() == "holographic"
    assert theme.accent() == "#52d3ff"
    assert theme.BG == "#030b13"
    assert "QComboBox" in theme.stylesheet()
    image = scene_pixmap(QSize(800, 560), theme.accent())
    assert isinstance(image, QPixmap) and not image.isNull()
    assert image.toImage().pixelColor(20, 20).alpha() == 255, "HUD background must be opaque"
    scene = AmbientScene()
    scene.resize(800, 560)
    scene.show()
    app.processEvents()
    scene._ensure_composed()
    assert scene._composed_soft.cacheKey() == scene._composed_sharp.cacheKey(), "Holographic must never blur the background"
    assert scene._wallpaper_timer.isActive() is False
    card = GlassSurface(scene)
    card.resize(300, 200)
    card.show()
    sidebar = GlassSidebar(scene)
    sidebar.resize(250, 500)
    sidebar.show()
    app.processEvents()
    assert not card.grab().isNull() and not sidebar.grab().isNull()
    scene.close()
    theme.set_mode("glass")
    assert theme.mode() == "glass"
    assert theme.accent() == "#4f8cff", "Default Glass accent must remain Vitalux Blue"
    print("Holographic native HUD + opaque backend + Glass default: OK")


if __name__ == "__main__":
    run()
