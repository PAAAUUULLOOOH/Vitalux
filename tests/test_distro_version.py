"""Versioned and rolling os-release metadata, including CachyOS BUILD_ID."""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux import distro
for raw,expected in (
    ({'VERSION':'24.04 LTS','VERSION_ID':'24.04','BUILD_ID':'123'},'24.04 LTS'),
    ({'VERSION_ID':'42','BUILD_ID':'rolling'},'42'),
    ({'ID':'cachyos','NAME':'CachyOS','BUILD_ID':'rolling'},'rolling'),
    ({'BUILD_ID':'20261101','IMAGE_VERSION':'1'},'20261101'),
    ({'IMAGE_VERSION':'2026.11'},'2026.11'),
    ({'ID':'cachyos'},''),
):
    with patch.object(distro,'_parse',return_value=raw):
        result=distro.info();assert result['version']==expected,(raw,result)
        if raw.get('ID')=='cachyos':assert result['color']==distro.BRAND['cachyos']
print('Version precedence, CachyOS rolling BUILD_ID, image version and unavailable metadata PASS')
