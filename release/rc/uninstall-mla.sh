#!/bin/sh
# CineView FHD MLA — uninstall / rollback on a test receiver.
#   wget -q -O /tmp/uninstall-mla.sh "https://raw.githubusercontent.com/habeb-s/CineView-FHD/dev/mla-openatv/release/rc/uninstall-mla.sh" && sh /tmp/uninstall-mla.sh
# * If CineView MLA is the selected skin, Enigma2 is stopped, the skin selection is removed from
#   /etc/enigma2/settings (the image's default skin is used at the next start), the package is removed and Enigma2
#   is started again.  Otherwise the package is simply removed.
# * The poster cache (e.g. /media/hdd/poster) and /etc/enigma2/cineview_mla are KEPT ('opkg remove'); add the
#   argument 'purge' to delete /etc/enigma2/cineview_mla too.  The poster cache is never deleted by remove / purge.
# * Deleting CineView MLA's poster cache is a separate, explicit option (the package is not touched):
#     sh /tmp/uninstall-mla.sh cache                 -> shows the cache folder and what would be deleted
#     CONFIRM=yes sh /tmp/uninstall-mla.sh cache     -> deletes it
#   Only MLA's own sub-folders are deleted: id/ (poster identities and their images) and sz*/ (widget-size copies).
#   Files directly in the cache folder (e.g. the original CineView FHD posters in /media/hdd/poster) are kept.
PKG=enigma2-plugin-skins-cineview-fhd-mla
MODE=${1:-remove}
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
cp -p /etc/enigma2/settings /tmp/settings.before-mla-uninstall 2>/dev/null
if grep -q "^config.skin.primary_skin=CineView_FHD_MLA/" /etc/enigma2/settings 2>/dev/null; then
  echo "CineView MLA is the selected skin: stopping Enigma2 to switch back to the image default skin."
  init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done
  sed -i '/^config.skin.primary_skin=CineView_FHD_MLA\//d' /etc/enigma2/settings
  if [ "$MODE" = "purge" ]; then opkg remove $PKG && rm -rf /etc/enigma2/cineview_mla; else opkg remove $PKG; fi
  init 3
else
  if [ "$MODE" = "purge" ]; then opkg remove $PKG && rm -rf /etc/enigma2/cineview_mla; else opkg remove $PKG; fi
fi
echo "Done. Previous settings saved in /tmp/settings.before-mla-uninstall."
