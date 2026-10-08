#!/bin/sh
# runs ON the receiver (Slot 4), read-only inventory of everything named CineView / PosterX, HDD excluded.
echo "== packages"; opkg list-installed | grep -i "cineview\|posterx"
for p in $(opkg list-installed | grep -i cineview | cut -d" " -f1); do
  echo "-- $p"; opkg status $p | grep -E "^(Version|Status|Depends|Installed-Time)"
  [ -e /var/lib/opkg/info/$p.postinst ] && { echo "   postinst (lines with actions):"; grep -nE "tar|cp |ln |mv |rm |sed |install|payload|/usr/|/etc/" /var/lib/opkg/info/$p.postinst | head -40; }
  [ -e /var/lib/opkg/info/$p.prerm ] && { echo "   prerm:"; head -30 /var/lib/opkg/info/$p.prerm; }
  [ -e /var/lib/opkg/info/$p.postrm ] && { echo "   postrm:"; head -30 /var/lib/opkg/info/$p.postrm; }
done
echo "== payload contents"
for t in /usr/share/cineview-fhd-offline/openvix/payload.tar.gz /usr/share/cineview-fhd-offline/universal/openvix/payload.tar.gz; do
  echo "-- $t"; tar -tzf $t | grep -v "/$" | head -600
done
echo "== paths named CineView / PosterX (rootfs only; /media /proc /sys /mnt /tmp excluded)"
find / -xdev \( -path /proc -o -path /sys -o -path /media -o -path /mnt -o -path /tmp \) -prune -o \( -iname "*cineview*" -o -iname "*posterx*" \) -print 2>/dev/null | sort
echo "== /usr/share/enigma2 skins"; ls -la /usr/share/enigma2 | grep "^d\|^l"
echo "== settings lines"; grep -in "cineview\|posterx" /etc/enigma2/settings
echo "== pre-start hook"; ls -la /usr/bin/enigma2_pre_start.sh 2>&1; head -5 /usr/bin/enigma2_pre_start.sh 2>/dev/null
echo "== cron / init"; grep -ril "cineview" /etc/cron* /etc/init.d /etc/rc*.d /var/spool/cron 2>/dev/null
echo "== symlinks pointing to CineView"
find / -xdev \( -path /proc -o -path /sys -o -path /media -o -path /mnt \) -prune -o -type l -print 2>/dev/null | while read l; do case "$(readlink "$l")" in *[Cc]ine[Vv]iew*|*PosterX*) echo "$l -> $(readlink "$l")";; esac; done
echo INV_DONE
