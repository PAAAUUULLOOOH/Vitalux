#!/usr/bin/env python3
"""Check a real manufacturer download and offline reuse when online is available."""
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vitalux.product_images import ProductCache, resolve


def main():
    product = dict(kind='gpu', vendor='SAPPHIRE', model='SAPPHIRE PURE Radeon RX 9070 XT',
                   revision='', exact=True)
    with tempfile.TemporaryDirectory(prefix='vitalux-manufacturer-check-') as directory:
        result = resolve(product, ProductCache(directory))
        if result is None:
            # Remote websites can refuse a CI runner. Offline/failure behavior
            # is independently covered by deterministic regression tests.
            print(json.dumps({'manufacturer_download': 'unavailable', 'cache_check': 'not_run'}), flush=True)
            return 0
        def offline(*args):
            raise AssertionError('The cached picture attempted an online request')
        restored = resolve(product, ProductCache(directory), download=offline)
        assert restored and restored['cached'] and restored['sha256'] == result['sha256']
        print(json.dumps({'manufacturer_download': 'passed', 'cache_check': 'passed',
                          'bytes': Path(restored['path']).stat().st_size,
                          'source': restored['source']}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
