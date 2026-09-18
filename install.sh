#!/bin/sh
set -eu

TMP="/tmp/cineview-smart-installer.$$.sh"
ESC="$(printf '\033')"
GREEN="$ESC[32m"; YELLOW="$ESC[33m"; CYAN="$ESC[36m"; RED="$ESC[31m"; RESET="$ESC[0m"
cleanup(){ rm -f "$TMP"; }
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

if command -v python3 >/dev/null 2>&1; then PYVER="$(python3 -V 2>&1)"; elif command -v python >/dev/null 2>&1; then PYVER="$(python -V 2>&1)"; else PYVER="not found"; fi
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
RAW="https://raw.githubusercontent.com/habeb-s/CineView-FHD/fca657540468c2044d20a82a31420144acabc192"

printf "%s[CineView]%s Downloading CineView FHD 2.0 Smart Installer...\n" "$CYAN" "$RESET"
if command -v wget >/dev/null 2>&1; then
  wget -q --no-check-certificate -O "$TMP" "$RAW/cineview-smart-install.sh"
elif command -v curl >/dev/null 2>&1; then
  curl -fsSLk "$RAW/cineview-smart-install.sh" -o "$TMP"
else
  printf "%s[FAIL]%s wget/curl not found\n" "$RED" "$RESET" >&2
  exit 1
fi
[ -s "$TMP" ] || { printf "%s[FAIL]%s download failed\n" "$RED" "$RESET" >&2; exit 1; }

# Bootstrap safety: allow reinstalling CineView when the receiver already has
# the same package version. This keeps upgrades/repairs idempotent on opkg images.
if [ "$PM" = opkg ]; then
  sed -i 's/^Version: 2\.0$/Version: 2.0.1/' "$TMP" 2>/dev/null || true
  sed -i 's|opkg install "$PKGFILE" || fail "opkg installation failed"|opkg install --force-reinstall "$PKGFILE" || fail "opkg installation failed"|' "$TMP" 2>/dev/null || true
fi

chmod 755 "$TMP"
printf "%s[CineView]%s Installer downloaded. Starting profile-aware preflight...\n" "$CYAN" "$RESET"

CINEVIEW_PROFILE="$PROFILE" \
CINEVIEW_DISTRO="$DISTRO_ID" \
CINEVIEW_IMAGE_NAME="$IMAGE_NAME" \
CINEVIEW_IMAGE_VERSION="$IMAGE_VERSION" \
CINEVIEW_IMAGE_BUILD="$IMAGE_BUILD" \
/bin/sh "$TMP" --restart

RC=$?
rm -f "$TMP"
trap - EXIT INT TERM
[ "$RC" -eq 0 ] && printf "%s[DONE]%s Installer file removed.\n" "$GREEN" "$RESET"
exit "$RC"
