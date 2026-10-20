#!/usr/bin/env python3
"""Compose the original vector identity in the Obsidian Gold README palette."""
from copy import deepcopy
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PySide6.QtGui import QColor

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
PALETTE = {'#272013': '#242329', '#15120d': '#141419', '#080705': '#08090c',
           '#a67c36': '#706044', '#e7bf65': '#e5c17b', '#f0cb7d': '#d8b774',
           '#fff1c9': '#fff0c8', '#ffe8ae': '#f7eed8'}


def layer(filename, light, prefix):
    source = (ROOT/'assets/brand'/filename).read_text()
    source = re.sub(r'#[0-9a-fA-F]{6}', lambda match: PALETTE.get(match.group().lower(), match.group()), source)
    if light:
        def readable(match):
            ink = QColor(match.group())
            return ink.darker(195).name() if ink.lightnessF() > .43 else ink.name()
        source = re.sub(r'#[0-9a-fA-F]{6}', readable, source)
    root = ET.fromstring(source)
    for node in root.iter():
        if node.get('id'):
            node.set('id', prefix+node.get('id'))
        for key, value in tuple(node.attrib.items()):
            node.set(key, re.sub(r'url\(#([^)]*)\)', lambda match: 'url(#'+prefix+match.group(1)+')', value))
    return [deepcopy(node) for node in root]


for variant in ('dark', 'light'):
    root = ET.Element('{'+NS+'}svg', width='600', height='375', viewBox='0 0 600 375',
                      role='img', attrib={'aria-labelledby': 'title desc'})
    ET.SubElement(root, '{'+NS+'}title', id='title').text = 'Vitalux'
    ET.SubElement(root, '{'+NS+'}desc', id='desc').text = 'Original Vitalux logo and wordmark in Obsidian Gold.'
    for filename, transform, prefix in (('vitalux-pulse-gold.svg', 'translate(185 9) scale(0.9)', 'icon-'),
                                        ('vitalux-wordmark-gold.svg', 'translate(54 261) scale(0.88)', 'mark-')):
        group = ET.SubElement(root, '{'+NS+'}g', transform=transform)
        group.extend(layer(filename, variant == 'light', prefix))
    ET.indent(root)
    (ROOT/'assets'/f'vitalux-readme-{variant}.svg').write_text(ET.tostring(root, encoding='unicode')+'\n')
    print('README identity:', variant)
