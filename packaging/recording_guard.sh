# >>> cineview recording guard >>>
# Canonical copy: packaging/recording_guard.sh (tools/sync_recording_guard.py copies it into every script that
# restarts Enigma2; tools/tests/test_recording_guard.sh checks the copies).  POSIX / BusyBox sh.
# cv_recording_active returns 0 while Enigma2 is recording:
#   1. OpenWebif /api/statusinfo reports "isRecording": "true" (when OpenWebif is installed and answers), or
#   2. the enigma2 process holds a recording file (*.ts) open for writing (timeshift files are ignored).
# CV_STATUS_URL / CV_PROC exist only for the tests.
cv_recording_active(){
  _cv_s=""
  if command -v wget >/dev/null 2>&1; then
    _cv_s="$(wget -q -T 3 -O - "${CV_STATUS_URL:-http://127.0.0.1/api/statusinfo}" 2>/dev/null || true)"
  elif command -v curl >/dev/null 2>&1; then
    _cv_s="$(curl -fsS -m 3 "${CV_STATUS_URL:-http://127.0.0.1/api/statusinfo}" 2>/dev/null || true)"
  fi
  case "$_cv_s" in
    *'"isRecording": "true"'*|*'"isRecording":"true"'*|*'"isRecording": true'*|*'"isRecording":true'*) return 0 ;;
  esac
  _cv_p="${CV_PROC:-/proc}"
  for _cv_c in "$_cv_p"/[0-9]*/comm; do
    [ -r "$_cv_c" ] || continue
    [ "$(cat "$_cv_c" 2>/dev/null)" = enigma2 ] || continue
    _cv_d="${_cv_c%/comm}"
    for _cv_f in "$_cv_d"/fd/*; do
      _cv_t="$(readlink "$_cv_f" 2>/dev/null)" || continue
      case "$_cv_t" in
        *timeshift*) continue ;;
        *.ts|*.ts.*) ;;
        *) continue ;;
      esac
      _cv_fl="$(sed -n 's/^flags:[[:space:]]*//p' "$_cv_d/fdinfo/${_cv_f##*/}" 2>/dev/null || true)"
      case "$_cv_fl" in
        *1|*2|*3|*5|*6|*7) return 0 ;;  # O_WRONLY / O_RDWR
      esac
    done
  done
  return 1
}
cv_recording_warn(){
  echo "[CineView][WARN] A recording is in progress - Enigma2 was NOT restarted."
  echo "[CineView][WARN] Restart Enigma2 after the recording has finished to activate the changes."
}
# <<< cineview recording guard <<<
