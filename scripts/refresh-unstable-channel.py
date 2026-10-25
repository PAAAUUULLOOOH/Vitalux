#!/usr/bin/env python3
"""Withdraw a caught-up test offer without renumbering or rebuilding packages."""
from pathlib import Path
import json,tempfile
from channel_metadata import describe,git
from publish_unstable_support import gh


def refresh():
    # A previous test build may remain downloadable, but is no longer a switch target.
    existing=gh('release','view','unstable','--json','assets',check=False)
    if existing.returncode:
        print('No rolling test release exists; no mirror build is needed.');return
    with tempfile.TemporaryDirectory(prefix='vitalux-test-metadata-') as folder:
        folder=Path(folder)
        gh('release','download','unstable','--pattern','Vitalux-unstable-channel.json','--dir',str(folder))
        path=folder/'Vitalux-unstable-channel.json';manifest=json.loads(path.read_text())
        commit=manifest['commit'];metadata=describe(commit)
        baseline=metadata['stable_version']
        stable=json.loads(gh('release','view','v'+baseline,'--json','assets').stdout)
        names=[asset['name'] for asset in stable['assets'] if asset['name'].endswith(('-linux-x86_64.zip','-x86_64.AppImage','-SHA256SUMS.txt','-ThirdPartySources.zip'))]
        if len(names)!=4:raise ValueError('Published Stable package set is incomplete')
        for name in names:gh('release','download','v'+baseline,'--pattern',name,'--dir',str(folder))
        rolling=json.loads(existing.stdout)
        for name in names:gh('release','upload','unstable',str(folder/name),'--clobber')
        manifest.update(metadata,has_test_changes=False,baseline_version=baseline,
                        baseline_commit=metadata['stable_commit'],build_base_version=baseline)
        path.write_text(json.dumps(manifest,indent=2)+'\n')
        gh('release','upload','unstable',str(path),'--clobber')
        for asset in rolling['assets']:
            if asset['name'] not in names and asset['name']!='Vitalux-unstable-channel.json':
                gh('release','delete-asset','unstable',asset['name'],'--yes')
        title='Unstable — same baseline as Stable v'+baseline
        notes=folder/'notes.md'
        notes.write_text('## Deutsch\n\nDiese Basis entspricht Stable v'+baseline+
            '. Aktuell gibt es keinen neueren Teststand. Der Wechsel zu Unstable ist deaktiviert.\n\n'+
            '## English\n\nThis baseline matches Stable v'+baseline+
            '. There is currently no newer test build. Switching to Unstable is disabled.\n')
        gh('release','edit','unstable','--title',title,'--prerelease','--latest=false','--notes-file',str(notes))
        print(title+'; no additional test build or release entry created.')


if __name__=='__main__':refresh()
