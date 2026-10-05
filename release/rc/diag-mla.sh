#!/bin/sh
# CineView MLA — read-only diagnostics for a test receiver (posters not shown, design not applied, errors).
# Nothing is installed, changed or deleted.  Output: screen + /tmp/cineview-mla-diag.txt (send that file back).
#   wget -q -O /tmp/diag-mla.sh "https://raw.githubusercontent.com/habeb-s/CineView-FHD/dev/mla-openatv/release/rc/diag-mla.sh" && sh /tmp/diag-mla.sh
OUT=/tmp/cineview-mla-diag.txt
R=/usr/lib/enigma2/python/Components/Renderer/CineViewMLAPosterX.py
{
echo "== CineView MLA diagnostics $(date)"
echo "-- image";   grep -E "^(distro|imageversion|imagebuild|machinebuild|architecture)=" /usr/lib/enigma.info 2>/dev/null
echo "-- python";  python3 -V 2>&1
echo "-- package"; opkg status enigma2-plugin-skins-cineview-fhd-mla 2>/dev/null | grep -E "^(Version|Status)"
echo "-- skin";    grep -E "^config\.skin\.primary_skin|^config\.plugins\.cineviewmla\." /etc/enigma2/settings 2>/dev/null
echo "-- MLA state"; cat /etc/enigma2/cineview_mla/runtime.json 2>/dev/null; ls -l /usr/share/enigma2/CineView_FHD_MLA/active 2>/dev/null
cat /etc/enigma2/cineview_mla/selection.json 2>/dev/null; echo
echo "-- mounts";  grep -E " /media/| / " /proc/mounts; if [ "${SKIPHDD:-0}" = 1 ]; then df -k / /tmp /media/usb 2>/dev/null; else df -k / /tmp /media/hdd /media/usb 2>/dev/null; fi
echo "-- poster cache the renderer would use (no directory created)"
if [ -f "$R" ]; then
python3 - "$R" <<'PY' 2>&1
import ast, os, sys
src = open(sys.argv[1]).read()
tree = ast.parse(src)
want = {"_cineview_mounts", "_cineview_is_multiboot_mount", "_mla_cache_plan", "_mla_cache_root"}
code = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in want and n.name != "_mla_cache_root"]
ns = {"os": os, "re": __import__("re")}
exec(compile(ast.Module(body=code, type_ignores=[]), "r", "exec"), ns)
if "_mla_cache_plan" in ns:
    print("plan:", ns["_mla_cache_plan"]())
else:
    print("this build has no _mla_cache_plan (older policy); its default cache path:")
    for l in src.splitlines():
        if "default = " in l and "poster" in l:
            print("  ", l.strip())
PY
else echo "renderer not installed: $R"; fi
HDDP=/media/hdd/poster; [ "${SKIPHDD:-0}" = 1 ] && HDDP=""
for d in $HDDP /media/usb/cineview-mla/dev-cache/mla/poster /media/usb/poster /tmp/CINEVIEW-MLA/poster /tmp/CINEVIEW/poster; do
  [ -d "$d" ] && echo "   $d: $(find $d -maxdepth 2 -type f 2>/dev/null | wc -l) files, $(du -sk $d 2>/dev/null | cut -f1) kB"
done
echo "-- poster engine log (last 40)"; tail -40 /tmp/CINEVIEW-MLA/poster.log 2>/dev/null || echo "no /tmp/CINEVIEW-MLA/poster.log"
echo "-- network to the poster sources"
for u in https://api.tvmaze.com/singlesearch/shows?q=test https://itunes.apple.com/search?term=test https://v3.sg.media-imdb.com/suggestion/x/test.json; do
  if wget -q -T 8 -O /dev/null "$u" 2>/dev/null; then echo "   OK   $u"; else echo "   FAIL $u"; fi
done
echo "-- current event (EPG text the poster identity reads)"
wget -q -T 5 -O - "http://127.0.0.1/api/statusinfo" 2>/dev/null | head -c 1500; echo
echo "-- enigma2 log: CineView lines, tracebacks, skin errors (last 40)"
L=$(ls -t /home/root/logs/*debug* 2>/dev/null | head -1)
echo "   log: ${L:-none}"
[ -n "$L" ] && grep -a -E "CineView|Traceback|Skin\] Error|accelAlloc failed" "$L" | grep -v "progressPercentWidth\|piconMargin" | tail -40
} 2>&1 | tee $OUT
echo; echo "Saved: $OUT"
