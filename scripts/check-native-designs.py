"""Exercise public native geometry and private camera/depth with real Qt windows."""
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
    with tempfile.TemporaryDirectory(prefix='vitalux-native-designs-') as folder:
        for kind in ('CONFIG','STATE','DATA','CACHE'):os.environ['XDG_'+kind+'_HOME']=str(Path(folder)/kind)
        os.environ['VITALUX_SPEC_OFFLINE']='1'
        from sensor_fixture import load_fixture
        app,sample=load_fixture()
        for disk in sample['disks']:disk.setdefault('fstype','ext4')
        from PySide6.QtCore import Qt,QEvent,QPointF
        from PySide6.QtGui import QPixmap,QMouseEvent,QCursor
        from vitalux import settings,theme,sensors,native_scene
        from vitalux.update_manager import UpdateManager
        from vitalux.window import MainWindow
        def wait_until(predicate,limit=15):
            end=time.monotonic()+limit
            while time.monotonic()<end:
                app.processEvents();time.sleep(.01)
                if predicate():return
            raise AssertionError('Native surface did not reach the expected state')
        settings.set_many(dict(theme='obsidian_gold',motion='off',component_images=False))
        theme.set_mode('obsidian_gold');app.setStyleSheet(theme.stylesheet())
        logo=QPixmap(96,96);logo.fill(Qt.transparent)
        with patch.object(sensors,'collect',return_value=sample):
            window=MainWindow(dict(name='Linux',version='1',color='#71837c'),logo,UpdateManager(),startup_sample=sample,startup_games=[])
            window.resize(1440,1000);window.show()
            pref=dict(window.pages)['Einstellungen'];overview=window.pages[0][1]
            scene=window.centralWidget();native_id=int(window.winId());results=[]
            def ready(host):return host.view is not None and host.view.ready and not host._frame.isNull()
            def move_pointer(x,y):
                local=QPointF(scene.width()*x,scene.height()*y)
                global_point=scene.mapToGlobal(local.toPoint())
                if app.platformName()=='xcb' and scene.screen().geometry().contains(global_point):
                    QCursor.setPos(global_point)
                    wait_until(lambda:scene.native_background.target_pointer[0]>.8,3)
                    return True
                event=QMouseEvent(QEvent.MouseMove,local,QPointF(global_point),Qt.NoButton,Qt.NoButton,Qt.NoModifier)
                app.sendEvent(scene,event)
                return False
            try:
                assert {tile.key for tile in pref.design_tiles}==set(theme_key for theme_key,_ in theme.CHOICES)
                assert 'sculpt' in dict(theme.CHOICES) and 'light' not in dict(theme.CHOICES)
                pref.select_design('sculpt')
                wait_until(lambda:hasattr(overview,'sculpt_host') and ready(overview.sculpt_host))
                host=overview.sculpt_host
                assert int(window.winId())==native_id
                assert host.view.context().format().majorVersion()>=3
                frame=host.view.grabFramebuffer()
                assert len({frame.pixel(x,y) for y in range(0,frame.height(),8) for x in range(0,frame.width(),8)})>40
                window.grab().save(str(args.output/'sculpt-overview.png'))
                tile=next(t for t in pref.design_tiles if t.key=='sculpt');tile.resize(220,112)
                tile.grab().save(str(args.output/'sculpt-tile.png'))
                pref.motion_combo.setCurrentIndex(pref.motion_combo.findData('smooth'));host.set_load(75)
                wait_until(lambda:host.frame_timer.isActive())
                window._switch_page(1);wait_until(lambda:not host.frame_timer.isActive())
                window._switch_page(0)
                for width in (1440,900):
                    window.resize(width,1000 if width==1440 else 780)
                    pref.search.setText('td')
                    wait_until(lambda:hasattr(scene,'native_background') and ready(scene.native_background))
                    background=scene.native_background
                    assert theme.mode()=='nexus' and int(window.winId())==native_id
                    assert overview.sculpt_host.view is None
                    assert not background._tool.windowHandle().isExposed(),'Preflight/rendering tool became visible'
                    settings.set('motion','smooth');background.enable(True)
                    wait_until(lambda:background.frame_timer.isActive())
                    before=background._frame.copy();geometry=(overview.board.geometry(),window.nav_buttons[0].geometry())
                    real_pointer=move_pointer(.97,.12)
                    assert background.target_pointer[0]>.8 and background.pointer[0]<background.target_pointer[0],'Camera jumped directly to the pointer'
                    wait_until(lambda:background.pointer[0]>.5)
                    assert background._frame!=before,'Mouse movement did not change the actual 3D pixels'
                    assert geometry==(overview.board.geometry(),window.nav_buttons[0].geometry()),'Pointer moved hit targets'
                    window.grab().save(str(args.output/('nexus-'+str(width)+'.png')))
                    window._switch_page(1)
                    assert background.frame_timer.isActive(),'Global background disappeared outside Overview'
                    window.hide();wait_until(lambda:not background.frame_timer.isActive())
                    window.show();wait_until(lambda:background.frame_timer.isActive())
                    pref.motion_combo.setCurrentIndex(pref.motion_combo.findData('off'))
                    wait_until(lambda:not background.frame_timer.isActive())
                    pref.motion_combo.setCurrentIndex(pref.motion_combo.findData('smooth'))
                    wait_until(lambda:background.frame_timer.isActive())
                    pref.motion_combo.setCurrentIndex(pref.motion_combo.findData('reduced'))
                    wait_until(lambda:background.frame_timer.interval()==80)
                    pref.motion_combo.setCurrentIndex(pref.motion_combo.findData('smooth'))
                    settings.set('ultra_eco',True);window.apply_appearance()
                    assert theme.mode()=='minimal' and background.view is None
                    settings.set('ultra_eco',False);window.apply_appearance()
                    wait_until(lambda:ready(background))
                    pref.select_design('glass');app.processEvents();app.sendPostedEvents(None,QEvent.DeferredDelete)
                    assert background.view is None and theme.mode()=='glass'
                    window._switch_page(0)
                    results.append(dict(width=width,logo_geometry=True,real_camera_pixels=True,
                        smooth_pointer=True,stable_hit_targets=True,native_window_preserved=True,
                        global_background=True,hidden_animation_paused=True,motion_toggle=True,eco_restore=True,
                        native_pointer_warp=real_pointer))
                for key,module in (('sculpt','vitalux.sculpt_scene'),('nexus','vitalux.nexus_scene')):
                    with patch.dict(native_scene._probe_results,{module:(False,'test unavailable driver')}):
                        if key=='nexus':pref.search.setText('td')
                        else:pref.select_design(key)
                        app.processEvents();assert theme.mode()==key
                        host=overview.sculpt_host if key=='sculpt' else scene.native_background
                        assert host.view is None
                        if key=='sculpt':assert host.notice.isVisible()
                        pref.select_design('obsidian_gold')
                pref.search.setText('td');wait_until(lambda:ready(scene.native_background))
            finally:
                window.quit_from_tray();wait_until(lambda:not window.isVisible())
                assert scene.native_background.view is None,'Background survived orderly shutdown'
                assert overview.sculpt_host.view is None,'Studio surface survived orderly shutdown'
                from vitalux.lifecycle import stop_product_workers,product_workers
                stop_product_workers()
                for worker in product_workers():worker.pool.waitForDone()
                import shiboken6
                window.sampler.stop();window.sampler.wait()
                shiboken6.delete(window._mini_hud);shiboken6.delete(window)
            for design in ('sculpt','nexus'):
                settings.set_many(dict(theme=design,component_images=False,motion='off'))
                startup_log=args.output/(design+'-startup.log')
                with startup_log.open('w') as stream:
                    process=subprocess.Popen([sys.executable,'-m','vitalux'],cwd=root,stdout=stream,
                                             stderr=subprocess.STDOUT,start_new_session=True)
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
            report=dict(platform=app.platformName(),cycles=results,public_tile=True,
                        driver_failures_safe=True,persisted_startup=['sculpt','nexus'],orderly_native_disposal=True)
            (args.output/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
