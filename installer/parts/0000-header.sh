#!/bin/sh
# CineView FHD 2.0 Smart Universal Installer
# Designed by habeb-s
set -u
SELF="$0"
RESTART=1
DRY=0
for a in "$@"; do
  case "$a" in --restart) RESTART=1;; --dry-run) DRY=1;; --no-restart) RESTART=0;; esac
done
ESC="$(printf '\033')"
RESET="${ESC}[0m"; BOLD="${ESC}[1m"; GREEN="${ESC}[32m"; YELLOW="${ESC}[33m"; BLUE="${ESC}[34m"; CYAN="${ESC}[36m"; RED="${ESC}[31m"
say(){ printf "%s[CineView]%s %s\n" "$CYAN" "$RESET" "$*"; }
ok(){ printf "%s[OK]%s %s\n" "$GREEN" "$RESET" "$*"; }
missing(){ printf "%s[MISSING]%s %s\n" "$YELLOW" "$RESET" "$*"; }
installing(){ printf "%s[INSTALL]%s %s\n" "$BLUE" "$RESET" "$*"; }
adapt(){ printf "%s[ADAPT]%s %s\n" "$CYAN" "$RESET" "$*"; }
warn(){ printf "%s[WARN]%s %s\n" "$YELLOW" "$RESET" "$*"; }
done_msg(){ printf "%s[DONE]%s %s\n" "$GREEN" "$RESET" "$*"; }
fail(){ printf "%s[FAIL]%s %s\n" "$RED" "$RESET" "$*" >&2; exit 1; }
havepy(){ ls "$1".py* >/dev/null 2>&1; }
printf "\n%s%s========================================%s\n" "$BOLD" "$CYAN" "$RESET"
printf "%s%s   CineView FHD 2.0 Smart Installer%s\n" "$BOLD" "$GREEN" "$RESET"
printf "%s      Designed by habeb-s%s\n" "$CYAN" "$RESET"
printf "%s%s========================================%s\n\n" "$BOLD" "$CYAN" "$RESET"
[ "$(id -u 2>/dev/null)" = 0 ] || fail "run as root"
TMP=$(mktemp -d /tmp/cineview-smart.XXXXXX 2>/dev/null || echo /tmp/cineview-smart.$$)
mkdir -p "$TMP" || fail "cannot create temporary directory"
trap 'rm -rf "$TMP"' EXIT INT TERM

IMG=$(cat /etc/image-version /etc/issue /etc/os-release /etc/hostname 2>/dev/null | tr '\n' ' ')
LOW=$(echo "$IMG" | tr 'A-Z' 'a-z')
case "$LOW" in
  *openpli*) FAMILY=openpli;;
  *dreamos*|*dreambox*|*gemini*|*merlin*) FAMILY=dreamos;;
  *openatv*|*openvix*|*openbh*|*openblackhole*|*opendroid*|*openspa*|*pure2*|*puree2*|*egami*|*teamblue*|*openhdf*|*nonsolosat*|*opentr*|*cobralib*|*satlodge*|*foxbob*|*pkteam*|*hyperion*|*vti*) FAMILY=oealliance;;
  *) FAMILY=generic;;
esac
if command -v opkg >/dev/null 2>&1; then PM=opkg; elif command -v apt-get >/dev/null 2>&1; then PM=apt; else PM=none; fi
if command -v python3 >/dev/null 2>&1; then PY=python3; elif command -v python >/dev/null 2>&1; then PY=python; else fail "Python is required by Enigma2 but was not found"; fi
PYVER=$($PY -V 2>&1 | head -n1)
ARCH=$(uname -m 2>/dev/null || echo unknown)
printf "%s--- Receiver / Image Detection ---%s\n" "$BOLD" "$RESET"
ok "Image family: $FAMILY"
ok "Package manager: $PM"
ok "Python: $PYVER"
ok "Architecture: $ARCH"
echo
printf "%s--- Dependency Preflight ---%s\n" "$BOLD" "$RESET"
ok "CineViewPosterX: built-in renderer will be installed (independent from image PosterX)"
if havepy /usr/lib/enigma2/python/Components/Sources/OAWeather; then ok "OAWeather: installed"; elif havepy /usr/lib/enigma2/python/Components/Sources/MSNWeather; then ok "WeatherPlugin: installed"; else missing "Weather provider: not installed -> will try OAWeather / WeatherPlugin"; fi
if command -v bitrate >/dev/null 2>&1; then ok "Bitrate: installed"; else missing "Bitrate: not installed -> will try to install"; fi
if "$PY" -c 'import requests' >/dev/null 2>&1; then ok "Python requests: installed"; else missing "Python requests: not installed -> will try to install"; fi
if [ -d /usr/lib/enigma2/python/Plugins/Extensions/IMDb ]; then ok "IMDb plugin: installed"; else missing "IMDb plugin: optional, will install when available"; fi
echo
printf "%s--- Compatibility Preflight ---%s\n" "$BOLD" "$RESET"
NEED_ADAPT=0
if ! havepy /usr/lib/enigma2/python/Components/Converter/PliExtraInfo; then adapt "PliExtraInfo missing -> CineViewTransponder fallback will be applied"; NEED_ADAPT=1; fi
if ! havepy /usr/lib/enigma2/python/Components/Converter/ServiceOrbitalPosition; then adapt "ServiceOrbitalPosition missing -> CineView orbital fallback will be applied"; NEED_ADAPT=1; fi
if ! havepy /usr/lib/enigma2/python/Components/Renderer/RunningText; then adapt "RunningText missing -> safe Label renderer will be used"; NEED_ADAPT=1; fi
if [ "$FAMILY" = generic ]; then adapt "Unknown/Generic image -> capability-based compatibility mode enabled"; NEED_ADAPT=1; fi
if [ "$NEED_ADAPT" = 0 ]; then ok "Image components are directly compatible"; else adapt "CineView will modify the staged skin automatically before installation"; fi
echo

FREE=$(df -Pk /usr 2>/dev/null | awk 'NR==2{print $4}')
[ -z "$FREE" ] && FREE=999999
[ "$FREE" -ge 15360 ] 2>/dev/null || fail "less than 15 MB free on /usr"

LINE=$(awk '/^__CINEVIEW_PAYLOAD_BELOW__$/{print NR+1; exit}' "$SELF")
[ -n "$LINE" ] || fail "embedded payload marker missing"
sed -n "${LINE},\$p" "$SELF" > "$TMP/payload.b64"
if command -v base64 >/dev/null 2>&1; then
  base64 -d "$TMP/payload.b64" > "$TMP/payload.tar.gz" 2>/dev/null || fail "payload decode failed"
elif command -v openssl >/dev/null 2>&1; then
  openssl base64 -d -in "$TMP/payload.b64" -out "$TMP/payload.tar.gz" >/dev/null 2>&1 || fail "payload decode failed"
else
  "$PY" - "$TMP/payload.b64" "$TMP/payload.tar.gz" <<'PY'
import sys,base64
open(sys.argv[2],'wb').write(base64.b64decode(open(sys.argv[1],'rb').read()))
PY
fi
mkdir -p "$TMP/stage"
tar -xzf "$TMP/payload.tar.gz" -C "$TMP/stage" || fail "payload extract failed"
PLUGSTAGE="$TMP/stage/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl"
SKINSTAGE="$TMP/stage/usr/share/enigma2/CineView_FHD"
[ -f "$SKINSTAGE/skin.xml" ] || fail "skin payload incomplete"

if [ "$DRY" = 0 ] && [ -x "$PLUGSTAGE/smartdeps.sh" ]; then
  installing "Checking and installing missing components from the current image feed..."
  CINEVIEW_LOG="$TMP/dependencies.log" sh "$PLUGSTAGE/smartdeps.sh" --install >/dev/null 2>&1 || true
  grep 'installing ' "$TMP/dependencies.log" 2>/dev/null | sed 's/^.*installing /  -> installed: /' || true
  grep -E '=(OK|INSTALLED)$' "$TMP/dependencies.log" 2>/dev/null | tail -n 12 | sed 's/^/  /' || true
  grep -E '=(SAFE-FALLBACK|UNAVAILABLE)$' "$TMP/dependencies.log" 2>/dev/null | tail -n 12 | sed 's/^/  /' || true
else
  : > "$TMP/dependencies.log"
fi

adapt "Adapting CineView to this Enigma2 image..."
"$PY" "$PLUGSTAGE/compat.py" "$SKINSTAGE" /usr/lib/enigma2/python "$TMP/compat.json" >/dev/null 2>&1 || fail "compatibility adaptation failed"
PATCHED=$("$PY" - "$TMP/compat.json" <<'PY'
import json,sys
try:
    d=json.load(open(sys.argv[1]))
    print(d.get("patched_files",0))
except Exception:
    print(0)
PY
)
if [ "${PATCHED:-0}" -gt 0 ] 2>/dev/null; then
  adapt "Compatibility changes applied to $PATCHED skin file(s)"
  "$PY" - "$TMP/compat.json" <<'PY' 2>/dev/null | while IFS= read -r line; do adapt "$line"; done
import json,sys
d=json.load(open(sys.argv[1])); seen=[]
for acts in d.get("changes",{}).values():
    for a in acts:
        if a not in seen:
            seen.append(a); print("  " + a)
PY
else
  ok "No skin compatibility patch was required"
fi

# OpenATV compatibility: use OpenATV's native 7.6/8.x screen contracts.
# OpenATV 8 PluginBrowser uses pluginList/pluginGrid mandatory sources and must not
# be skinned with the OpenViX/OpenBH list bindings.
case "$LOW" in
  *openatv*)
    ATV_VERSION=$(printf '%s\n' "$IMG" | sed -n 's/.*version=\([^ ]*\).*/\1/p' | head -n1)
    [ -n "$ATV_VERSION" ] || ATV_VERSION=detected
    adapt "OpenATV detected ($ATV_VERSION) -> applying dedicated CineView FHD OpenATV screen contracts"
    "$PY" "$PLUGSTAGE/openatv_compat.py" "$SKINSTAGE" >/dev/null 2>&1 || fail "OpenATV screen compatibility patch failed"
    ok "OpenATV PluginBrowser list/grid, EventView, SecondInfoBar and EPG layouts adapted"
    ;;
esac

# OpenViX compatibility: force the stable classic PluginBrowser binding.
# Current OpenViX supports both classic <widget name="list"> and templated source/list
# modes. The classic path avoids grid/template regressions and duplicate PluginBrowser
# definitions while preserving the native PluginList component.
case "$LOW" in
  *openvix*)
    adapt "OpenViX detected -> applying stable native PluginBrowser list binding"
    "$PY" - "$SKINSTAGE" <<'PY'
from __future__ import print_function
import os, re, sys

root = sys.argv[1]
pattern = re.compile(
    r'\n?[ \t]*<screen\b(?=[^>]*\bname="PluginBrowser")[^>]*>.*?</screen>[ \t]*\n?',
    re.S
)
replacement = '''
	<screen name="PluginBrowser" position="fill" flags="wfNoBorder">
		<panel name="PigTemplate"/>
		<widget name="list" position="780,100" size="1110,912" scrollbarMode="showOnDemand"/>
	</screen>
'''

changed = 0
for name in os.listdir(root):
    if not (name.startswith("skin") and name.endswith(".xml")):
        continue
    path = os.path.join(root, name)
    try:
        data = open(path, "r").read()
    except Exception:
        continue
    matches = pattern.findall(data)
    if not matches:
        continue
    data = pattern.sub("\n", data)
    idx = data.rfind("</skin>")
    if idx < 0:
        continue
    data = data[:idx] + "\n" + replacement + "\n" + data[idx:]
    with open(path, "w") as fh:
        fh.write(data)
    changed += 1

print(changed)
if changed == 0:
    sys.exit(3)
PY
    PB_PATCHED=$?
    [ "$PB_PATCHED" = 0 ] || fail "OpenViX PluginBrowser compatibility patch failed"
    ok "OpenViX PluginBrowser switched to native classic list mode"
    ;;
esac

case "$LOW" in
  *openbh*|*openblackhole*)
    adapt "OpenBH detected -> applying dedicated CineView FHD plugin/EPG compatibility"
    "$PY" "$PLUGSTAGE/openbh_compat.py" "$SKINSTAGE" >/dev/null 2>&1 || fail "OpenBH screen compatibility patch failed"
    ok "OpenBH PluginBrowser / Extensions / EPG layouts adapted"
    if [ -f "$TMP/stage/usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py" ]; then
      ok "CineViewPosterX is embedded for OpenBH"
    else
      fail "CineViewPosterX missing from payload"
    fi
    ;;
esac

"$PY" - "$SKINSTAGE" <<'PY'
from __future__ import print_function
import os,sys
try:
    import xml.etree.ElementTree as ET
except Exception:
    sys.exit(2)
root=sys.argv[1]; bad=[]; n=0
for base,dirs,files in os.walk(root):
    for name in files:
        if name.endswith('.xml'):
            n+=1
            p=os.path.join(base,name)
            try: ET.parse(p)
            except Exception as e: bad.append('%s: %s' % (p,e))
if bad:
    print('\n'.join(bad)); sys.exit(1)
print('validated %d XML files' % n)
PY
[ $? = 0 ] || fail "XML validation failed"

if [ "$DRY" = 1 ]; then
  ok "Dry-run passed: dependency logic and compatibility adaptation are valid"
  cat "$TMP/compat.json" 2>/dev/null || true
  exit 0
fi

STAMP=$(date +%Y%m%d-%H%M%S 2>/dev/null || echo now)
BACK=/etc/enigma2/cineview-backup-$STAMP.tar.gz
if [ -d /usr/share/enigma2/CineView_FHD ] || [ -d /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl ]; then
  tar -czf "$BACK" /usr/share/enigma2/CineView_FHD /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl /etc/enigma2/settings 2>/dev/null || true
  say "Backup: $BACK"
fi

PKGROOT="$TMP/pkg"
mkdir -p "$PKGROOT/CONTROL" || fail "cannot create package metadata"
cat > "$PKGROOT/CONTROL/control" <<'EOF'
Package: enigma2-plugin-skins-cineview-fhd
Version: 2.0.1
Architecture: all
Maintainer: habeb-s
Description: CineView FHD 2.0 Smart Enigma2 Skin
EOF
printf '2.0\n' > "$TMP/debian-binary"
tar -C "$PKGROOT/CONTROL" -czf "$TMP/control.tar.gz" . || fail "control package creation failed"
tar -C "$TMP/stage" -czf "$TMP/data.tar.gz" . || fail "data package creation failed"

if [ "$PM" = apt ]; then PKGFILE="/tmp/cineview-fhd-2.0-smart-$$.deb"; else PKGFILE="/tmp/cineview-fhd-2.0-smart-$$.ipk"; fi

"$PY" - "$PKGFILE" "$TMP/debian-binary" "$TMP/control.tar.gz" "$TMP/data.tar.gz" <<'PY'
from __future__ import print_function
import os, sys, time
out = sys.argv[1]
members = sys.argv[2:]
def b(x):
    return x if isinstance(x, bytes) else x.encode("ascii")
with open(out, "wb") as f:
    f.write(b("!<arch>\n"))
    for p in members:
        name = os.path.basename(p) + "/"
        data = open(p, "rb").read()
        header = ("%-16s%-12d%-6d%-6d%-8o%-10d`\n" % (name, int(time.time()), 0, 0, 0o100644, len(data)))
        f.write(b(header)); f.write(data)
        if len(data) & 1: f.write(b("\n"))
PY
[ -s "$PKGFILE" ] || fail "temporary package creation failed"
say "Temporary package: $PKGFILE"

installing "Installing CineView FHD 2.0..."
if [ "$PM" = opkg ]; then
  if opkg install "$PKGFILE"; then
    :
  else
    warn "Normal opkg install was refused (same version or cached state) -> retrying with --force-reinstall"
    opkg install --force-reinstall "$PKGFILE" || fail "opkg installation failed"
  fi
elif [ "$PM" = apt ]; then
  if command -v dpkg >/dev/null 2>&1; then dpkg -i "$PKGFILE" || fail "dpkg installation failed"; else fail "dpkg not found on apt image"; fi
else
  cp -a "$TMP/stage/usr/." /usr/ 2>/dev/null || cp -Rpf "$TMP/stage/usr/." /usr/ || fail "file installation failed"
fi
chmod 755 /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/*.sh 2>/dev/null || true

SETTINGS=/etc/enigma2/settings
[ -f "$SETTINGS" ] || touch "$SETTINGS"
set_key(){ key="$1"; val="$2"; if grep -q "^${key}=" "$SETTINGS" 2>/dev/null; then sed -i "s|^${key}=.*|${key}=${val}|" "$SETTINGS"; else echo "${key}=${val}" >> "$SETTINGS"; fi; }
get_key(){ grep "^$1=" "$SETTINGS" 2>/dev/null | tail -1 | cut -d= -f2-; }
[ -n "$(get_key config.plugins.cineview.theme)" ] || set_key config.plugins.cineview.theme black
[ -n "$(get_key config.plugins.cineview.poster_infobar)" ] || set_key config.plugins.cineview.poster_infobar True
[ -n "$(get_key config.plugins.cineview.poster_second)" ] || set_key config.plugins.cineview.poster_second True
[ -n "$(get_key config.plugins.cineview.poster_channels)" ] || set_key config.plugins.cineview.poster_channels True
[ -n "$(get_key config.plugins.cineview.weatherprovider)" ] || set_key config.plugins.cineview.weatherprovider oa
[ -n "$(get_key config.plugins.cineview.timeformat)" ] || set_key config.plugins.cineview.timeformat 24
[ -n "$(get_key config.plugins.cineview.servermode)" ] || set_key config.plugins.cineview.servermode profile
[ -n "$(get_key config.plugins.cineview.secondtimeout)" ] || set_key config.plugins.cineview.secondtimeout 20
set_key config.skin.primary_skin CineView_FHD/skin.xml
/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/activate.sh >/dev/null 2>&1 || true

REPORT=/etc/enigma2/cineview-smart-report.txt
{
  echo "CineView FHD 2.0 Smart Installer"
  echo "family=$FAMILY"
  echo "package_manager=$PM"
  echo "python=$PYVER"
  echo "arch=$ARCH"
  echo "installed=$(date 2>/dev/null || true)"
  echo "--- compatibility ---"
  cat "$TMP/compat.json" 2>/dev/null || true
  echo "--- dependencies ---"
  cat "$TMP/dependencies.log" 2>/dev/null || true
} > "$REPORT"
ok "CineView FHD 2.0 installed successfully"
say "Diagnostic report: $REPORT"
ok "Second InfoBar transparent overlay locked for all 6 themes"

if [ "$RESTART" = 1 ]; then
  installing "Restarting Enigma2 GUI..."
  if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^enigma2.service'; then
    systemctl restart enigma2.service || true
  elif command -v init >/dev/null 2>&1; then
    init 4; sleep 3; init 3
  elif command -v killall >/dev/null 2>&1; then
    killall -9 enigma2 2>/dev/null || true
  else
    warn "Automatic GUI restart is not supported on this image; restart Enigma2 manually"
  fi
else
  warn "Enigma2 restart skipped by --no-restart."
fi

if [ -n "${PKGFILE:-}" ] && [ -f "$PKGFILE" ]; then
  rm -f "$PKGFILE"
  ok "Temporary IPK/DEB installation package removed"
fi
done_msg "CineView FHD 2.0 installation complete"
exit 0
__CINEVIEW_PAYLOAD_BELOW__
