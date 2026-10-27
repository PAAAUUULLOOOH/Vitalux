"""Per-frame lows, complete/incomplete sessions and real MangoHud CSV schemas."""
import math
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vitalux import game_reports as reports

with tempfile.TemporaryDirectory() as folder:
    log = Path(folder)/'game.csv'
    durations = [10.]*9900 + [50.]*100
    elapsed = 0
    with log.open('w') as stream:
        stream.write('v1\n0.8.2\n---SYSTEM INFO---\nos,cpu,gpu,ram,kernel,driver,cpuscheduler\nLinux,CPU,GPU,32,6,driver,sched\n')
        stream.write('fps,frametime,cpu_load,gpu_temp,gpu_vram_used,elapsed\n')
        for value in durations:
            elapsed += round(value*1e6)
            stream.write(f'{1000/value},{value},32,70,5.5,{elapsed}\n')
    result = reports.analyze([log], target_fps=60)
    assert result['frames']==10000 and result['complete']
    assert math.isclose(result['duration'],sum(durations)/1000)
    assert math.isclose(result['average_fps'],10000/(sum(durations)/1000))
    assert math.isclose(result['low_1'],20.) and math.isclose(result['low_01'],20.)
    assert result['maxima']['gpu_temp']==70 and result['maxima']['gpu_vram_used']==5.5
    assert len(result['plot'])<=reports.MAX_PLOT_POINTS
    assert any(row[2]==50 for row in result['plot']), 'A long frame vanished from the condensed plot'
    assert reports.analyze([log],complete=False)['grade']=='incomplete'
    sampled=reports.analyze([log],per_frame=False)
    assert sampled['low_1'] is None and sampled['low_01'] is None and sampled['grade']=='insufficient'
    assert 'sampled_log' in sampled['warnings']
    # MangoHud benchmark summaries are not mistaken for raw frame histories.
    summary=Path(folder)/'game_summary.csv';summary.write_text('0.1% Min FPS,1% Min FPS,Average FPS\n20,20,96\n')
    assert reports.analyze([summary])['frames']==0
    with patch.object(reports,'MAX_FRAMES',500):
        limited=reports.analyze([log]);assert limited['frames']==500 and not limited['complete']
        assert 'frame_limit' in limited['warnings'] and limited['grade']=='incomplete'
    broken=Path(folder)/'broken.csv';broken.write_text('fps,frametime,elapsed\n60,nan,0\n60,-1,1\n60,inf,2\n')
    assert reports.analyze([broken])['average_fps'] is None
    short=Path(folder)/'short.csv';short.write_text('fps,frametime,elapsed\n60,16.666666,16666666\n')
    assert reports.analyze([short])['grade']=='insufficient'
    missing=reports.analyze([Path(folder)/'missing.csv'])
    assert not missing['complete'] and 'unreadable_log' in missing['warnings']
    damaged=Path(folder)/'damaged.csv'
    damaged.write_text('fps,frametime,elapsed\n60,16.6,16600000\n'+'x'*150000)
    partial=reports.analyze([damaged])
    assert partial['frames']==1 and not partial['complete'] and partial['grade']=='incomplete'
    # A launcher's concurrent frames must not inflate the actual game's FPS.
    launcher=Path(folder)/'launcher_2026-10-27_12-00-00.csv'
    launcher.write_text('fps,frametime,elapsed\n1000,1,1000000\n1000,1,2000000\n')
    game=Path(folder)/'game_2026-10-27_12-00-00.csv';game.write_bytes(log.read_bytes())
    segment=Path(folder)/'game_2026-10-27_12-05-00.csv';segment.write_bytes(short.read_bytes())
    selected=reports.analyze_session([launcher,game,segment])
    assert selected['source_process']=='game' and selected['frames']==10001
    assert selected['other_source_processes']==['launcher']
    assert 'multiple_graphics_processes' in selected['warnings']
    assert launcher.name not in selected['source_files']
assert reports.grade(60,58,.001,60,120)=='excellent'
assert reports.grade(132,108,.002,120,120)=='good'
assert reports.grade(50,30,.04,60,120)=='adequate'
assert reports.grade(30,15,.1,60,120)=='improve'
print('MangoHud versioned/raw CSVs, exact frame-time statistics, target-relative grades and honest partial-session handling PASS')
