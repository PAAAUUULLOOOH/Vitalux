"""Exercise private native 3D activation, animation, page switches and teardown."""
import argparse,json,os,sys,tempfile,time,subprocess,signal
from pathlib import Path
from unittest.mock import patch


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    root=args.source.resolve()
    sys.path.insert(0,str(root));sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
    with tempfile.TemporaryDirectory(prefix='vitalux-native-private-') as folder:
        for kind in ('CONFIG','STATE','DATA','CACHE'):os.environ['XDG_'+kind+'_HOME']=str(Path(folder)/kind)
        os.environ['VITALUX_SPEC_OFFLINE']='1'
        from sensor_fixture import load_fixture
        app,sample=load_fixture()
        for disk in sample['disks']:disk.setdefault('fstype','ext4')
        from PySide6.QtCore import Qt,QEvent
        from PySide6.QtGui import QPixmap
        from vitalux import settings,theme,sensors
        from vitalux.update_manager import UpdateManager
        from vitalux.window import MainWindow
        def wait_until(predicate,limit=15):
            end=time.monotonic()+limit
            while time.monotonic()<end:
                app.processEvents();time.sleep(.01)
                if predicate():return
            raise AssertionError('Native view did not reach the expected state')
        settings.set_many(dict(theme='obsidian_gold',motion='off',component_images=False))
        theme.set_mode('obsidian_gold');app.setStyleSheet(theme.stylesheet())
        logo=QPixmap(96,96);logo.fill(Qt.transparent)
        with patch.object(sensors,'collect',return_value=sample):
            window=MainWindow(dict(name='Linux',version='1',color='#71837c'),logo,UpdateManager(),startup_sample=sample,startup_games=[])
            window.resize(1440,1000);window.show()
            pref=next(page for name,page in window.pages if name=='Einstellungen')
            overview=window.pages[0][1]
            native_id=int(window.winId())
            results=[]
            try:
                for cycle in range(2):
                    window.resize(1440 if cycle==0 else 900,1000 if cycle==0 else 780)
                    pref.search.setText('td')
                    wait_until(lambda:hasattr(overview,'sculpt_host') and overview.sculpt_host.view is not None and overview.sculpt_host.view.ready)
                    view=overview.sculpt_host.view
                    assert int(window.winId())==native_id,'Design activation recreated the app window'
                    assert view.context().format().majorVersion()>=3
                    frame=view.grabFramebuffer();assert not frame.isNull()
                    colors={frame.pixel(x,y) for y in range(0,frame.height(),8) for x in range(0,frame.width(),8)}
                    assert len(colors)>40,'3D geometry or material was not rendered'
                    for chip in overview.chips.chips.values():
                        assert chip.isVisible() and chip.geometry().bottom()<=overview.chips.height()+1
                    if cycle==0:window.grab().save(str(args.output/'native-private-design.png'))
                    settings.set('motion','smooth');overview.sculpt_host.set_load(75)
                    wait_until(lambda:view.phase>0 and overview.sculpt_host.frame_timer.isActive())
                    window._switch_page(1)
                    wait_until(lambda:not overview.sculpt_host.frame_timer.isActive())
                    window._switch_page(0)
                    settings.set('motion','off');overview.sculpt_host._render_frame()
                    assert not overview.sculpt_host.frame_timer.isActive()
                    pref.select_design('glass');app.processEvents()
                    app.sendPostedEvents(None,QEvent.DeferredDelete)
                    assert overview.sculpt_host.view is None and theme.mode()=='glass'
                    assert overview.chips.parentWidget() is overview.hero_card
                    results.append(dict(cycle=cycle,native_geometry=True,physical_materials=True,
                        hidden_animation_paused=True,normal_design_restored=True))
                # A driver failure in the isolated child must leave an operable UI.
                from vitalux import sculpt_host
                with patch.object(sculpt_host,'_probe_result',(False,'test unavailable driver')):
                    pref.search.setText('td');app.processEvents()
                    assert overview.sculpt_host.view is None and overview.sculpt_host.notice.isVisible()
                    pref.select_design('obsidian_gold')
                pref.search.setText('td')
                wait_until(lambda:overview.sculpt_host.view is not None and overview.sculpt_host.view.ready)
            finally:
                window.quit_from_tray()
                wait_until(lambda:not window.isVisible())
                assert overview.sculpt_host.view is None,'Native surface survived orderly app shutdown'
                from vitalux.lifecycle import stop_product_workers,product_workers
                stop_product_workers()
                for worker in product_workers():worker.pool.waitForDone()
                import shiboken6
                window.sampler.stop();window.sampler.wait()
                shiboken6.delete(window._mini_hud);shiboken6.delete(window)
            # Exercise the actual entry point with the saved private choice,
            # including initialization and the isolated graphics preflight.
            settings.set_many(dict(theme='sculpt',component_images=False))
            startup_log=args.output/'persisted-startup.log'
            with startup_log.open('w') as stream:
                process=subprocess.Popen([sys.executable,'-m','vitalux'],cwd=root,
                    stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                try:
                    deadline=time.monotonic()+25
                    while time.monotonic()<deadline:
                        if 'native 3D surface initialized' in startup_log.read_text(errors='replace'):break
                        if process.poll() is not None:raise AssertionError(startup_log.read_text(errors='replace')[-4000:])
                        time.sleep(.05)
                    else:raise AssertionError(startup_log.read_text(errors='replace')[-4000:])
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid,signal.SIGTERM)
                        try:process.wait(timeout=5)
                        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            report=dict(platform=app.platformName(),cycles=results,driver_failure_safe=True,persisted_startup=True)
            (args.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps(report),flush=True)


if __name__=='__main__':main()
