#!/usr/bin/env python3
"""Compare existing overview/chart pixels against the pre-optimization source."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def capture(source, output):
    sys.path.insert(0, str(source))
    # Reuse deterministic, source-controlled sensor fixtures, never host values.
    fixture = source/'tests/test_component_charts.py'
    scope = {'__file__': str(fixture)}
    text = fixture.read_text()
    exec(compile(text[:text.index('with tempfile.TemporaryDirectory()')], str(fixture), 'exec'), scope)
    app, sample = scope['app'], scope['sample']
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QPixmap
    from vitalux import settings, theme, i18n
    from vitalux.pages import OverviewPage
    from vitalux.widgets import Gauge
    try:
        from vitalux.charts import HistoryGraph
    except ImportError:
        from vitalux.widgets import HistoryGraph
    history = {key: [None if i % 113 == 0 else (i*7+index*13) % 100
                     for i in range(900)]
               for index, key in enumerate(('cpu','gpu','ram','net_down','net_up'))}
    output.mkdir(parents=True, exist_ok=True)
    for design in [key for key, _ in theme.CHOICES]+['eclipse_crystal','minimal']:
        settings.set_many(dict(theme=design,motion='off',component_images=False))
        theme.set_mode(design)
        app.setStyleSheet(theme.stylesheet())
        i18n.set_lang('de')
        logo=QPixmap(96,96);logo.fill(Qt.transparent)
        page=OverviewPage(dict(name='Linux',version='1'),logo)
        page.static=dict(kernel='7.3',plasma='6.8',mesa='26.2',session='wayland',arch='x86_64')
        page.resize(1180,1800);page.show();page.refresh(sample,history)
        for _ in range(3):app.processEvents();page.board.refresh_geometry(animate=False)
        for timer in page.findChildren(QTimer):timer.stop()
        for gauge in page.findChildren(Gauge):gauge._render_value=gauge.value
        page.grab().save(str(output/(design+'-overview.png')))
        page.close();page.deleteLater();app.processEvents()
        for mode in ('percent','rate','mixed'):
            graph=HistoryGraph(maxlen=900,mode=mode)
            graph.resize(700,260);graph.horizon_seconds=900
            graph.sample_times=list(range(1793100000,1793100900))
            graph.series_names=['CPU','GPU','RAM']
            graph.series_modes=['percent','temperature','frequency'] if mode=='mixed' else [mode]*3
            graph.series_styles=[Qt.SolidLine,Qt.DashLine,Qt.DotLine]
            graph.set_series([(history[key],tone) for key,tone in
                              zip(('cpu','gpu','ram'),(theme.accent(),theme.secondary_accent(),theme.TEAL))])
            graph.show();app.processEvents()
            for pointer in (None,250.):
                graph._pointer=pointer
                graph.grab().save(str(output/(design+'-'+mode+'-'+str(pointer)+'.png')))
            graph.close();graph.deleteLater();app.processEvents()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--reference',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--capture',action='store_true')
    parser.add_argument('--scales',default='1,1.25,1.5,2')
    parser.add_argument('--compare-only',action='store_true')
    args=parser.parse_args()
    if args.capture:
        capture(args.source.resolve(),args.output.resolve());return
    if not args.reference:parser.error('--reference is required')
    from PySide6.QtGui import QImage
    results=[]
    for scale in args.scales.split(','):
        paths=[]
        for name,root in (('reference',args.reference),('current',args.source)):
            output=args.output/scale/name;paths.append(output)
            if args.compare_only:continue
            with tempfile.TemporaryDirectory(prefix='vitalux-parity-') as directory:
                env=dict(os.environ,QT_QPA_PLATFORM='offscreen',QT_SCALE_FACTOR=scale,VITALUX_SPEC_OFFLINE='1')
                for kind in ('CONFIG','STATE','CACHE','DATA'):env['XDG_'+kind+'_HOME']=str(Path(directory)/kind)
                subprocess.run([sys.executable,__file__,'--capture','--source',str(root.resolve()),
                                '--output',str(output.resolve())],env=env,check=True,timeout=240)
        before_files=sorted(paths[0].glob('*.png'))
        assert len(before_files)==56 and {p.name for p in before_files}=={p.name for p in paths[1].glob('*.png')}
        for before in before_files:
            a,b=(QImage(str(path)).convertToFormat(QImage.Format_RGBA8888)
                 for path in (before,paths[1]/before.name))
            assert not a.isNull() and a.size()==b.size(),(scale,before.name,a.size(),b.size())
            maximum=0 if a==b else max(abs(x-y) for x,y in zip(a.constBits(),b.constBits()))
            assert maximum<=1,(scale,before.name,maximum)
            results.append(dict(scale=scale,image=before.name,max_channel_difference=maximum))
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'{len(results)} existing overview/chart comparisons passed at 1/1.25/1.5/2x')


if __name__=='__main__':main()
