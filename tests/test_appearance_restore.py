"""Restore real combined-profile fixtures without losing data or Stable settings."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vitalux import appearance, profiles, theme

# Values written by Unstable .5/.6 when importing the former fixed designs.
fixtures = (
    ('obsidian_gold', 'obsidian_gold', '#e5c17b'),
    ('obsidian_gold', 'obsidian_gold', '#e5c17b'),
    ('aurora_gold', 'obsidian_gold', '#ecc784'),
    ('liquid_silver', 'obsidian_gold', '#b9ccdc'),
    ('aether_glass', 'aether_glass', '#b7a6ff'),
    ('eclipse_crystal', 'eclipse_crystal', '#efc68d'),
    ('black_glass_gold', 'black_glass_gold', '#f3cd79'),
)
personal = dict(custom_accents=[dict(name='Personal', color='#f472b6')],
                custom_backgrounds=[dict(name='Personal', file='owned.png')],
                custom_background_selected='owned.png', dashboard_hidden=['gpu'],
                lang='de', render_backend='x11_opengl', network_app_limits={'Firefox': 100},
                interval=2)
for original, merged, color in fixtures:
    before = dict(personal, theme=merged, accent=color, background_style=original,
                  background_tint='#273c51', _appearance_revision=1,
                  accent_before_design_migration='#f472b6',
                  background_before_design_migration='custom_image')
    after = appearance.migrate(before)
    assert after['theme'] == original, (original, after)
    assert after['accent'] == '#f472b6' and after['background_style'] == 'custom_image'
    assert all(after[key] == value for key, value in personal.items())
    assert after['appearance_before_design_restore']['background_tint'] == '#273c51'
    assert 'background_tint' not in after
    assert appearance.migrate(after) == after
    assert before['_appearance_revision'] == 1

for background in ('black_glass', 'prism', 'custom_image'):
    after = appearance.migrate(dict(personal, _appearance_revision=1,
                              theme='black_glass_gold', accent='#f472b6', background_style=background))
    assert after['theme'] == 'black_glass'
    assert after['accent'] == '#f472b6' and after['background_style'] == background

for mode in ('dark', 'light', 'glass', 'holographic', 'minimal'):
    old = dict(personal, theme=mode, accent='#f472b6', background_style='prism')
    assert appearance.migrate(old) == old
    after = appearance.migrate(dict(old, _appearance_revision=1))
    assert all(after[key] == value for key, value in old.items())

fresh = appearance.migrate(dict(_appearance_revision=1, accent='design_default'))
assert fresh['theme'] == theme.DEFAULT_THEME == 'obsidian_gold'
assert fresh['accent'] == '#4f8cff'
auto = appearance.migrate(dict(personal, _appearance_revision=1, theme='glass',
                              accent='wallpaper_auto', accent_before_wallpaper_auto='design_default',
                              background_style='custom_image'))
assert auto['accent'] == 'wallpaper_auto' and auto['accent_before_wallpaper_auto'] == '#4f8cff'
assert appearance.migrate({}) == {}
assert appearance.migrate(dict(theme='liquid_chrome')) == dict(theme='liquid_silver')
malformed = appearance.migrate(dict(_appearance_revision=1, theme=[], background_style=[], accent=[]))
assert malformed['theme'] == theme.DEFAULT_THEME and malformed['accent'] == '#4f8cff'

with tempfile.TemporaryDirectory(prefix='vitalux-restored-designs-') as folder:
    env = {f'XDG_{kind.upper()}_HOME': str(Path(folder)/kind) for kind in profiles.KINDS}
    with patch.dict(os.environ, env):
        stable = profiles.directory('config', 'stable')/'settings.json'
        profiles.atomic_json(stable, dict(theme='glass', accent='#52d3ff'))
        stable_bytes = stable.read_bytes()
        active = profiles.directory('config', 'unstable')
        active.mkdir(parents=True)
        (active/'backgrounds').mkdir()
        owned = active/'backgrounds'/'owned.png'
        owned.write_bytes(b'personal image retained byte for byte')
        image_bytes = owned.read_bytes()
        before = dict(personal, _appearance_revision=1, theme='obsidian_gold',
                      accent='#b9ccdc', background_style='liquid_silver',
                      accent_before_design_migration='#f472b6',
                      background_before_design_migration='custom_image')
        target = active/'settings.json'
        profiles.atomic_json(target, before)
        profiles.initialize()
        assert profiles.read(target)['theme'] == 'liquid_silver'
        assert all(profiles.read(target)[key] == value for key, value in personal.items())
        saved = target.read_bytes()
        profiles.initialize()
        assert target.read_bytes() == saved
        assert stable.read_bytes() == stable_bytes and owned.read_bytes() == image_bytes
        backups = (profiles.root('config')/'profile-backups'/'unstable').glob('*/settings.json')
        assert any(profiles.read(path) == before for path in backups)
        profiles.reset_preferences(target)
        assert '_appearance_revision' not in profiles.read(target)
        assert not profiles.read(target).get('first_start_guide_seen')
        assert stable.read_bytes() == stable_bytes and not owned.exists()

print('Separate designs restored; .5/.6 migration, backups, personal data, reset and Stable isolation PASS')
