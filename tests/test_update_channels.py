"""Channel downgrades, rolling manifests and independent profile migrations."""
import hashlib,io,json,os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux import profiles,versions,updater


def run():
    assert versions.key('0.9.6.0-unstable.9')<versions.key('0.9.6.0-unstable.10')<versions.key('0.9.6.0')
    assert versions.key('0.9.5.9')<versions.key('0.9.6.0-unstable.1')
    with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{f'XDG_{kind.upper()}_HOME':str(Path(folder)/kind) for kind in profiles.KINDS}):
        stable=profiles.directory('config','stable');stable.mkdir(parents=True)
        original={'ui_sound_volume':70,'lang':'de','theme':'glass','render_backend':'bad'}
        profiles.atomic_json(stable/'settings.json',original)
        (stable/'backgrounds').mkdir();(stable/'backgrounds/a.png').write_bytes(b'profile-owned resource')
        saved=(stable/'settings.json').read_bytes()
        with patch.object(profiles,'__version__','0.9.6.1-unstable.1'):
            profiles.initialize();target=profiles.directory('config')
            assert profiles.read(target/'settings.json')['ui_sound_volume']==50
            assert profiles.read(target/'settings.json')['render_backend']=='software'
            assert (target/'backgrounds/a.png').read_bytes()==(stable/'backgrounds/a.png').read_bytes()
            profiles.atomic_json(target/'settings.json',dict(profiles.read(target/'settings.json'),theme='light',ui_sound_volume=35))
            profiles.initialize();assert profiles.read(target/'settings.json')['ui_sound_volume']==35
            profiles.initialize();assert profiles.read(target/'settings.json')['ui_sound_volume']==35
            assert (stable/'settings.json').read_bytes()==saved
            assert profiles.read(target/'settings.json')['theme']=='light','Later launches overwrote the automatic test profile'
            assert all(profiles.directory(kind)!=profiles.directory(kind,'stable') for kind in profiles.KINDS)
            profiles.select('stable');assert profiles.selected()=='stable' and profiles.installed()=='unstable'
        assert (stable/'settings.json').read_bytes()==saved
        url=f'https://github.com/{updater.DEFAULT_REPO}/releases/download/v0.9.5.9/Vitalux-v0.9.5.9-linux-x86_64.zip'
        release={'tag_name':'v0.9.5.9','assets':[{'name':'Vitalux-v0.9.5.9-linux-x86_64.zip','browser_download_url':url,'digest':'sha256:'+'a'*64}]}
        with patch.object(updater,'__version__','0.9.6.1-unstable.1'),patch.object(updater,'_get_release',return_value=release):
            result=updater.check('stable');assert result['ok'] and result['newer'] and result['latest']=='0.9.5.9',result
        version='0.9.6.1-unstable.1';name=f'Vitalux-v{version}-linux-x86_64.zip'
        manifest=json.dumps(dict(schema=1,version=version,stable_version='0.9.6.0',has_test_changes=True,assets={name:{'sha256':'b'*64}})).encode()
        base=f'https://github.com/{updater.DEFAULT_REPO}/releases/download/unstable/'
        test_release={'tag_name':'unstable','prerelease':True,'assets':[
            dict(name='Vitalux-unstable-channel.json',browser_download_url=base+'Vitalux-unstable-channel.json',digest='sha256:'+hashlib.sha256(manifest).hexdigest()),
            dict(name=name,browser_download_url=base+name,digest='sha256:'+'b'*64)]}
        with patch.object(updater,'__version__','0.9.6.0'),patch.object(updater,'_get_release',return_value={'tag_name':'v0.9.6.0','body':'## Deutsch\nStable-Änderungen\n## English\nStable changes','assets':[]}),patch.object(updater,'_get_unstable_release',return_value=test_release),patch.object(updater,'_github_request',side_effect=lambda *a,**k:io.BytesIO(manifest)):
            result=updater.check('unstable');assert result['ok'] and result['newer'] and result['url']==base+name,result
            test_release['assets'][1]['digest']='sha256:'+'c'*64
            assert not updater.check('unstable')['ok'],'Accepted mismatched rolling test assets'
        # A rollback launched from the destination channel must restore the
        # source profile, without writing its preferences into the other one.
        root=Path(folder)/'application';(root/'vitalux').mkdir(parents=True)
        (root/'vitalux/__main__.py').write_text('original application')
        stable_settings=stable/'settings.json'
        test_settings=profiles.directory('config','unstable')/'settings.json'
        test_saved=test_settings.read_bytes()
        with patch.object(profiles,'__version__','0.9.6.0'),patch.object(updater.settings,'PATH',str(stable_settings)):
            updater._stage_backup(str(root),[])
        assert json.loads((root/'.backup/metadata.json').read_text())['profile_channel']=='stable'
        stable_settings.write_text('{}')
        (root/'vitalux/__main__.py').write_text('destination application')
        with patch.object(profiles,'__version__','0.9.6.1-unstable.1'),patch.object(updater.settings,'PATH',str(test_settings)):
            updater.restore_previous(str(root))
        assert stable_settings.read_bytes()==saved
        assert test_settings.read_bytes()==test_saved
        assert (root/'vitalux/__main__.py').read_text()=='original application'
    print('Rolling manifest, prerelease ordering, stable downgrade, isolated profiles and migrations PASS')


if __name__=='__main__':run()
