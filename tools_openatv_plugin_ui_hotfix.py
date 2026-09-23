#!/usr/bin/env python3
from pathlib import Path
import re, sys, xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/usr/share/enigma2/CineView_FHD')

PACKAGE_ACTION = r'''<screen name="PackageAction" title="Plugin Browser Action" position="0,0" size="1920,1080" flags="wfNoBorder">
    <eLabel position="0,0" size="1920,1080" backgroundColor="steThemePrimary" zPosition="0"/>
    <eLabel text="Plugin Manager" position="45,24" size="1830,52" font="Regular;38" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="3"/>
    <eLabel position="35,88" size="1850,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
    <widget source="plugins" render="Listbox" position="45,110" size="1830,800" scrollbarMode="showOnDemand" backgroundColor="steThemePrimary" transparent="1" zPosition="5">
        <convert type="TemplatedMultiContent">
{"template": [
MultiContentEntryPixmapAlphaBlend(pos=(12, 10), size=(72, 60), png=6, flags=BT_SCALE),
MultiContentEntryText(pos=(105, 3), size=(1620, 40), font=0, flags=RT_VALIGN_CENTER, text=2),
MultiContentEntryText(pos=(105, 40), size=(1050, 28), font=1, flags=RT_VALIGN_CENTER, text=3),
MultiContentEntryText(pos=(1180, 40), size=(430, 28), font=1, flags=RT_VALIGN_CENTER | RT_HALIGN_RIGHT, text=5),
MultiContentEntryText(pos=(105, 67), size=(1500, 24), font=2, flags=RT_VALIGN_CENTER, text=4, color=0x00b0b0b0),
MultiContentEntryPixmapAlphaBlend(pos=(1740, 16), size=(54, 54), png=7, flags=BT_SCALE)
],
"fonts": [gFont("Regular", 30), gFont("Regular", 23), gFont("Regular", 20)],
"itemHeight": 96
}
        </convert>
    </widget>
    <widget name="quickselect" position="45,110" size="1830,800" font="Regular;120" foregroundColor="secondFG" halign="center" valign="center" transparent="1" zPosition="8"/>
    <widget name="description" position="55,925" size="1810,55" font="Regular;24" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1" valign="center" zPosition="4"/>
    <eLabel position="35,995" size="1850,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
    <widget source="key_red" render="Label" position="55,1010" size="310,45" backgroundColor="key_red" font="Regular;25" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
    <widget source="key_green" render="Label" position="385,1010" size="310,45" backgroundColor="key_green" font="Regular;25" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
    <widget source="key_yellow" render="Label" position="715,1010" size="310,45" backgroundColor="key_yellow" conditional="key_yellow" font="Regular;25" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
    <widget source="key_help" render="Label" position="1575,1010" size="300,45" backgroundColor="key_back" conditional="key_help" font="Regular;24" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
</screen>'''

PACKAGE_LOG = r'''<screen name="PackageActionLog" title="Plugin Action Log" position="0,0" size="1920,1080" flags="wfNoBorder">
    <eLabel position="0,0" size="1920,1080" backgroundColor="steThemePrimary" zPosition="0"/>
    <eLabel text="Plugin Action Log" position="45,24" size="1830,52" font="Regular;38" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="3"/>
    <eLabel position="35,88" size="1850,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
    <widget name="log" position="45,110" size="1830,850" font="Regular;25" backgroundColor="steThemePrimary" transparent="1"/>
    <eLabel position="35,995" size="1850,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
    <widget source="key_red" render="Label" position="55,1010" size="360,45" backgroundColor="key_red" conditional="key_red" font="Regular;24" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
    <widget source="key_help" render="Label" position="1515,1010" size="360,45" backgroundColor="key_back" conditional="key_help" font="Regular;24" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
</screen>'''

PLUGIN_DOWNLOAD = r'''<screen name="PluginDownloadBrowser" title="Downloadable plugins" position="0,0" size="1920,1080" flags="wfNoBorder">
    <eLabel position="0,0" size="1920,1080" backgroundColor="steThemePrimary" zPosition="0"/>
    <eLabel text="Downloadable plugins" position="45,24" size="1830,52" font="Regular;38" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="3"/>
    <eLabel position="35,88" size="1850,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
    <widget name="text" position="45,105" size="1830,70" zPosition="2" transparent="1" font="Regular;30" foregroundColor="grey" valign="center" halign="center"/>
    <widget name="list" position="45,185" size="1830,805" zPosition="3" transparent="1" scrollbarMode="showOnDemand"/>
    <eLabel position="35,1015" size="1850,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
</screen>'''

def replace_screen(text, name, xml):
    pat = re.compile(r'<screen\b(?=[^>]*\bname=["\']%s["\'])[^>]*>.*?</screen>' % re.escape(name), re.S)
    if pat.search(text):
        return pat.sub(xml, text, count=1), 'replace'
    # insert before final </skin>
    pos=text.rfind('</skin>')
    if pos < 0:
        raise RuntimeError('no </skin>')
    return text[:pos] + '\n\n' + xml + '\n' + text[pos:], 'insert'

def color_plugin_footer(text, name):
    pat = re.compile(r'(<screen\b(?=[^>]*\bname=["\']%s["\'])[^>]*>)(.*?)(</screen>)' % re.escape(name), re.S)
    m=pat.search(text)
    if not m:
        return text, False
    body=m.group(2)
    changed=False
    for key in ('red','green','yellow','blue'):
        wp=re.compile(r'<widget\b(?=[^>]*source=["\']key_%s["\'])[^>]*?/?>' % key, re.S)
        wm=wp.search(body)
        if not wm:
            continue
        tag=wm.group(0)
        if 'backgroundColor=' in tag:
            continue
        closing='/>' if tag.rstrip().endswith('/>') else '>'
        core=tag.rstrip()
        if closing=='/>':
            core=core[:-2].rstrip()
        else:
            core=core[:-1].rstrip()
        core += ' backgroundColor="key_%s" foregroundColor="key_text"' % key
        tag2=core + closing
        body=body[:wm.start()] + tag2 + body[wm.end():]
        changed=True
    if changed:
        text=text[:m.start()] + m.group(1)+body+m.group(3)+text[m.end():]
    return text, changed

count=0
stats={}
for p in ROOT.rglob('*.xml'):
    try:
        text=p.read_text(errors='ignore')
    except Exception:
        continue
    orig=text
    for n in ('PluginBrowser','PluginBrowserList','PluginBrowserGrid'):
        text,ch=color_plugin_footer(text,n)
        if ch: stats[n]=stats.get(n,0)+1
    # QuickMenu already has native key colors in good CineView; enforce if an older variant is missing them.
    text,ch=color_plugin_footer(text,'QuickMenu')
    if ch: stats['QuickMenu']=stats.get('QuickMenu',0)+1

    # FHD package/download screens.
    for n,xml in [('PackageAction',PACKAGE_ACTION),('PackageActionLog',PACKAGE_LOG),('PluginDownloadBrowser',PLUGIN_DOWNLOAD)]:
        # Only add PackageAction screens to the principal/live layout family files; safe to add to all CineView XML layouts too.
        text,mode=replace_screen(text,n,xml)
        stats[n]=stats.get(n,0)+1

    if text != orig:
        ET.fromstring(text)
        p.write_text(text)
        count += 1

print('FILES_PATCHED',count)
for k in sorted(stats): print(k,stats[k])

# Contract audit on active skin.
active=ROOT/'skin.xml'
r=ET.parse(active).getroot()
for n in ('PluginBrowser','PluginBrowserList','PluginBrowserGrid','QuickMenu','PluginDownloadBrowser','PackageAction','PackageActionLog'):
    s=next((x for x in r.findall('.//screen') if x.get('name')==n),None)
    if s is None: raise SystemExit('MISSING '+n)
    if n not in ('QuickMenu',) and (s.get('position')!='0,0' or s.get('size')!='1920,1080'):
        raise SystemExit('NOT_FHD %s %s %s'%(n,s.get('position'),s.get('size')))
for n in ('PluginBrowser','PluginBrowserList','PluginBrowserGrid'):
    s=next(x for x in r.findall('.//screen') if x.get('name')==n)
    for key in ('red','green','yellow','blue'):
        w=next((x for x in list(s) if x.get('source')=='key_'+key),None)
        if w is None or w.get('backgroundColor')!='key_'+key:
            raise SystemExit('MISSING_COLOR %s %s'%(n,key))
print('PLUGIN_UI_CONTRACT_OK')
