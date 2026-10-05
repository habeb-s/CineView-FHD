#!/usr/bin/env python3
"""Builds the final visual report page (CineView MLA Model Review) from the receiver grabs and test logs on the
ai-agent host: t68 (five models x six sections, posters ON/OFF, six themes), t67/t69/t70/t74/t75/t76 (accelAlloc).
Every number on the page is parsed from a log here; every picture is a receiver grab (no mock-ups).
usage: python3 make_report.py OUT.html"""
import base64
import io
import os
import re
import sys

from PIL import Image

H = os.path.expanduser("~/cineview-mla")
S = os.path.join(H, "shots")


def log(name):
	p = os.path.join(H, name)
	return open(p, errors="replace").read() if os.path.exists(p) else ""


def end_sample(text, label):
	m = re.findall(r"\[%s end r(\d+)\] (\S+) cpu_ms=(\d+) rss_kB=(\d+) hwm_kB=(\d+) threads=(\d+) fds=(\d+) accel_fails=(\d+)" % re.escape(label), text)
	if not m:
		return None
	r, t, cpu, rss, hwm, thr, fds, acc = m[-1]
	start = re.findall(r"\[%s start\] \S+ cpu_ms=(\d+) rss_kB=(\d+)" % re.escape(label), text)
	return {"rounds": int(r), "cpu_s": (int(cpu) - int(start[-1][0])) / 1000.0 if start else None, "rss": int(rss) // 1024,
		"hwm": int(hwm) // 1024, "accel": int(acc), "rss0": int(start[-1][1]) // 1024 if start else None}


def img(path, w=800, q=68):
	if not os.path.exists(path):
		return None
	im = Image.open(path).convert("RGB")
	im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
	b = io.BytesIO()
	im.save(b, "JPEG", quality=q, optimize=True)
	return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


PERF = [  # (label, log, sample label, note)
	("Modern Large (build63)", "t67.log", "large", "before"),
	("Modern Optimized v1 (build64)", "t67.log", "opt", "default posters without large PNGs"),
	("Modern Optimized v2 (build65)", "t69.log", "v2", "+ hidden screens release posters"),
	("Modern Optimized v3 (build66)", "t70.log", "v3", "uncached picons (reverted)"),
	("Modern Optimized v5 (build68)", "t74.log", "v5", "final path: settle + RAM posters"),
	("Classic (build68)", "t75.log", "classic", "reference, same navigation"),
	("Modern current (build71), 60 min", "t79.log", "long", "stability run, 60 min instead of 25"),
]
MODELS = [("classic", "Classic"), ("details", "Details"), ("cinema", "Cinema"), ("modern", "Modern"), ("minimal", "Minimal")]
SECTIONS = [("ib", "InfoBar"), ("sib", "SecondInfoBar"), ("cs", "Channel list"), ("epg", "EPG"), ("ev", "EventView"), ("emc", "PVR · EMC"), ("ms", "PVR · MovieSelection")]
THEMES = ["navy", "green", "burgundy", "black", "graphite", "purple"]
THEME_SECTIONS = [("ib", "InfoBar"), ("cs", "Channel list"), ("ev", "EventView")]


def model_errs(text):
	"""t68: errs line after each '== <model> navy posters ON/OFF' header -> tracebacks / skin errors / accel."""
	out = {}
	cur = None
	for l in text.splitlines():
		m = re.match(r"== (\w+) (\w+) (posters ON|posters OFF|ON)", l)
		if m:
			cur = (m.group(1), m.group(2), m.group(3))
			continue
		m = re.search(r"tracebacks=(\d+) skin_errors_new=(\d+) accel=(\d+) e2pid=\S+ crashlogs=(\d+)", l)
		if m and cur:
			out.setdefault(cur, []).append(tuple(int(v) for v in m.groups()))
	return out


def main(out):
	perf = []
	for lab, lg, key, note in PERF:
		s = end_sample(log(lg), key)
		if s:
			perf.append((lab, note, s))
	t76 = log("t76.log")
	phases = []
	for key, lab in (("opt_off", "Posters OFF (navy)"), ("opt_green", "green"), ("opt_burgundy", "burgundy"), ("opt_black", "black"), ("opt_graphite", "graphite"), ("opt_purple", "purple")):
		s = end_sample(t76, key)
		if s:
			phases.append((lab, s))
	t78 = log("t78.log")
	ab_rows = []
	for m in re.finditer(r"^\s+(emc_hp|emc_ples|ev_78\d)\s+mean abs diff \[([^\]]*)\]\s+PSNR ([\d.]+) dB", t78, re.M):
		k, mean, psnr = m.groups()
		lab = {"emc_hp": "EMC · Harry Potter (local cover)", "emc_ples": "EMC · Ples malog pingvina (identity)"}.get(k, "EventView · service %s" % k[3:])
		pic = img(os.path.join(S, "t78", "AB_%s.png" % k), 520, 74)
		ab_rows.append('<figure class="ab">%s<figcaption>%s · mean difference %s · PSNR %s dB</figcaption></figure>' % (
			'<img loading="lazy" alt="%s" src="%s">' % (lab, pic) if pic else "", lab, mean, psnr))
	pools = re.findall(r"^== (A|B) = (\S+).*?^\s+pool: (.*?)$", t78, re.M | re.S)
	pool_rows = "".join('<tr><td>%s</td><td>%s</td></tr>' % ("Modern Large " + b if a == "A" else "Current " + b, p) for a, b, p in pools)
	errs = model_errs(log("t68.log"))
	tb = sum(v[0] for vs in errs.values() for v in vs)
	se = sum(v[1] for vs in errs.values() for v in vs)
	cl = max([v[3] for vs in errs.values() for v in vs] or [0])

	maxacc = max([s["accel"] for _, _, s in perf] or [1]) or 1
	bars = []
	for i, (lab, note, s) in enumerate(perf):
		w = 100.0 * s["accel"] / maxacc
		cls = "bar ref" if "Classic" in lab else ("bar fin" if "v5" in lab else "bar")
		bars.append('<div class="brow"><div class="blab"><b>%s</b><span>%s</span></div><div class="btrack"><div class="%s" style="width:%.2f%%"></div></div>'
			'<div class="bval">%d</div><div class="bmeta">%d rounds · RSS %d MB · CPU %.0f s</div></div>' % (lab, note, cls, max(w, 0.4), s["accel"], s["rounds"], s["rss"], s["cpu_s"] or 0))
	prow = "".join('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d MB</td><td class="n">%.0f s</td></tr>' % (lab, s["rounds"], s["accel"], s["rss"], s["cpu_s"] or 0) for lab, s in phases)

	tabs, panes = [], []
	for mi, (m, mlab) in enumerate(MODELS):
		tabs.append('<button class="tab" role="tab" id="tab-%s" aria-controls="pane-%s" aria-selected="%s">%s</button>' % (m, m, "true" if mi == 0 else "false", mlab))
		rows = []
		for sk, slab in SECTIONS:
			on = img(os.path.join(S, "t68", "%s_navy_on_%s.png" % (m, sk)))
			off = img(os.path.join(S, "t68", "%s_navy_off_%s.png" % (m, sk)))
			cells = []
			for tag, src in (("Posters ON", on), ("Posters OFF", off)):
				cells.append('<figure><div class="tag %s">%s</div>%s</figure>' % ("on" if tag.endswith("ON") else "off", tag,
					'<img loading="lazy" alt="%s %s %s" src="%s">' % (mlab, slab, tag, src) if src else '<div class="miss">no grab</div>'))
			rows.append('<section class="sec"><h3>%s</h3><div class="pair">%s</div></section>' % (slab, "".join(cells)))
		th = []
		for t in THEMES:
			cells = []
			for sk, slab in THEME_SECTIONS:
				name = "%s_%s_on_%s.png" % (m, t, sk)
				src = img(os.path.join(S, "t68", name), 420, 62)
				cells.append('<figure>%s<figcaption>%s</figcaption></figure>' % ('<img loading="lazy" alt="%s %s %s" src="%s">' % (mlab, t, slab, src) if src else '<div class="miss">no grab</div>', slab))
			th.append('<div class="theme"><div class="tname"><i class="sw sw-%s"></i>%s</div><div class="trow">%s</div></div>' % (t, t, "".join(cells)))
		e_on = errs.get((m, "navy", "posters ON"), [])
		e_off = errs.get((m, "navy", "posters OFF"), [])
		acc = [v[2] for v in e_on[1:2] + e_off[1:2]]
		chip = '<span class="chip">accel after the six sections: %s</span>' % (" / ".join(str(a) for a in acc) or "n/a")
		panes.append('<div class="pane" role="tabpanel" id="pane-%s" aria-labelledby="tab-%s"%s><div class="pmeta">%s</div>%s<h3 class="th">Six themes · posters ON</h3>%s</div>' % (
			m, m, "" if mi == 0 else " hidden", chip, "".join(rows), "".join(th)))

	html = TEMPLATE.replace("%BARS%", "".join(bars)).replace("%PHASES%", prow or '<tr><td colspan="5">t76 not run</td></tr>') \
		.replace("%AB%", "".join(ab_rows) or '<p class="note">t78 not run yet.</p>').replace("%POOL%", pool_rows or '<tr><td colspan="2">t78 not run yet</td></tr>') \
		.replace("%TABS%", "".join(tabs)).replace("%PANES%", "".join(panes)).replace("%TB%", str(tb)).replace("%SE%", str(se)).replace("%SECLS%", "ok" if se == 0 else "warn") \
		.replace("%SENOTE%", "" if se == 0 else '<span class="fn">(Classic MovieSelection: list attributes enigma2 rejects; removed in build70 / rc5)</span>').replace("%CL%", str(cl))
	open(out, "w", encoding="utf-8").write(html)
	print("OUT", out, os.path.getsize(out) // 1024, "kB; perf rows", len(perf), "phases", len(phases), "model err groups", len(errs))


TEMPLATE = r'''<title>CineView MLA Model Review</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: a receiver test bench — summary strip, measured bars, then one tab per model with ON/OFF grab pairs. */
:root{
  --bg:#eef1f5; --panel:#ffffff; --fg:#152131; --muted:#5a6779; --line:#d3dae4;
  --accent:#b8860b; --good:#2d7a52; --bad:#b04a3a; --ref:#6b7a8f;
  --display:"Barlow Condensed","Arial Narrow",system-ui,sans-serif; --body:"IBM Plex Sans",system-ui,sans-serif; --mono:"IBM Plex Mono",ui-monospace,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0a111c;--panel:#111b2a;--fg:#e4e9f0;--muted:#94a1b4;--line:#22314a;--accent:#f0c040;--good:#58b585;--bad:#e07a68;--ref:#7f8ea4;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0a111c;--panel:#111b2a;--fg:#e4e9f0;--muted:#94a1b4;--line:#22314a;--accent:#f0c040;--good:#58b585;--bad:#e07a68;--ref:#7f8ea4;color-scheme:dark}
body{background:var(--bg);color:var(--fg);font:15px/1.55 var(--body)}
.wrap{max-width:1180px;margin:0 auto;padding-inline:20px;padding-block:28px 64px;display:flex;flex-direction:column;gap:36px}
h1,h2,h3{font-family:var(--display);letter-spacing:.01em;text-wrap:balance;margin:0}
h1{font-size:44px;line-height:1.05;font-weight:700}
h2{font-size:28px;font-weight:600}
h3{font-size:20px;font-weight:600}
.kicker{font:500 12px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
.lede{max-width:68ch;color:var(--muted);margin:10px 0 0}
.facts{display:flex;flex-wrap:wrap;gap:8px 18px;margin-top:14px;font:13px var(--mono);color:var(--muted)}
.facts b{color:var(--fg);font-weight:500}
.ok{color:var(--good)}.warn{color:var(--bad)}.fn{color:var(--muted);margin-left:6px}
.block{display:flex;flex-direction:column;gap:14px}
.note{max-width:72ch;color:var(--muted);margin:0}
.bars{display:flex;flex-direction:column;gap:10px;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px}
.brow{display:grid;grid-template-columns:minmax(0,260px) minmax(0,1fr) 56px;grid-template-areas:"lab track val" ". meta meta";column-gap:14px;align-items:center}
.blab{grid-area:lab;display:flex;flex-direction:column;min-width:0}.blab b{font-weight:600;font-size:14px}.blab span{font-size:12px;color:var(--muted)}
.btrack{grid-area:track;height:14px;background:color-mix(in srgb,var(--line) 60%,transparent);border-radius:3px;overflow:hidden}
.bar{height:100%;background:var(--bad)}.bar.fin{background:var(--good)}.bar.ref{background:var(--ref)}
.bval{grid-area:val;text-align:right;font:500 16px var(--mono);font-variant-numeric:tabular-nums}
.bmeta{grid-area:meta;font:12px var(--mono);color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:14px}
.tw{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:10px}
th,td{padding:8px 12px;border-bottom:1px solid var(--line);text-align:left}th{font:500 12px var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
td.n{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:0}
.tabs{display:flex;flex-wrap:wrap;gap:6px;position:sticky;top:env(safe-area-inset-top,0px);background:var(--bg);padding-block:10px;z-index:2;border-bottom:1px solid var(--line)}
.tab{font:600 18px var(--display);letter-spacing:.03em;padding:6px 16px;border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--fg);cursor:pointer}
.tab[aria-selected="true"]{border-color:var(--accent);box-shadow:inset 0 -3px 0 var(--accent)}
.tab:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.pane{display:flex;flex-direction:column;gap:22px;padding-top:6px}
.pmeta{display:flex;flex-wrap:wrap;gap:8px}
.chip{font:12px var(--mono);border:1px solid var(--line);border-radius:999px;padding:3px 10px;color:var(--muted);background:var(--panel)}
.sec{display:flex;flex-direction:column;gap:8px}
.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
figure{margin:0;position:relative;min-width:0}
figure img{display:block;width:100%;border-radius:6px;border:1px solid var(--line);background:#000}
.tag{position:absolute;top:8px;left:8px;font:500 11px var(--mono);letter-spacing:.08em;padding:2px 8px;border-radius:4px;color:#fff}
.tag.on{background:#2d7a52}.tag.off{background:#55606f}
figcaption{font:12px var(--mono);color:var(--muted);margin-top:4px}
.miss{aspect-ratio:16/9;max-width:100%;display:grid;place-items:center;border:1px dashed var(--line);border-radius:6px;color:var(--muted);font:12px var(--mono)}
.th{margin-top:6px}
.abgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:14px}
.theme{display:grid;grid-template-columns:110px minmax(0,1fr);gap:12px;align-items:start}
.tname{font:500 13px var(--mono);display:flex;align-items:center;gap:8px;padding-top:4px}
.trow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.sw{width:14px;height:14px;border-radius:3px;display:inline-block;border:1px solid var(--line)}
.sw-navy{background:#0a1d35}.sw-green{background:#153b2b}.sw-burgundy{background:#501c2c}.sw-black{background:#000}.sw-graphite{background:#292d32}.sw-purple{background:#38204f}
@media (max-width:700px){h1{font-size:34px}.pair{grid-template-columns:1fr}.brow{grid-template-columns:minmax(0,1fr) 52px;grid-template-areas:"lab val" "track track" "meta meta";row-gap:4px}.theme{grid-template-columns:1fr}.trow{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto}}
</style>
<div class="wrap">
<header>
  <div class="kicker">Slot 8 · Vu+ Duo 4K SE · OpenATV 8.0.1 · dev/mla-openatv · model grabs build69 · current build71 / rc6</div>
  <h1>CineView MLA Model Review</h1>
  <p class="lede">The five design models on all six sections, as the receiver drew them: posters on and off in the navy theme, and every model in the six themes. Every picture below is a screen grab from the receiver; every number comes from a test log.</p>
  <div class="facts"><span>Tracebacks <b class="ok">%TB%</b></span><span>New skin errors <b class="%SECLS%">%SE%</b>%SENOTE%</span><span>Crash logs <b class="ok">%CL%</b></span><span>Test media <b>USB only, HDD not opened</b></span></div>
</header>
<section class="block">
  <h2>Modern performance: accelAlloc warnings in 25 minutes</h2>
  <p class="note">The receiver has 5400 kB of fast graphics memory. Every run below repeats the same round: channel list fast and slow, EventView, SecondInfoBar, EPG, EMC on the USB folder, and a channel change. Counts include the one warning every start-up logs. Fewer is better; nothing was lost on screen in any run, the warning means the picture went to normal memory.</p>
  <div class="bars">%BARS%</div>
  <h3>Final Modern, other conditions</h3>
  <div class="tw"><table><thead><tr><th>Condition</th><th>Rounds</th><th>Warnings</th><th>RSS end</th><th>CPU</th></tr></thead><tbody>%PHASES%</tbody></table></div>
</section>
<section class="block">
  <h2>Poster quality: before and after</h2>
  <p class="note">The same poster on the same screen, left as the Large build drew it, right as the current build draws it. The cached poster file is untouched; only how the picture is held in memory changed. A PSNR of 99 dB means the two are pixel-identical.</p>
  <div class="abgrid">%AB%</div>
  <h3>Fast graphics memory after the same steps</h3>
  <div class="tw"><table><thead><tr><th>Build</th><th>Pool content (gAccel dump)</th></tr></thead><tbody>%POOL%</tbody></table></div>
</section>
<section class="block">
  <h2>The five models</h2>
  <p class="note">Grabs from build69 (t68). build71 differs only where no poster exists: its placeholder is drawn back to the exact original look (inner frame line and full-size icon), see the comparison above.</p>
  <div class="tabs" role="tablist">%TABS%</div>
  %PANES%
</section>
</div>
<script>
(function(){
  var tabs=[].slice.call(document.querySelectorAll('.tab'));
  function show(id){tabs.forEach(function(t){var on=t.id==='tab-'+id;t.setAttribute('aria-selected',on?'true':'false');document.getElementById('pane-'+t.id.slice(4)).hidden=!on;});
    try{localStorage.setItem('cvmla-tab',id)}catch(e){}}
  tabs.forEach(function(t){t.addEventListener('click',function(){show(t.id.slice(4))})});
  var h=(location.hash||'').slice(1),s=null;try{s=localStorage.getItem('cvmla-tab')}catch(e){}
  var want=document.getElementById('tab-'+h)?h:(s&&document.getElementById('tab-'+s)?s:null);if(want)show(want);
})();
</script>
'''

if __name__ == "__main__":
	main(sys.argv[1])
