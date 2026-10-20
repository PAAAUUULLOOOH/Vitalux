"""An idle output is released so the next click follows a changed device."""
import os
from pathlib import Path
import queue
import sys
import tempfile
import threading
import time
from unittest.mock import patch

sys.path.insert(0, os.getcwd())
from vitalux import settings
from vitalux.ui_sound import _pulse_worker


def run():
    previous = settings.PATH
    with tempfile.TemporaryDirectory() as folder:
        settings.PATH = str(Path(folder)/'settings.json')
        settings.set_many({'ui_sounds': True, 'ui_sound_volume': 70})
        outputs, default = [], ['speakers']
        class Output:
            def __init__(self):
                self.device = default[0]
                self.frames = 0
                self.closed = threading.Event()
                outputs.append(self)
            def write(self, pcm):
                self.frames += len(pcm)//2
                time.sleep(.005)
            def close(self):
                self.closed.set()
        pending = queue.Queue()
        with patch('vitalux.ui_sound._PulseOutput', Output):
            worker = threading.Thread(target=_pulse_worker, args=(pending,), daemon=True)
            worker.start()
            try:
                pending.put(True)
                deadline = time.monotonic()+3.5
                while (not outputs or not outputs[0].closed.is_set()) and time.monotonic() < deadline:
                    time.sleep(.01)
                assert outputs and outputs[0].closed.is_set()
                default[0] = 'headphones'
                pending.put(True)
                deadline = time.monotonic()+1
                while (len(outputs) < 2 or outputs[1].frames < 480) and time.monotonic() < deadline:
                    time.sleep(.01)
                assert [output.device for output in outputs] == ['speakers', 'headphones']
                assert all(output.frames >= 480 for output in outputs)
            finally:
                pending.put(None)
                worker.join(2)
                assert not worker.is_alive()
        settings.PATH = previous
    print('Audio recovery: idle release, changed default device and worker shutdown PASS')


if __name__ == '__main__':
    run()
