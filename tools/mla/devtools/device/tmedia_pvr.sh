#!/bin/sh
# PVR test media on the Slot 8 USB stick ONLY (user rule 2026-10-05 08:45: never HDD content for PVR tests).
# Copies of the existing USB test clip with .meta titles chosen to exercise the three cover paths:
#   A identity lookup from the recording's own title/description (no local cover)
#   B local cover file next to the recording (copied from the USB poster cache)
#   C generic programme -> CineView default image
# Idempotent; refuses to run if the target is not on the USB device.
set -e
D=/media/usb/cineview-mla/testmedia
SRC="$D/20261003 1717 - HRT1 HD. - CineView MLA test clip.ts"
[ "$(stat -c %d "$D")" = "$(stat -c %d /media/usb)" ] || { echo "not on usb"; exit 1; }
[ "$(stat -c %d "$D")" != "$(stat -c %d /media/hdd)" ] || { echo "hdd!"; exit 1; }
mk() {  # $1 file base, $2 sref, $3 title, $4 description, $5 epoch
  f="$D/$1.ts"
  [ -f "$f" ] || cp "$SRC" "$f"
  printf '%s\n%s\n%s\n%s\n\n1174597\n8855552\nf:0\n188\n0\n' "$2" "$3" "$4" "$5" > "$f.meta"
}
mk "20261004 2015 - HBO HD - Ples malog pingvina" "1:0:19:784:C6D4:16E:A00000:0:0:0:" "Ples malog pingvina" "(SAD/Australija, 2006, film) U svijetu carskih pingvina jednostavna pjesma može odrediti hoće li pingvin živjeti sretno do kraja života." 1791137700
mk "20261004 2140 - HBO 2 HD - Harry Potter i plameni pehar" "1:0:19:785:C6D4:16E:A00000:0:0:0:" "Harry Potter i plameni pehar" "(VB/SAD, 2005, film) Harry je neočekivano izabran za Tromagijski turnir." 1791142800
cp "/media/usb/cineview-mla/dev-cache/reference/poster/harry potter i plameni pehar film.jpg" "$D/20261004 2140 - HBO 2 HD - Harry Potter i plameni pehar.jpg"
mk "20261004 1900 - HRT1 HD - Dnevnik" "1:0:19:D49:C738:16E:A00000:0:0:0:" "Dnevnik" "Informativni program." 1791133200
ls -la "$D"
