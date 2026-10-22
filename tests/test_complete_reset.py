"""Complete profile reset: owned files only, channel isolation and write rollback."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vitalux import profiles

for channel in ('stable', 'unstable'):
    with tempfile.TemporaryDirectory(prefix='vitalux-full-reset-') as folder:
        base=Path(folder)
        env={f'XDG_{kind.upper()}_HOME':str(base/kind) for kind in profiles.KINDS}
        with patch.dict(os.environ,env),patch.object(profiles,'__version__',
                '0.9.6.2' if channel=='stable' else '0.9.6.3-unstable.8'):
            other='unstable' if channel=='stable' else 'stable'
            active=profiles.directory('config');path=active/'settings.json'
            original=base/'Pictures'/'original.png';original.parent.mkdir()
            original.write_bytes(b'original user photo')
            owned=active/'backgrounds';owned.mkdir(parents=True)
            (owned/'copy.png').write_bytes(original.read_bytes())
            (owned/'linked-original').symlink_to(original.parent,target_is_directory=True)
            before=dict(theme='aurora_gold',lang='de',render_backend='opengl',
                        custom_accents=[dict(name='Own',color='#123456')],
                        custom_backgrounds=[dict(name='Own',file='copy.png')],
                        dashboard_hidden=['cpu'],guide_intro_choice='completed')
            profiles.atomic_json(path,before)
            marker=active/'profile-state.json';profiles.atomic_json(marker,dict(initialized=True))
            cache=profiles.directory('cache');cache.mkdir(parents=True)
            (cache/'thumbnail.bin').write_bytes(b'cached image')
            other_config=profiles.directory('config',other)/'settings.json'
            profiles.atomic_json(other_config,dict(theme='glass',lang='en'))
            other_cache=profiles.directory('cache',other);other_cache.mkdir(parents=True,exist_ok=True)
            (other_cache/'keep.bin').write_bytes(b'other channel cache')
            other_saved=other_config.read_bytes()
            profiles.backup()
            profiles.backup(other)
            own_backups=profiles.root('config')/'profile-backups'/channel
            other_backups=profiles.root('config')/'profile-backups'/other
            other_backup_files={p:p.read_bytes() for p in other_backups.rglob('*') if p.is_file()}

            # Failure before defaults commit restores every quarantined item.
            with patch.object(profiles,'atomic_json',side_effect=OSError('write denied')):
                try:profiles.reset_preferences(path)
                except OSError:pass
                else:raise AssertionError('A failed reset was reported as successful')
            assert profiles.read(path)==before
            assert (owned/'copy.png').read_bytes()==original.read_bytes()
            assert (cache/'thumbnail.bin').read_bytes()==b'cached image'
            assert own_backups.exists()

            assert profiles.reset_preferences(path)
            assert not owned.exists() and not (cache/'thumbnail.bin').exists()
            assert not own_backups.exists()
            assert original.read_bytes()==b'original user photo'
            assert other_config.read_bytes()==other_saved
            assert (other_cache/'keep.bin').read_bytes()==b'other channel cache'
            assert all(p.read_bytes()==data for p,data in other_backup_files.items())
            assert profiles.read(path)=={'_schema_version':profiles.SCHEMA}
            assert profiles.read(marker)['initialized'] is True
            profiles.initialize()
            assert profiles.read(path)=={'_schema_version':profiles.SCHEMA}
            assert not list(active.glob('.vitalux-reset-*'))

assert profiles.validate(dict(theme='champagne_glass',ui_sounds=True,
    ui_sound_volume=80,_soft_click_revision=1))['theme']=='obsidian_gold'
assert not {'ui_sounds','ui_sound_volume','_soft_click_revision'} & profiles.validate(
    dict(ui_sounds=True,ui_sound_volume=80,_soft_click_revision=1)).keys()
print('Complete Stable/Unstable reset, original-image protection, symlinks, backup/cache removal and rollback PASS')
