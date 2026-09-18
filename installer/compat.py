# OpenATV 8 safe-candidate maintained compatibility source
# -*- coding: utf-8 -*-
from __future__ import print_function

import glob
import json
import os
import re
import sys

SKIN_DEFAULT = '/usr/share/enigma2/CineView_FHD'
E2PY = '/usr/lib/enigma2/python'

BUILTIN_RENDERERS = set(['Label', 'FixedLabel', 'Pixmap', 'Listbox', 'Progress', 'Pig', 'Canvas'])
OPTIONAL_CONVERTERS = ('ClientsStreaming', 'RotorPosition', 'SensorToText', 'CryptoInfo')
OPTIONAL_RENDERERS = ('PositionGauge', 'VideoSize', 'ChannelNumber')


def exists_component(kind, name, root=E2PY):
    if kind == 'Renderer' and name in BUILTIN_RENDERERS:
        return True
    base = os.path.join(root, 'Components', kind, name)
    return bool(glob.glob(base + '.py*'))


def detect_image():
    bits = []
    for p in ('/etc/image-version', '/etc/issue', '/etc/os-release', '/etc/hostname', '/etc/apt/sources.list'):
        try:
            bits.append(open(p, 'r').read())
        except Exception:
            pass
    text = ' '.join(bits).lower()
    if 'openpli' in text:
        fam = 'openpli'
    elif any(x in text for x in ('dreambox', 'dreamos', 'gemini', 'merlin')):
        fam = 'dreamos'
    elif any(x in text for x in ('openatv', 'openvix', 'openbh', 'openblackhole', 'opendroid', 'openspa', 'pure2', 'puree2', 'egami', 'teamblue', 'openhdf', 'nonsolosat', 'opentr', 'cobralib', 'satlodge', 'foxbob')):
        fam = 'oealliance'
    else:
        fam = 'generic'
    name = 'unknown'
    for token in ('openatv', 'openvix', 'openpli', 'openbh', 'openblackhole', 'opendroid', 'openspa', 'pure2', 'puree2', 'egami', 'teamblue', 'openhdf', 'dreamos', 'gemini', 'merlin', 'vti'):
        if token in text:
            name = token
            break
    return fam, name


def strip_widget_by_converter(data, converter):
    needle1 = 'type="%s"' % converter
    needle2 = "type='%s'" % converter
    def repl(match):
        block = match.group(0)
        return '\n' if (needle1 in block or needle2 in block) else block
    return re.sub(r'<widget\b[^>]*>.*?</widget>', repl, data, flags=re.S)


def strip_widget_by_renderer(data, renderer):
    needle1 = 'render="%s"' % renderer
    needle2 = "render='%s'" % renderer
    def repl(match):
        block = match.group(0)
        return '\n' if (needle1 in block or needle2 in block) else block
    data = re.sub(r'<widget\b[^>]*>.*?</widget>', repl, data, flags=re.S)
    def repl2(match):
        block = match.group(0)
        return '\n' if (needle1 in block or needle2 in block) else block
    return re.sub(r'<widget\b[^>]*/>', repl2, data, flags=re.S)


def patch_xml(path, component_root=E2PY):
    try:
        data = open(path, 'r').read()
    except Exception:
        return []
    original = data
    actions = []
    _, image_name = detect_image()

    # OpenATV theme colors must remain owned by theme.py. Older CineView
    # compatibility logic forced a fixed SecondInfoBar tint after theme
    # activation, which could override the selected OpenATV theme.
    if image_name != 'openatv':
        data = re.sub(
            r'(<color\s+name=["\']steSecondInfoBG["\']\s+value=["\'])#[0-9A-Fa-f]{8}(["\'])',
            r'\1#B8101214\2',
            data
        )

    # RunningText fallback: only when the image truly lacks the renderer.
    if not exists_component('Renderer', 'RunningText', component_root):
        if 'render="RunningText"' in data or "render='RunningText'" in data:
            data = data.replace('render="RunningText"', 'render="Label"').replace("render='RunningText'", "render='Label'")
            data = re.sub(r'\s+options=["\'][^"\']*["\']', '', data)
            actions.append('RunningText->Label')

    # Use CineView transponder fallbacks only when the image component is absent.
    if not exists_component('Converter', 'PliExtraInfo', component_root):
        data = re.sub(
            r'<convert\s+type=["\']PliExtraInfo["\']>TransponderInfo</convert>',
            '<convert type="CineViewTransponder">Info</convert>',
            data
        )
        actions.append('PliExtraInfo->CineViewTransponder')
    if not exists_component('Converter', 'TransponderInfo', component_root):
        data = re.sub(r'<convert\s+type=["\']TransponderInfo["\']\s*/>', '<convert type="CineViewTransponder">Info</convert>', data)
        data = re.sub(r'<convert\s+type=["\']TransponderInfo["\']>.*?</convert>', '<convert type="CineViewTransponder">Info</convert>', data, flags=re.S)
        actions.append('TransponderInfo->CineViewTransponder')
    if not exists_component('Converter', 'ServiceOrbitalPosition', component_root):
        data = re.sub(r'<convert\s+type=["\']ServiceOrbitalPosition["\']\s*/>', '<convert type="CineViewTransponder">Orbital</convert>', data)
        data = re.sub(r'<convert\s+type=["\']ServiceOrbitalPosition["\']>.*?</convert>', '<convert type="CineViewTransponder">Orbital</convert>', data, flags=re.S)
        actions.append('ServiceOrbitalPosition->CineViewTransponder')

    for name in OPTIONAL_CONVERTERS:
        if not exists_component('Converter', name, component_root) and ('type="%s"' % name in data or "type='%s'" % name in data):
            data = strip_widget_by_converter(data, name)
            actions.append('removed converter:' + name)

    for name in OPTIONAL_RENDERERS:
        if not exists_component('Renderer', name, component_root) and ('render="%s"' % name in data or "render='%s'" % name in data):
            data = strip_widget_by_renderer(data, name)
            actions.append('removed renderer:' + name)

    if data != original:
        open(path, 'w').write(data)
    return actions


def adapt(skin_dir=SKIN_DEFAULT, component_root=E2PY, report_path=None):
    fam, name = detect_image()
    changes = {}
    total = 0
    for root, dirs, files in os.walk(skin_dir):
        for fn in files:
            if not fn.endswith('.xml'):
                continue
            p = os.path.join(root, fn)
            acts = patch_xml(p, component_root)
            if acts:
                changes[os.path.relpath(p, skin_dir)] = acts
                total += 1
    report = {'image_family': fam, 'image_name': name, 'patched_files': total, 'changes': changes}
    if report_path:
        try:
            open(report_path, 'w').write(json.dumps(report, indent=2, sort_keys=True))
        except Exception:
            pass
    return report


if __name__ == '__main__':
    skin = sys.argv[1] if len(sys.argv) > 1 else SKIN_DEFAULT
    component_root = sys.argv[2] if len(sys.argv) > 2 else E2PY
    rpt = sys.argv[3] if len(sys.argv) > 3 else '/tmp/cineview-compat-report.json'
    print(json.dumps(adapt(skin, component_root, rpt), sort_keys=True))
