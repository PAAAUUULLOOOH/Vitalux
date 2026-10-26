"""Navigation snapshots stay inside content; frame controls survive every design."""
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['VITALUX_SPEC_OFFLINE'] = '1'
os.environ['VITALUX_LOCAL_PREVIEW'] = '1'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication
from vitalux import distro, settings, theme
from vitalux.logo import load_logo
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow, Sampler

app = QApplication([])
app.setQuitOnLastWindowClosed(False)


def wait(milliseconds=30):
    deadline = time.monotonic() + milliseconds / 1000
    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.005)


def bounds(widget):
    return QRect(widget.mapTo(window, QPoint()), widget.size())


def check_frame():
    image = window.grab().toImage()
    for x, y in ((0, 0), (image.width()-1, 0),
                 (0, image.height()-1), (image.width()-1, image.height()-1)):
        assert image.pixelColor(x, y).alpha() == (255 if window.isMaximized() else 0)
    bar = bounds(window.window_frame.titlebar)
    assert bar.top() == 0
    assert bounds(window.content_host).top() < bar.bottom()
    if not window.collapse_button.isHidden():assert bounds(window.collapse_button).top() > bar.bottom()
    if window._sidebar_collapsed and not window.collapse_button.isHidden():
        assert not bounds(window.collapse_button).intersects(bounds(window.nav_buttons[0]))
    for button in window.window_frame.buttons.values():
        assert not button.isHidden() and bar.contains(bounds(button))


evidence = Path(os.environ['VITALUX_NAV_EVIDENCE']) if os.environ.get('VITALUX_NAV_EVIDENCE') else None
if evidence:
    evidence.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as folder, \
        patch.object(settings, 'PATH', str(Path(folder)/'settings.json')), \
        patch.object(Sampler, 'start', lambda self: None), \
        patch.object(MainWindow, '_start_background_smart', lambda self: None):
    settings.set_many(dict(theme='obsidian_gold', motion='full', component_images=False,
                           close_to_tray=False, sidebar_collapsed=False))
    theme.set_mode('obsidian_gold')
    app.setStyleSheet(theme.stylesheet())
    info = distro.info()
    window = MainWindow(info, load_logo(info, 96), UpdateManager())
    window._freshness_timer.stop()
    window.resize(1200, 840)
    window.show()
    wait(70)
    try:
        for design in [key for key, _ in theme.CHOICES] + ['eclipse_crystal', 'minimal']:
            print('Checking framed navigation:',design,flush=True)
            settings.set_many(dict(theme='obsidian_gold' if design == 'minimal' else design,
                                   ultra_eco=design == 'minimal'))
            window.apply_appearance()
            appearance = window._appearance_overlay
            if appearance is not None:
                appearance.animation.pause()
                for position in (0., .5, 1.):
                    appearance._frame(position)
                    check_frame()
                appearance.finish()
            wait(30)
            check_frame()
            window._switch_page(9)
            preferences=window.pages[9][1]
            preferences.search_overlay.open_search()
            wait(50)
            header=window.design_shell.header
            header_bottom=bounds(header).bottom() if not header.isHidden() else bounds(window.window_frame.titlebar).bottom()
            assert bounds(preferences.search_overlay).top()>header_bottom
            preferences.search_overlay.close_search()
            wait(100)
            window._switch_page(0)
            wait(30)
            page = window.pages[0][1]
            layout_button = window.window_frame.layout_button
            controls = [layout_button] + list(window.window_frame.buttons.values())
            assert page.layout_toggle is layout_button and not layout_button.isHidden()
            for first, second in zip(controls, controls[1:]):
                a, b = bounds(first), bounds(second)
                assert a.size() == b.size() and a.top() == b.top()
                assert b.left()-a.right()-1 == 2
            assert page.root.contentsMargins().top() == page._frame_top_margin
            assert page.root.contentsMargins().left() == page.root.contentsMargins().right() == 16
            page.board.refresh_geometry(animate=False)
            before_tiles = {key:tile.geometry() for key,tile in page.board.tiles.items()}
            layout_button.click()
            wait(300)
            assert page.board.editing and layout_button.isChecked()
            assert page.layout_actions.parentWidget() is window.window_frame.titlebar
            assert bounds(window.window_frame.titlebar).contains(bounds(page.layout_actions))
            assert {key:tile.geometry() for key,tile in page.board.tiles.items()} == before_tiles
            layout_button.click()
            wait(300)
            assert not page.board.editing and not layout_button.isChecked()
            for width in (420, 630, 920):
                page.board.resize(width, page.board.height())
                page.board.refresh_geometry(animate=False)
                frames = [page.board._frame(rect) for rect in page.board._last_targets.values()]
                assert max(rect.right()+1 for rect in frames) == width
                assert min(rect.left() for rect in frames) == 0
                assert all(0 <= rect.left() <= rect.right() < width for rect in frames)
            window.resize(1202,842)
            wait(40)
            window.resize(1200,840)
            wait(40)
            window.stack.currentWidget().verticalScrollBar().setValue(0)
            wait(30)
            initial = window.grab().toImage()
            buttons = [bounds(button) for button in controls]
            bar = window.window_frame.titlebar
            point = bar.rect().center()
            wheel = QWheelEvent(QPointF(point),QPointF(bar.mapToGlobal(point)),QPoint(),QPoint(0,-120),
                                Qt.NoButton,Qt.NoModifier,Qt.ScrollUpdate,False)
            QApplication.sendEvent(bar,wheel)
            wait(400)
            assert window.stack.currentWidget().verticalScrollBar().value() > 0
            assert [bounds(button) for button in controls] == buttons
            scroll = window.stack.currentWidget()
            scroll._cancel_scroll()
            scroll.verticalScrollBar().setValue(min(scroll.verticalScrollBar().maximum(),bounds(page.board.tiles['hero']).top()+scroll.verticalScrollBar().value()+20))
            wait(30)
            peek = QRect(bounds(window.stack).left()+30,12,80,14)
            dpr=initial.devicePixelRatio()
            peek=QRect(round(peek.x()*dpr),round(peek.y()*dpr),round(peek.width()*dpr),round(peek.height()*dpr))
            if evidence:window.grab().save(str(evidence/(design+'-scroll-under-frame.png')))
            assert initial.copy(peek) != window.grab().toImage().copy(peek), design
            window.stack.currentWidget().verticalScrollBar().setValue(0)
            wait(30)
            if window.collapse_button.isHidden():
                # Authored header/dock navigation keeps its own layout and has no
                # hidden sidebar state changed by an accidental direct invocation.
                saved = window._sidebar_collapsed
                window.toggle_sidebar()
                assert window._sidebar_collapsed == saved
                assert window._sidebar_overlay is None
                continue
            for _ in range(2):
                # Exercise overview tiles and ordinary tab contents in both directions.
                for index in (0, 9):
                    window._switch_page(index)
                    wait(20)
                    clean_top=None
                    if index==0 and _==0 and window.devicePixelRatioF()==1:
                        bar=window.window_frame.titlebar
                        bar.hide()
                        scene=window.centralWidget()
                        area=QRect(window.content_host.mapTo(scene,QPoint()),window.content_host.size())
                        clean_top=scene.grab(area).toImage()
                        bar.show();bar.raise_()
                    window.toggle_sidebar()
                    animation = window._sidebar_motion
                    overlay = window._sidebar_overlay
                    if animation is None:
                        assert design == 'minimal', (design,index,window.sidebar.width(),window._sidebar_collapsed,window.collapse_button.isHidden())
                        check_frame()
                        continue
                    animation.pause()
                    if clean_top is not None:
                        cache=overlay._before_content.toImage()
                        band=window.window_frame.titlebar.height()-bounds(window.content_host).top()
                        assert cache.copy(0,0,cache.width(),band)==clean_top.copy(overlay.old_width,0,cache.width(),band), 'Window controls were captured into moving content'
                    expected = bounds(window.content_host)
                    if evidence:
                        window.grab().save(str(evidence/(design+'-moving.png')))
                    assert bounds(overlay) == expected, (design, bounds(overlay), expected)
                    old_bar = window.window_frame.titlebar.grab().toImage()
                    for position in (0., .5, 1.):
                        overlay.set_progress(position)
                        check_frame()
                        assert window.window_frame.titlebar.grab().toImage() == old_bar
                        if evidence and position==.5:window.grab().save(str(evidence/(design+'-mid-transition.png')))
                    window._sidebar_finish()
                    wait(20)
                    assert window.collapse_button.isEnabled()
                    assert window.sidebar.width() == (74 if window._sidebar_collapsed else 250)
                    assert bounds(window.sidebar).right() < bounds(window.stack).left()
            if evidence:
                window.grab().save(str(evidence/(design+'-settled.png')))
        # A theme change interrupts an in-flight sidebar transition before reparenting
        # navigation; resizing/maximizing also discards its obsolete cached geometry.
        settings.set_many(dict(theme='obsidian_gold', ultra_eco=False))
        window.apply_appearance()
        if window._appearance_overlay is not None:
            window._appearance_overlay.finish()
        window.toggle_sidebar()
        assert window._sidebar_motion is not None
        settings.set('theme', 'nebula_prism')
        window.apply_appearance()
        assert window._sidebar_motion is None and window.collapse_button.isHidden()
        if window._appearance_overlay is not None:
            window._appearance_overlay.finish()
        settings.set('theme', 'glass')
        window.apply_appearance()
        if window._appearance_overlay is not None:
            window._appearance_overlay.finish()
        window.toggle_sidebar()
        assert window._sidebar_motion is not None
        window.resize(1280, 900)
        wait(30)
        assert window._sidebar_overlay is None
        window.window_frame.buttons['maximize'].click()
        wait(30)
        check_frame()
        window.toggle_sidebar()
        window._sidebar_finish()
        wait(30)
        check_frame()
        window.toggle_sidebar()
        window._sidebar_finish()
        wait(30)
        window.window_frame.buttons['maximize'].click()
        wait(30)
        check_frame()
        window.resize(800,560)
        window._switch_page(0)
        window.window_frame.layout_button.click()
        wait(300)
        assert bounds(window.window_frame.titlebar).contains(bounds(window.pages[0][1].layout_actions))
        assert bounds(window.window_frame.titlebar).contains(bounds(window.window_frame.layout_button))
        window.pages[0][1].discard_edit()
        check_frame()
    finally:
        window.close()
        wait(80)
print('All eight framed layouts, repeated sidebar glides, themed blends, interrupted transitions and resize PASS')
