"""Build the approved Vitalux branding as standalone vector assets.

The checked-in outlined geometry and palette file are the source of truth.
The builder uses only the Python standard library; no tracing tools or fonts
are needed to rebuild the native and standalone animated vectors.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT/'assets/brand'
CONFIG = json.loads((BRAND/'palettes.json').read_text())
SVG = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG)
GEOMETRY = json.loads((BRAND / 'geometry.json').read_text())
POINTS = CONFIG['geometry']['waveform']
WAVE = 'M ' + ' L '.join(f'{x},{y}' for x, y in POINTS)
LENGTH = sum(math.dist(a, b) for a, b in zip(POINTS, POINTS[1:]))


def rgb(hex_color):
    return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))


def mix(a, b, amount):
    return '#' + ''.join(f'{round(x*(1-amount)+y*amount):02x}'
                        for x, y in zip(rgb(a), rgb(b)))


PALETTES = CONFIG['variants']


def node(parent, tag, **attributes):
    return ET.SubElement(parent, f'{{{SVG}}}{tag}',
                         {key.replace('_', '-'): str(value)
                          for key, value in attributes.items()})


def gradient(defs, ident, stops, *, radial=False, **attributes):
    result = node(defs, 'radialGradient' if radial else 'linearGradient',
                  id=ident, **attributes)
    for item in stops:
        position, color, *opacity = item
        attrs = dict(offset=position, stop_color=color)
        if opacity:
            attrs['stop_opacity'] = opacity[0]
        node(result, 'stop', **attrs)
    return result


def document(kind, pal, viewbox, animated):
    root = ET.Element(f'{{{SVG}}}svg', {
        'width': '256' if kind == 'pulse' else '560',
        'height': '256' if kind == 'pulse' else str(round(560*viewbox[3]/viewbox[2], 2)),
        'viewBox': ' '.join(map(str, viewbox)), 'role': 'img',
        'aria-labelledby': 'brand-title brand-description',
        'data-vitalux-brand-version': 'v0.9.5.8',
        'data-motion': 'animated' if animated else 'static',
    })
    node(root, 'title', id='brand-title').text = f"Vitalux {kind} — {pal['name']}"
    node(root, 'desc', id='brand-description').text = (
        'Approved slim outer arcs, smoked-glass lens and independent heartbeat.'
        if kind == 'pulse' else
        'Approved title-case Vitalux lettering, converted to vector outlines; no font dependency.'
    )
    return root, node(root, 'defs')


def logo(pal, animated=False):
    root, defs = document('pulse', pal, [0, 0, 1254, 1254], animated)
    gradient(defs, 'outer-metal', [
        (0, pal['spec']), (.12, pal['top']), (.29, pal['mid']),
        (.47, pal['low']), (.67, pal['top']), (.83, pal['mid']), (1, pal['top'])],
        gradientUnits='userSpaceOnUse', x1=180, y1=80, x2=1070, y2=1120)
    gradient(defs, 'outer-edge', [(0, pal['spec']), (.48, pal['low']),
                                 (.72, pal['top']), (1, pal['spec'])],
             gradientUnits='userSpaceOnUse', x1=140, y1=100, x2=1070, y2=1160)
    gradient(defs, 'glass', [(0, mix(pal['secondary'], '#292820', .88)),
                              (.31, mix(pal['low'], '#151515', .88)),
                              (.67, '#121211'), (1, '#08090b')],
             radial=True, cx='36%', cy='24%', r='83%')
    gradient(defs, 'metal-reflection', [(0, pal['spec'], .34),
                                        (.42, pal['spec'], .015),
                                        (.78, pal['top'], .11), (1, pal['top'], 0)],
             radial=True, cx='19%', cy='13%', r='90%')
    gradient(defs, 'pulse-aura', [(0, pal['accent'], .13),
                                  (.55, pal['accent'], .035), (1, pal['accent'], 0)],
             radial=True, cx='50%', cy='50%', r='50%')
    gradient(defs, 'glass-reflection', [(0, pal['spec'], .12),
                                       (.5, pal['top'], .025), (1, pal['top'], 0)],
             x1=0, y1=0, x2=1, y2=1)
    gradient(defs, 'lens-metal', [(0, pal['spec']), (.19, pal['mid']),
                                  (.53, pal['low']), (.79, pal['mid']), (1, pal['top'])],
             x1='0%', y1='0%', x2='100%', y2='100%')
    gradient(defs, 'pulse-metal', [(0, mix(pal['low'], pal['mid'], .26)),
                                   (.48, pal['low']), (.82, pal['mid']),
                                   (1, mix(pal['low'], pal['mid'], .35))],
             gradientUnits='userSpaceOnUse', x1=320, y1=460, x2=900, y2=790)
    gradient(defs, 'pulse-light', [(0, pal['mid']), (.48, pal['top']), (1, pal['spec'])],
             gradientUnits='userSpaceOnUse', x1=318, y1=616, x2=939, y2=616)

    lens = node(root, 'g', id='stationary-lens')
    node(lens, 'circle', cx=634, cy=608, r=384, fill='url(#glass)',
         stroke='url(#lens-metal)', stroke_width=17)
    node(lens, 'circle', cx=634, cy=608, r=367, fill='none',
         stroke='#08090b', stroke_width=7)
    node(lens, 'path', d='M 300,464 C 348,241 655,205 861,323 C 644,248 460,330 300,464 Z',
         fill='url(#glass-reflection)')
    node(lens, 'ellipse', cx=634, cy=617, rx=295, ry=240, fill='url(#pulse-aura)')

    rotor = node(root, 'g', id='outer-bands', data_rotation_center='634 608',
                 data_period_seconds=48)
    shape = GEOMETRY['outer_bands']['path']
    node(rotor, 'path', d=shape, fill=pal['low'], fill_rule='evenodd',
         transform='translate(0 2.6)', stroke=pal['low'], stroke_width=1)
    node(rotor, 'path', d=shape, fill='url(#outer-metal)', fill_rule='evenodd',
         stroke='url(#outer-edge)', stroke_width=3.2, stroke_linejoin='round')
    node(rotor, 'path', d=shape, fill='url(#metal-reflection)', fill_rule='evenodd')
    if animated:
        node(rotor, 'animateTransform', attributeName='transform', type='rotate',
             values='0 634 608;360 634 608', dur='48s', repeatCount='indefinite',
             calcMode='linear')

    pulse = node(root, 'g', id='pulse-core', fill='none', stroke_linecap='round',
                 stroke_linejoin='round', data_period_seconds=2.4)
    node(pulse, 'path', d=WAVE, stroke=mix(pal['low'], '#0a0907', .62),
         stroke_width=77, opacity=.72)
    node(pulse, 'path', d=WAVE, stroke='url(#lens-metal)', stroke_width=65)
    node(pulse, 'path', id='pulse-baseline', d=WAVE, stroke='url(#pulse-metal)', stroke_width=55)
    trail = node(pulse, 'g', id='pulse-trail', opacity=0)
    for ident, width, fraction, color, opacity in (
            ('pulse-halo', 65, .24, pal['top'], .11),
            ('pulse-signal', 41, .24, 'url(#pulse-light)', .94),
            ('pulse-leading-edge', 13, .055, pal['spec'], .96)):
        length = LENGTH*fraction
        child = node(trail, 'path', id=ident, d=WAVE, stroke=color,
                     stroke_width=width, opacity=opacity,
                     stroke_dasharray=f'{length:.4f} {LENGTH*2:.4f}',
                     stroke_dashoffset=f'{length:.4f}')
        if animated:
            end = -(LENGTH + LENGTH*.24-length)
            node(child, 'animate', attributeName='stroke-dashoffset',
                 values=f'{length:.4f};{end:.4f};{end:.4f}', keyTimes='0;0.78;1',
                 dur='2.4s', repeatCount='indefinite', calcMode='linear')
    if animated:
        node(trail, 'animate', attributeName='opacity', values='0;1;1;0;0',
             keyTimes='0;0.035;0.70;0.78;1', dur='2.4s', repeatCount='indefinite')
    return root


def wordmark(pal, animated=False, light=False):
    viewbox = GEOMETRY['wordmark']['viewbox']
    _, _, width, height = viewbox
    root, defs = document('wordmark', pal, viewbox, animated)
    top, mid, low = pal['top'], pal['mid'], pal['low']
    if light:
        top, mid, low = (mix(pal['accent'], '#142238', .56),
                         mix(pal['accent'], '#152137', .33), pal['low'])
    gradient(defs, 'letter-metal', [(0, top), (.15, mix(top, mid, .16)),
                                    (.36, mid), (.49, mix(mid, top, .27)),
                                    (.59, mix(mid, top, .12)), (.83, mix(mid, low, .57)),
                                    (1, low)],
             gradientUnits='userSpaceOnUse', x1=0, y1=0, x2=0, y2=height)
    gradient(defs, 'letter-edge', [(0, pal['spec'] if not light else top),
                                   (.4, mid), (1, low)],
             gradientUnits='userSpaceOnUse', x1=0, y1=0, x2=0, y2=height)
    shape = GEOMETRY['wordmark']['path']
    node(root, 'path', d=shape, fill=low, fill_rule='evenodd', transform='translate(0 3)')
    node(root, 'path', id='wordmark-outline', d=shape, fill='url(#letter-metal)',
         stroke='url(#letter-edge)', stroke_width=5.4, stroke_linejoin='round',
         fill_rule='evenodd')
    sweep = gradient(defs, 'wordmark-sweep', [
        (0, pal['spec'], 0), (.20, pal['spec'], .025),
        (.42, pal['spec'], .16), (.51, pal['spec'], .40),
        (.62, pal['spec'], .18), (.85, pal['spec'], .025), (1, pal['spec'], 0)],
        gradientUnits='userSpaceOnUse', x1=-280, y1=0, x2=280, y2=height*.6)
    glint = node(root, 'path', id='wordmark-glint', d=shape,
                 fill='url(#wordmark-sweep)', fill_rule='evenodd', opacity=0,
                 data_period_seconds=8)
    if animated:
        end = width+500
        node(sweep, 'animateTransform', attributeName='gradientTransform', type='translate',
             values=f'-500 0;{end} 0;{end} 0', keyTimes='0;0.46;1',
             calcMode='spline', keySplines='.42 0 .58 1;0 0 1 1',
             dur='8s', repeatCount='indefinite')
        node(glint, 'animate', attributeName='opacity', values='0;1;1;0;0',
             keyTimes='0;0.02;0.43;0.46;1', dur='8s', repeatCount='indefinite')
    return root


def write(path, root):
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space='  ')
    path.write_bytes(ET.tostring(root, encoding='utf-8', xml_declaration=True)+b'\n')


def main():
    files = []
    for animated in (False, True):
        directory = BRAND/'animated' if animated else BRAND
        prefix = directory if animated else ROOT/'assets'
        for key, pal in PALETTES.items():
            for kind, builder in (('pulse', logo), ('wordmark', wordmark)):
                path = directory / f'vitalux-{kind}-{key}.svg'
                write(path, builder(pal, animated))
                files.append(path)
            if key not in ('gold', 'obsidian-gold', 'black-glass-gold', 'champagne-glass', 'aurora-gold'):
                path = directory / f'vitalux-wordmark-{key}-light.svg'
                write(path, wordmark(pal, animated, light=True))
                files.append(path)
        for name, builder, kwargs in (
                ('vitalux-pulse.svg', logo, {}),
                ('vitalux-wordmark.svg', wordmark, {}),
                ('vitalux-wordmark-light.svg', wordmark, {'light': True})):
            path = prefix/name
            write(path, builder(PALETTES['gold'], animated, **kwargs))
            files.append(path)
    manifest = []
    for path in files:
        data = path.read_bytes()
        assert b'<image' not in data and b'data:image' not in data and b'<text' not in data
        manifest.append(dict(file=str(path.relative_to(ROOT)), bytes=len(data),
                             sha256=hashlib.sha256(data).hexdigest()))
    (BRAND/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Built {len(files)} genuine vector SVGs: static and animated variants.')


if __name__ == '__main__':
    main()
