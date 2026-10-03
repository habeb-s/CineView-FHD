#!/bin/sh
# ISS-02 offline reproduction. Read-only on inputs; all work in $OUT.
# usage: GOLD=<extracted openatv-final-20260926 root> ATV80=<openatv enigma2 checkout @45414bc> OUT=<scratch dir> sh repro_iss02_save_paths.sh
set -e
P=$GOLD/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl
rm -rf "$OUT"; mkdir -p "$OUT/croot/Components"
cp -r "$ATV80/lib/python/Components/Renderer" "$ATV80/lib/python/Components/Converter" "$OUT/croot/Components/"
cp "$GOLD"/usr/lib/enigma2/python/Components/Renderer/*.py "$OUT/croot/Components/Renderer/"
cp "$GOLD"/usr/lib/enigma2/python/Components/Converter/*.py "$OUT/croot/Components/Converter/"
for p in A_activate B_keysave; do cp -a "$GOLD/usr/share/enigma2/CineView_FHD" "$OUT/$p"; done
( cd "$OUT/A_activate"; cp -f skin.layout-111-oa.xml skin.xml; python3 $P/theme.py . navy; python3 $P/timeformat.py . 24
  python3 $P/compat.py . "$OUT/croot" "$OUT/A_compat.json"; python3 $P/openatv_v5.py skin.xml; python3 $P/openatv_auditfix.py skin.xml; python3 $P/openatv_plugin_ui.py . ) >/dev/null
( cd "$OUT/B_keysave"; python3 $P/theme.py . navy; cp -p skin.layout-111-oa.xml skin.xml; python3 $P/theme.py . navy; python3 $P/timeformat.py . 24 ) >/dev/null
python3 - "$GOLD" "$OUT" <<'PY'
import sys,xml.etree.ElementTree as E
g,o=sys.argv[1],sys.argv[2]
def s(p): return {x.get('name'):E.tostring(x) for x in E.parse(p).getroot().iter('screen')}
gold=s(g+'/usr/share/enigma2/CineView_FHD/skin.xml')
for t in ('A_activate','B_keysave'):
    x=s(f'{o}/{t}/skin.xml'); d=sorted(k for k in set(gold)|set(x) if gold.get(k)!=x.get(k))
    print(t,len(d),d)
PY
