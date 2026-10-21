"""Real UI: independently combine every background, accent and retained surface."""
import os,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor
from vitalux import distro,settings,theme,backdrops,premium,appearance,eco
from vitalux.logo import load_logo
from vitalux.glass import AmbientScene
from vitalux.window import MainWindow
from vitalux.update_manager import UpdateManager
app=QApplication.instance() or QApplication([]);app.setQuitOnLastWindowClosed(False)
def wait(ms):
    end=time.monotonic()+ms/1000
    while time.monotonic()<end:app.processEvents();time.sleep(.01)

with tempfile.TemporaryDirectory() as d,patch.object(settings,'PATH',str(Path(d)/'settings.json')):
    settings.set_many(dict(theme='obsidian_gold',accent='design_default',background_style='theme_default',motion='off',close_to_tray=False,ui_sounds=False))
    theme.set_mode('obsidian_gold');theme.set_accent(theme.default_accent())
    info=distro.info();manager=UpdateManager();manager._timer.stop()
    win=MainWindow(info,load_logo(info,96),manager);win.resize(1380,1000);win.show();wait(1300)
    try:
        page=dict(win.pages)['Einstellungen'];sampler=win.sampler
        assert len(page.design_tiles)==len(theme.CHOICES)==9
        assert not {'black_glass','champagne_glass','aurora_gold','liquid_silver'} & {tile.key for tile in page.design_tiles}
        assert not page.accent_combo.isVisible() and not page.background_combo.isVisible()
        assert len(page.background_tiles)==len(backdrops.PRESETS)+1
        assert all(page.accent_combo.findData(color)>=0 for _,color in appearance.ACCENTS)
        page.select_background('aurora_gold');page.change_accent('#b9ccdc');wait(30)
        gold_geometry=(win.sidebar.width(),win.pulse_core.size(),win.pages[0][1].board._render_positions())
        for mode,_ in theme.CHOICES:
            page.select_design(mode);wait(30)
            assert theme.mode()==mode
            assert settings.get('background_style')=='aurora_gold' and settings.get('accent')=='#b9ccdc'
            assert not page.background_combo.isLocked() and not page.accent_combo.isLocked()
            assert page.custom_accent_button.isEnabled() and all(tile.isEnabled() for tile in page.background_tiles)
            assert win.sampler is sampler and sampler.isRunning()
            assert sum(t.isChecked() for t in page.design_tiles)==1
            page.change_accent('#ecc784');page.change_accent('#b9ccdc')
            assert settings.get('accent')=='#b9ccdc'
        page.select_design('obsidian_gold');wait(30)
        assert gold_geometry==(win.sidebar.width(),win.pulse_core.size(),win.pages[0][1].board._render_positions())
        settings.set('motion','smooth')
        page.change_accent('#ecc784');overlay=win._appearance_overlay
        assert overlay is not None
        page.change_accent('#ecc784');assert win._appearance_overlay is overlay
        page.select_design('obsidian_gold');assert win._appearance_overlay is overlay
        settings.set('motion','off');win.apply_appearance();assert win._appearance_overlay is None
        page.change_accent('#b9ccdc')
        scene=AmbientScene();scene.resize(320,220)
        for mode,_ in theme.CHOICES:
            theme.set_mode(mode);theme.set_accent('#b9ccdc')
            for style in backdrops.KEYS:
                settings.set('background_style',style);scene.sync_background()
                assert backdrops.resolve(style,mode)==(mode if style=='theme_default' else style)
                if mode=='minimal' and backdrops.resolve(style,mode)=='minimal':
                    assert scene.sharp_backdrop().isNull()
                else:
                    assert scene.sharp_backdrop().size()==QSize(320,220),(mode,style)
                    assert not scene.soft_backdrop().isNull(),(mode,style)
        personal=Path(d)/'backgrounds';personal.mkdir()
        image=QImage(50,40,QImage.Format_RGB32);image.fill(QColor('#17609b'))
        assert image.save(str(personal/'owned.png'))
        settings.set_many(dict(custom_background_selected='owned.png',custom_backgrounds=[dict(name='Own image',file='owned.png')],background_style='custom_image'))
        for mode,_ in theme.CHOICES:
            theme.set_mode(mode);scene.sync_background()
            assert scene.sharp_backdrop().toImage().pixelColor(160,110).name()=='#17609b',mode
        scene.close();page.select_design('obsidian_gold')
        page.select_background('champagne_glass');before=win.centralWidget().sharp_backdrop().toImage()
        page.set_background_tint('#276caf');after=win.centralWidget().sharp_backdrop().toImage()
        assert before!=after
        assert settings.get('accent')=='#b9ccdc'
        page.background_tint_clear.click();assert win.centralWidget().sharp_backdrop().toImage()==before
        page.reset_category('appearance');wait(50)
        assert theme.mode()=='obsidian_gold' and theme.accent()=='#e5c17b'
        assert settings.get('background_style')=='theme_default' and settings.get('background_tint')==''
        assert win.centralWidget().sharp_backdrop().toImage()==premium.scene_pixmap(win.centralWidget().size(),'obsidian_gold').toImage()
        assert not page._reset_reveals['appearance'].revealed
        for width in (1380,1000,800):
            win.resize(width,700);wait(40)
            index=next(i for i,(name,_) in enumerate(win.pages) if name=='Einstellungen')
            win.nav_buttons[index].click();wait(20)
            scroll=win.stack.currentWidget()
            assert page.width()<=scroll.viewport().width()+2,(width,page.width(),scroll.viewport().width())
            assert all(t.mapTo(page,t.rect().topRight()).x()<=page.width()+2 for t in page.background_tiles+page.accent_tiles)
    finally:
        win.quit_from_tray();wait(500);assert win.isHidden()
print('Nine retained surfaces, all shared backgrounds, all accents, independent tint, exact original default and responsive gallery PASS')
