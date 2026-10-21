"""Merged skins preserve visible palettes/backgrounds and isolate Stable profiles."""
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
from vitalux import appearance,profiles,theme,premium,brand,wallpaper_accents
app=QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory(prefix='vitalux-appearance-migration-') as folder,patch.dict(os.environ,{f'XDG_{kind.upper()}_HOME':str(Path(folder)/kind) for kind in profiles.KINDS}):
    stable=profiles.directory('config','stable')/'settings.json'
    profiles.atomic_json(stable,dict(theme='glass',lang='de'))
    stable_bytes=stable.read_bytes()
    target=profiles.directory('config')/'settings.json'
    for source in ('obsidian_gold','champagne_glass','aurora_gold','liquid_silver','liquid_chrome','black_glass_gold','black_glass'):
        before=dict(theme=source,accent='#f472b6',background_style='prism',dashboard_hidden=['gpu'],custom_accents=[dict(name='Pink',color='#d6498e')])
        profiles.atomic_json(target,before);profiles.initialize();after=profiles.read(target)
        assert after['theme']==appearance.canonical(source)
        if source!='black_glass':
            origin='liquid_silver' if source=='liquid_chrome' else source
            expected=premium.COLLECTIONS[origin]['accent'] if origin in premium.COLLECTIONS else '#f3cd79'
            assert after['accent']==expected and after['background_style']==origin
            assert after['accent_before_design_migration']=='#f472b6'
            assert after['background_before_design_migration']=='prism'
        else:assert after['accent']=='#f472b6' and after['background_style']=='prism'
        assert after['dashboard_hidden']==['gpu'] and after['custom_accents']==before['custom_accents']
        assert stable.read_bytes()==stable_bytes
        raw=target.read_bytes();profiles.initialize();assert target.read_bytes()==raw
        backups=list((profiles.root('config')/'profile-backups/unstable').glob('*/settings.json'))
        assert any(profiles.read(p).get('theme')==source and '_appearance_revision' not in profiles.read(p) for p in backups)
        changed=dict(after,accent='#123456',background_style='deep_ocean')
        profiles.atomic_json(target,changed);profiles.initialize()
        assert profiles.read(target)['accent']=='#123456' and profiles.read(target)['background_style']=='deep_ocean'
    assert appearance.migrate(dict(theme='black_glass'))['background_style']=='black_glass'
    for source in appearance.MERGED:
        theme.set_mode(source);assert theme.mode()==appearance.canonical(source)
    profiles.reset_preferences(target);profiles.initialize()
    assert profiles.read(target).get('accent','design_default')=='design_default'
    assert profiles.read(target).get('theme','obsidian_gold')=='obsidian_gold'
    assert stable.read_bytes()==stable_bytes

# The renamed default keeps the original material roles and authored identity.
theme.set_mode('obsidian_gold');theme.set_accent(wallpaper_accents.resolve_accent('design_default'))
assert theme.accent()=='#e5c17b' and premium.palette()==premium.COLLECTIONS['obsidian_gold']
assert brand._brand_asset(True).endswith('pulse-obsidian-gold.svg')
assert dict(theme.CHOICES)['obsidian_gold']=='Obsidian'
assert dict(theme.CHOICES)['black_glass_gold']=='Black Glass'
for title,color in appearance.ACCENTS:
    for key,_ in theme.CHOICES:
        theme.set_mode(key);theme.set_accent(color)
        assert QColor(theme.accent()).isValid()
        assert not brand.themed_icon_pixmap(80).isNull()
        assert not brand.wordmark_pixmap(200,44).isNull()
print('All merged skin migrations, backups, idempotence, original Obsidian Gold default and all-design preset SVG colors PASS')
