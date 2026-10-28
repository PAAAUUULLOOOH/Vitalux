"""Regression tests for Vitalux's new 0...9 versioning policy."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import versioning
import importlib.util


def check():
    assert versioning.parse("v0.9.4.0") == (0, 9, 4, 0)
    assert versioning.parse("0.9.4.9") == (0, 9, 4, 9)
    assert versioning.next_version("v0.9.4.0") == "0.9.4.1"
    assert versioning.next_version("v0.9.4.8") == "0.9.4.9"
    assert versioning.next_version("v0.9.4.9") == "0.9.5.0"
    assert versioning.next_version("v0.9.9.9") == "0.9.10.0"
    assert versioning.verify_successor("v0.9.4.9", "0.9.5.0") == "0.9.5.0"
    for previous, proposed in [
        ("0.9.4.0", "0.9.4.2"),
        ("0.9.4.9", "0.9.4.10"),
        ("0.9.4.9", "0.9.5.1"),
        ("0.9.4.8", "0.9.5.0"),
    ]:
        try:
            versioning.verify_successor(previous, proposed)
            raise AssertionError((previous, proposed))
        except ValueError:
            pass
    for invalid in ("0.9.4.10", "0.9.4.99", "0.9.4", "bad", "0.9.4.-1"):
        try:
            versioning.parse(invalid)
            raise AssertionError(invalid)
        except ValueError:
            pass
    script = ROOT / "scripts" / "versioning.py"
    ok = subprocess.run([sys.executable, str(script), "verify",
                         "v0.9.4.9", "0.9.5.0"], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    bad = subprocess.run([sys.executable, str(script), "verify",
                          "v0.9.4.9", "0.9.4.10"], capture_output=True, text=True)
    assert bad.returncode != 0
    spec=importlib.util.spec_from_file_location('prepare_unstable',ROOT/'scripts/prepare-unstable-build.py')
    prepare=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepare)
    assets={'Vitalux-v0.9.6.4-unstable.8-linux-x86_64.zip','Vitalux-v0.9.6.4-unstable.8-x86_64.AppImage'}
    assert prepare.unpublished_test_version('0.9.6.4-unstable.8','0.9.6.3',assets)=='0.9.6.4-unstable.9'
    assert prepare.unpublished_test_version('0.9.6.4-unstable.9','0.9.6.3',assets)=='0.9.6.4-unstable.9'
    assert prepare.unpublished_test_version('0.9.6.4-unstable.9','0.9.6.4',assets)=='0.9.6.5-unstable.1'
    assert prepare.unpublished_test_version('0.9.6.3','0.9.6.3',assets)=='0.9.6.4-unstable.1'
    assert prepare.unpublished_test_version('0.9.6.4-unstable.9','0.9.6.3',{'Vitalux-v0.9.6.4-unstable.9-x86_64.AppImage'})=='0.9.6.4-unstable.10'
    print("Vitalux releases: .0 through .9, then next patch .0: PASS")


if __name__ == "__main__":
    check()
