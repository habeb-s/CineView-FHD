#!/usr/bin/env python3
"""Static guard: report functions that bind the name "_" (assignment, loop, unpacking) and also
call _() — in Enigma2 "_" is the gettext builtin, so the call then raises TypeError at runtime
(found on device: CineViewMLASetup.updatePreview, crash log 20261003-184108)."""
import ast
import os
import sys


def binds(fn):
	for node in ast.walk(fn):
		if isinstance(node, ast.Name) and node.id == "_" and isinstance(node.ctx, ast.Store):
			return node.lineno
	return None


def calls(fn):
	return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_" for n in ast.walk(fn))


bad = 0
for root in sys.argv[1:]:
	for dp, _dn, fns in os.walk(root):
		for f in fns:
			if not f.endswith(".py"):
				continue
			p = os.path.join(dp, f)
			try:
				tree = ast.parse(open(p, encoding="utf-8").read())
			except SyntaxError as e:
				print("SYNTAX %s: %s" % (p, e))
				bad += 1
				continue
			for fn in ast.walk(tree):
				if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
					ln = binds(fn)
					if ln and calls(fn):
						print("SHADOW %s:%d %s() binds '_' and calls _()" % (p, ln, fn.name))
						bad += 1
print("gettext-shadow check: %d problem(s)" % bad)
sys.exit(1 if bad else 0)
