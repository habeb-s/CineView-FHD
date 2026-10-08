#!/bin/bash
# Install-path simulation of the automatic repair (fake opkg; nothing real is installed on this PC):
#   halfthenok  : the first opkg install leaves the package half-installed, the repair (--force-reinstall) succeeds
#   halfalways  : the repair fails too -> clear stop, the user is told to run the installer again
INST=$(readlink -f "${1:?installer}"); H=$(cd "$(dirname "$0")" && pwd); W=$H/work; mkdir -p $W/rbin
cat > $W/rbin/opkg <<'EOT'
#!/bin/bash
S=$FAKE_DIR/state
case "$1" in
  print-architecture) echo "arch all 1" ;;
  status) if [ "$2" = "enigma2-plugin-skins-cineview-fhd-mla" ]; then
            st=$(cat $S 2>/dev/null || echo "install ok installed:$FAKE_CUR"); echo "Package: $2"; echo "Version: ${st#*:}"; echo "Status: ${st%%:*}"
          else echo "Status: install ok installed"; fi ;;
  compare-versions) exec python3 $FAKE_DIR/../bin/vercmp.py "$2" "$3" "$4" ;;
  install)
    if [ "$2" = "--force-reinstall" ] && [ "$FAKE_INSTALL" = halfthenok ]; then echo "install ok installed:1.0.1" > $S; exit 0; fi
    echo " * pkg_run_script: package postinst script returned status 1."; echo "Collected errors:"; echo "install reinstreq half-installed:1.0.1" > $S; exit 1 ;;
  *) exit 0 ;;
esac
EOT
chmod +x $W/rbin/opkg
for mode in halfthenok halfalways; do
	rm -f $W/rbin/state
	out=$(env -i PATH="$W/rbin:/usr/bin:/bin" HOME=/tmp FAKE_DIR=$W/rbin FAKE_INSTALL=$mode FAKE_CUR=1.0.0 CVMLA_ROOT=$W/atv CVMLA_PYV=3.14 \
		PKG_DIR=$H/../dist/packages/openatv sh "$INST" 2>&1)
	echo "== $mode"; echo "$out" | sed -n '/^Installing/,$p' | head -9 | sed 's/^/   /'
	echo "   leftovers: $(ls -d /tmp/.cvmla.* 2>/dev/null | wc -l)"
done
