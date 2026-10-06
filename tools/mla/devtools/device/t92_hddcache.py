# t92 (user 2026-10-06 14:31): dedicated, minimal test of the HDD poster-cache path.  Runs ON THE RECEIVER:
#   python3 - check  < t92_hddcache.py      read-only: mount / device / rw / space / permissions + the skin's own plan
#   python3 - write  < t92_hddcache.py      only if every check passes: ONE new test file in /media/hdd/poster
# Rules: no delete / rename of anything that exists, no cleaning, no cache move, no mount change, no fsck.  The only
# file written is a new uniquely named test file (exclusive create); it is removed afterwards.  /media/hdd/poster is
# removed again only if this test created it and it is still empty.  Nothing else on the HDD is opened or listed.
import ast
import hashlib
import os
import stat
import sys
import time

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"
HDD, TARGET = "/media/hdd", "/media/hdd/poster"
ok = True


def say(k, v, good=None):
    global ok
    if good is False:
        ok = False
    print("   %-28s %s%s" % (k, v, "" if good is None else ("  OK" if good else "  FAIL")))


print("== t92 mode=%s %s" % (MODE, time.strftime("%Y-%m-%d %H:%M:%S")))
mounts = [l.split() for l in open("/proc/mounts") if len(l.split()) >= 4]
ent = [m for m in mounts if m[1] == HDD]
say("/proc/mounts entry", " ".join(ent[0][:4]) if ent else "none", bool(ent))
if ent:
    src, mp, fs, opts = ent[0][:4]
    say("read-write", opts.split(",")[0], "rw" in opts.split(","))
    try:
        isblk = src.startswith("/dev/") and stat.S_ISBLK(os.stat(src).st_mode)
    except OSError:
        isblk = False
    say("block device", src, isblk)
    say("filesystem", fs, fs not in ("tmpfs", "overlay", "squashfs", "nfs", "nfs4", "cifs", "fuse.sshfs"))
    say("os.path.ismount", os.path.ismount(HDD), os.path.ismount(HDD))
    say("not the root filesystem", "dev %d vs root %d" % (os.stat(HDD).st_dev, os.stat("/").st_dev), os.stat(HDD).st_dev != os.stat("/").st_dev)
    sv = os.statvfs(HDD)
    free_mb = sv.f_bavail * sv.f_frsize // (1 << 20)
    say("free space", "%d MB" % free_mb, free_mb > 1024)
    say("writable by enigma2 (root)", os.access(HDD, os.W_OK), os.access(HDD, os.W_OK))
    exists = os.path.isdir(TARGET)
    say("poster dir exists", exists)
    if exists:
        say("poster dir writable", os.access(TARGET, os.W_OK), os.access(TARGET, os.W_OK))

# the skin's own plan, exactly as shipped, WITHOUT importing the renderer (import would create directories) and
# WITHOUT the development pin in runtime.json (a fresh release install has none)
rend = None
for d in ("/usr/lib/enigma2/python/Components/Renderer",):
    for f in sorted(os.listdir(d)):
        if f.endswith(".py") and "_mla_cache_plan" in open(os.path.join(d, f), errors="replace").read():
            rend = os.path.join(d, f)
            break
plan = None
if rend:
    tree = ast.parse(open(rend, errors="replace").read())
    want = {"_mla_cache_plan", "_cineview_mounts", "_cineview_is_multiboot_mount"}
    funcs = []
    for n in tree.body:  # standard-library imports only (no Enigma2 module, no other module code)
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            try:
                exec(compile(ast.Module(body=[n], type_ignores=[]), "imp", "exec"), {})
                funcs.append(n)
            except Exception:
                pass
    funcs += [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in want]
    ns = {"os": os}
    real_open = open

    def fake_open(p, *a, **k):
        if str(p).endswith("runtime.json"):
            raise IOError("no runtime.json (fresh release install)")
        return real_open(p, *a, **k)
    ns["open"] = fake_open
    exec(compile(ast.Module(body=funcs, type_ignores=[]), rend, "exec"), ns)
    plan = ns["_mla_cache_plan"]()
say("renderer", rend or "not found", bool(rend))
say("release plan (no pin)", "%s (%s)" % plan if plan else "n/a", bool(plan) and plan[0] == TARGET)

if MODE == "write":
    if not ok:
        print("== NOT WRITING: a check failed")
        sys.exit(1)
    created = False
    if not os.path.isdir(TARGET):
        os.mkdir(TARGET)
        created = True
        say("created", TARGET + " (the skin does the same on first use)")
    src_poster = None
    roots = []
    try:
        import json
        roots.append(json.load(open("/etc/enigma2/cineview_mla/runtime.json")).get("poster_cache") or "")
    except Exception:
        pass
    for root in [r for r in roots if r and not r.startswith(HDD)] + ["/media/usb/cineview-mla/poster", "/media/usb/poster"]:
        for dp, dn, fn in os.walk(root):
            for f in sorted(fn):
                if f.lower().endswith(".jpg"):
                    src_poster = os.path.join(dp, f)
                    break
            if src_poster:
                break
        if src_poster:
            break
    data = open(src_poster, "rb").read() if src_poster else os.urandom(150000)
    test = os.path.join(TARGET, ".cineview-mla-hddtest-%d-%d.jpg" % (int(time.time()), os.getpid()))
    t0 = time.time()
    fd = os.open(test, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)  # exclusive: never overwrites anything
    os.write(fd, data)
    os.fsync(fd)
    os.close(fd)
    t1 = time.time()
    back = open(test, "rb").read()
    same = hashlib.sha256(back).hexdigest() == hashlib.sha256(data).hexdigest()
    say("test file", "%s (%d bytes, from %s)" % (test, len(data), src_poster or "random"))
    say("write + fsync", "%.1f ms" % ((t1 - t0) * 1000))
    say("read back identical", same, same)
    os.remove(test)  # only the file this test created
    say("test file removed", not os.path.exists(test), not os.path.exists(test))
    if created:
        try:
            os.rmdir(TARGET)  # only if empty (rmdir fails otherwise) and only because this test created it
            say("poster dir removed", "created by this test, empty")
        except OSError as err:
            say("poster dir kept", str(err))
    else:
        say("poster dir", "existed before: kept as it was")
print("== t92 %s: %s" % (MODE, "PASS" if ok else "FAIL"))
