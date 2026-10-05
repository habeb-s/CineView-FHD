#!/usr/bin/env python3
"""Static compatibility of a built CineView MLA tree with another OpenATV enigma2 source tree.

Compares what the MLA skin and components USE against what the target image PROVIDES, relative to the image the
package is verified on (reference tree): only differences between reference and target are reported, so anything
that already works on the reference is not re-litigated.
Checks:
  1. renderers / converters named in the skin (render=, <convert type=>) that are native (not shipped by MLA);
  2. converter arguments (tokens) — each token must occur as a string in the target converter's source;
  3. widget attributes used by the skin — each must be handled by the target skin.py (AttributeParser method or a
     named attribute check), or be a renderer/addon-specific attribute present in the target source;
  4. Screen contracts (skinName + self[...] names) via contracts.py, reference vs target;
  5. enigma Python API used by MLA components (ePicLoad, loadPNG/savePNG, eTimer, ...);
  6. Python modules imported by MLA components that come from the image.
Static analysis only: a clean result is necessary, not a runtime proof.
usage: compat_image.py <build root> <reference enigma2 tree> <target enigma2 tree>"""
import ast
import json
import os
import re
import subprocess
import sys

BUILD, REF, TGT = sys.argv[1:4]
SKIN = os.path.join(BUILD, "usr/share/enigma2/CineView_FHD_MLA")
PYC = os.path.join(BUILD, "usr/lib/enigma2/python/Components")
OWN_PREFIX = ("CineView",)


def xmls():
	out = []
	for root, _, files in os.walk(SKIN):
		if "/generations/" in root or root.endswith("/active") or "/active/" in root:
			continue
		for f in files:
			if f.endswith(".xml"):
				out.append(os.path.join(root, f))
	return out


def src(tree, kind, name):
	p = os.path.join(tree, "lib/python/Components", kind, name + ".py")
	return open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else None


def skinpy(tree):
	return open(os.path.join(tree, "lib/python/skin.py"), encoding="utf-8", errors="replace").read()


renders, converts, attrs = {}, {}, {}
for f in xmls():
	s = open(f, encoding="utf-8", errors="replace").read()
	for m in re.finditer(r'render="([^"]+)"', s):
		renders.setdefault(m.group(1), set()).add(os.path.relpath(f, SKIN))
	for m in re.finditer(r'<convert type="([^"]+)">([^<]*)</convert>', s):
		converts.setdefault(m.group(1), set()).update(t.strip() for t in m.group(2).split(",") if t.strip())
	for m in re.finditer(r'<(widget|eLabel|ePixmap|panel|screen)\b([^>]*)>', s):
		for a in re.findall(r'\s(\w+)="', m.group(2)):
			attrs.setdefault(a, set()).add(m.group(1))

shipped = set()
for kind in ("Renderer", "Converter"):
	d = os.path.join(PYC, kind)
	if os.path.isdir(d):
		shipped.update(f[:-3] for f in os.listdir(d) if f.endswith(".py"))

problems, notes = [], []
# 1 + 2
for kind, names in (("Renderer", renders), ("Converter", converts)):
	for n in sorted(names):
		if n in shipped or n.startswith(OWN_PREFIX):
			continue
		r, t = src(REF, kind, n), src(TGT, kind, n)
		if r is None and t is None:
			notes.append("%s %s: in neither tree (C++ or plugin component?)" % (kind, n))
			continue
		if r is not None and t is None:
			problems.append("%s %s: present on the reference image, MISSING on the target" % (kind, n))
			continue
		if kind == "Converter":
			for tok in sorted(converts[n]):
				if not re.match(r"^[A-Za-z_][\w ]*$", tok):
					continue  # formats (ClockToText Format:...), numbers, etc.
				if r and ('"%s"' % tok in r or "'%s'" % tok in r) and not ('"%s"' % tok in t or "'%s'" % tok in t):
					problems.append("Converter %s token %r: handled on the reference, not found on the target" % (n, tok))
# 3 attributes
rs, ts = skinpy(REF), skinpy(TGT)
for a in sorted(attrs):
	inr = re.search(r"\bdef %s\(" % a, rs) or ('"%s"' % a in rs)
	int = re.search(r"\bdef %s\(" % a, ts) or ('"%s"' % a in ts)
	if inr and not int:
		problems.append("skin attribute %r: parsed by the reference skin.py, not by the target" % a)
# 4 screen contracts
ref_c, tgt_c = "/tmp/compat_ref.json", "/tmp/compat_tgt.json"
here = os.path.dirname(os.path.abspath(__file__))
for tree, out in ((REF, ref_c), (TGT, tgt_c)):
	subprocess.run([sys.executable, os.path.join(here, "contracts.py"), "extract", os.path.join(tree, "lib/python"), out], check=True, capture_output=True)
packs = [f for f in xmls() if "/layouts/" in f]
def chk(c):
	r = subprocess.run([sys.executable, os.path.join(here, "contracts.py"), "check", c] + packs, capture_output=True, text=True)
	return set(l.strip() for l in r.stdout.splitlines() if l.strip() and not l.startswith(("checked", "OK", "SUMMARY")))
cr, ct = chk(ref_c), chk(tgt_c)
for l in sorted(ct - cr):
	problems.append("screen contract (target only): " + l)
# 5 + 6 enigma API / imports of MLA components
api = set()
mods = set()
for root, _, files in os.walk(os.path.join(BUILD, "usr/lib/enigma2/python")):
	for f in files:
		if not f.endswith(".py"):
			continue
		try:
			tree = ast.parse(open(os.path.join(root, f), encoding="utf-8", errors="replace").read())
		except SyntaxError as e:
			problems.append("syntax error in %s: %s" % (f, e)); continue
		for n in ast.walk(tree):
			if isinstance(n, ast.ImportFrom) and n.module:
				if n.module == "enigma":
					api.update(a.name for a in n.names)
				elif n.module.split(".")[0] in ("Components", "Screens", "Tools", "Plugins") and not n.module.split(".")[-1].startswith("CineView"):
					mods.add((n.module, tuple(a.name for a in n.names)))
for name in sorted(api):
	found = subprocess.run(["grep", "-rlw", "--include=*.h", "--include=*.i", "--include=*.cpp", name, os.path.join(TGT, "lib")], capture_output=True, text=True).stdout.strip()
	if not found:
		problems.append("enigma API %s: not found in the target C++ headers" % name)
for mod, names in sorted(mods):
	p = os.path.join(TGT, "lib/python", *mod.split(".")) + ".py"
	if not os.path.exists(p):
		if os.path.exists(os.path.join(REF, "lib/python", *mod.split(".")) + ".py") and "Plugins" not in mod:
			problems.append("module %s: missing on the target" % mod)
		continue
	s = open(p, encoding="utf-8", errors="replace").read()
	for nm in names:
		if nm != "*" and not re.search(r"(^|\n)(class|def)\s+%s\b|(^|\n)%s\s*=" % (re.escape(nm), re.escape(nm)), s):
			problems.append("module %s: name %s not defined on the target" % (mod, nm))
print("renderers %d, converters %d, attributes %d, layout files %d, enigma API names %d, image modules %d" % (
	len(renders), len(converts), len(attrs), len(packs), len(api), len(mods)))
for n in notes:
	print("NOTE", n)
for p in problems:
	print("DIFF", p)
print("RESULT", "no difference found" if not problems else "%d difference(s)" % len(problems))
