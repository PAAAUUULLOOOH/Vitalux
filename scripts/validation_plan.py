#!/usr/bin/env python3
"""Select costly Unstable checks; basic regressions and packaging always run."""
import argparse
import json
from pathlib import Path
import subprocess

GROUPS=('overlay','game_artwork','navigation','resources','hardware_network','kernel','graphics','source_startup')
CORE=('vitalux/theme.py','vitalux/settings.py','vitalux/profiles.py','vitalux/window',
      'vitalux/control.py','vitalux/widgets.py','vitalux/ui_locale.py','vitalux/page_base.py',
      'vitalux/pages.py','vitalux/glass.py','vitalux/quick_scene.py','vitalux/renderer.py',
      'vitalux/startup.py','vitalux/__main__.py','vitalux/appearance',
      'vitalux/signature_designs.py','vitalux/premium.py','vitalux/design_',
      'vitalux/brand.py','vitalux/backdrops.py','vitalux/image_cache.py',
      'vitalux/presentation.py','vitalux/charts.py','vitalux/motion.py','vitalux/eco.py',
      'assets/','packaging/','portable-runtime/','requirements', '.github/workflows/',
      'scripts/validation_plan.py','scripts/run-regressions.py')
RELATED={
 'overlay':('vitalux/game','third_party/','tests/test_game','scripts/check-game-recording',
            'scripts/check-flatpak','scripts/check-steam','scripts/bundle-mangohud'),
 'game_artwork':('vitalux/game_artwork.py','vitalux/game_library.py','vitalux/games_page.py',
                 'scripts/check-game-artwork','tests/test_game_artwork','tests/test_game_capsules'),
 'navigation':('vitalux/nav','vitalux/search','vitalux/dashboard','vitalux/smooth_scroll',
               'tests/test_navigation','tests/test_framed','tests/test_search'),
 'resources':('scripts/check-resource','scripts/check-ui-endurance',
              'scripts/check-render-parity','scripts/check-performance-render'),
 'hardware_network':('vitalux/product','vitalux/spec_','vitalux/hardware', 'vitalux/sensors.py',
                     'scripts/check-product','scripts/check-spec-translation','tests/test_product',
                     'tests/test_specification','tests/test_spec_language'),
 'kernel':('vitalux/network','vitalux/monitor_extra.py','scripts/check-network-kernel','tests/test_network'),
 'graphics':('vitalux/','scripts/run-graphics-checks','scripts/capture-release-ui'),
 'source_startup':('scripts/ensure-runtime.sh','run.sh','Portable-pruefen.sh',
                   'Obsidian-Gold.sh','Quantum-Core.sh','scripts/check-source-startup'),
}


def select(paths, *, complete=False):
    """Unknown/core changes fail closed to the complete validation matrix."""
    paths=sorted(set(paths))
    full=complete or any(path.startswith(CORE) for path in paths)
    selected=set()
    for path in paths:
        if path.endswith('.md') or path=='vitalux/__init__.py':continue
        matched={group for group,prefixes in RELATED.items() if path.startswith(prefixes)}
        if path.startswith('vitalux/') and not (matched-{'graphics','resources'}):full=True
        if matched:selected.update(matched)
        elif not path.startswith(('tests/','scripts/')):full=True
        elif path.startswith('scripts/') and not path.endswith(('run-regressions.py','validation_plan.py')):full=True
    if full:selected=set(GROUPS)
    return dict(full=full,changed_files=paths,groups={group:group in selected for group in GROUPS})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',default='refs/tags/unstable')
    parser.add_argument('--full',action='store_true')
    parser.add_argument('--output',type=Path,default=Path('build/setup/validation-plan.json'))
    parser.add_argument('--github-output',type=Path)
    args=parser.parse_args()
    try:
        changes=subprocess.check_output(['git','diff','--name-only','--no-renames',args.base,'HEAD'],text=True).splitlines()
        old=subprocess.check_output(['git','show',args.base+':vitalux/__init__.py'],text=True)
        new=Path('vitalux/__init__.py').read_text()
        without_version=lambda value:'\n'.join(line for line in value.splitlines() if not line.startswith('__version__ = '))
        core_init=without_version(old)!=without_version(new)
        plan=select(changes,complete=args.full or core_init)
    except subprocess.CalledProcessError:
        plan=select([],complete=True);plan['reason']='Published baseline unavailable'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(plan,indent=2)+'\n')
    if args.github_output:
        with args.github_output.open('a') as stream:
            for group,enabled in plan['groups'].items():stream.write(f'{group}={str(enabled).lower()}\n')
    print(json.dumps(plan,indent=2))


if __name__=='__main__':main()
