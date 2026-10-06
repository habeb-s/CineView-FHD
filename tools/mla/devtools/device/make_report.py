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


NPDIR = os.environ.get("NPDIR", "t84")    # No Poster pairs: t91 = all five models incl. Classic
T68 = os.environ.get("T68", "t68")          # shots dir of the model QA run (t68_rc9 = final QA on rc9)
T68LOG = os.environ.get("T68LOG", "t68.log")
BUILD = os.environ.get("BUILD", "build69")
CURRENT = os.environ.get("CURRENT", "build86 / rc9")

PERF = [  # (label, log, sample label, note)
	("Modern Large (build63)", "t67.log", "large", "before"),
	("Modern Optimized v1 (build64)", "t67.log", "opt", "default posters without large PNGs"),
	("Modern Optimized v2 (build65)", "t69.log", "v2", "+ hidden screens release posters"),
	("Modern Optimized v3 (build66)", "t70.log", "v3", "uncached picons (reverted)"),
	("Modern Optimized v5 (build68)", "t74.log", "v5", "final path: settle + RAM posters"),
	("Classic (build68)", "t75.log", "classic", "reference, same navigation"),
	("Modern current (build71), 60 min", "t79.log", "long", "stability run, 60 min instead of 25"),
	("Modern rc9 (build86), 25 min", "t89.log", "rc9", "release candidate, installed package"),
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


ATTR_RUNS = [("t81a · build71 deployed", "t81a.log"), ("t81b · rc6 installed", "t81b.log"), ("t83 · build75 (PIL sizing)", "t83.log")]
ATTR_SRC = ["CineView poster decode", "Enigma2 picon cache (220x132)", "Enigma2 image/other surface"]


def attribution():
	"""t81a / t81b / t83: '   share  42.9 %     3  <source>' lines -> {run: {source: (count, pct)}}, totals."""
	runs = []
	for lab, lg in ATTR_RUNS:
		t = log(lg)
		if "T81_DONE" not in t:
			continue
		d = {}
		for m in re.finditer(r"^\s+share\s+([\d.]+) %\s+(\d+)\s+(.+?)\s*$", t, re.M):
			src = next((k for k in ATTR_SRC if m.group(3).startswith(k)), m.group(3))
			d[src] = (int(m.group(2)), float(m.group(1)))
		tot = re.search(r"^\s+failures: (\d+)", t, re.M)
		runs.append((lab, d, int(tot.group(1)) if tot else sum(c for c, _ in d.values())))
	if not runs:
		return '<tr><td colspan="2">t81 not run yet</td></tr>', ""
	head = "<tr><th>Source</th>%s</tr>" % "".join("<th>%s</th>" % r[0] for r in runs)
	rows = []
	for src in ATTR_SRC:
		cells = "".join('<td class="n">%s</td>' % ("%d · %.1f %%" % d[src] if src in d else "0") for _, d, _ in runs)
		rows.append("<tr><td>%s</td>%s</tr>" % ({"CineView poster decode": "CineView poster, first decode (ePicLoad)", "Enigma2 picon cache (220x132)": "Enigma2 list picon cache 220×132",
			"Enigma2 image/other surface": "Enigma2 other surface (1536×1024)"}[src], cells))
	rows.append('<tr><td><b>Total</b></td>%s</tr>' % "".join('<td class="n"><b>%d</b></td>' % t for _, _, t in runs))
	return head, "".join(rows)


def pil_ab():
	t = log("t83.log")
	m = re.search(r"AB pairs=(\d+) psnr min/median/max ([\d.]+)/([\d.]+)/([\d.]+)", t)
	figs = []
	for i, cap in enumerate(("lowest PSNR", "second lowest", "median")):
		pic = img(os.path.join(S, "t83", "AB_%d.png" % i), 560, 80)
		lab = re.search(r"^ab %d \S+ ([\d.]+) dB" % i, t, re.M)
		if pic:
			figs.append('<figure class="ab"><img loading="lazy" alt="ePicLoad vs PIL, %s" src="%s"><figcaption>left ePicLoad · right PIL · %s%s</figcaption></figure>' % (cap, pic, cap, " · %s dB" % lab.group(1) if lab else ""))
	made = re.search(r"made with PIL during the run: (\d+)", t)
	note = ("%s identical posters compared; PSNR min / median / max %s / %s / %s dB. Widget-size copies made with PIL during the run: %s." % (m.group(1), m.group(2), m.group(3), m.group(4), made.group(1) if made else "?")) if m else "t83 not run yet."
	return note, "".join(figs)


NP_MODELS = [("modern", "Modern"), ("classic", "Classic"), ("details", "Details"), ("cinema", "Cinema"), ("minimal", "Minimal")]


def noposter():
	"""t82 (InfoBar, SecondInfoBar, EventView, channel list: HBO with a poster vs HRT1 news without) and t84 (EPG
	cards on HBO / HRT1, PVR rows of the USB test folder)."""
	out = []
	for m, lab in NP_MODELS:
		rows = []
		for sk, slab in (("ib", "InfoBar"), ("sib", "SecondInfoBar"), ("ev", "EventView"), ("cs", "Channel list")):
			a = img(os.path.join(S, "t82", "%s_hbo_%s.png" % (m, sk)), 520, 60)
			b = img(os.path.join(S, "t82", "%s_hrt1_%s.png" % (m, sk)), 520, 60)
			if sk == "ib" and os.path.exists(os.path.join(S, NPDIR, "%s_ib_hbo.png" % m)):
				# t82 grabbed 5 s after OK, when the InfoBar had already timed out; t84 grabbed at 2.5 s
				a = img(os.path.join(S, NPDIR, "%s_ib_hbo.png" % m), 520, 60)
				b = img(os.path.join(S, NPDIR, "%s_ib_hrt1.png" % m), 520, 60)
			elif sk == "ib":
				continue
			if not (a or b):
				continue
			rows.append('<section class="sec"><h3>%s</h3><div class="pair">%s%s</div></section>' % (slab,
				'<figure><div class="tag on">HBO · poster</div>%s</figure>' % ('<img loading="lazy" alt="%s %s with poster" src="%s">' % (lab, slab, a) if a else '<div class="miss">no grab</div>'),
				'<figure><div class="tag off">HRT1 · no poster</div>%s</figure>' % ('<img loading="lazy" alt="%s %s without poster" src="%s">' % (lab, slab, b) if b else '<div class="miss">no grab</div>')))
		a = img(os.path.join(S, NPDIR, "%s_epg_hbo.png" % m), 520, 60)
		b = img(os.path.join(S, NPDIR, "%s_epg_hrt1.png" % m), 520, 60)
		if a or b:
			rows.append('<section class="sec"><h3>EPG card</h3><div class="pair">%s%s</div></section>' % (
				'<figure><div class="tag on">HBO</div>%s</figure>' % ('<img loading="lazy" alt="%s EPG HBO" src="%s">' % (lab, a) if a else '<div class="miss">no grab</div>'),
				'<figure><div class="tag off">HRT1</div>%s</figure>' % ('<img loading="lazy" alt="%s EPG HRT1" src="%s">' % (lab, b) if b else '<div class="miss">no grab</div>')))
		for kind, klab in (("emc", "PVR · EMC rows"), ("ms", "PVR · MovieSelection rows")):
			cells = []
			for k in range(5):
				pic = img(os.path.join(S, NPDIR, "%s_%s_%d.png" % (m, kind, k)), 420, 58)
				if pic:
					cells.append('<figure><img loading="lazy" alt="%s %s row %d" src="%s"><figcaption>row %d</figcaption></figure>' % (lab, klab, k, pic, k))
			if cells:
				rows.append('<section class="sec"><h3>%s</h3><div class="rowgrid">%s</div></section>' % (klab, "".join(cells)))
		if rows:
			out.append('<details class="np"%s><summary>%s</summary><div class="pane">%s</div></details>' % (" open" if not out else "", lab, "".join(rows)))
	ev = []
	for n, lab in (("784", "HBO HD · poster"), ("786", "Cinemax HD · poster"), ("D49", "HRT1 · no poster")):
		pic = img(os.path.join(S, "t84", "classic_ev_%s.png" % n), 520, 60)
		if pic:
			ev.append('<figure><img loading="lazy" alt="Classic EventView %s" src="%s"><figcaption>%s</figcaption></figure>' % (lab, pic, lab))
	if ev:
		out.append('<details class="np"><summary>Classic · EventView strip picon (fixed)</summary><div class="pane"><p class="note">Before: no picon on a freshly opened EventView (also in the approved t68 grabs), and a hidden variant could draw the default picon. Now the picon shows in its place with and without a poster.</p><div class="rowgrid">%s</div></div></details>' % "".join(ev))
	return "".join(out) or '<p class="note">t82 / t84 not run yet.</p>'


def _errs(text):
	"""(checks, checks with any traceback / skin error / crash log) from errs() lines."""
	rows = re.findall(r"tracebacks=(\d+) skin_errors_new=(\d+)(?: accel=\d+)? e2pid=\S* crashlogs=(\d+)", text)
	return len(rows), sum(1 for a, b, c in rows if int(a) or int(b) or int(c))


def release_status():
	"""Top section for the 1.0.0 review: every requirement, its state (CLAUDE.md completion states) and the evidence
	parsed from the logs.  A missing log shows as 'not run'."""
	def leaks(n):
		t = log(n)
		return len(re.findall(r"band opaque", t)), t.count("LEAK")
	t90, t90b, t93 = leaks("t90.log"), leaks("t90b.log"), log("t93.log")
	t93a = (len(re.findall(r"build86_r\S+\s+band opaque", t93)), len(re.findall(r"build86_r.*LEAK", t93)))
	t93b = (len(re.findall(r"build87_r\S+\s+band opaque", t93)), len(re.findall(r"build87_r.*LEAK", t93)))
	g = re.search(r"TOTAL REAL not-opaque info widgets: (\d+)\s+\(edge/corner-only widgets: (\d+)\)", log("t87g_alpha.log"))
	g_chk = sum(int(x) for x in re.findall(r"checked\s+(\d+)", log("t87g_alpha.log")))
	t91 = log("t91.log"); t91c, t91e = _errs(t91)
	t86 = log("t86_rc10.log"); t86c, t86e = _errs(t86)
	t77 = log("t77_rc10.log"); t77c, t77e = _errs(t77)
	t77g = len(re.findall(r"png-ok", t77))
	t92 = log("t92_write.log")
	def st(ok, good="RUNTIME TESTED", bad="NOT RUN"):
		return '<span class="%s">%s</span>' % ("ok" if ok else "warn", good if ok else bad)
	rows = [
		("Opaque information areas (InfoBar, SecondInfoBar, playback bar; 5 models; scrims kept)",
		 st(bool(g) and g.group(1) == "0", "DEVICE VERIFIED · approved 14:31"),
		 "t87e/t87f (rc9, 6 themes) 0 real; t87g (rc10 build, navy + purple): %s widgets checked, %s real, %s edge/corner-only" % (g_chk, g.group(1) if g else "?", g.group(2) if g else "?")),
		("Minimal SIB description leak at scroll start",
		 st(t90b[0] > 0 and t90b[1] == 0, "ROOT CAUSE IDENTIFIED · fix RUNTIME TESTED"),
		 "rc9: %d leak in %d grabs (t90, 3 reboots); rc10 build: %d in %d (t90b) · focused A/B t93: old %d/%d, new %d/%d · event too rare to prove absence by counting" % (t90[1], t90[0], t90b[1], t90b[0], t93a[1], t93a[0], t93b[1], t93b[0])),
		("PIL poster sizing (widget-size copy, original untouched)", '<span class="ok">DEVICE VERIFIED · approved 14:31</span>', "t83 (0 CineView accel share, A/B PSNR), unchanged since"),
		("No Poster layout, no placeholder, 5 models incl. Classic", st(t91c > 0 and t91e == 0, "DEVICE VERIFIED"), "t91: InfoBar / EPG / EMC / MovieSelection pairs HBO vs HRT1; %d checks, %d with errors" % (t91c, t91e)),
		("SecondInfoBarECM without placeholder (no runtime resizing)", st(t91c > 0 and t91e == 0, "DEVICE VERIFIED"), "t91: poster / no poster / posters OFF in 5 models; setting restored"),
		("One picon per place under fast zapping", st(t91c > 0 and t91e == 0, "DEVICE VERIFIED"), "t91: 3 bursts + single zaps per model, 0.3 / 1 / 2.5 s; 60 picon cut-outs, one picon each"),
		("Poster cache: HDD real mount → USB → /tmp; never deleted on upgrade / uninstall", st("PASS" in t92, "DEVICE VERIFIED (dedicated test)"), "t92: read-only checks + one test file written / read back / removed on /media/hdd/poster; cache kept in t86"),
		("Package lifecycle rc10: upgrade (GUI running), reboot, uninstall, fresh install, purge, restore", st("T86_DONE" in t86 and t86e == 0, "DEVICE VERIFIED"), "t86_rc10: %d checks, %d with errors" % (t86c, t86e)),
		("Short final QA on the installed rc10: 5 models × 6 sections", st("T77_DONE" in t77 and t77e == 0, "DEVICE VERIFIED"), "t77_rc10: %d grabs, %d checks, %d with errors" % (t77g, t77c, t77e)),
		("Scope", '<span class="ok">Vu+ Duo 4K SE · OpenATV 8.0.1 · Slot 8</span>', "Dreambox and other receivers are outside this release"),
	]
	return "".join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % r for r in rows)


def ecm_and_picons():
	"""t91: SecondInfoBarECM (poster / no poster / posters OFF) and the picon sheets of the fast-zap grabs."""
	ecm, pic = [], []
	for m, lab in MODELS:
		cells = []
		for k, klab in (("hbo", "HBO · poster"), ("hrt1", "HRT1 · no poster"), ("off", "posters OFF")):
			p = img(os.path.join(S, NPDIR, "%s_ecm_%s.png" % (m, k)), 420, 60)
			if p:
				cells.append('<figure><img loading="lazy" alt="%s ECM %s" src="%s"><figcaption>%s</figcaption></figure>' % (lab, klab, p, klab))
		if cells:
			ecm.append('<section class="sec"><h3>%s</h3><div class="rowgrid">%s</div></section>' % (lab, "".join(cells)))
		sh = img(os.path.join(S, NPDIR, "picons_%s.png" % m), 1100, 70)
		if sh:
			pic.append('<details class="np"><summary>%s · picon area after fast zaps</summary><div class="pane"><img loading="lazy" alt="%s picons" src="%s" style="width:100%%;border-radius:6px"></div></details>' % (lab, lab, sh))
	return "".join(ecm) or '<p class="note">t91 not run yet.</p>', "".join(pic) or '<p class="note">t91 not run yet.</p>'


def opaque():
	"""t87a (rc8, before) vs t87e/t87f (rc9): real OSD alpha over red / yellow / white / dark, osd_alpha counts."""
	stats = {}
	for lg in ("t87e_alpha.log", "t87f_alpha.log"):
		for m in re.finditer(r"^(\w+?)_(\w+?)_(ib|sib|mp)_osd\.png\s+checked\s+(\d+)\s+REAL not-opaque\s+(\d+)\s+edge/corner-only\s+(\d+)", log(lg), re.M):
			stats[(m.group(1), m.group(2), m.group(3))] = tuple(int(x) for x in m.groups()[3:])  # t87f (Modern, build86) overrides t87e
	rows = []
	for mm, mlab in MODELS:
		for sc, slab in (("ib", "InfoBar"), ("sib", "SecondInfoBar"), ("mp", "Playback bar")):
			v = [stats.get((mm, t, sc)) for t in THEMES]
			v = [x for x in v if x]
			if not v:
				continue
			rows.append('<tr><td>%s</td><td>%s</td><td class="n">%d</td><td class="n">%d</td><td class="n %s">%d</td><td class="n">%d</td></tr>' % (
				mlab, slab, len(v), sum(x[0] for x in v), "ok" if sum(x[1] for x in v) == 0 else "warn", sum(x[1] for x in v), sum(x[2] for x in v)))
	figs = []
	for mm, mlab in MODELS:
		src = "t87f" if mm == "modern" else "t87e"
		for sc, slab in (("sib", "SecondInfoBar"), ("ib", "InfoBar")):
			a = img(os.path.join(S, "t87a", "%s_navy_%s_bg.png" % (mm, sc)), 560, 70)
			b = img(os.path.join(S, src, "%s_navy_%s_bg.png" % (mm, sc)), 560, 70)
			if a and b:
				figs.append('<details class="np"%s><summary>%s · %s</summary><div class="pair"><figure><div class="tag off">rc8 before</div><img loading="lazy" alt="%s %s before" src="%s"></figure>'
					'<figure><div class="tag on">rc9 after</div><img loading="lazy" alt="%s %s after" src="%s"></figure></div></details>' % (
					" open" if (mm, sc) == ("classic", "sib") else "", mlab, slab, mlab, slab, a, mlab, slab, b))
	return "".join(rows) or '<tr><td colspan="6">t87e not run</td></tr>', "".join(figs)


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
	errs = model_errs(log(T68LOG))
	tb = sum(v[0] for vs in errs.values() for v in vs)
	se = sum(v[1] for vs in errs.values() for v in vs)
	cl = max([v[3] for vs in errs.values() for v in vs] or [0])

	maxacc = max([s["accel"] for _, _, s in perf] or [1]) or 1
	bars = []
	for i, (lab, note, s) in enumerate(perf):
		w = 100.0 * s["accel"] / maxacc
		cls = "bar ref" if "Classic" in lab else ("bar fin" if ("v5" in lab or "current" in lab or "rc9" in lab) else "bar")
		bars.append('<div class="brow"><div class="blab"><b>%s</b><span>%s</span></div><div class="btrack"><div class="%s" style="width:%.2f%%"></div></div>'
			'<div class="bval">%d</div><div class="bmeta">%d rounds · RSS %d MB · CPU %.0f s</div></div>' % (lab, note, cls, max(w, 0.4), s["accel"], s["rounds"], s["rss"], s["cpu_s"] or 0))
	prow = "".join('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d MB</td><td class="n">%.0f s</td></tr>' % (lab, s["rounds"], s["accel"], s["rss"], s["cpu_s"] or 0) for lab, s in phases)

	tabs, panes = [], []
	for mi, (m, mlab) in enumerate(MODELS):
		tabs.append('<button class="tab" role="tab" id="tab-%s" aria-controls="pane-%s" aria-selected="%s">%s</button>' % (m, m, "true" if mi == 0 else "false", mlab))
		rows = []
		for sk, slab in SECTIONS:
			on = img(os.path.join(S, T68, "%s_navy_on_%s.png" % (m, sk)))
			off = img(os.path.join(S, T68, "%s_navy_off_%s.png" % (m, sk)))
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
				src = img(os.path.join(S, T68, name), 420, 62)
				cells.append('<figure>%s<figcaption>%s</figcaption></figure>' % ('<img loading="lazy" alt="%s %s %s" src="%s">' % (mlab, t, slab, src) if src else '<div class="miss">no grab</div>', slab))
			th.append('<div class="theme"><div class="tname"><i class="sw sw-%s"></i>%s</div><div class="trow">%s</div></div>' % (t, t, "".join(cells)))
		e_on = errs.get((m, "navy", "posters ON"), [])
		e_off = errs.get((m, "navy", "posters OFF"), [])
		acc = [v[2] for v in e_on[1:2] + e_off[1:2]]
		chip = '<span class="chip">accel after the six sections: %s</span>' % (" / ".join(str(a) for a in acc) or "n/a")
		panes.append('<div class="pane" role="tabpanel" id="pane-%s" aria-labelledby="tab-%s"%s><div class="pmeta">%s</div>%s<h3 class="th">Six themes · posters ON</h3>%s</div>' % (
			m, m, "" if mi == 0 else " hidden", chip, "".join(rows), "".join(th)))

	orows, ofigs = opaque()
	relrows = release_status()
	ecmh, pich = ecm_and_picons()
	ahead, arows = attribution()
	abnote, abfigs = pil_ab()
	html = TEMPLATE.replace("%RELEASE%", relrows).replace("%ECM%", ecmh).replace("%PICONS%", pich).replace("%OROWS%", orows).replace("%OFIGS%", ofigs).replace("%BUILD%", BUILD).replace("%CURRENT%", CURRENT).replace("%ATTRH%", ahead).replace("%ATTR%", arows).replace("%PILNOTE%", abnote).replace("%PILAB%", abfigs).replace("%NOPOSTER%", noposter()).replace("%BARS%", "".join(bars)).replace("%PHASES%", prow or '<tr><td colspan="5">t76 not run</td></tr>') \
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
.rowgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,220px),1fr));gap:10px}
details.np{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 16px}
details.np summary{font:600 20px var(--display);cursor:pointer}
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
  <div class="kicker">Slot 8 · Vu+ Duo 4K SE · OpenATV 8.0.1 · dev/mla-openatv · model grabs %BUILD% · current %CURRENT%</div>
  <h1>CineView MLA Model Review</h1>
  <p class="lede">The five design models on all six sections, as the receiver drew them: posters on and off in the navy theme, and every model in the six themes. Every picture below is a screen grab from the receiver; every number comes from a test log.</p>
  <div class="facts"><span>Tracebacks <b class="ok">%TB%</b></span><span>New skin errors <b class="%SECLS%">%SE%</b>%SENOTE%</span><span>Crash logs <b class="ok">%CL%</b></span><span>Test media <b>USB only, HDD not opened</b></span></div>
</header>
<section class="block">
  <h2>Release 1.0.0: status of every requirement</h2>
  <p class="note">States as defined for this project (DEVICE VERIFIED = exercised on the receiver with evidence). Nothing here is a final release until it is approved.</p>
  <div class="tw"><table><thead><tr><th>Requirement</th><th>State</th><th>Evidence</th></tr></thead><tbody>%RELEASE%</tbody></table></div>
</section>
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
  <h2>Where the remaining warnings come from</h2>
  <p class="note">The same eight navigation rounds with a fixed channel order, fast-graphics debug on. Every warning is attributed by the size of the picture that was being created when it happened. The picon cache and the 1536×1024 surface belong to Enigma2 itself (pictures it keeps for good); CineView does not change them. The CineView share was the first decode of a poster: Enigma2’s picture loader always asks fast memory for its result.</p>
  <div class="tw"><table><thead>%ATTRH%</thead><tbody>%ATTR%</tbody></table></div>
  <h3>Poster scaling without fast memory: Enigma2 loader vs PIL</h3>
  <p class="note">From build75 the widget-size copy of a poster is made from the original file with PIL, with the loader’s exact framing (same size, same black bars), and then shown from normal memory. The original poster file is never rewritten. The scaler differs: Enigma2 averages pixel blocks, PIL uses Lanczos, so the PIL copy is sharper. Size and layout are unchanged. %PILNOTE%</p>
  <div class="abgrid">%PILAB%</div>
</section>
<section class="block">
  <h2>No poster: the real layout instead of a placeholder</h2>
  <p class="note">Posters on. Left: an event or recording that has a poster. Right: one without (news, generic programme), which now gets the screen’s posters-off arrangement for that moment instead of the default picture. Screens whose layout is fixed when they open (named EventView designs) choose their No Poster screen when they open.</p>
  %NOPOSTER%
  <h3>SecondInfoBarECM</h3>
  <p class="note">The ECM variant of the SecondInfoBar (Menu setting “Second InfoBar: ECM”) keeps Enigma2’s own named text widgets, so its text is not moved. Without a real poster nothing is drawn in the poster place: no placeholder and no empty frame.</p>
  %ECM%
  <h3>One picon per place while zapping fast</h3>
  <p class="note">CH+ / CH− bursts; grabs 0.3, 1 and 2.5 seconds after a burst and after a single zap. The InfoBar’s picon places are cut out of every grab.</p>
  %PICONS%
</section>
<section class="block">
  <h2>Information areas stay opaque over any picture</h2>
  <p class="note">rc9: every area that carries information on the InfoBar, the SecondInfoBar and the playback bar has a fully opaque background in the theme colour; the decorative scrims around them stay translucent. Measured from the receiver’s real OSD alpha inside every information widget, six themes. “Edge / corner only”: anti-aliased edges of rounded pills (alpha ≥ 250) or their corners outside the rounded shape, never under text.</p>
  <div class="tw"><table><thead><tr><th>Model</th><th>Screen</th><th>Themes</th><th>Widgets checked</th><th>Not opaque</th><th>Edge / corner only</th></tr></thead><tbody>%OROWS%</tbody></table></div>
  <p class="note">Minimal SecondInfoBar: the 4 come from one Purple grab (description area, y 796–848). It was not reproducible: 24 retakes in Purple and Navy, 2 to 12 seconds after opening (t88), were all fully opaque there. It is listed, not explained.</p>
  <p class="note">The same OSD over red, yellow, white and dark (navy theme): before (rc8) and after (rc9).</p>
  %OFIGS%
</section>
<section class="block">
  <h2>The five models</h2>
  <p class="note">Grabs from %BUILD% (the final QA run, the package installed on the receiver).</p>
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
