#!/usr/bin/env python3
"""Verify repeated UI notes through an owned PulseAudio sink and monitor.

No user's audio server or volume is changed. Requires pulseaudio, pactl, parec.
"""
import argparse
import json
import os
from pathlib import Path
import queue
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def check(args, output):
    env = os.environ.copy()
    programs = {name: shutil.which(name) for name in ('pulseaudio', 'pactl', 'parec')}
    modules = None
    if args.sysroot:
        root = args.sysroot.resolve()
        programs = {name: str(root/'usr/bin'/name) for name in programs}
        lib = root/'usr/lib/x86_64-linux-gnu'
        modules = next((root/'usr/lib').glob('pulse-*/modules'))
        env['LD_LIBRARY_PATH'] = ':'.join(map(str, (lib, lib/'pulseaudio', modules)))+':'+env.get('LD_LIBRARY_PATH', '')
    if not all(programs.values()):
        raise RuntimeError('Install pulseaudio and pulseaudio-utils for the audio integration check')
    from vitalux import settings, ui_sound
    original_settings = settings.PATH
    with tempfile.TemporaryDirectory(prefix='vitalux-audio-') as directory:
        private = Path(directory)
        private.chmod(0o700)
        socket = private/'pulse-native'
        env.update(XDG_CONFIG_HOME=str(private/'config'), PULSE_RUNTIME_PATH=str(private/'runtime'))
        env.pop('PULSE_SERVER', None)
        command = [programs['pulseaudio'], '-n', '--daemonize=no', '--exit-idle-time=-1',
                   '--use-pid-file=no', '--disable-shm=yes', '--log-target=stderr',
                   '--load=module-native-protocol-unix auth-anonymous=1 socket='+str(socket),
                   '--load=module-null-sink sink_name=vitalux_test rate=48000 channels=1']
        if modules:
            command.append('--dl-search-path='+str(modules))
        pending, worker, recorder = queue.Queue(maxsize=32), None, None
        with (output/'pulse.log').open('w') as log:
            server = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
            try:
                env['PULSE_SERVER'] = 'unix:'+str(socket)
                deadline = time.monotonic()+10
                while True:
                    result = subprocess.run([programs['pactl'], 'list', 'short', 'sources'], env=env,
                                             capture_output=True, text=True, timeout=3)
                    if result.returncode == 0 and 'vitalux_test.monitor' in result.stdout:
                        break
                    if server.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError((output/'pulse.log').read_text())
                    time.sleep(.1)
                settings.PATH = str(private/'settings.json')
                settings.set_many({'ui_sounds': True, 'ui_sound_volume': 70})
                # libpulse reads this at connection time; the system server is untouched.
                previous_server = os.environ.get('PULSE_SERVER')
                os.environ['PULSE_SERVER'] = env['PULSE_SERVER']
                raw = output/'glass-loopback.raw'
                try:
                    with raw.open('wb') as stream, (output/'recorder.log').open('w') as errors:
                        recorder = subprocess.Popen([programs['parec'], '--raw', '--format=s16le',
                            '--rate=48000', '--channels=1', '--device=vitalux_test.monitor',
                            '--latency-msec=10'], env=env, stdout=stream, stderr=errors)
                        worker = threading.Thread(target=ui_sound._pulse_worker, args=(pending,), daemon=True)
                        worker.start()
                        # Prime the owned null sink quietly: its initial clock
                        # negotiation can omit monitor frames for two seconds.
                        pending.put((time.monotonic(), 1))
                        time.sleep(2.4)
                        started = time.monotonic()
                        timings = (.25, .9, 6.0, 6.6, 6.68, 6.76)
                        for moment in timings:
                            while time.monotonic()-started < moment:
                                time.sleep(min(.02, max(0, moment-(time.monotonic()-started))))
                            pending.put((time.monotonic(), 70))
                        time.sleep(.45)
                        assert worker.is_alive(), 'Audio worker stopped after a note'
                        pending.put(None)
                        worker.join(timeout=2)
                        assert not worker.is_alive(), 'Audio worker did not shut down'
                        recorder.terminate()
                        recorder.wait(timeout=3)
                    pcm = raw.read_bytes()
                    samples = struct.unpack('<'+'h'*(len(pcm)//2), pcm)
                    # The monitor may omit initial silence while negotiating.
                    # Compare observed note intervals, not its wall-clock origin.
                    groups = []
                    clip=ui_sound._samples(70)
                    threshold=max(100,round(max(map(abs,clip))*.18))
                    for offset in range(0, len(samples), 480):
                        peak = max(map(abs, samples[offset:offset+480]), default=0)
                        if peak > threshold:
                            moment = offset/48000
                            if groups and moment-groups[-1][1] < .055:
                                groups[-1][1] = moment
                                groups[-1][2] = max(groups[-1][2], peak)
                            else:
                                groups.append([moment, moment, peak])
                    assert len(groups) == 4, f'Expected three single notes and one rapid group, got {groups}'
                    for expected, left, right in zip((.65, 5.1, .6), groups, groups[1:]):
                        assert abs(right[0]-left[0]-expected) < .12, (expected, groups)
                    assert .18 <= groups[-1][1]-groups[-1][0] <= .36, groups
                    peaks = [group[2] for group in groups]
                    result = {'repeated_notes': 'PASS', 'resume_after_idle': 'PASS',
                              'rapid_notes': 'PASS', 'single_note_peaks': peaks,
                              'recorded_frames': len(samples), 'observed_groups': groups,
                              'transport': 'owned PulseAudio loopback'}
                    (output/'results.json').write_text(json.dumps(result, indent=2)+'\n')
                    print('UI audio: repeated notes, five-second idle, rapid clicks and shutdown PASS', flush=True)
                finally:
                    if previous_server is None:
                        os.environ.pop('PULSE_SERVER', None)
                    else:
                        os.environ['PULSE_SERVER'] = previous_server
            finally:
                settings.PATH = original_settings
                if worker is not None and worker.is_alive():
                    pending.put_nowait(None)
                    worker.join(timeout=2)
                if recorder is not None and recorder.poll() is None:
                    recorder.terminate()
                    recorder.wait(timeout=3)
                server.terminate()
                server.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sysroot', type=Path)
    parser.add_argument('--output', type=Path, default=Path('build/audio-checks'))
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    try:
        check(args, output)
    except Exception:
        (output/'audio-error.log').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
