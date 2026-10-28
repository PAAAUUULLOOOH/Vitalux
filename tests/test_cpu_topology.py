"""Sparse/offline CPU IDs and complete, expanding numerical grids."""
import os
import sys
import tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication, QScrollArea
from vitalux.cpu_topology import cpu_ids, logical_cpus
from vitalux import i18n, theme
from vitalux.component_pages import CpuPage

assert cpu_ids('0-3,8,10-11') == [0, 1, 2, 3, 8, 10, 11]
assert cpu_ids('bad,1000000-2000000') == []
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root/'present').write_text('0-3,8,10-11')
    (root/'online').write_text('0-3,8,11')
    stat = root/'stat'
    stat.write_text('\n'.join(f'cpu{i} 1 2 3' for i in (0, 1, 2, 3, 8, 11)))
    for ident in (0, 1, 2, 3, 8, 10, 11):
        topology = root/f'cpu{ident}'/'topology'
        topology.mkdir(parents=True)
        (topology/'core_id').write_text(str(ident//2))
        (topology/'physical_package_id').write_text('0')
    entries = logical_cpus([0, 1, 2, 3, 8, 11], str(root), str(stat))
    assert [row['id'] for row in entries] == [0, 1, 2, 3, 8, 10, 11]
    assert entries[4]['usage'] == 8 and entries[5]['usage'] is None
    assert not entries[5]['online'] and entries[-1]['usage'] == 11
    assert entries[0]['usage'] == 0
    fallback = logical_cpus([2, 4], str(root/'missing'), str(root/'missing-stat'))
    assert [row['id'] for row in fallback] == [0, 1]

app = QApplication.instance() or QApplication([])
cpu = dict(model='CPU fixture', cores=64, threads=128, usage=20, temp=None,
           freq=None, freq_max=None, load=[0, 0, 0], per_core=[20]*128,
           logical_cpus=[dict(id=i, usage=None if i == 127 else i%100,
                             online=i != 127, core=i//2, package=0) for i in range(128)])
area = QScrollArea()
area.setWidgetResizable(True)
page = CpuPage()
area.setWidget(page)
for design in ('obsidian_gold', 'quantum_core', 'minimal'):
    theme.set_mode(design)
    app.setStyleSheet(theme.stylesheet())
    for language in ('de', 'en'):
        i18n.set_lang(language)
        for width in (550, 1280):
            area.resize(width, 750)
            area.show()
            page.refresh({'cpu': cpu}, {'cpu': [20]})
            for _ in range(3): app.processEvents()
            assert len(page.core_meters) == 128
            assert [int(m.name.text().split()[1]) for m in page.core_meters] == list(range(128))
            for index, meter in enumerate(page.core_meters):
                assert page.cores_grid.getItemPosition(page.cores_grid.indexOf(meter))[:2] == divmod(index, page._core_columns)
                assert meter.height() >= meter.minimumSizeHint().height()
            assert page.core_meters[-1].value.text() == 'Offline'
            area.verticalScrollBar().setValue(area.verticalScrollBar().maximum())
            app.processEvents()
            last = page.core_meters[-1]
            assert last.mapTo(area.viewport(), last.rect().bottomLeft()).y() <= area.viewport().height()
            assert area.horizontalScrollBar().maximum() == 0,(design,language,width,page.width(),page.minimumWidth(),page._core_columns)
cpu['logical_cpus'] = cpu['logical_cpus'][:4]
page.refresh({'cpu': cpu}, {'cpu': [20]})
app.processEvents()
assert len(page.core_meters) == 4
area.close()
print('Sparse and offline CPU identities, all 128 entries, numerical order, responsive height and scrolling PASS')
