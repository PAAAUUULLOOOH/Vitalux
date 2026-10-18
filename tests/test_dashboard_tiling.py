"""Dashboard gap filling with unchanged physical spacing."""
import os
import sys

sys.path.insert(0, os.getcwd())
from vitalux.dashboard_model import DEFAULT, GAP, ORDER, grid_pack, intersect, normalize_order


def check_layout(layout, columns):
    for key, (x, y, w, h) in layout.items():
        assert 0 <= x < columns and x + w <= columns, (key, layout)
        assert y >= 0 and w > 0 and h >= DEFAULT[key][3]
    keys = list(layout)
    for i, key in enumerate(keys):
        for other in keys[i+1:]:
            assert not intersect(layout[key], layout[other]), (key, other, layout)
    # Logical row widths always span the viewport, with 14px gaps in _frame.
    for y in set(p[1] for p in layout.values()):
        row = sorted((v for v in layout.values() if v[1] == y), key=lambda v: v[0])
        assert row[0][0] == 0 and sum(v[2] for v in row) == columns, row
        assert len({v[3] for v in row}) == 1
        for left, right in zip(row, row[1:]):
            assert left[0] + left[2] == right[0]
            pixel_gap = round(right[0]*100) - round((left[0]+left[2])*100-GAP)
            assert pixel_gap == GAP


def run():
    assert GAP == 14
    assert grid_pack(ORDER, (), 12) == DEFAULT
    for columns in (3, 6, 12):
        for cut in range(len(ORDER)+1):
            check_layout(grid_pack(ORDER, ORDER[:cut], columns), columns)
        for hidden in ((), ('gpu', 'ram'), ('network', 'health')):
            check_layout(grid_pack(ORDER, hidden, columns), columns)
    custom = normalize_order(['cpu','hero','gpu'])
    assert custom[:3] == ['cpu','hero','gpu']
    variants = [
        ['hero','graph_load','cpu','graph_net','network','drives','gpu','ram','disk'],
        list(reversed(ORDER)), list(ORDER[2:])+list(ORDER[:2]),
    ]
    for order in variants:
        for columns in (3,6,12):
            check_layout(grid_pack(order, (), columns), columns)
    assert grid_pack(['cpu'], (), 12)['cpu'][2] == 12
    row = grid_pack(['graph_load','cpu'], (), 6)
    assert row['graph_load'][2] + row['cpu'][2] == 6
    assert grid_pack(ORDER, (), 12) == grid_pack(ORDER, (), 12)
    print('Dashboard fills row space; fixed 14px gaps: OK')


if __name__ == '__main__':
    run()
