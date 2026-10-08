#!/bin/sh
# runs ON the receiver (Slot 4): ownership and dependency checks, read-only.
C=/usr/lib/enigma2/python/Components
P=/usr/lib/enigma2/python/Plugins/Extensions
echo "== package owner of each candidate file"
for f in $C/Renderer/PosterX.py $C/Renderer/iPosterX.py $C/Renderer/iPosterXDownloadThread.py $C/Renderer/AglarePosterX.py $C/Renderer/LukaPosterX.py \
         $C/Renderer/CineViewPosterX.py $C/Converter/CineViewBitrate.py $C/Converter/CineViewCamInfo.py /etc/enigma2/skin_user_YouViX-PosterX.xml \
         $P/CineViewControl/plugin.py /usr/share/enigma2/CineView_FHD/skin.xml /usr/bin/enigma2_pre_start.sh; do
  o=$(opkg search "$f" 2>/dev/null | cut -d" " -f1 | tr "\n" " "); echo "$f -> ${o:-(no package)}"
done
echo "== activate.sh"; cat $P/CineViewControl/activate.sh
echo "== smartdeps.sh (head)"; head -30 $P/CineViewControl/smartdeps.sh
echo "== CineViewControl: writes outside its own folder? (open/write/copy/patch targets)"
grep -nE "open\(.*['\"]w|shutil\.|os\.(rename|remove|symlink|system)|subprocess|/usr/lib/enigma2/python/(Screens|Components)|/etc/enigma2/settings" $P/CineViewControl/*.py | cut -c1-200 | head -40
echo "== who references the old components (outside the old CineView folders)"
for n in CineViewPosterX CineViewBitrate CineViewCPUTemp CineViewCamInfo CineViewIMDb CineViewTransponder CineViewControl "config.plugins.cineview\b"; do
  echo "-- $n"
  grep -rlE "$n" /usr/share/enigma2 /usr/lib/enigma2/python /etc/enigma2 2>/dev/null \
    | grep -v "^/usr/share/enigma2/CineView_FHD/\|^/usr/share/enigma2/CineView_FHD.rollback-broken\|^/etc/enigma2/CineView_FHD-before\|/Plugins/Extensions/CineViewControl/\|/Converter/CineView[A-Z][a-z]*\.pyc\?$\|/Renderer/CineViewPosterX\.pyc\?$" | head -10
done
echo "== old config namespace owner"; grep -n "config.plugins.cineview\b\|config.plugins.cineview =" $P/CineViewControl/*.py | head -5
echo "== /root"; ls -la /root; du -sh /root/cineview-openvix-backups /etc/enigma2/CineView_FHD-before-latest-merge-20260922-221719 /etc/enigma2/CineViewControl-before-update-20260922-185907.tar.gz /usr/share/enigma2/CineView_FHD /usr/share/enigma2/CineView_FHD.rollback-broken-20260922 /usr/share/cineview-fhd-offline $P/CineViewControl 2>/dev/null
echo "== CineView_FHD files not from the payload"
tar -tzf /usr/share/cineview-fhd-offline/openvix/payload.tar.gz | sed 's#^\./##; s#/$##' | sort > /tmp/cv_pl.txt
find /usr/share/enigma2/CineView_FHD $P/CineViewControl | sed 's#^/##' | sort > /tmp/cv_disk.txt
comm -13 /tmp/cv_pl.txt /tmp/cv_disk.txt | head -40; echo "count not in payload: $(comm -13 /tmp/cv_pl.txt /tmp/cv_disk.txt | wc -l)"
rm -f /tmp/cv_pl.txt /tmp/cv_disk.txt
echo "== pyc of old converters/renderer"; ls -la $C/Converter/CineView[A-Z]*.pyc $C/Renderer/CineViewPosterX.pyc $C/Converter/__pycache__/CineView* $C/Renderer/__pycache__/CineView* 2>/dev/null | grep -v CineViewMLA
echo INV2_DONE
