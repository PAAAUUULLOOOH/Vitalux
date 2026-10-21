"""Channel browsing, restart latches, offline notes and promotion notices."""
import os,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from vitalux import profiles,i18n,updater
from vitalux import update_manager as module
from vitalux.pages_extra import UpdatePage

app=QApplication.instance() or QApplication([])


def record(channel,version,newer=False,eligible=True):
    return dict(ok=True,latest=version,notes='## Deutsch\n- Aktueller Stand\n## English\n- Current changes',
                channel=channel,newer=newer,eligible=eligible,stable_version='0.9.6.0',same_as_stable=not eligible,
                url=f'https://github.com/{updater.DEFAULT_REPO}/releases/download/test/package.zip' if newer else '',
                sha256='a'*64 if newer else '')


with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{f'XDG_{k.upper()}_HOME':str(Path(folder)/k) for k in profiles.KINDS}),patch.object(profiles,'__version__','0.9.6.0'),patch.object(module,'__version__','0.9.6.0'):
    profiles.select('unstable')  # An old saved destination must not change the installed channel.
    m=module.UpdateManager();m._timer.stop()
    assert m.channel=='stable'
    m._on_checked({'stable':record('stable','0.9.6.0'), 'unstable':record('unstable','0.9.6.1-unstable.2',False,False)})
    page=UpdatePage(m);page.resize(1100,900);page.show();app.processEvents()
    assert page.changelog_card.isHidden()
    assert not hasattr(page,'fresh_profile')
    page.channel_buttons['unstable'].click();app.processEvents()
    assert page.changelog_card.isVisible() and 'Aktueller Stand' in page.changelog_details.text()
    assert not page.install_button.isEnabled() and not m.available
    assert profiles.selected()=='unstable','Browsing rewrote the saved installation channel'
    page.channel_buttons['stable'].click();app.processEvents()
    assert page.changelog_card.isVisible() and not m.can_install and not m.available
    i18n.set_lang('en');page.retranslate()
    assert 'Current changes' in page.changelog_details.text() and 'Aktueller Stand' not in page.changelog_details.text()
    i18n.set_lang('de');page.retranslate()
    # A real newer test enables only the explicit switch, never a Stable notification.
    m._on_checked({'stable':record('stable','0.9.6.0'),'unstable':record('unstable','0.9.6.1-unstable.3',True,True)})
    page.channel_buttons['unstable'].click();app.processEvents()
    assert m.can_install and not m.available and m.status=='switch_available'
    assert page.install_button.isEnabled()
    # The install snapshot is immutable while the user browses other notes.
    events=[];m.restart.connect(lambda:events.append('restart'))
    worker=SimpleNamespace(channel='unstable',version='0.9.6.1-unstable.3',pending_path=None,sha256='a'*64)
    m._on_installed('',worker);assert m.pending_restart and not m.available
    QTest.qWait(1000);assert not events,'Restart happened without the user choosing it'
    page.channel_buttons['stable'].click();app.processEvents()
    assert m.status=='installed' and not m.available and not m.can_install
    assert m.pending['channel']=='unstable' and '0.9.6.1' in page.latest.v.text()
    before=dict(m.pending);m.check();assert m._thread is None
    m._on_checked({'stable':record('stable','0.9.6.2',True)});assert m.pending==before and not m.available
    m.defer_restart();assert m.restart_deferred
    assert not page.later_button.isVisible() and page.restart_button.isVisible()
    m._restart();assert events==['restart']
    pending_file=m._pending_file
    again=module.UpdateManager();again._timer.stop();assert again.pending_restart and not again.available
    again.shutdown()
    with patch.object(module,'__version__','0.9.6.1-unstable.3'),patch.object(profiles,'__version__','0.9.6.1-unstable.3'):
        restarted=module.UpdateManager();assert not restarted.pending_restart and not pending_file.exists();restarted.shutdown()
    m.pending_restart=False;m.pending={};m.status='idle';page.close();m.shutdown()
    # Cached information survives restart, but cannot authorize an offline install.
    cached=module.UpdateManager();cached._timer.stop();cached.set_channel('unstable')
    assert 'Aktueller Stand' in cached.notes and not cached.can_install and not cached.available
    checked=cached.last_checked
    cached._on_checked({'error':'Offline'})
    assert cached.status=='error' and cached.last_checked==checked and 'Aktueller Stand' in cached.notes
    cached.shutdown()
    # AppImages prepared with Later are activated on Exit, without reopening.
    image=Path(folder)/'staged.AppImage';image.write_bytes(b'candidate')
    m=module.UpdateManager();m._timer.stop()
    m._on_installed('',SimpleNamespace(channel='unstable',version='0.9.6.1-unstable.4',pending_path=str(image),sha256='a'*64))
    with patch.object(updater,'activate_appimage_update') as activate:
        m.defer_restart();assert not activate.called
        m.finalize_exit();activate.assert_called_once_with(str(image),relaunch=False)
        m.finalize_exit();assert activate.call_count==1
    m._pending_file.unlink(missing_ok=True);m.shutdown()
    # Stable's adoption message appears only after the tested version is caught up.
    with patch.object(profiles,'__version__','0.9.6.1-unstable.3'),patch.object(module,'__version__','0.9.6.1-unstable.3'):
        m=module.UpdateManager();m._timer.stop()
        m._on_checked({'stable':record('stable','0.9.6.1',True),'unstable':record('unstable','0.9.6.1-unstable.3',False,False)})
        assert m.stable_has_test_changes and not m.available
        m.set_channel('stable');assert m.can_install and not m.available
        m._on_checked({'stable':record('stable','0.9.6.1',True),'unstable':record('unstable','0.9.6.2-unstable.1',True,True)})
        assert not m.stable_has_test_changes and m.available and m.notification_version=='0.9.6.2-unstable.1'
        m.shutdown()
print('Channel views, gated switching, explicit restart, pending snapshot, offline notes and Stable promotion PASS')
