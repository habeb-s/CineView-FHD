#!/bin/bash
# Smart Installer 1.2.1 (service mode) - simulation of the decisions (DRYRUN=1: nothing is installed) on simulated receivers:
# a receiver root per case (CVMLA_ROOT: enigma.info, the image's own files, /proc/stb/info), a fake opkg (package
# state + Debian/opkg version comparison) and CVMLA_PYV.  Expected result per case: PASS (all checks passed) or the
# exact stop reason.  Usage: run_sim.sh <installer>
INST=$(readlink -f "${1:?installer}")
H=$(cd "$(dirname "$0")" && pwd); W=$H/work; rm -rf "$W"; mkdir -p "$W/bin"
cat > "$W/bin/opkg" <<'EOF'
#!/bin/bash
echo "$*" >> "$(dirname "$0")/../opkg.calls"
case "$1" in
  print-architecture) echo "arch all 1"; echo "arch armv7ahf-neon 16" ;;
  status)
    if [ "$2" = "enigma2-plugin-skins-cineview-fhd-mla" ]; then
      [ -n "$FAKE_CUR" ] && { echo "Package: $2"; echo "Version: $FAKE_CUR"; echo "Status: ${FAKE_STATE:-install ok installed}"; }
    else echo "Package: $2"; echo "Status: install ok installed"; fi ;;
  compare-versions) exec python3 "$(dirname "$0")/vercmp.py" "$2" "$3" "$4" ;;
  list|update) ;;
  *) echo "fake opkg: $*" >&2; exit 1 ;;
esac
EOF
cat > "$W/bin/vercmp.py" <<'EOF'
import sys
def order(c):
    if c == "~": return -1
    if c.isdigit(): return 0
    if c.isalpha(): return ord(c)
    return ord(c) + 256
def cmp_part(a, b):
    while a or b:
        fa = ""; fb = ""
        while a and not a[0].isdigit(): fa += a[0]; a = a[1:]
        while b and not b[0].isdigit(): fb += b[0]; b = b[1:]
        for i in range(max(len(fa), len(fb))):
            x = order(fa[i]) if i < len(fa) else 0; y = order(fb[i]) if i < len(fb) else 0
            if x != y: return x - y
        na = ""; nb = ""
        while a and a[0].isdigit(): na += a[0]; a = a[1:]
        while b and b[0].isdigit(): nb += b[0]; b = b[1:]
        d = int(na or 0) - int(nb or 0)
        if d: return d
    return 0
a, op, b = sys.argv[1:4]
r = cmp_part(a, b)
ok = {"<<": r < 0, ">>": r > 0, "<=": r <= 0, ">=": r >= 0, "=": r == 0}[op]
sys.exit(0 if ok else 1)
EOF
chmod +x "$W/bin/opkg"
SV=$H/../svc
python3 $SV/cvmla_dist.py --catalog $SV/catalog.json --store $SV/store --secret-file $SV/secret --port 18443 --bind 127.0.0.1 \
	--cert $SV/tls/srv.crt --key $SV/tls/srv.key --test-faults 2>$W/service.log & SRV=$!; sleep 1.5
kill -0 $SRV 2>/dev/null || { echo "service did not start"; cat $W/service.log; exit 2; }
trap 'kill $SRV 2>/dev/null' EXIT
PKGS=$H/../dist/packages
mkroot() {  # mkroot <name> <distro> <ver> <brand> <machinebuild> <markers...>
	local r=$W/$1; shift; local d=$1 v=$2 br=$3 mb=$4; shift 4
	mkdir -p $r/usr/bin $r/usr/lib/enigma2/python/Components $r/proc/stb/info
	printf '#!/bin/sh\n' > $r/usr/bin/enigma2; chmod +x $r/usr/bin/enigma2
	printf "distro='%s'\nimageversion='%s'\nbrand='%s'\ndisplaybrand='%s'\nmachinebuild='%s'\ndisplaymodel='%s'\n" "$d" "$v" "$br" "$br" "$mb" "$mb" > $r/usr/lib/enigma.info
	for m in "$@"; do mkdir -p $r/usr/lib/enigma2/python/$(dirname $m); : > $r/usr/lib/enigma2/python/$m.pyc; done
	echo $r
}
ATV="Components/International Components/Opkg"
BH="Screens/BpBlue Plugins/SystemPlugins/OBH/plugin"
VIX="Plugins/SystemPlugins/ViX/plugin Plugins/SystemPlugins/ViX/ImageManager"
N=0; NP=0; NF=0
run() {  # run <id> <expect: PASS|text> <root> [VAR=value ...]
	local id=$1 exp=$2 r=$3; shift 3
	local out; out=$(env -i PATH="$W/bin:/usr/bin:/bin" HOME=/tmp CVMLA_ROOT="$r" DRYRUN=1 CVMLA_SERVICE=https://127.0.0.1:18443 SSL_CERT_FILE=$SV/tls/ca.crt "$@" ${SIMSH:-sh} "$INST" 2>&1)
	local got
	if echo "$out" | grep -q "All checks passed"; then got=PASS; else got=$(echo "$out" | grep -m1 '\[XX\]' | sed 's/.*\[XX\] //'); fi
	N=$((N+1))
	if { [ "$exp" = PASS ] && [ "$got" = PASS ]; } || { [ "$exp" != PASS ] && echo "$got" | grep -qF -- "$exp"; }; then
		NP=$((NP+1)); printf 'PASS  %-34s -> %s\n' "$id" "${got:0:118}"
	else
		NF=$((NF+1)); printf 'FAIL  %-34s expected [%s] got [%s]\n' "$id" "$exp" "$got"; echo "$out" | sed 's/^/        | /' | tail -12
	fi
	echo "$out" > "$W/$id.out"
}
vu() { echo "$1" > $2/proc/stb/info/vumodel; echo dm8000 > $2/proc/stb/info/model; }
# --- the three tested images on the Vu+ Duo 4K SE (as the receiver: vumodel duo4kse, legacy model file dm8000)
r=$(mkroot atv openatv 8.0.1 vuplus vuduo4kse $ATV); vu duo4kse $r
run atv_8.0_fresh PASS $r CVMLA_PYV=3.14
run atv_8.0_upgrade_from_1.0.0 PASS $r CVMLA_PYV=3.14 FAKE_CUR=1.0.0
grep -q "Upgrade: your design" $W/atv_8.0_upgrade_from_1.0.0.out && echo "      (mode: upgrade 1.0.0 -> 1.0.1 confirmed)"
run atv_same_1.0.1 PASS $r CVMLA_PYV=3.14 FAKE_CUR=1.0.1
run atv_newer_installed "A newer CineView MLA (1.0.2) is already installed" $r CVMLA_PYV=3.14 FAKE_CUR=1.0.2
run atv_halfinstalled_repair PASS $r CVMLA_PYV=3.14 FAKE_CUR=1.0.1 FAKE_STATE="install reinstreq half-installed"
grep -q "repaired with a verified reinstall" $W/atv_halfinstalled_repair.out && echo "      (mode: repair confirmed)"
run atv_rollback_to_1.0.0 PASS $r CVMLA_PYV=3.14 FAKE_CUR=1.0.1 ROLLBACK=1
grep -q "Return to the earlier version 1.0.0" $W/atv_rollback_to_1.0.0.out && echo "      (mode: downgrade 1.0.1 -> 1.0.0 confirmed)"
run atv_force_reinstall PASS $r CVMLA_PYV=3.14 FAKE_CUR=1.0.1 FORCE=1
grep -q "Reinstall requested" $W/atv_force_reinstall.out && echo "      (mode: reinstall confirmed)"
run atv_pkg_dir PASS $r CVMLA_PYV=3.14 PKG_DIR=$PKGS/openatv
grep -q "Package source: $PKGS/openatv/enigma2-plugin-skins-cineview-fhd-mla_1.0.1_all.ipk (local file)" $W/atv_pkg_dir.out && echo "      (package source: local file confirmed)"
grep -q "not published yet" $W/atv_8.0_fresh.out && echo "      (no PKG_DIR, no distribution point: 'not published yet' warning confirmed)"
run atv_wrong_python "Python 3.13 found; this package is built for Python 3.14" $r CVMLA_PYV=3.13
r=$(mkroot bh openbh 5.6.008 vuplus vuduo4kse $BH); vu duo4kse $r
run bh_5.6 PASS $r CVMLA_PYV=3.13
run bh_rollback_to_openbh17 PASS $r CVMLA_PYV=3.13 FAKE_CUR=1.0.1~openbh1 ROLLBACK=1
grep -q "Return to the earlier version 1.0.0~openbh17" $W/bh_rollback_to_openbh17.out && echo "      (mode: downgrade -> 1.0.0~openbh17 confirmed)"
run bh_upgrade_from_openbh17 PASS $r CVMLA_PYV=3.13 FAKE_CUR=1.0.0~openbh17
grep -q "Upgrade: your design" $W/bh_upgrade_from_openbh17.out && echo "      (mode: upgrade 1.0.0~openbh17 -> 1.0.1~openbh1 confirmed)"
r=$(mkroot vix openvix 6.9.002 vuplus vuduo4kse $VIX); vu duo4kse $r
run vix_6.9 PASS $r CVMLA_PYV=3.14
run vix_upgrade_from_openvix1 PASS $r CVMLA_PYV=3.14 FAKE_CUR=1.0.0~openvix1
grep -q "Upgrade: your design" $W/vix_upgrade_from_openvix1.out && echo "      (mode: upgrade 1.0.0~openvix1 -> 1.0.1~openvix1 confirmed)"
# --- untested versions (D5)
r=$(mkroot atv76 openatv 7.6.0 vuplus vuduo4kse $ATV); vu duo4kse $r;  run atv_7.6_refused "OpenATV 7.6.0 has not been tested" $r CVMLA_PYV=3.13
r=$(mkroot atv81 openatv 8.1 vuplus vuduo4kse $ATV); vu duo4kse $r;    run atv_8.1_refused "OpenATV 8.1 has not been tested" $r CVMLA_PYV=3.14
r=$(mkroot bh60 openbh 6.0.003 vuplus vuduo4kse $BH); vu duo4kse $r;   run bh_6.0_refused "OpenBH 6.0.003 has not been tested" $r CVMLA_PYV=3.14
r=$(mkroot vix70 openvix 7.0.001 vuplus vuduo4kse $VIX); vu duo4kse $r; run vix_7.0_refused "OpenViX 7.0.001 has not been tested" $r CVMLA_PYV=3.14
# --- image identification by the image's own files
r=$(mkroot fake_bh openbh 5.6.008 vuplus vuduo4kse $VIX); vu duo4kse $r;  run openvix_files_says_openbh "enigma.info names OpenBH, but the image's own files point to 'openvix'" $r CVMLA_PYV=3.13
r=$(mkroot fake_vix openvix 6.9.002 vuplus vuduo4kse $BH); vu duo4kse $r; run openbh_files_says_openvix "enigma.info names OpenViX, but the image's own files point to 'openbh'" $r CVMLA_PYV=3.14
r=$(mkroot mixed openatv 8.0.1 vuplus vuduo4kse $ATV Plugins/SystemPlugins/OBH/plugin); vu duo4kse $r; run atv_with_obh_file "point to 'openatv openbh'" $r CVMLA_PYV=3.14
r=$(mkroot half_bh openbh 5.6.008 vuplus vuduo4kse Screens/BpBlue); vu duo4kse $r; run bh_one_marker_enough PASS $r CVMLA_PYV=3.13
r=$(mkroot nofiles openatv 8.0.1 vuplus vuduo4kse); vu duo4kse $r;     run atv_no_image_files "point to 'no known image'" $r CVMLA_PYV=3.14
r=$(mkroot pli openpli 9.1 vuplus vuduo4kse); vu duo4kse $r;           run openpli_refused "This image is 'openpli'" $r CVMLA_PYV=3.12
r=$(mkroot nodistro "" 1.0 vuplus vuduo4kse $ATV); vu duo4kse $r;      run distro_missing "does not name itself" $r CVMLA_PYV=3.14
# --- receiver model, several brands
r=$(mkroot vu_mismatch openatv 8.0.1 vuplus vuduo4k $ATV); vu duo4kse $r; run vu_model_mismatch_not_blocking PASS $r CVMLA_PYV=3.14
r=$(mkroot vu_nodrv openatv 8.0.1 vuplus vuduo4kse $ATV);                run vu_brand_without_driver PASS $r CVMLA_PYV=3.14
r=$(mkroot gb_vum openatv 8.0.1 gigablue gbquad4k $ATV); echo duo4kse > $r/proc/stb/info/vumodel; run vumodel_on_other_brand PASS $r CVMLA_PYV=3.14
r=$(mkroot gb openatv 8.0.1 gigablue gbquad4k $ATV); echo quad4k > $r/proc/stb/info/gbmodel; run gigablue_gbmodel PASS $r CVMLA_PYV=3.14
grep -q "confirmed by the receiver driver" $W/gigablue_gbmodel.out && echo "      (model confirmed by gbmodel)"
r=$(mkroot dm openatv 8.0.1 dreambox dm920 $ATV); echo dm920 > $r/proc/stb/info/model; run dreambox_model_file PASS $r CVMLA_PYV=3.14
r=$(mkroot zg openatv 8.0.1 zgemma h7 $ATV); echo h7 > $r/proc/stb/info/boxtype; run zgemma_boxtype PASS $r CVMLA_PYV=3.14
r=$(mkroot hw openatv 8.0.1 edision osmio4k $ATV); echo osmio4k > $r/proc/stb/info/hwmodel; run hwmodel PASS $r CVMLA_PYV=3.14
r=$(mkroot legacy openatv 8.0.1 zgemma h7 $ATV); echo dm8000 > $r/proc/stb/info/model; run legacy_model_not_blocking PASS $r CVMLA_PYV=3.14
r=$(mkroot nodrv openatv 8.0.1 octagon sf8008 $ATV);                   run no_driver_file_single_source PASS $r CVMLA_PYV=3.14
grep -q "from the image information only" $W/no_driver_file_single_source.out && echo "      (single-source model shown as such, no invented model)"
r=$(mkroot nomb openatv 8.0.1 vuplus "" $ATV); vu duo4kse $r;          run machinebuild_missing_not_blocking PASS $r CVMLA_PYV=3.14
# --- foreign pre-start hook
r=$(mkroot hook openatv 8.0.1 vuplus vuduo4kse $ATV); vu duo4kse $r; printf '#!/bin/sh\n# other\n' > $r/usr/bin/enigma2_pre_start.sh
run foreign_prestart_hook PASS $r CVMLA_PYV=3.14   # 1.3.5: another add-on's hook is kept, CineView does not use it
grep -q "kept as it is" $W/foreign_prestart_hook.out && echo "      (foreign hook reported as kept, not replaced)"
run foreign_prestart_hook_rollback "uses /usr/bin/enigma2_pre_start.sh" $r CVMLA_PYV=3.14 ROLLBACK=1   # 1.0.4 still needs the file
r=$(mkroot ownhook openatv 8.0.1 vuplus vuduo4kse $ATV); vu duo4kse $r; printf '#!/bin/sh\n# CineView MLA guardian\n' > $r/usr/bin/enigma2_pre_start.sh
run own_prestart_hook PASS $r CVMLA_PYV=3.14
echo "TOTAL $N  PASS $NP  FAIL $NF"
