#!/bin/sh
# CineView MLA - uninstall.  Design & Development by habeb-s (c) 2026
#   wget -qO /tmp/cineview-uninstall.sh "<raw url of this file>" && sh /tmp/cineview-uninstall.sh
#   sh /tmp/cineview-uninstall.sh            remove the skin; keeps your profiles, settings and the poster cache
#   sh /tmp/cineview-uninstall.sh purge      also deletes the CineView MLA settings and profiles (the backup folder
#                                            /etc/enigma2/cineview_mla/backup is kept)
#   sh /tmp/cineview-uninstall.sh cache      shows the poster cache; CONFIRM=yes ... cache deletes only CineView's
#                                            own folders in it (other skins' posters are kept)
# If CineView MLA is the selected skin, the GUI is stopped, the image's default skin is selected and the GUI restarts.
SELF="$0"; trap 'case "$SELF" in /tmp/cineview-uninstall*.sh) rm -f "$SELF" 2>/dev/null ;; esac' EXIT
PKG=enigma2-plugin-skins-cineview-fhd-mla
MODE=${1:-remove}
purge_state() {  # settings and profiles go; backups (restore points, settings copies) stay
  for f in /etc/enigma2/cineview_mla/* /etc/enigma2/cineview_mla/.[!.]*; do
    [ -e "$f" ] || continue
    [ "${f##*/}" = backup ] || rm -rf "$f"
  done
}
if [ "$MODE" = "cache" ]; then
  python3 - "${CONFIRM:-no}" "${CACHE_PATH:-}" <<'PYEOF'
import json, os, shutil, sys
confirm, override = sys.argv[1] == "yes", sys.argv[2]
def plan():
    if override:
        return override, "CACHE_PATH"
    try:
        p = json.load(open("/etc/enigma2/cineview_mla/runtime.json")).get("poster_cache")
        if p:
            return p, "runtime.json"
    except Exception:
        pass
    root = os.stat("/").st_dev
    mounts = [l.split()[:4] for l in open("/proc/mounts") if len(l.split()) >= 4]
    def real(src, mp, opts):
        try:
            return "rw" in opts.split(",") and os.path.ismount(mp) and os.stat(mp).st_dev != root and src.startswith("/dev/")
        except OSError:
            return False
    for src, mp, fs, opts in mounts:
        if mp == "/media/hdd" and real(src, mp, opts):
            return "/media/hdd/poster", "HDD"
    usb = sorted((0 if "usb" in mp else 1, mp) for src, mp, fs, opts in mounts if mp.startswith("/media/") and mp != "/media/hdd" and real(src, mp, opts))
    if usb:
        return os.path.join(usb[0][1], "poster"), "removable storage"
    return "/tmp/CINEVIEW-MLA/poster", "/tmp"
path, why = plan()
print("CineView MLA poster cache: %s (%s)" % (path, why))
if not os.path.isdir(path):
    print("   nothing there."); sys.exit(0)
own = [d for d in sorted(os.listdir(path)) if os.path.isdir(os.path.join(path, d)) and (d == "id" or d == "sz" or d.startswith("sz."))]
if not own:
    print("   no CineView MLA folders (id/, sz/) in it - nothing to delete."); sys.exit(0)
for d in own:
    fp = os.path.join(path, d)
    n = sum(len(f) for _, _, f in os.walk(fp))
    print("   %s/  %d files" % (fp, n))
print("   kept: %d files directly in %s (other skins' posters)" % (len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]), path))
if not confirm:
    print("Nothing deleted. Run again with CONFIRM=yes to delete the folders listed above."); sys.exit(0)
for d in own:
    shutil.rmtree(os.path.join(path, d), ignore_errors=True)
print("Deleted. CineView MLA downloads posters again when they are needed.")
PYEOF
  exit 0
fi
opkg status $PKG 2>/dev/null | grep -q "^Status: install" || { echo "CineView MLA is not installed."; exit 0; }
mkdir -p /etc/enigma2/cineview_mla/backup 2>/dev/null; cp -p /etc/enigma2/settings /etc/enigma2/cineview_mla/backup/settings.before-uninstall 2>/dev/null
if grep -q "^config.skin.primary_skin=CineView_FHD_MLA/" /etc/enigma2/settings 2>/dev/null; then
  echo "CineView MLA is the selected skin: stopping Enigma2 to switch back to the image default skin."
  init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done
  sed -i '/^config.skin.primary_skin=CineView_FHD_MLA\//d' /etc/enigma2/settings
  if [ "$MODE" = "purge" ]; then opkg remove $PKG && purge_state; else opkg remove $PKG; fi
  init 3
else
  if [ "$MODE" = "purge" ]; then opkg remove $PKG && purge_state; else opkg remove $PKG; fi
fi
if opkg status $PKG 2>/dev/null | grep -q "^Status: install"; then echo "CineView MLA could not be removed (see the lines above)."; exit 1; fi
if [ "$MODE" = "purge" ]; then echo "CineView MLA removed. Your poster cache and backups (/etc/enigma2/cineview_mla/backup) are kept."
else echo "CineView MLA removed. Your poster cache is kept."; fi
