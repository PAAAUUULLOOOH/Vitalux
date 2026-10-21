#!/usr/bin/env python3
"""Update ONE rolling prerelease, promoting its verified manifest last."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from vitalux import __version__
from vitalux.versions import channel
from channel_metadata import describe
from publish_unstable_support import gh


def publish(folder):
    assert channel(__version__)=='unstable'
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    files=sorted(p for p in folder.iterdir() if p.is_file() and p.suffix in ('.zip','.AppImage','.txt'))
    assert any(p.name==f'Vitalux-v{__version__}-linux-x86_64.zip' for p in files)
    assert any(p.name==f'Vitalux-v{__version__}-x86_64.AppImage' for p in files)
    metadata=describe()
    assert metadata['has_test_changes'],'A mirrored Stable build must not be published as a newer test.'
    title='Unstable — test changes after Stable v'+metadata['stable_version']
    metadata['build_base_version']=metadata['stable_version']
    assets={}
    for item in files:
        with item.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        assets[item.name]={'sha256':digest,'bytes':item.stat().st_size}
    manifest=folder/'Vitalux-unstable-channel.json'
    manifest.write_text(json.dumps(dict(schema=1,channel='unstable',version=__version__,commit=commit,assets=assets,**metadata),indent=2)+'\n')
    notes=folder/'unstable-notes.md'
    subprocess.run([sys.executable,'scripts/release_notes.py',__version__,str(notes)],cwd=ROOT,check=True)
    existing=gh('release','view','unstable','--json','assets',check=False)
    if existing.returncode:
        # A draft is promoted only once all initial packages and metadata exist.
        gh('release','create','unstable','--target',commit,'--title',title,'--prerelease','--draft','--latest=false','--notes-file',str(notes))
        gh('release','upload','unstable',*[str(p) for p in files],str(manifest))
        gh('release','edit','unstable','--draft=false','--prerelease','--latest=false')
    else:
        old_names=[a['name'] for a in json.loads(existing.stdout)['assets']]
        # Unique build filenames keep the previous manifest usable throughout upload.
        gh('release','upload','unstable',*[str(p) for p in files])
        gh('release','upload','unstable',str(manifest),'--clobber')
        gh('release','edit','unstable','--title',title,'--draft=false','--prerelease','--latest=false','--notes-file',str(notes))
        for name in old_names:
            if name not in assets and name!=manifest.name:gh('release','delete-asset','unstable',name,'--yes')
    # The rolling manifest pins the exact code commit; the fixed tag follows it.
    subprocess.run(['git','tag','-f','unstable',commit],cwd=ROOT,check=True,capture_output=True)
    subprocess.run(['git','push','origin','refs/tags/unstable','--force'],cwd=ROOT,check=True)
    print('Updated the single rolling Unstable prerelease: '+__version__)


if __name__=='__main__':publish(Path(sys.argv[1]).resolve())
