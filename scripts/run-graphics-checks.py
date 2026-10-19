#!/usr/bin/env python3
"""Own and clean up X11/Wayland test sessions for the five-renderer matrix."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sysroot', type=Path)
    parser.add_argument('--output', type=Path, default=Path('build/graphics-checks'))
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['LIBGL_ALWAYS_SOFTWARE'] = '1'
    programs = {}
    icd = None
    if args.sysroot:
        root = args.sysroot.resolve()
        lib = root/'usr/lib/x86_64-linux-gnu'
        env['LD_LIBRARY_PATH'] = ':'.join(map(str, (lib, lib/'weston', lib/'pulseaudio')))+':'+env.get('LD_LIBRARY_PATH', '')
        modules = list((lib/'libweston-14').glob('*.so'))+list((lib/'weston').glob('*.so'))
        env['WESTON_MODULE_MAP'] = ';'.join(p.name+'='+str(p) for p in modules)
        programs = {name: str(root/'usr/bin'/name) for name in ('Xvfb', 'weston')}
        icd = root/'usr/share/vulkan/icd.d/lvp_icd.json'
    else:
        programs = {name: shutil.which(name) for name in ('Xvfb', 'weston')}
        icd = next(Path('/usr/share/vulkan/icd.d').glob('lvp_icd*.json'), None)
    if not all(programs.values()) or not icd or not icd.is_file():
        raise RuntimeError('Install Xvfb, Weston and Mesa Vulkan/Lavapipe')
    env['VK_DRIVER_FILES'] = env['VK_ICD_FILENAMES'] = str(icd)
    with tempfile.TemporaryDirectory(prefix='vitalux-graphics-') as directory:
        runtime = Path(directory)
        runtime.chmod(0o700)
        env['XDG_RUNTIME_DIR'] = str(runtime)
        for key, part in (('XDG_CONFIG_HOME', 'config'), ('XDG_STATE_HOME', 'state'),
                          ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache')):
            env[key] = str(runtime/part)
        processes, streams = [], []
        read_fd, write_fd = os.pipe()
        try:
            for name in ('Xvfb', 'weston'):
                streams.append((output/(name+'.log')).open('w'))
            xvfb = subprocess.Popen([programs['Xvfb'], '-displayfd', str(write_fd),
                '-screen', '0', '1600x1100x24', '-nolisten', 'tcp', '-noreset'],
                env=env, pass_fds=(write_fd,), stdout=streams[0], stderr=subprocess.STDOUT)
            processes.append(xvfb)
            os.close(write_fd)
            write_fd = None
            import select
            if not select.select([read_fd], [], [], 15)[0]:
                raise RuntimeError('Xvfb did not allocate a display')
            env['DISPLAY'] = ':'+os.read(read_fd, 32).decode().strip()
            env['WAYLAND_DISPLAY'] = 'wayland-vitalux-test'
            help_text = subprocess.check_output([programs['weston'], '--help'], env=env,
                                                stderr=subprocess.STDOUT, text=True)
            renderer = ['--renderer=gl'] if '--renderer=' in help_text else ['--use-gl']
            weston = subprocess.Popen([programs['weston'], '--backend=headless-backend.so',
                '--shell=kiosk-shell.so', '--socket='+env['WAYLAND_DISPLAY'],
                '--width=1600', '--height=1100', '--no-config', '--idle-time=0', *renderer],
                env=env, stdout=streams[1], stderr=subprocess.STDOUT)
            processes.append(weston)
            deadline = time.monotonic()+20
            while not (runtime/env['WAYLAND_DISPLAY']).exists():
                if weston.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError('Weston startup failed; see '+str(output/'weston.log'))
                time.sleep(.1)
            subprocess.run([sys.executable, str(Path(__file__).with_name('check-graphics-startup.py')),
                            '--output', str(output)], env=env, check=True, timeout=240)
        finally:
            if write_fd is not None:
                os.close(write_fd)
            os.close(read_fd)
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            for stream in streams:
                stream.close()


if __name__ == '__main__':
    main()
