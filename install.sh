#!/bin/sh
set -eu

TMP="/tmp/cineview-smart-installer.$.sh"\nAUDIT_TMP="/tmp/cineview-openatv-auditfix.$.py"
ESC="$(printf '\033')"
GREEN="$ESC[32m"; YELLOW="$ESC[33m"; CYAN="$ESC[36m"; RED="$ESC[31m"; RESET="$ESC[0m"
cleanup(){ rm -f "$TMP" "$AUDIT_TMP"; }
trap cleanup EXIT INT TERM

iv_get(){
  key="$1"
  [ -f /etc/image-version ] || return 0
  awk -F '=' -v wanted="$key" '
    {
      k=$1
      gsub(/^[ \t]+|[ \t]+$/, "", k)
      if (tolower(k)==tolower(wanted)) {
        v=substr($0,index($0,"=")+1)
        gsub(/^[ \t]+|[ \t]+$/, "", v)
        print v
        exit
      }
    }' /etc/image-version 2>/dev/null
}

IMG="$(cat /etc/image-version /etc/issue /etc/os-release /etc/hostname 2>/dev/null | tr 'A-Z' 'a-z' | tr '\n' ' ')"
IMAGE_VERSION="$(iv_get Version)"
[ -n "$IMAGE_VERSION" ] || IMAGE_VERSION="$(iv_get imageversion)"
IMAGE_BUILD="$(iv_get Build)"
[ -n "$IMAGE_BUILD" ] || IMAGE_BUILD="$(iv_get imagebuild)"
DISTRO_ID="$(iv_get distro)"
DISTRO_ID="$(printf '%s' "$DISTRO_ID" | tr 'A-Z' 'a-z' | tr -d ' ')"

case "$IMG" in
  *openvix*) IMAGE_NAME="OpenViX"; DISTRO_ID=openvix; FAMILY=oealliance; PROFILE="oealliance/openvix" ;;
  *openbh*|*openblackhole*) IMAGE_NAME="OpenBH"; DISTRO_ID=openbh; FAMILY=oealliance; PROFILE="oealliance/openbh" ;;
  *opendroid*) IMAGE_NAME="OpenDroid"; DISTRO_ID=opendroid; FAMILY=oealliance; PROFILE="oealliance/opendroid" ;;
  *openatv*) IMAGE_NAME="OpenATV"; DISTRO_ID=openatv; FAMILY=oealliance; PROFILE="oealliance/openatv" ;;
  *openhdf*) IMAGE_NAME="OpenHDF"; DISTRO_ID=openhdf; FAMILY=oealliance; PROFILE="oealliance/openhdf" ;;
  *openspa*) IMAGE_NAME="OpenSPA"; DISTRO_ID=openspa; FAMILY=oealliance; PROFILE="oealliance/openspa" ;;
  *egami*) IMAGE_NAME="EGAMI"; DISTRO_ID=egami; FAMILY=oealliance; PROFILE="oealliance/egami" ;;
  *teamblue*) IMAGE_NAME="teamBlue"; DISTRO_ID=teamblue; FAMILY=oealliance; PROFILE="oealliance/teamblue" ;;
  *vti*) IMAGE_NAME="VTi"; DISTRO_ID=vti; FAMILY=oealliance; PROFILE="oealliance/vti" ;;
  *openpli*) IMAGE_NAME="OpenPLi"; DISTRO_ID=openpli; FAMILY=openpli; PROFILE="openpli" ;;
  *dreamos*|*dreambox*|*gemini*|*merlin*) IMAGE_NAME="DreamOS"; DISTRO_ID=dreamos; FAMILY=dreamos; PROFILE="dreamos" ;;
  *) IMAGE_NAME="$(iv_get Creator)"; [ -n "$IMAGE_NAME" ] || IMAGE_NAME="Unknown Enigma2 image"; FAMILY=generic; PROFILE="generic" ;;
esac

# OpenViX live-reference path: install the exact receiver snapshot captured on 2026-09-22.
if [ "$DISTRO_ID" = "openvix" ]; then
  LIVE_RAW="https://raw.githubusercontent.com/habeb-s/CineView-FHD/3c4519ba47ba59444ff2392507e67d9c133f14ec/install-openvix-live.sh"
  printf "%s[CineView]%s OpenViX detected -> using pinned live receiver snapshot installer.\n" "$CYAN" "$RESET"
  if command -v wget >/dev/null 2>&1; then
    wget -q --no-check-certificate -O "$TMP" "$LIVE_RAW"
  elif command -v curl >/dev/null 2>&1; then
    curl -fsSLk "$LIVE_RAW" -o "$TMP"
  else
    printf "%s[FAIL]%s wget/curl not found\n" "$RED" "$RESET" >&2
    exit 1
  fi
  [ -s "$TMP" ] || { printf "%s[FAIL]%s OpenViX live installer download failed\n" "$RED" "$RESET" >&2; exit 1; }
  chmod 755 "$TMP"
  /bin/sh "$TMP"
  RC=$?
  rm -f "$TMP"
  trap - EXIT INT TERM
  exit "$RC"
fi

# Official CineView FHD 2.1 OpenATV support gate.
if [ "$DISTRO_ID" != "openatv" ]; then
  printf "%s[FAIL]%s CineView FHD 2.1 supports OpenATV only. Detected: %s\n" "$RED" "$RESET" "$IMAGE_NAME" >&2
  exit 2
fi
case "$IMAGE_VERSION" in
  7.4*|7.5*|7.6*|8.0*) ;;
  *)
    printf "%s[FAIL]%s Unsupported OpenATV version: %s. Supported: 7.4, 7.5, 7.6, 8.0.\n" "$RED" "$RESET" "$IMAGE_VERSION" >&2
    exit 2
    ;;
esac

if command -v python3 >/dev/null 2>&1; then
  PYVER="$(python3 -V 2>&1)"
else
  printf "%s[FAIL]%s Python 3 is required by CineView FHD 2.1.\n" "$RED" "$RESET" >&2
  exit 2
fi
if command -v opkg >/dev/null 2>&1; then PM=opkg; elif command -v apt-get >/dev/null 2>&1; then PM=apt; else PM=none; fi
ARCH="$(uname -m 2>/dev/null || echo unknown)"
IMAGE_LINE="$IMAGE_NAME"
[ -n "$IMAGE_VERSION" ] && IMAGE_LINE="$IMAGE_LINE $IMAGE_VERSION"
[ -n "$IMAGE_BUILD" ] && IMAGE_LINE="$IMAGE_LINE build $IMAGE_BUILD"

printf "\n%s[CineView Smart Detection]%s\n" "$CYAN" "$RESET"
printf "%s[OK]%s Image: %s\n" "$GREEN" "$RESET" "$IMAGE_LINE"
printf "%s[OK]%s Profile: %s\n" "$GREEN" "$RESET" "$PROFILE"
printf "%s[OK]%s Python: %s\n" "$GREEN" "$RESET" "$PYVER"
printf "%s[OK]%s Package manager: %s\n" "$GREEN" "$RESET" "$PM"
printf "%s[OK]%s Architecture: %s\n" "$GREEN" "$RESET" "$ARCH"

case "$PROFILE" in
  oealliance/openbh)
    printf "%s[ADAPT]%s OpenBH detected -> OE-Alliance/OpenBH rules selected before installation.\n" "$CYAN" "$RESET"
    ;;
  oealliance/openvix)
    printf "%s[ADAPT]%s OpenViX detected -> OE-Alliance/OpenViX rules selected before installation.\n" "$CYAN" "$RESET"
    ;;
  oealliance/opendroid)
    printf "%s[ADAPT]%s OpenDroid detected -> OE-Alliance/OpenDroid rules selected before installation.\n" "$CYAN" "$RESET"
    ;;
  oealliance/openatv)
    case "$IMAGE_VERSION" in
      8* )
        printf "%s[ADAPT]%s OpenATV 8 detected -> dedicated receiver-matched OpenATV 8 screen contracts selected.\n" "$CYAN" "$RESET"
        ;;
      * )
        printf "%s[ADAPT]%s OpenATV detected -> dedicated OpenATV screen contracts selected.\n" "$CYAN" "$RESET"
        ;;
    esac
    ;;
  generic)
    printf "%s[ADAPT]%s Unknown image -> capability-only safe mode selected.\n" "$YELLOW" "$RESET"
    ;;
  *)
    printf "%s[ADAPT]%s %s compatibility profile selected.\n" "$CYAN" "$RESET" "$PROFILE"
    ;;
esac

# Verified image-aware OE-Alliance smart installer.
RAW="https://raw.githubusercontent.com/habeb-s/CineView-FHD/v2.1.1"

printf "%s[CineView]%s Downloading CineView FHD 2.1 OpenATV Installer...\n" "$CYAN" "$RESET"
if command -v wget >/dev/null 2>&1; then
  wget -q --no-check-certificate -O "$TMP" "$RAW/cineview-smart-install.sh"
elif command -v curl >/dev/null 2>&1; then
  curl -fsSLk "$RAW/cineview-smart-install.sh" -o "$TMP"
else
  printf "%s[FAIL]%s wget/curl not found\n" "$RED" "$RESET" >&2
  exit 1
fi
[ -s "$TMP" ] || { printf "%s[FAIL]%s download failed\n" "$RED" "$RESET" >&2; exit 1; }


chmod 755 "$TMP"
printf "%s[CineView]%s Installer downloaded. Starting profile-aware preflight...\n" "$CYAN" "$RESET"

CINEVIEW_PROFILE="$PROFILE" \
CINEVIEW_DISTRO="$DISTRO_ID" \
CINEVIEW_IMAGE_NAME="$IMAGE_NAME" \
CINEVIEW_IMAGE_VERSION="$IMAGE_VERSION" \
CINEVIEW_IMAGE_BUILD="$IMAGE_BUILD" \
/bin/sh "$TMP" --no-restart

RC=$?

if [ "$RC" -eq 0 ] && printf '%s' "$IMAGE_VERSION" | grep -q '^8'; then
  AUDIT_RAW="https://raw.githubusercontent.com/habeb-s/CineView-FHD/main/installer/openatv_auditfix.py"
  PLUGIN_DIR="/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl"
  printf "%s[ADAPT]%s Installing persistent OpenATV 8 audit hook...\n" "$CYAN" "$RESET"
  if command -v wget >/dev/null 2>&1; then
    wget -q --no-check-certificate -O "$AUDIT_TMP" "$AUDIT_RAW" || RC=1
  elif command -v curl >/dev/null 2>&1; then
    curl -fsSLk "$AUDIT_RAW" -o "$AUDIT_TMP" || RC=1
  else
    RC=1
  fi
  if [ "$RC" -eq 0 ] && [ -s "$AUDIT_TMP" ] && [ -d "$PLUGIN_DIR" ]; then
    cp -f "$AUDIT_TMP" "$PLUGIN_DIR/openatv_auditfix.py"
    chmod 644 "$PLUGIN_DIR/openatv_auditfix.py"
    python3 -m py_compile "$PLUGIN_DIR/openatv_auditfix.py" || RC=1
  else
    RC=1
  fi
  if [ "$RC" -eq 0 ] && [ -f "$PLUGIN_DIR/activate.sh" ]; then
    if ! grep -q 'openatv_auditfix.py' "$PLUGIN_DIR/activate.sh"; then
      HOOK_LINE='"$PY" "$PLUGIN/openatv_auditfix.py" "$SKIN/skin.xml" >/dev/null 2>&1 || true'
      HOOK_TMP="$PLUGIN_DIR/activate.sh.audit.$"
      awk -v hook="$HOOK_LINE" '{ print; if ($0 ~ /openatv_v5.py.*skin.xml/) print hook }' "$PLUGIN_DIR/activate.sh" > "$HOOK_TMP" || RC=1
      if [ "$RC" -eq 0 ]; then
        chmod --reference="$PLUGIN_DIR/activate.sh" "$HOOK_TMP" 2>/dev/null || chmod 755 "$HOOK_TMP"
        mv -f "$HOOK_TMP" "$PLUGIN_DIR/activate.sh"
      else
        rm -f "$HOOK_TMP"
      fi
    fi
    sh -n "$PLUGIN_DIR/activate.sh" || RC=1
    [ "$RC" -eq 0 ] && "$PLUGIN_DIR/activate.sh" || true
  else
    RC=1
  fi
  [ "$RC" -eq 0 ] || printf "%s[FAIL]%s OpenATV 8 audit hook installation failed.\n" "$RED" "$RESET" >&2
fi

rm -f "$TMP" "$AUDIT_TMP"
trap - EXIT INT TERM

if [ "$RC" -eq 0 ]; then
  printf "%s[CineView]%s Restarting Enigma2 once after final OpenATV adaptation...\n" "$CYAN" "$RESET"
  sync
  if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^enigma2.service'; then
    systemctl restart enigma2.service || true
  elif command -v killall >/dev/null 2>&1; then
    killall -9 enigma2 >/dev/null 2>&1 || true
  fi
fi

[ "$RC" -eq 0 ] && printf "%s[DONE]%s Installer files removed.\n" "$GREEN" "$RESET"
exit "$RC"
