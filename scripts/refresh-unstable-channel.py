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
        manifest.update(metadata,has_test_changes=False)
        base=manifest.get('build_base_version')
        if not base:
            base=git('describe','--tags','--match','v[0-9]*','--abbrev=0',commit,check=False).stdout.decode().strip().removeprefix('v')
        base=base or metadata['stable_version'];manifest['build_base_version']=base
        path.write_text(json.dumps(manifest,indent=2)+'\n')
        gh('release','upload','unstable',str(path),'--clobber')
        title='Unstable — based on Stable v'+base
        notes=folder/'notes.md'
        notes.write_text('## Deutsch\n\nDieses Testpaket basiert auf Stable v'+base+
            '. Aktuell gibt es keinen neueren Teststand. Der Wechsel zu Unstable ist deaktiviert.\n\n'+
            '## English\n\nThis test package is based on Stable v'+base+
            '. There is currently no newer test build. Switching to Unstable is disabled.\n')
        gh('release','edit','unstable','--title',title,'--prerelease','--latest=false','--notes-file',str(notes))
        print(title+'; no additional test build or release entry created.')


if __name__=='__main__':refresh()
