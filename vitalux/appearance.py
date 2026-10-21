"""Appearance migration and authored accents, independent of surface geometry."""
from PySide6.QtGui import QColor

MERGED = {'champagne_glass': 'obsidian_gold', 'aurora_gold': 'obsidian_gold',
          'liquid_silver': 'obsidian_gold', 'liquid_chrome': 'obsidian_gold',
          'black_glass': 'black_glass_gold'}
ACCENTS = (('Obsidian Gold', '#e5c17b'), ('Champagne', '#f0d5ad'),
           ('Liquid Silver', '#b9ccdc'), ('Aurora Gold', '#ecc784'),
           ('Black Glass Gold', '#f3cd79'), ('Aether', '#b7a6ff'),
           ('Eclipse', '#efc68d'))


def canonical(key):
    return MERGED.get(key, key)


def migrate(data):
    """Preserve the effective old appearance once; never re-import on reset."""
    result = dict(data)
    tint = result.get('background_tint', '')
    if tint and (not isinstance(tint,str) or not QColor(tint).isValid()):
        result['background_tint']=''
    if result.get('_appearance_revision') == 1:
        return result
    from .premium import COLLECTIONS
    old = result.get('theme', 'obsidian_gold')
    if not isinstance(old,str):old='obsidian_gold'
    source = 'liquid_silver' if old == 'liquid_chrome' else old
    # Previously fixed styles ignored saved accent/background choices. Retain
    # those dormant choices separately while migrating the visible appearance.
    if data and (source in COLLECTIONS or old == 'black_glass_gold'):
        result['accent_before_design_migration'] = result.get('accent', '#4f8cff')
        result['background_before_design_migration'] = result.get('background_style', 'theme_default')
        result['accent'] = COLLECTIONS[source]['accent'] if source in COLLECTIONS else '#f3cd79'
        result['background_style'] = source
    if old=='black_glass' and result.get('background_style','theme_default')=='theme_default':
        result['background_style']='black_glass'
    if data:result['theme'] = canonical(old)
    result['_appearance_revision'] = 1
    return result


def authored(color):
    from .premium import COLLECTIONS
    return next((p for p in COLLECTIONS.values() if p['accent'] == color), None)
