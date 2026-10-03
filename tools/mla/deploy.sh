#!/bin/sh
# Deploy a built MLA tree to the receiver's ACTIVE slot (run on ai-agent).
# usage: deploy.sh <build root> ; requires ~/cineview-mla/r.sh (ssh wrapper)
set -e
B=$1; R=~/cineview-mla/r.sh
( cd "$B" && find usr -type f -o -type l | sort ) > "$B.files"
# Refuse to overwrite anything not owned by MLA.
$R 'cat > /tmp/cvmla/mla.files'  < "$B.files"
$R 'cd / && for f in $(cat /tmp/cvmla/mla.files); do case "$f" in usr/share/enigma2/CineView_FHD_MLA/*|*/CineViewMLA*|*/Extensions/CineViewMLA/*) ;; *) echo "REFUSE $f"; exit 3;; esac; done; echo paths-ok'
tar -C "$B" -czf - usr | $R 'tar -C / --no-same-owner -xzf - && mkdir -p /media/usb/cineview-mla/state && cp /tmp/cvmla/mla.files /media/usb/cineview-mla/state/mla.installed-files && echo deployed'
