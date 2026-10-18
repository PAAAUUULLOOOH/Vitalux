"""Dashboard system status: real readings, gaps and severity boundaries."""
from vitalux.pages import _system_state
from vitalux.dashboard_model import DEFAULT, TITLES
def run():
    assert 'health' in DEFAULT and TITLES['health'] == 'Systemzustand'
    score, state, detail = _system_state({'cpu': {'temp': None, 'usage': None},
                                         'ram': {}, 'gpus': [], 'disks': []})
    assert score is None and state
    score, state, detail = _system_state({'cpu': {'temp': 44, 'usage': 12},
      'ram': {'percent': 34}, 'gpus': [{'temp': 45, 'hotspot': 53, 'usage': 15}],
      'disks': [{'mount': '/', 'percent': 39}]})
    assert score == 100 and state
    score, state, detail = _system_state({'cpu': {'temp': 101, 'usage': 99},
      'ram': {'percent': 99}, 'gpus': [{'temp': 98, 'hotspot': 110, 'usage': 99}],
      'disks': [{'mount': '/', 'percent': 99}]})
    assert score < 76 and detail
    print('System health score: OK')
if __name__ == '__main__': run()
