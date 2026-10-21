"""Verified Stable ancestry metadata gates test offers independently of labels."""
import hashlib,io,json,sys,urllib.error
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux import updater
BASE=f'https://github.com/{updater.DEFAULT_REPO}/releases/download/'
stable=dict(tag_name='v0.9.6.1',prerelease=False,body='## Deutsch\n- Stable aktuell\n## English\n- Stable current',assets=[])


def test_offer(version='0.9.6.2-unstable.1',**metadata):
    name=f'Vitalux-v{version}-linux-x86_64.zip'
    manifest=json.dumps(dict(schema=1,version=version,assets={name:{'sha256':'a'*64}},**metadata)).encode()
    release=dict(tag_name='unstable',prerelease=True,body='## Deutsch\n- Teständerung\n## English\n- Test change',assets=[
        dict(name='Vitalux-unstable-channel.json',browser_download_url=BASE+'unstable/Vitalux-unstable-channel.json',digest='sha256:'+hashlib.sha256(manifest).hexdigest()),
        dict(name=name,browser_download_url=BASE+'unstable/'+name,digest='sha256:'+'a'*64)])
    with patch.object(updater,'__version__','0.9.6.1'),patch.object(updater,'_get_release',return_value=stable),patch.object(updater,'_get_unstable_release',return_value=release),patch.object(updater,'_github_request',side_effect=lambda *a,**k:io.BytesIO(manifest)):
        return updater.check('unstable')

for metadata in ({},{'has_test_changes':False,'stable_version':'0.9.6.1'},
                 {'has_test_changes':True,'stable_version':'0.9.6.0'},
                 {'has_test_changes':'true','stable_version':'0.9.6.1'}):
    result=test_offer(**metadata)
    assert result['ok'] and not result['eligible'] and not result['newer'] and not result['url'],result
    assert 'Stable aktuell' in result['notes'],'Mirror changelog did not use current Stable notes'
result=test_offer(stable_version='0.9.6.1',has_test_changes=True)
assert result['ok'] and result['eligible'] and result['newer'] and result['url'],result
result=test_offer(version='0.9.6.1-unstable.99',stable_version='0.9.6.1',has_test_changes=True)
assert not result['eligible'],'A test for an already published Stable version was offered'
with patch.object(updater,'__version__','0.9.6.1'),patch.object(updater,'_get_release',return_value=stable):
    result=updater.check('stable')
    assert result['ok'] and not result['newer'] and 'Stable aktuell' in result['notes']
    with patch.object(updater,'_get_unstable_release',side_effect=urllib.error.HTTPError('test',404,'missing',{},None)):
        result=updater.catalog()
        assert result['stable']['ok'] and result['unstable']['ok'] and not result['unstable']['eligible']
        assert result['unstable']['notes']==result['stable']['notes']
print('Newer test/Stable baseline/actual-change gates, legacy manifest rejection, current notes and missing-test catalog PASS')
