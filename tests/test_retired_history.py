"""Removed placeholder notes cannot return through files or cached catalogs."""
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QCoreApplication
from vitalux import changelog, profiles
from vitalux.update_manager import UpdateManager

app = QCoreApplication.instance() or QCoreApplication([])
retired = '0.9.6.1-unstable.2'
record = dict(ok=True, latest=retired, eligible=True, newer=True,
              notes='Placeholder', release_notes='Placeholder')
for language in ('de', 'en'):
    assert all(v != retired for v, _ in changelog.entries(lang=language))
    assert all(v != retired for v, _ in changelog.channel_history('unstable', record, lang=language))
with tempfile.TemporaryDirectory() as folder:
    folder = Path(folder)
    old = folder/'old-changelog.md'
    old.write_text('## [v0.9.6.3-unstable.1]\n- Genuine\n\n'
                   '## [v'+retired+']\n- Placeholder\n\n## [v0.9.6.1]\n- Stable\n')
    assert changelog.entries(old) == [('0.9.6.3-unstable.1', ['Genuine']), ('0.9.6.1', ['Stable'])]
    with patch.dict(os.environ, {'XDG_CACHE_HOME': str(folder/'cache'), 'XDG_STATE_HOME': str(folder/'state')}):
        profiles.atomic_json(profiles.directory('cache')/'release-catalog.json',
                             dict(records=dict(unstable=record)))
        manager = UpdateManager()
        assert 'unstable' not in manager.records
        manager._on_checked(dict(unstable=record))
        assert 'unstable' not in manager.records
        assert not manager.can_install
        manager.shutdown()
print('Placeholder removal, section boundaries, remote/cache rejection and DE/EN history PASS')
