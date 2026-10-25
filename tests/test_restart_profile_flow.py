"""Real launcher/Qt shutdown/reset/relaunch with isolated channel profiles."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DRIVER = r'''
import json, os, sys
from pathlib import Path
from functools import partial
from unittest.mock import patch
stage=Path.cwd();sys.path.insert(0,str(stage))
state=stage/'phase';phase=int(state.read_text())+1 if state.exists() else 1
state.write_text(str(phase))
def log(event,**details):
 with (stage/'events.jsonl').open('a') as stream:
  stream.write(json.dumps(dict(event=event,phase=phase,pid=os.getpid(),**details))+'\n')
import vitalux
vitalux.__version__='0.9.6.3' if os.environ['TEST_CHANNEL']=='stable' else '0.9.6.3-unstable.25'
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from vitalux import __main__,profiles,single_instance,guide
from vitalux.update_manager import UpdateManager
from vitalux.ui_locale import QMessageBox
Guard=single_instance.InstanceGuard
log('entry')
def blocked(**kwargs):log('blocked');return 0
def guide_exec(self):log('guide');return self.Accepted
def drive_check(self):
 self._timer.stop()
 def act():
  from vitalux.window import MainWindow
  win=next(w for w in QApplication.instance().topLevelWidgets() if isinstance(w,MainWindow))
  data=profiles.read(profiles.directory('config')/'settings.json')
  log('ready',settings=data)
  if phase < int(os.environ['TEST_LAUNCHES']):
   log('reset')
   next(p for title,p in win.pages if title=='Einstellungen').restore_defaults()
  else:win.quit_from_tray()
 QTimer.singleShot(2700,act)
with patch.object(single_instance,'InstanceGuard',partial(Guard,directory=stage/'instance')), \
     patch.object(single_instance,'already_running',blocked), \
     patch.object(UpdateManager,'check',drive_check), \
     patch.object(QMessageBox,'question',return_value=QMessageBox.Yes), \
     patch.object(guide.GuideDialog,'exec',guide_exec):
 try:__main__.main()
 except SystemExit as result:log('exit',code=result.code);raise
'''

for channel, launches in (('stable', 2), ('unstable', 3)):
    with tempfile.TemporaryDirectory(prefix='vitalux-reset-flow-') as folder:
        stage = Path(folder)
        (stage/'driver.py').write_text(DRIVER)
        shutil.copy2(ROOT/'run.sh', stage/'run.sh')
        for name in ('vitalux', 'assets', 'packaging'):
            (stage/name).symlink_to(ROOT/name, target_is_directory=True)
        # The launcher's permission recovery must never chmod the source tree.
        shutil.copytree(ROOT/'bin', stage/'bin')
        runtime = stage/'runtime/bin'
        runtime.mkdir(parents=True)
        executable = shlex.quote(sys.executable)
        driver = shlex.quote(str(stage/'driver.py'))
        (runtime/'python3.12').write_text(
            '#!/bin/sh\nif [ "$1" = -m ] && [ "$2" = vitalux ]; then exec '
            + executable+' '+driver+'; fi\nexec '+executable+' "$@"\n')
        (runtime/'python3.12').chmod(0o755)
        env = os.environ.copy()
        env.update(QT_QPA_PLATFORM='offscreen', VITALUX_LOCAL_PREVIEW='1',
                   TEST_CHANNEL=channel, TEST_LAUNCHES=str(launches), LANG='en_US.UTF-8')
        for kind in ('CONFIG', 'DATA', 'STATE', 'CACHE'):
            env['XDG_'+kind+'_HOME'] = str(stage/kind.lower())
        stable = stage/'config/vitalux/settings.json'
        stable.parent.mkdir(parents=True)
        stable.write_text(json.dumps(dict(guide_intro_choice='completed', lang='en',
            theme='glass', close_to_tray=False,  render_backend='software')))
        stable_before = stable.read_bytes()
        image = stable.parent/'backgrounds/keep.png'
        image.parent.mkdir()
        image.write_bytes(b'resource-kept')
        result = subprocess.run(['bash', str(stage/'run.sh')], cwd=stage, env=env,
                                capture_output=True, text=True, timeout=55)
        events = [json.loads(line) for line in (stage/'events.jsonl').read_text().splitlines()]
        logs = '\n'.join(p.read_text()[-6000:] for p in (stage/'state').rglob('*.log'))
        assert result.returncode == 0, result.stdout+result.stderr+logs
        assert not any(e['event'] == 'blocked' for e in events), events
        assert [e['code'] for e in events if e['event'] == 'exit'] == [42]*(launches-1)+[0], events
        assert [e['phase'] for e in events if e['event'] == 'entry'] == list(range(1, launches+1))
        assert [e['phase'] for e in events if e['event'] == 'guide'] == list(range(2, launches+1)), events
        ready = [e['settings'] for e in events if e['event'] == 'ready']
        assert ready[0]['theme'] == 'glass', 'First Unstable launch must inherit Stable'
        assert all(d.get('theme', 'obsidian_gold') == 'obsidian_gold' for d in ready[1:]), events
        if channel == 'unstable':
            assert image.read_bytes() == b'resource-kept'
            assert stable.read_bytes() == stable_before, 'Unstable reset modified Stable'
            assert not (stable.parent/'profiles/unstable/backgrounds/keep.png').exists()
        else:
            assert not image.exists()
print('Real run.sh: repeated reset/exit42/relaunch, guide reopening, default theme, resource and Stable isolation PASS')
