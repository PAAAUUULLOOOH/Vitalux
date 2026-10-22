"""Recover separate designs from the temporary combined-appearance profiles."""
from PySide6.QtGui import QColor


def _manual_accent(value):
    if value == 'auto' or isinstance(value, str) and QColor(value).isValid():
        return value
    return '#4f8cff'


def migrate(data):
    """Restore standalone choices once, retaining a snapshot and personal data."""
    result = dict(data)
    if result.get('theme') == 'liquid_chrome':
        result['theme'] = 'liquid_silver'
    if result.get('_appearance_revision') != 1:
        return result

    from .backdrops import KEYS
    from .design_capabilities import FIXED
    from .premium import COLLECTIONS

    result['appearance_before_design_restore'] = {
        key: result[key] for key in (
            'theme', 'accent', 'background_style', 'background_tint',
            'accent_before_design_migration', 'background_before_design_migration',
            'accent_before_wallpaper_auto') if key in result}
    selected = result.get('theme', 'obsidian_gold')
    background = result.get('background_style', 'theme_default')
    accent = result.get('accent', '#4f8cff')
    if not isinstance(selected, str):
        selected = 'obsidian_gold'
    if not isinstance(background, str):
        background = 'theme_default'
    # Old fixed collections were stored as Obsidian plus their native pair.
    variants = ('obsidian_gold', 'champagne_glass', 'aurora_gold', 'liquid_silver')
    if (selected == 'obsidian_gold' and background in variants
            and accent == COLLECTIONS[background]['accent']):
        selected = background
    # The former editable Black Glass retained its original backdrop and hue.
    if (selected == 'black_glass_gold' and accent not in ('#f3cd79', 'design_default')
            and 'accent_before_design_migration' not in result):
        selected = 'black_glass'
    result['theme'] = selected
    if selected in FIXED:
        accent = result.get('accent_before_design_migration', accent)
        background = result.get('background_before_design_migration', 'theme_default')
    if not isinstance(background, str):
        background = 'theme_default'
    result['accent'] = _manual_accent(accent) if accent != 'wallpaper_auto' else accent
    result['background_style'] = background if background in (*KEYS, 'custom_image') else 'theme_default'
    if result.get('accent_before_wallpaper_auto') == 'design_default':
        result['accent_before_wallpaper_auto'] = '#4f8cff'
    for key in ('background_tint', 'accent_before_design_migration', 'background_before_design_migration'):
        result.pop(key, None)
    result['_appearance_revision'] = 2
    return result
