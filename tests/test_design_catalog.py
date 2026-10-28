"""Factory restoration, preserved retired presets and isolated design settings."""
import os,sys,tempfile,json,subprocess
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtCore import QSize
from vitalux import settings,theme,design_catalog as catalog,backdrops,appearance,wallpaper_accents
from vitalux.control import PreferencesPage
from vitalux.design_capabilities import capabilities
app=QApplication.instance() or QApplication([])
# Direct imports must not depend on importing theme first.
for module in ('crystal_atrium','aurora_bloom'):
    subprocess.run([sys.executable,'-B','-c',f'import vitalux.{module}'],check=True)
class Host(QWidget):
    render_backend_active='software';_tray=object()
    def apply_appearance(self, *, before=None):
        theme.set_mode(settings.get('theme','obsidian_gold'))
        theme.set_accent(wallpaper_accents.resolve_accent(settings.get('accent','design_default'),'#73ba25'))
        catalog.remember()
with tempfile.TemporaryDirectory() as folder,patch.object(settings,'PATH',str(Path(folder)/'settings.json')):
    assert tuple(dict(theme.CHOICES))==catalog.VISIBLE and len(theme.CHOICES)==6
    assert set(theme._THEMES)==set(catalog.AVAILABLE)
    for key in catalog.VISIBLE:assert all(capabilities(key).values())
    assert not any(capabilities('minimal').values())
    personal=dict(custom_accents=[dict(name='Own',color='#123456')],custom_backgrounds=[dict(name='Own',file='own.png')],dashboard_hidden=['gpu'],lang='en')
    for old,target in catalog.RETIRED.items():
        before=dict(personal,theme=old,accent='#ff00ff',background_style='theme_default',_crystal_design_revision=2)
        after=appearance.migrate(before)
        assert after['theme']==target and after['background_style']==('theme_default' if old=='crystal_glass' else old)
        assert all(after[k]==v for k,v in personal.items())
        assert appearance.migrate(after)==after
    assert catalog.migrate(dict(theme='crystal_glass'))['theme']=='crystal_atrium'
    for revision in (1,2):
        before=dict(theme='glass',accent='palette:crystal_atrium',_design_catalog_revision=revision,
                    design_settings={'glass':dict(accent='palette:crystal_atrium')})
        after=catalog.migrate(before)
        assert after['accent']=='palette:crystal_atrium_original'
        assert after['design_settings']['glass']['accent']=='palette:crystal_atrium_original'
        assert before['design_settings']['glass']['accent']=='palette:crystal_atrium'
    for revision in (1,2):
        for background in ('theme_default','custom_image','crystal_glass'):
            before=dict(personal,theme='crystal_glass',accent='#aabbcc',background_style=background,
                        custom_background_selected='own.png',_design_catalog_revision=revision,
                        design_settings={'crystal_glass':dict(accent='#123456',background_style=background)})
            after=catalog.migrate(before)
            assert after['theme']=='crystal_atrium' and after['accent']=='#aabbcc'
            assert after['background_style']==background and after['custom_background_selected']=='own.png'
            assert after['design_settings']['crystal_atrium']==before['design_settings']['crystal_glass']
            assert 'crystal_glass' not in after['design_settings'] and catalog.migrate(after)==after
    # The factory scene must use the actual original image, independently of accent or motion.
    original=backdrops._cover(QSize(180,120),catalog.ROOT/'assets/backgrounds/crystal_atrium.png').toImage()
    assert backdrops.render(QSize(180,120),'original:crystal_atrium')[0].toImage()==original
    assert backdrops.render(QSize(180,120),'original:crystal_atrium',phase=.9)[0].toImage()==original
    assert 'accent' not in catalog.migrate({})
    settings.set_many(dict(personal,theme='glass',accent='#123456',background_style='prism',motion='off',_design_catalog_revision=1))
    host=Host();host.apply_appearance();page=PreferencesPage(host)
    assert page.background_combo.itemText(page.background_combo.findData('theme_default')) in ('Originalhintergrund','Original background')
    for key,item in catalog.PRESETS.items():
        assert page.background_combo.findData(key)>=0
        assert page.accent_combo.findData('palette:'+key)>=0
        assert not backdrops.render(QSize(150,100),key)[0].isNull()
    page.select_design('obsidian_gold');assert settings.get('accent')=='design_default'
    page.change_accent('palette:crystal_glass');page.background_combo.setCurrentIndex(page.background_combo.findData('crystal_glass'))
    assert theme.mode()=='obsidian_gold' and settings.get('theme')=='obsidian_gold'
    custom=theme.palette_for('obsidian_gold');assert custom['card']==catalog.factory('obsidian_gold')['card']
    assert custom['accent']!=catalog.factory('obsidian_gold')['accent']
    page.select_design('glass');assert settings.get('accent')=='#123456' and settings.get('background_style')=='prism'
    page.select_design('obsidian_gold');assert settings.get('accent')=='palette:crystal_glass'
    page.reset_category('appearance');assert settings.get('theme')=='obsidian_gold'
    assert settings.get('accent')=='design_default' and settings.get('background_style')=='theme_default'
    assert all(settings.get(k)==v for k,v in personal.items())
    page.select_design('glass');assert settings.get('accent')=='#123456'
    for key in catalog.VISIBLE:
        page.select_design(key)
        original=backdrops.render(QSize(180,120),backdrops.resolve('theme_default',key))[0].toImage()
        page.change_accent('#f472b6')
        assert original==backdrops.render(QSize(180,120),backdrops.resolve('theme_default',key))[0].toImage(),key
        assert not page.accent_combo.isLocked() and not page.background_combo.isLocked()
    visible=[tile.key for tile in page.design_tiles]
    page.search_settings('bloo');assert theme.mode()!='aurora_bloom'
    page.search.setText('  BLOOM  ');app.processEvents()
    assert theme.mode()=='aurora_bloom' and settings.get('theme')=='aurora_bloom'
    assert page.search.text()=='' and [tile.key for tile in page.design_tiles]==visible
    assert 'aurora_bloom' not in dict(theme.CHOICES)
    assert page.background_combo.findData('aurora_bloom')<0
    assert page.accent_combo.findData('palette:aurora_bloom')<0
    assert not backdrops.render(QSize(640,480),'original:aurora_bloom')[0].isNull()
    settings._cache_identity=None;settings._cache_value=None
    theme.set_mode(settings.get('theme'));assert theme.mode()=='aurora_bloom'
    page.select_design('glass');page.search_settings('timbooh');assert theme.mode()=='eclipse_crystal'
    page.close();host.close()
print('Six designs, retired data-only presets, personal settings, independent factory background and per-design reset PASS')
