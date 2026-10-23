#!/usr/bin/env python3
"""Compose the approved slim identity from its Obsidian Gold vector files."""
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


def layer(filename, light, prefix):
    source = (ROOT/'assets/brand'/filename).read_text()
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


def compose(variant):
    root = ET.Element('{'+NS+'}svg', width='600', height='400', viewBox='0 0 600 400',
                      role='img', attrib={'aria-labelledby': 'title desc'})
    ET.SubElement(root, '{'+NS+'}title', id='title').text = 'Vitalux'
    ET.SubElement(root, '{'+NS+'}desc', id='desc').text = 'Slim circular logo and sculpted uppercase VITALUX wordmark in Obsidian Gold.'
    for filename, transform, prefix in (('vitalux-pulse-obsidian-gold.svg', 'translate(175 8) scale(0.1993620415)', 'icon-'),
                                        ('vitalux-wordmark-obsidian-gold.svg', 'translate(50 282) scale(0.3888024883)', 'mark-')):
        group = ET.SubElement(root, '{'+NS+'}g', transform=transform)
        group.extend(layer('animated/'+filename, variant == 'light', prefix))
    ET.indent(root)
    (ROOT/'assets'/f'vitalux-readme-{variant}-animated.svg').write_text(ET.tostring(root, encoding='unicode')+'\n')
    print('README identity:', variant, 'animated')


for variant in ('dark','light'):
    compose(variant)
