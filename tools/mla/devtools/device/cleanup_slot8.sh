#!/bin/sh
# Slot 8 cleanup (user 2026-10-07 12:17): remove every CineView / CineView MLA trace from THIS slot only.
# Explicit paths only (inventory 2026-10-07 12:20), no wildcards.  /media/hdd is never touched (guard below).
# Runs with Enigma2 stopped (settings and resumepoints are rewritten by Enigma2 on shutdown).
# Rollback copy of every config/skin/component item: agent ~/cineview-mla/cleanup/rollback-20261007-092310.
set -u
del() {
	for p in "$@"; do
		case "$p" in /media/hdd|/media/hdd/*) echo "REFUSED $p"; continue ;; esac
		if [ -e "$p" ] || [ -L "$p" ]; then rm -rf -- "$p" && echo "deleted  $p" || echo "FAILED   $p"
		else echo "absent   $p"; fi
	done
}
echo "== stop GUI"
init 4; for i in $(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done
pidof enigma2 >/dev/null && { echo "enigma2 still running - stop"; exit 1; }

echo "== Enigma2 settings"
python3 - <<'PYEOF'
import ast
p = "/etc/enigma2/settings"
lines = open(p).read().split("\n")
exact = {
    "config.EMC.movie_homepath=/media/usb/cineview-mla/testmedia",
    "config.EMC.movie_pathlimit=/media/usb/cineview-mla/testmedia",
    "config.EMC.movie_trashcan_path=/media/usb/cineview-mla/testmedia/trashcan",
    "config.EMC.movie_trashcan_clean=False",
}
out = []
for l in lines:
    if l in exact or (l.startswith("config.usage.last_movie_played=") and "/media/usb/cineview-mla/" in l) \
            or l.startswith("config.skin.primary_skin=CineView") or l.startswith("config.plugins.CineView"):
        print("removed line: " + l[:130]); continue
    if l.startswith("config.usage.plugin_sort_weight="):
        d = ast.literal_eval(l.split("=", 1)[1])
        for k in ("cineview designs", "cineview control"):
            if k in d:
                del d[k]; print("plugin_sort_weight: removed key '%s'" % k)
        l = "config.usage.plugin_sort_weight=" + repr(d)
    out.append(l)
open(p, "w").write("\n".join(out))
PYEOF

echo "== resume points"
python3 - <<'PYEOF'
import pickle
p = "/etc/enigma2/resumepoints.pkl"
d = pickle.load(open(p, "rb"))
for k in [k for k in d if "/media/usb/cineview-mla/" in str(k)]:
    del d[k]; print("removed resume point: " + str(k)[:120])
pickle.dump(d, open(p, "wb"), pickle.HIGHEST_PROTOCOL)
print("resume points left: %d" % len(d))
PYEOF

echo "== package manager"
opkg remove enigma2-plugin-skins-cineview-fhd-mla 2>&1
opkg list-installed | grep -i cineview || echo "no CineView package installed"

echo "== files"
C=/usr/lib/enigma2/python/Components
del /usr/share/enigma2/CineView_FHD_MLA /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA \
    /usr/share/enigma2/CineView_FHD /usr/share/enigma2/CineView_FHD_1001 \
    /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl \
    $C/Converter/CineViewBitrate.py $C/Converter/CineViewBitrate.pyc \
    $C/Converter/CineViewCPUTemp.py $C/Converter/CineViewCPUTemp.pyc \
    $C/Converter/CineViewCamInfo.py $C/Converter/CineViewCamInfo.pyc \
    $C/Converter/CineViewIMDb.py $C/Converter/CineViewIMDb.pyc \
    $C/Converter/CineViewTransponder.py $C/Converter/CineViewTransponder.pyc \
    $C/Converter/CineViewTransponderInfo.py $C/Converter/CineViewTransponderInfo.pyc \
    $C/Renderer/CineViewPosterX.py $C/Renderer/CineViewPosterX.pyc \
    /usr/bin/enigma2_pre_start.sh \
    /etc/enigma2/cineview_mla \
    /tmp/CINEVIEW-MLA /tmp/cineview_mla_postinst.log /tmp/cvmla /home/root/cvmla \
    /media/usb/cineview-mla /media/usb/cineview-live-backup-20261001-184821 \
    /media/usb/cineview-v3-pretest-20260926 /media/usb/cineview-v3-retired-xml
sync
echo CLEANUP_DONE
