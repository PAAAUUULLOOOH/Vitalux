"""Live design-shell changes, fixed controls, palette assets and small windows."""
import os,sys,tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer,QCoreApplication,QEvent
from PySide6.QtWidgets import QApplication
from vitalux import distro,settings,theme
from vitalux.brand import _brand_asset
from vitalux.logo import load_logo
from vitalux.update_manager import UpdateManager
from vitalux.window import MainWindow


def run():
    app=QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    previous=settings.PATH
    errors=[]
    with tempfile.TemporaryDirectory() as folder:
        settings.PATH=str(Path(folder)/'settings.json')
        settings.set_many(dict(theme='obsidian_gold',accent='#f472b6',close_to_tray=False,
            guide_intro_choice='completed'))
        theme.set_mode('obsidian_gold');app.setStyleSheet(theme.stylesheet())
        info=distro.info();window=MainWindow(info,load_logo(info,96),UpdateManager())
        window.resize(1380,1000);window.show()
        sampler=window.sampler
        preferences=dict(window.pages)['Einstellungen']
        network=dict(window.pages)['Netzwerk']
        assert network.watcher.worker is None,'Network scanning started before opening its tab'
        def verify():
            try:
                assert window.last_sample is not None
                for mode in ('nebula_prism','eclipse_crystal','quantum_core','glass','crystal_atrium','obsidian_gold'):
                    window.pulse_core._phase=73
                    if mode=='eclipse_crystal':preferences.search.setText('timbooh')
                    else:preferences.select_design(mode)
                    app.processEvents()
                    assert window.sampler is sampler and sampler.isRunning()
                    assert window.pulse_core._phase>=73,'Design change reset rotation phase'
                    assert not preferences.accent_combo.isLocked() and not preferences.background_combo.isLocked()
                    signature=mode in ('nebula_prism','eclipse_crystal','quantum_core','crystal_atrium')
                    assert window.pages[0][1].design_metric_hosts['cpu'].currentIndex()==int(signature)
                    assert window.sidebar.isHidden()==(mode in ('eclipse_crystal','nebula_prism'))
                    assert not window.grab().isNull()
                preferences.search.setText('timbooh')
                window.resize(800,560);app.processEvents()
                assert window.width()==800 and window.height()==560
                assert window.design_shell.primary_scroll.horizontalScrollBar().maximum()>0
                window.nav_buttons[7].click();app.processEvents()
                assert window.stack.currentIndex()==7
                window.set_language('en');app.processEvents()
                assert window.nav_buttons[9].text().endswith('Settings')
                window.set_language('de');app.processEvents()
                assert window.nav_buttons[9].text().endswith('Einstellungen')
                assert not window.grab().isNull()
            except BaseException as exc:errors.append(exc)
            finally:window.quit_from_tray()
        QTimer.singleShot(1800,verify)
        app.exec()
        window.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
        app.processEvents();settings.PATH=previous
    if errors:raise errors[0]
    print('Signature layouts, fixed fields, preserved sampling/phase, DE/EN and 800px navigation PASS')

if __name__=='__main__':run()
