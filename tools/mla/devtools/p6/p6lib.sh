R=~/cineview-mla/r.sh; RC=~/cineview-mla/rc.sh; S=~/cineview-mla/shots/p6; mkdir -p $S
g() { curl -s -m 20 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=osd&r=1920"; echo "cap $1 @$($R 'date +%T')"; }
X() { for i in 1 2 3 4; do $RC 174; sleep 0.6; done; sleep 1.5; }
up() { sleep 8; for i in $(seq 1 90); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 2; done; echo "webif up @$($R 'date +%T')"; }
st() { $R 'python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py status 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(\"STATE active=%s lkg=%s journal=%s theme=%s gens=%s\" % (d[\"active\"], d[\"lkg\"], (d[\"journal\"] or {}).get(\"state\"), d[\"selection\"][\"theme\"], d[\"generations\"]))"; echo "boot.count=$(cat /etc/enigma2/cineview_mla/boot.count) e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; tail -4 /etc/enigma2/cineview_mla/history.log 2>/dev/null'; }
openui() { X; $RC 399; sleep 3; $RC 106 106 106; sleep 1; $RC 352; sleep 4; }
e2log() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); grep -a "CineViewMLA\]\|Traceback\|Error" $f | grep -v "SetupSummary\|ePyObject\]" | tail -'${1:-15}; }
pid() { $R 'pidof enigma2'; }
newe2() { old=$1; for i in $(seq 1 120); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$old" ] && break; sleep 2; done; echo "new e2 pid=$p @$($R 'date +%T')"; up; }
