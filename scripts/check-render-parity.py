#!/usr/bin/env python3
"""Compare native vector/material rendering with a reference checkout at 1/1.5/2x."""
import argparse,json,os,subprocess,sys,tempfile
from pathlib import Path

def capture(source, output):
    sys.path.insert(0,str(source))
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout
    from vitalux import theme,settings
    from vitalux.brand import PulseCore
    from vitalux.glass import AmbientScene,GlassSidebar
    app=QApplication([])
    output.mkdir(parents=True,exist_ok=True)
    for key,_ in theme.CHOICES:
        settings.set_many(dict(theme=key,accent='design_default',motion='smooth',background_style='theme_default'))
        theme.set_mode(key);theme.set_accent('#4f8cff');app.setStyleSheet(theme.stylesheet())
        host=QWidget();layout=QVBoxLayout(host);pulse=PulseCore(152);layout.addWidget(pulse)
        host.show();app.processEvents();pulse._timer.stop()
        for phase in (0,73,249):
            pulse._display_cpu=45;pulse._heartbeat_phase=.23;pulse._phase=phase
            host.grab().save(str(output/(key+'-logo-'+str(phase)+'.png')))
        host.close()
        scene=AmbientScene();scene.resize(620,480)
        sidebar=GlassSidebar(scene);sidebar.setGeometry(0,0,245,480)
        scene.show();app.processEvents()
        scene.grab().save(str(output/(key+'-sidebar.png')))
        scene.close();host.deleteLater();scene.deleteLater();app.processEvents()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--reference',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--capture',action='store_true')
    args=parser.parse_args()
    if args.capture:
        capture(args.source.resolve(),args.output.resolve());return
    if not args.reference:parser.error('--reference is required for comparison')
    from PySide6.QtGui import QImage
    results=[]
    for scale in ('1','1.5','2'):
        paths=[]
        for name,root in (('reference',args.reference),('current',args.source)):
            output=args.output/scale/name;paths.append(output)
            with tempfile.TemporaryDirectory(prefix='vitalux-render-') as directory:
                env=dict(os.environ,QT_QPA_PLATFORM='offscreen',QT_SCALE_FACTOR=scale,VITALUX_SPEC_OFFLINE='1')
                for kind in ('CONFIG','STATE','CACHE','DATA'):env['XDG_'+kind+'_HOME']=str(Path(directory)/kind)
                subprocess.run([sys.executable,__file__,'--capture','--source',str(root.resolve()),'--output',str(output.resolve())],env=env,check=True,timeout=90)
        for before in sorted(paths[0].glob('*.png')):
            after=paths[1]/before.name
            a=QImage(str(before)).convertToFormat(QImage.Format_RGBA8888)
            b=QImage(str(after)).convertToFormat(QImage.Format_RGBA8888)
            assert not a.isNull() and a.size()==b.size(),(scale,before.name,a.size(),b.size())
            maximum=0 if a==b else max(abs(x-y) for x,y in zip(a.constBits(),b.constBits()))
            # Native raster caching may round a composited channel by one level.
            assert maximum<=1,(scale,before.name,maximum)
            results.append(dict(scale=scale,image=before.name,max_channel_difference=maximum))
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'{len(results)} reference comparisons passed at 1/1.5/2x')
if __name__=='__main__':main()
