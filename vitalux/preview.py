"""Local design preview with separate preferences and no release updates."""
import argparse
import os
from pathlib import Path


DESIGNS = ('obsidian_gold', 'black_glass_gold', 'aether_glass', 'eclipse_crystal', 'champagne_glass', 'aurora_gold', 'liquid_silver')


def prepare(design=None):
    # Resolve before importing settings: ordinary installed Vitalux preferences
    # and desktop integration must never be touched by a local design test.
    root = Path(__file__).resolve().parent.parent
    data = root / 'design-test-data'
    for variable, suffix in (
            ('XDG_CONFIG_HOME', 'config'), ('XDG_STATE_HOME', 'state'),
            ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache')):
        directory = data / suffix
        directory.mkdir(parents=True, exist_ok=True)
        os.environ[variable] = str(directory)
    os.environ['VITALUX_LOCAL_PREVIEW'] = '1'
    from . import settings
    changes = {}
    if not Path(settings.PATH).exists():
        changes.update(theme='obsidian_gold', lang='de', render_backend='software',
                       guide_intro_choice='never', motion='smooth')
    if design is not None:
        if design not in DESIGNS:
            raise ValueError('Unknown Vitalux preview design')
        from .appearance import migrate
        choices=migrate(dict(theme=design))
        changes.update({k:v for k,v in choices.items() if not k.endswith('_migration')})
        changes.update(ultra_eco=False,background_tint='')
    if changes and not settings.set_many(changes):
        raise RuntimeError('Unable to save local preview preferences')


def main():
    parser = argparse.ArgumentParser(description='Vitalux local glass design preview')
    parser.add_argument('design', nargs='?', choices=DESIGNS)
    args = parser.parse_args()
    prepare(args.design)
    from .__main__ import main as run
    run()


if __name__ == '__main__':
    main()
