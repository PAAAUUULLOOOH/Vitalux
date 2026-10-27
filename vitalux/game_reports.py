"""Streaming MangoHud frame analysis; honest statistics and bounded plot data."""
from array import array
import csv
import heapq
import math
import re
from pathlib import Path

MAX_FRAMES = 8_000_000
MAX_LOG_BYTES = 1024 * 1024 * 1024
MAX_PLOT_POINTS = 4096
HARDWARE = ('cpu_load', 'gpu_load', 'cpu_temp', 'gpu_temp', 'gpu_vram_used',
            'gpu_power', 'cpu_power', 'ram_used', 'cpu_mhz', 'gpu_core_clock')


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError, OverflowError):
        return None


def _compress(points):
    compact = []
    for index in range(0, len(points), 4):
        group = points[index:index+4]
        low = min(group, key=lambda row: row[2])
        high = max(group, key=lambda row: row[2])
        compact.extend(sorted([low] if low is high else [low, high], key=lambda row: row[0]))
    return compact


def grade(average, low, long_frame_ratio, target, duration, complete=True):
    """A target-relative smoothness assessment, not a hardware-health verdict."""
    if not complete:
        return 'incomplete'
    if duration < 30 or average is None or low is None:
        return 'insufficient'
    if average >= target*.99 and low >= target*.95 and long_frame_ratio <= .01:
        return 'excellent'
    if average >= target*.90 and low >= target*.70 and long_frame_ratio <= .03:
        return 'good'
    if average >= target*.70 and low >= target*.45 and long_frame_ratio <= .08:
        return 'adequate'
    return 'improve'


def analyze(paths, *, target_fps=60, complete=True, per_frame=True, cancelled=None):
    """Read supported MangoHud CSV versions without loading whole files as text.

    Average FPS = frame count / sum of frame times. Lows use the average of
    the slowest ceil(N*p) frame times, never averages of sampled FPS readings.
    All valid frames enter statistics; only the displayed plot is condensed.
    """
    target = number(target_fps)
    target = max(20., min(1000., target if target and target > 0 else 60.))
    frames = array('f')
    points, maxima, sources, warnings = [], {}, [], []
    frame_time_sum, clock, long_frames, invalid = 0., 0., 0, 0
    limited = False
    for source in paths:
        source = Path(source)
        if source.name.endswith('_summary.csv'):
            continue
        accepted=0
        try:
            if source.stat().st_size > MAX_LOG_BYTES:
                warnings.append('log_too_large')
                complete = False
                continue
            header, last_elapsed, first_elapsed, offset = None, None, None, clock
            first_frame = 0.
            with source.open(encoding='utf-8-sig', errors='replace', newline='') as stream:
                for row in csv.reader(stream):
                    if cancelled is not None and cancelled.is_set():
                        raise InterruptedError('Game report analysis cancelled')
                    if len(row) > 128 or any(len(value) > 100000 for value in row):
                        invalid += 1
                        continue
                    normalized = [value.strip().casefold() for value in row]
                    if 'fps' in normalized and 'frametime' in normalized:
                        header = normalized
                        continue
                    if header is None or len(row) != len(header):
                        continue
                    values = dict(zip(header, row))
                    milliseconds = number(values.get('frametime'))
                    if milliseconds is None or not 0 < milliseconds <= 60000:
                        invalid += 1
                        continue
                    if len(frames) >= MAX_FRAMES:
                        limited = True
                        break
                    elapsed = number(values.get('elapsed'))
                    if elapsed is not None and elapsed >= 0:
                        elapsed /= 1e9  # MangoHud CSV elapsed is nanoseconds.
                        if last_elapsed is not None and elapsed < last_elapsed:
                            invalid += 1
                            continue
                        if first_elapsed is None:
                            first_elapsed = elapsed
                            first_frame = milliseconds/1000
                        clock = offset + elapsed-first_elapsed+first_frame
                        last_elapsed = elapsed
                    else:
                        clock += milliseconds/1000
                    frames.append(milliseconds)
                    frame_time_sum += milliseconds
                    long_frames += milliseconds > max(50., 2000/target)
                    accepted += 1
                    points.append([round(clock, 5), 1000/milliseconds, milliseconds])
                    if len(points) >= MAX_PLOT_POINTS*2:
                        points = _compress(points)
                    for field in HARDWARE:
                        value = number(values.get(field))
                        if value is not None and value >= 0:
                            if field.endswith('_temp') and value > 300:
                                continue
                            if field.endswith('_load') and value > 100:
                                continue
                            maxima[field] = max(value, maxima.get(field, value))
        except InterruptedError:
            raise
        except (OSError,csv.Error):
            complete=False
            warnings.append('unreadable_log')
        if accepted:
            sources.append(source.name)
        if limited:
            break
    if not frames:
        return dict(schema=1, frames=0, duration=0., average_fps=None, low_1=None,
                    low_01=None, grade='insufficient', target_fps=target, plot=[],
                    maxima=maxima, warnings=list(dict.fromkeys(warnings+['no_frames'])),
                    complete=False, per_frame=per_frame, source_files=sources)
    count = len(frames)

    def low(fraction, minimum):
        if not per_frame or count < minimum:
            return None
        worst = heapq.nlargest(max(1, math.ceil(count*fraction)), frames)
        return 1000/(math.fsum(worst)/len(worst))

    average = count*1000/frame_time_sum
    low1, low01 = low(.01, 100), low(.001, 10000)
    if limited:
        warnings.append('frame_limit')
    if invalid:
        warnings.append('invalid_rows')
    if not per_frame:
        warnings.append('sampled_log')
    complete = bool(complete and not limited and invalid <= max(2, count*.01))
    while len(points) > MAX_PLOT_POINTS:
        points = _compress(points)
    result = dict(schema=1, frames=count, duration=clock, average_fps=average,
                  low_1=low1, low_01=low01, target_fps=target,
                  long_frames=long_frames, long_frame_ratio=long_frames/count,
                  grade=grade(average, low1, long_frames/count, target, clock, complete),
                  plot=points, maxima=maxima, complete=complete,
                  per_frame=bool(per_frame), invalid_rows=invalid,
                  warnings=list(dict.fromkeys(warnings)), source_files=sources)
    if not per_frame:
        result['grade'] = 'insufficient'
    return result


def analyze_session(paths, **options):
    """Keep different graphics executables out of the same FPS statistics.

    MangoHud can log both a game's launcher and its actual renderer. Combine
    recording segments of one executable; select the longest recorded stream
    if several executables were present and disclose that choice in the report.
    """
    groups={}
    for path in paths:
        path=Path(path)
        if path.name.endswith('_summary.csv'):continue
        match=re.match(r'^(.*)_\d{4}-\d{2}-\d{2}_\d{2}[-:]\d{2}[-:]\d{2}(?:[._-].*)?\.csv$',path.name)
        process=match[1] if match else path.stem
        groups.setdefault(process,[]).append(path)
    if not groups:return analyze([],**options)
    best=None
    for process,files in groups.items():
        report=analyze(sorted(files),**options)
        report['source_process']=process
        if best is None or (report['duration'],report['frames'])>(best['duration'],best['frames']):
            best=report
    if len(groups)>1:
        best['warnings'].append('multiple_graphics_processes')
        best['other_source_processes']=[name for name in groups if name!=best['source_process']]
    return best
