#!/bin/sh
# CineView FHD MLA — uninstall / rollback on a test receiver.
#   wget -q -O /tmp/uninstall-mla.sh "https://raw.githubusercontent.com/habeb-s/CineView-FHD/dev/mla-openatv/release/rc/uninstall-mla.sh" && sh /tmp/uninstall-mla.sh
# * If CineView MLA is the selected skin, Enigma2 is stopped, the skin selection is removed from
#   /etc/enigma2/settings (the image's default skin is used at the next start), the package is removed and Enigma2
#   is started again.  Otherwise the package is simply removed.
# * The poster cache (e.g. /media/hdd/poster) and /etc/enigma2/cineview_mla are KEPT ('opkg remove'); add the
#   argument 'purge' to delete /etc/enigma2/cineview_mla too.  The poster cache is never deleted by this script.
PKG=enigma2-plugin-skins-cineview-fhd-mla
MODE=${1:-remove}
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
