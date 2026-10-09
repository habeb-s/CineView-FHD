#!/bin/bash
# preinst of every range package, run against simulated receiver roots: image/version/Python/capabilities.
cd ~/cineview-mla/rangecheck; T=$PWD/t_pre; rm -rf $T; mkdir -p $T
PASS=0; FAILN=0
extract() { local d=$T/ctl_$1; mkdir -p $d; (cd $d && ar p ../../pkg/enigma2-plugin-skins-cineview-fhd-mla_$1_all.ipk control.tar.gz | tar -xz); echo $d/preinst; }
case_() {  # case_ <variant> <distro> <imageversion> <python> <addons 0/1> <fulldesc 0/1> <expect ok|stop> <label>
	local V=$1 R=$T/root_$RANDOM; mkdir -p $R/usr/lib/enigma2/python/Components/Converter $R/usr/lib/enigma2/python/Components/Addons $R/bin
	printf "distro='%s'\nimageversion='%s'\nmachinebuild='anybox'\n" $2 $3 > $R/usr/lib/enigma.info
	[ "$5" = 1 ] && echo x > $R/usr/lib/enigma2/python/Components/Addons/ColorButtonsSequence.pyc
	[ "$6" = 1 ] && echo "FullDescription" > $R/usr/lib/enigma2/python/Components/Converter/MovieInfo.pyc || echo "ShortDescription" > $R/usr/lib/enigma2/python/Components/Converter/MovieInfo.pyc
	printf '#!/bin/sh\necho %s\n' $4 > $R/bin/python3; chmod +x $R/bin/python3
	local P=$(extract $V); sed -e "s#/usr/lib/enigma.info#$R/usr/lib/enigma.info#g; s#/usr/lib/enigma2/python#$R/usr/lib/enigma2/python#g; s#/usr/bin/enigma2_pre_start.sh#$R/hook#g; s#\[ -x /bin/busybox \]#false#" $P > $R/preinst
	local OUT; OUT=$(PATH=$R/bin:$PATH sh $R/preinst install 2>&1); local RC=$?
	local GOT=ok; [ $RC -ne 0 ] && GOT=stop
	if [ "$GOT" = "$7" ]; then PASS=$((PASS+1)); M=PASS; else FAILN=$((FAILN+1)); M=FAIL; fi
	printf '%-4s %-20s %-8s %-7s py%-5s -> %-4s  %s | %s\n' $M $V $2 $3 $4 $GOT "$8" "$(echo "$OUT" | grep -v '^CineView MLA: image' | tail -1)"
}
case_ 1.0.1~openatv.py313 openatv 7.6   3.13 1 1 ok   "OpenATV 7.6"
case_ 1.0.1~openatv.py313 openatv 7.6.1 3.13 1 1 ok   "OpenATV 7.6.x"
case_ 1.0.1~openatv.py314 openatv 8.1   3.14 1 1 ok   "OpenATV 8.1 (future)"
case_ 1.0.1~openatv.py314 openatv 9.0   3.14 1 1 ok   "OpenATV 9.0 (future)"
case_ 1.0.1~openatv.py312 openatv 7.5   3.12 0 0 stop "OpenATV 7.5 (no Addons, no FullDescription)"
case_ 1.0.1~openatv.py312 openatv 7.5   3.12 1 0 stop "OpenATV 7.5 with Addons but no FullDescription"
case_ 1.0.1~openatv.py312 openatv 7.5   3.12 1 1 ok   "OpenATV 7.5 build that has both components"
case_ 1.0.1~openatv.py313 openatv 7.4   3.13 1 1 stop "OpenATV 7.4 (below 7.5)"
case_ 1.0.1~openatv.py313 openatv 7.6   3.14 1 1 stop "wrong Python for the package"
case_ 1.0.1~openatv.py313 openvix 6.8   3.13 1 1 stop "wrong image"
case_ 1.0.1~openatv.py313 openatv abc   3.13 1 1 stop "unreadable version"
case_ 1.0.1~openbh.py313  openbh  5.6   3.13 1 1 ok   "OpenBH 5.6"
case_ 1.0.1~openbh.py313  openbh  5.7   3.13 1 1 ok   "OpenBH 5.7"
case_ 1.0.1~openbh.py314  openbh  6.0   3.14 1 1 ok   "OpenBH 6.0"
case_ 1.0.1~openbh.py314  openbh  6.1   3.14 1 1 ok   "OpenBH 6.1 (future)"
case_ 1.0.1~openbh.py313  openbh  5.5   3.13 1 1 stop "OpenBH 5.5 (below 5.6)"
case_ 1.0.1~openbh.py314  openbh  6.0   3.13 1 1 stop "wrong Python"
case_ 1.0.1~openvix.py312 openvix 6.7   3.12 1 1 ok   "OpenViX 6.7"
case_ 1.0.1~openvix.py313 openvix 6.8   3.13 1 1 ok   "OpenViX 6.8"
case_ 1.0.1~openvix.py314 openvix 6.9   3.14 1 1 ok   "OpenViX 6.9"
case_ 1.0.1~openvix.py314 openvix 7.0   3.14 1 1 ok   "OpenViX 7.0 (future)"
case_ 1.0.1~openvix.py312 openvix 6.6   3.12 1 1 stop "OpenViX 6.6 (below 6.7)"
case_ 1.0.1~openvix.py312 openvix 6.10  3.12 1 1 ok   "OpenViX 6.10 numeric compare"
case_ 1.0.1~openvix.py313 openbh  6.8   3.13 1 1 stop "wrong image"
echo "RESULT pass=$PASS fail=$FAILN"
