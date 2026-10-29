#!/usr/bin/env python3
"""Own X11/Wayland sessions for all renderers and repeated Wayland CPU resets."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vitalux.process_environment import host_environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sysroot', type=Path)
    parser.add_argument('--output', type=Path, default=Path('build/graphics-checks'))
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['LIBGL_ALWAYS_SOFTWARE'] = '1'
    # Bound Mesa's software worker pools on shared CI machines. This changes
    # test-driver scheduling, not rendering quality or Vitalux's runtime.
    env.setdefault('LP_NUM_THREADS', '2')
    programs = {}
    if args.sysroot:
        root = args.sysroot.resolve()
        lib = root/'usr/lib/x86_64-linux-gnu'
        env['LD_LIBRARY_PATH'] = ':'.join(map(str, (lib, lib/'weston')))+':'+env.get('LD_LIBRARY_PATH', '')
        modules = list((lib/'libweston-14').glob('*.so'))+list((lib/'weston').glob('*.so'))
        env['WESTON_MODULE_MAP'] = ';'.join(p.name+'='+str(p) for p in modules)
        programs = {name: str(root/'usr/bin'/name) for name in ('Xvfb', 'weston')}
    else:
        programs = {name: shutil.which(name) for name in ('Xvfb', 'weston')}
    if not all(programs.values()):
        raise RuntimeError('Install Xvfb, Weston and Mesa OpenGL')
    def desktop_environment():
        # The compositor is a host program, not a shipped Qt process. Its
        # GLib/font stack must not inherit Vitalux's private dependencies.
        clean=host_environment(env)
        if args.sysroot:
            clean['LD_LIBRARY_PATH']=':'.join(map(str,(lib,lib/'weston')))+':'+clean.get('LD_LIBRARY_PATH','')
        return clean
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
                env=desktop_environment(), pass_fds=(write_fd,), stdout=streams[0], stderr=subprocess.STDOUT)
            processes.append(xvfb)
            os.close(write_fd)
            write_fd = None
            import select
            if not select.select([read_fd], [], [], 15)[0]:
                raise RuntimeError('Xvfb did not allocate a display')
            env['DISPLAY'] = ':'+os.read(read_fd, 32).decode().strip()
            help_probe = subprocess.run([programs['weston'], '--help'], env=desktop_environment(),
                                        capture_output=True, text=True)
            (output/'weston-help.log').write_text(help_probe.stdout+help_probe.stderr)
            help_probe.check_returncode();help_text=help_probe.stdout
            compositor_renderer = ['--renderer=gl'] if '--renderer=' in help_text else ['--use-gl']
            sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
            from vitalux import renderer
            results = []
            cases=[(mode,None,mode) for mode in renderer.CHOICES]
            # The reported native reset crashes occurred on Wayland/software,
            # a distinct platform path from the normal X11 software check.
            cases += [(renderer.SOFTWARE,'wayland',f'wayland-software-reset-{index}') for index in range(1,4)]
            for mode,platform,case in cases:
                case_output=output if platform is None else output/case
                case_output.mkdir(exist_ok=True)
                weston = None
                try:
                    if (platform or renderer.display_api(mode)) == 'wayland':
                        # Each client gets a fresh compositor, so GL/Vulkan
                        # resources and protocol state cannot leak across modes.
                        env['WAYLAND_DISPLAY'] = 'wayland-vitalux-'+case
                        # Exercise real windowed client corners and restore.
                        # A bare extracted sysroot may lack desktop helpers.
                        shell = 'kiosk-shell.so' if args.sysroot else 'desktop-shell.so'
                        weston = subprocess.Popen([programs['weston'], '--backend=headless-backend.so',
                            '--shell='+shell, '--socket='+env['WAYLAND_DISPLAY'],
                            '--width=1600', '--height=1100', '--no-config', '--idle-time=0',
                            *compositor_renderer], env=desktop_environment(), stdout=streams[1], stderr=subprocess.STDOUT)
                        processes.append(weston)
                        deadline = time.monotonic()+20
                        while not (runtime/env['WAYLAND_DISPLAY']).exists():
                            if weston.poll() is not None or time.monotonic() > deadline:
                                raise RuntimeError('Weston startup failed; see '+str(output/'weston.log'))
                            time.sleep(.1)
                    command=[sys.executable,
                        str(Path(__file__).with_name('check-graphics-startup.py')),
                        '--mode', mode, '--output', str(case_output)]
                    if platform:command.extend(['--platform',platform])
                    check = subprocess.run(command, env=env,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60)
                    (case_output/(mode+'-runner.log')).write_text(check.stdout)
                    print(check.stdout, end='', flush=True)
                    if check.returncode:
                        status = weston.poll() if weston else None
                        message = f'{mode}: validation exit {check.returncode}; compositor status {status}'
                        with (case_output/(mode+'-runner.log')).open('a') as failure_log:
                            failure_log.write('\n'+message+'\n')
                        raise RuntimeError(message)
                    results.extend(json.loads((case_output/'results.json').read_text()))
                finally:
                    if weston is not None and weston.poll() is None:
                        weston.terminate()
                        try:
                            weston.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            weston.kill()
                            weston.wait()
            (output/'results.json').write_text(json.dumps(results, indent=2)+'\n')
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
