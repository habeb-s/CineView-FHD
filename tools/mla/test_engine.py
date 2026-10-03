#!/usr/bin/env python3
"""Fault-injection tests for the MLA composition engine.

Runs against an isolated COPY of a built skin dir (never the live one):
  test_engine.py <built CineView_FHD_MLA dir> <scratch dir>
Simulates: crashes at stage/seal/switch, a process killed mid-write (partial generation,
no seal), a corrupted file inside the active generation, a broken `active` symlink,
a stale active.tmp, a corrupted journal, unknown layout/theme, and normal apply/rollback.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys

SRC, SCRATCH = sys.argv[1], sys.argv[2]
SKIN = os.path.join(SCRATCH, "skin")
STATE = os.path.join(SCRATCH, "state")
results = []


def fresh():
	shutil.rmtree(SCRATCH, ignore_errors=True)
	shutil.copytree(SRC, SKIN, symlinks=True)
	os.makedirs(STATE)


def engine():
	os.environ["MLA_SKIN_DIR"], os.environ["MLA_STATE_DIR"] = SKIN, STATE
	os.environ.pop("MLA_FAULT", None)
	spec = importlib.util.spec_from_file_location("composer", os.path.join(SKIN, "mla", "engine", "composer.py"))
	m = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(m)
	return m


def cli(*args, fault=None):
	env = dict(os.environ, MLA_SKIN_DIR=SKIN, MLA_STATE_DIR=STATE)
	env.pop("MLA_FAULT", None)
	if fault:
		env["MLA_FAULT"] = fault
	p = subprocess.run([sys.executable, os.path.join(SKIN, "mla", "engine", "composer.py")] + list(args), env=env, capture_output=True, text=True)
	return p.returncode, p.stdout + p.stderr


def active():
	return os.path.basename(os.readlink(os.path.join(SKIN, "active")))


def check(name, cond, detail=""):
	results.append((name, bool(cond), detail))
	print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


def sel(theme="navy", **lay):
	m = engine()
	s = {"theme": theme, "layouts": {k: "classic" for k in m.sections()}}
	s["layouts"].update(lay)
	return s


# 1. normal apply / commit / rollback
fresh(); m = engine()
check("factory generation verifies", m.verify_generation("g000000"))
rc, out = cli("apply", "--theme", "graphite")
g1 = active()
check("apply theme=graphite switches to new sealed generation", rc == 0 and g1 != "g000000" and m.verify_generation(g1), out)
check("lkg updated after non-trial apply", open(os.path.join(STATE, "lkg")).read().strip() == g1)
rc, out = cli("apply", "--theme", "purple", "--trial")
g2 = active()
check("trial apply switches but keeps lkg", rc == 0 and g2 != g1 and open(os.path.join(STATE, "lkg")).read().strip() == g1, out)
rc, out = cli("rollback")
check("rollback returns to lkg", rc == 0 and active() == g1, out)
rc, out = cli("rollback", "--to", "factory")
check("rollback --to factory", rc == 0 and active() == "g000000", out)

check("factory rollback makes factory the last-known-good", open(os.path.join(STATE, "lkg")).read().strip() == "g000000")

# 1b. trial lifecycle across sessions (P6): a trial that got a GUI session but was never confirmed is
#     reverted at the next start, even when the process never crashed (guardian counter not involved).
fresh(); m = engine()
cli("apply", "--theme", "graphite"); good = active()
rc, out = cli("apply", "--theme", "purple", "--trial"); trial = active()
rc, out = cli("recover")
check("first start of a trial keeps it (state TRIAL)", active() == trial, out)
check("session start marks TRIAL_RUNNING", m.mark_trial_running() and json.load(open(os.path.join(STATE, "txn.json")))["state"] == "TRIAL_RUNNING")
rc, out = cli("recover")
check("next start with unconfirmed trial -> last-known-good", active() == good, out)
fresh(); m = engine()
cli("apply", "--theme", "graphite"); cli("apply", "--theme", "purple", "--trial"); trial = active()
m.mark_trial_running(); m.commit()
rc, out = cli("recover")
check("confirmed trial survives the next start", active() == trial, out)

# 2. validation refuses bad selections and leaves active untouched
fresh(); before = active()
rc, out = cli("apply", "--set", "infobar=doesnotexist")
check("unknown layout refused, active unchanged", rc != 0 and active() == before, out)
rc, out = cli("apply", "--theme", "nosuchtheme")
check("unknown theme refused, active unchanged", rc != 0 and active() == before, out)

# 3. injected crashes at each step
for step in ("stage", "seal", "switch"):
	fresh(); before = active(); base_gens = sorted(os.listdir(os.path.join(SKIN, "generations")))
	rc, out = cli("apply", "--theme", "green", fault=step)
	j = json.load(open(os.path.join(STATE, "txn.json")))
	gens = sorted(os.listdir(os.path.join(SKIN, "generations")))
	if step in ("stage", "seal"):
		check(f"crash at {step}: active unchanged + generation discarded", rc != 0 and active() == before and j.get("gid") not in gens and gens == base_gens, f"{gens} {j}")
	else:
		rc2, out2 = cli("recover")
		check(f"crash at {step}: active still valid after recover", active() == before and m.verify_generation(active()) and not os.path.lexists(os.path.join(SKIN, "active.tmp")), out + out2)

# 4. process killed mid-write: unsealed partial generation + journal left in PREPARING
fresh()
part = os.path.join(SKIN, "generations", "g000007")
os.makedirs(part)
open(os.path.join(part, "infobar.xml"), "w").write("<skin><screen name=")  # truncated write
json.dump({"state": "PREPARING", "gid": "g000007", "prev": "g000000"}, open(os.path.join(STATE, "txn.json"), "w"))
rc, out = cli("recover")
check("killed mid-write: partial generation removed, active intact", not os.path.exists(part) and active() == "g000000", out)

# 5. corrupted file inside the ACTIVE generation (e.g. power loss on ext4 data)
fresh(); cli("apply", "--theme", "burgundy"); good = active()
cli("apply", "--theme", "black", "--trial"); bad = active()
with open(os.path.join(SKIN, "generations", bad, "infobar.xml"), "a") as f:
	f.write("CORRUPTION")
rc, out = cli("recover")
check("corrupted active generation -> rolled back to lkg", active() == good, out)

# 6. corrupted lkg too -> factory
fresh(); cli("apply", "--theme", "graphite"); g = active()
open(os.path.join(SKIN, "generations", g, "theme.xml"), "w").write("x")
rc, out = cli("recover")
check("active and lkg corrupted -> factory g000000", active() == "g000000", out)

# 7. broken symlink + stale active.tmp
fresh()
os.remove(os.path.join(SKIN, "active")); os.symlink("generations/g999999", os.path.join(SKIN, "active"))
os.symlink("generations/g000000", os.path.join(SKIN, "active.tmp"))
rc, out = cli("recover")
check("dangling active + stale active.tmp repaired", active() == "g000000" and not os.path.lexists(os.path.join(SKIN, "active.tmp")), out)

# 8. corrupted journal
fresh(); open(os.path.join(STATE, "txn.json"), "w").write("{not json")
rc, out = cli("recover")
check("corrupted journal tolerated", rc == 0 and active() == "g000000", out)
rc, out = cli("apply", "--theme", "navy")
check("apply works after journal corruption", rc == 0 and m.verify_generation(active()), out)

# 9. retention: only KEEP old generations + factory + active survive
fresh()
for t in ["black", "navy", "graphite", "burgundy", "green", "purple", "navy"]:
	cli("apply", "--theme", t)
gens = sorted(os.listdir(os.path.join(SKIN, "generations")))
check("retention keeps factory + bounded history", "g000000" in gens and len(gens) <= 5 and active() in gens, str(gens))

ok = sum(1 for _, r, _ in results if r)
print(f"\nRESULT: {ok}/{len(results)} passed")
sys.exit(0 if ok == len(results) else 1)
