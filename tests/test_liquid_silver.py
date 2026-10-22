"""Obsidian geometry in silver, fixed capabilities and safe removed-skin migration."""
import os,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtGui import QColor,QPalette
from PySide6.QtWidgets import QApplication
from vitalux import distro,settings,theme,brand,design_capabilities,profiles
from vitalux.logo import load_logo
from vitalux.window import MainWindow
from vitalux.update_manager import UpdateManager

app=QApplication.instance() or QApplication([]);app.setQuitOnLastWindowClosed(False)
def wait(ms):
    deadline=time.monotonic()+ms/1000
    while time.monotonic()<deadline:app.processEvents();time.sleep(.01)

with tempfile.TemporaryDirectory(prefix='vitalux-silver-') as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
    settings.set_many(dict(theme='obsidian_gold',accent='#f472b6',background_style='prism',close_to_tray=False,motion='off'))
    theme.set_mode('obsidian_gold');app.setStyleSheet(theme.stylesheet())
    info=distro.info();manager=UpdateManager();manager._timer.stop()
    win=MainWindow(info,load_logo(info,96),manager);win.resize(1380,1000);win.show();wait(300)
    try:
        overview=win.pages[0][1];page=dict(win.pages)['Einstellungen']
        geometry=(win.sidebar.width(),win.pulse_core.size(),overview.board._render_positions(),overview.graph_load.graph.minimumHeight())
        sampler=win.sampler
        page.select_design('liquid_silver');wait(300)
        assert not theme.is_light() and QColor(theme.BG).lightness()<30
        contrast=(theme._luminance(QColor(theme.TEXT))+.05)/(theme._luminance(QColor(theme.CARD))+.05)
        assert contrast>10,contrast
        assert geometry==(win.sidebar.width(),win.pulse_core.size(),overview.board._render_positions(),overview.graph_load.graph.minimumHeight())
        assert all(host.currentIndex()==0 for host in overview.design_metric_hosts.values())
        assert win.sampler is sampler and sampler.isRunning()
        assert len(theme.CHOICES)==12 and 'liquid_chrome' not in dict(theme.CHOICES)
        assert 'liquid-silver.svg' in brand._brand_asset(False)
        assert b'#718ba2' in brand._themed_svg(True)
        assert not any(design_capabilities.capabilities('liquid_silver').values())
        assert not page.custom_accent_button.isEnabled()
        assert page.custom_accent_button.palette().color(QPalette.Disabled,QPalette.ButtonText).name()=='#9299a3'
        assert page.background_combo.isLocked() and page.accent_combo.isLocked()
        settings.set('motion','smooth');win.apply_appearance();wait(350)
        assert win.pulse_core._timer.isActive() and win.brand_mark._timer.isActive()
        page.select_design('glass');wait(350)
        assert settings.get('accent')=='#f472b6' and settings.get('background_style')=='prism'
    finally:
        win.quit_from_tray();wait(400);assert win.isHidden()

with tempfile.TemporaryDirectory(prefix='vitalux-skin-migration-') as folder,patch.dict(os.environ,{f'XDG_{kind.upper()}_HOME':str(Path(folder)/kind) for kind in profiles.KINDS}):
    stable=profiles.directory('config','stable')/'settings.json'
    profiles.atomic_json(stable,dict(theme='glass',lang='de'))
    stable_bytes=stable.read_bytes()
    target=profiles.directory('config')/'settings.json'
    before=dict(theme='liquid_chrome',accent='#f472b6',background_style='prism',dashboard_hidden=['gpu'])
    profiles.atomic_json(target,before)
    profiles.initialize()
    after=profiles.read(target)
    assert after['theme']=='liquid_silver'
    assert all(after[k]==v for k,v in before.items() if k!='theme')
    assert stable.read_bytes()==stable_bytes
    backups=list((profiles.root('config')/'profile-backups/unstable').glob('*/settings.json'))
    assert any(profiles.read(p).get('theme')=='liquid_chrome' for p in backups)
    theme.set_mode('liquid_chrome');assert theme.mode()=='liquid_silver'
print('Obsidian geometry, dark silver contrast/branding, fixed options, live animation and isolated backed-up skin migration PASS')
