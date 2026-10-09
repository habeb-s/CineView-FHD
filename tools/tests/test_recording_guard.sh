#!/bin/sh
# Recording guard tests (POSIX sh; run under BusyBox, e.g. the alpine image): simulated OpenWebif + /proc.
# usage: sh tools/tests/test_recording_guard.sh <repo root>
R="${1:-.}"; PASS=0; FAIL=0; W="$(mktemp -d)"
. "$R/packaging/recording_guard.sh"
python3 -m http.server 18080 --bind 127.0.0.1 --directory "$W/www" >/dev/null 2>&1 &
SRV=$!; mkdir -p "$W/www/api"; sleep 1
webif(){ if [ "$1" = none ]; then rm -f "$W/www/api/statusinfo"; else printf '{\n "inStandby": "false",\n "isRecording": "%s"\n}\n' "$1" > "$W/www/api/statusinfo"; fi; }
proc(){  # proc <comm> <target file> <flags>
  rm -rf "$W/proc"; mkdir -p "$W/proc/123/fd" "$W/proc/123/fdinfo"
  [ -n "$1" ] || return 0
  echo "$1" > "$W/proc/123/comm"; touch "$2" 2>/dev/null; ln -s "$2" "$W/proc/123/fd/7"
  printf 'pos:\t0\nflags:\t%s\nmnt_id:\t23\n' "$3" > "$W/proc/123/fdinfo/7"
}
t(){  # t <expect active|idle> <label>
  if cv_recording_active; then got=active; else got=idle; fi
  if [ "$got" = "$1" ]; then PASS=$((PASS+1)); echo "PASS  $2 -> $got"; else FAIL=$((FAIL+1)); echo "FAIL  $2 -> $got (expected $1)"; fi
}
export CV_STATUS_URL="http://127.0.0.1:18080/api/statusinfo" CV_PROC="$W/proc"
mkdir -p "$W/movie" "$W/timeshift"
webif true;  proc "" "" "";                                      t active "OpenWebif isRecording=true"
webif false; proc "" "" "";                                      t idle   "OpenWebif isRecording=false, nothing open"
webif none;  proc enigma2 "$W/movie/rec.ts" 0100001;             t active "no OpenWebif, enigma2 writes rec.ts (O_WRONLY)"
webif none;  proc enigma2 "$W/movie/rec.ts" 0100002;             t active "no OpenWebif, enigma2 rec.ts O_RDWR"
webif none;  proc enigma2 "$W/movie/rec.ts.ap" 0102001;          t active "no OpenWebif, enigma2 writes rec.ts.ap"
webif none;  proc enigma2 "$W/movie/rec.ts" 0400000;             t idle   "no OpenWebif, enigma2 plays rec.ts (read only)"
webif none;  proc enigma2 "$W/timeshift/timeshift.ts" 0100001;   t idle   "no OpenWebif, timeshift file written"
webif none;  proc python3 "$W/movie/rec.ts" 0100001;             t idle   "no OpenWebif, other process writes .ts"
webif none;  proc enigma2 "$W/movie/notes.txt" 0100001;          t idle   "no OpenWebif, enigma2 writes a non-recording file"
webif false; proc enigma2 "$W/movie/rec.ts" 0100001;             t active "OpenWebif false but recording file open for writing"
export CV_STATUS_URL="http://127.0.0.1:1/none"; proc "" "" "";   t idle   "OpenWebif unreachable, nothing open"

# postinst: restart only when allowed (systemctl replaced by a logger)
mkdir -p "$W/bin"; printf '#!/bin/sh\necho "systemctl $*" >> %s/calls\n' "$W" > "$W/bin/systemctl"; chmod +x "$W/bin/systemctl"
sed "s/@VERSION@/9.9.9/g" "$R/packaging/postinst.in" > "$W/postinst"
touch /tmp/cineview-before-test-keep.tar.gz /tmp/cineview-test-drop.tmp
pi(){  # pi <expect restart|norestart> <label> [env]
  rm -f "$W/calls"; env PATH="$W/bin:$PATH" CV_STATUS_URL="http://127.0.0.1:18080/api/statusinfo" CV_PROC="$W/proc" $3 sh "$W/postinst" >/dev/null 2>&1
  if [ -s "$W/calls" ]; then got=restart; else got=norestart; fi
  if [ "$got" = "$1" ]; then PASS=$((PASS+1)); echo "PASS  postinst: $2 -> $got"; else FAIL=$((FAIL+1)); echo "FAIL  postinst: $2 -> $got (expected $1)"; fi
}
webif false; proc "" "" ""; pi restart   "idle receiver"
webif true;                 pi norestart "recording running"
webif false;                pi norestart "CINEVIEW_NO_RESTART=1 (online updater)" "CINEVIEW_NO_RESTART=1"
if [ -f /tmp/cineview-before-test-keep.tar.gz ] && [ ! -f /tmp/cineview-test-drop.tmp ]; then
  PASS=$((PASS+1)); echo "PASS  postinst keeps /tmp/cineview-before-* rollback backups, removes other temp files"
else FAIL=$((FAIL+1)); echo "FAIL  postinst /tmp cleanup"; fi
rm -f /tmp/cineview-before-test-keep.tar.gz
kill $SRV 2>/dev/null; rm -rf "$W"
echo "RESULT pass=$PASS fail=$FAIL"
[ "$FAIL" = 0 ]
