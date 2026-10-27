"""Evidence-based health score: no fabricated SMART or benchmark expectations."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from vitalux.page_base import _system_state


def sample():
    return {
        'cpu': {'usage': 15, 'temp': 52},
        'ram': {'percent': 38, 'swap_percent': 0},
        'gpus': [{'usage': 30, 'temp': 53, 'hotspot': 68,
                  'vram_used': 3, 'vram_total': 16}],
        'disks': [
            {'mount': '/', 'device': '/dev/nvme0n1p2', 'percent': 30},
            {'mount': '/games', 'device': '/dev/nvme1n1p1', 'percent': 40},
        ],
        'smart_reports': [
            {'name': 'nvme0n1', 'health': 'Gut', 'health_percent': 95},
            {'name': 'nvme1n1', 'health': 'Gut', 'health_percent': 88},
        ]
    }


def main():
    ordinary = sample()
    healthy, name, _ = _system_state(ordinary)
    assert healthy >= 90 and name == 'Sehr gut', (healthy, name)
    busy = sample()
    busy['cpu']['usage'] = 99
    busy['cpu']['temp'] = 92
    busy['ram']['percent'] = 96
    busy['ram']['swap_percent'] = 95
    busy['gpus'][0]['vram_used'] = 15.8
    busy_score, _, _ = _system_state(busy)
    assert busy_score < healthy, (busy_score, healthy)
    all_disks = sample()
    all_disks['disks'][1]['percent'] = 98
    full_score, _, reason = _system_state(all_disks)
    assert full_score < healthy and '/games' in reason, (full_score, reason)
    smart_warning = sample()
    smart_warning['smart_reports'][1]['health'] = 'Warnung'
    degraded, _, reason = _system_state(smart_warning)
    assert degraded < healthy and 'SMART' in reason, (degraded, reason)
    no_smart = sample()
    no_smart.pop('smart_reports')
    incomplete, _, note = _system_state(no_smart)
    assert incomplete <= 89 and 'SMART' in note, (incomplete, note)
    assert _system_state({})[0] is None
    # Full GPU utilization alone is normal during gaming.
    gaming = sample()
    gaming['gpus'][0]['usage'] = 100
    score, _, _ = _system_state(gaming)
    assert score >= 90
    print('Health score reacts to every volume, memory pressure, load and real SMART flags: PASS')


if __name__ == '__main__':
    main()
