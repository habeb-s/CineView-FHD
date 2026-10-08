#!/usr/bin/env python3
"""CineView MLA distribution service (reference implementation, Python 3 standard library only).

The public installer script holds no package list, no versions, no SHA256 values and no image compatibility rules:
it asks this service.  Packages live in a private store on the server (never in a public repository) and are
handed out only through short-lived signed links.  No accounts, keys, IP / User-Agent checks or device fingerprints:
any receiver that runs the official installer gets the package that fits it.

  GET /v1/probe                 -> {"paths": [...]}  files the installer checks for on the receiver (no labels)
  GET /v1/resolve?distro=&version=&python=&found=<bits>&channel=current|previous
                                -> {"ok": true, "image", "support", "python", "version", "file", "sha256", "url"}
                                   or {"ok": false, "message"}
  GET /v1/pkg/<id>/<expiry>/<sig>  the package (Range supported for resumed downloads); 410 when the link expired

Run behind HTTPS with a certificate from a public CA (e.g. a reverse proxy with Let's Encrypt), or directly with
--cert/--key.  The secret signs the links; keep it and the store outside any repository.
usage: cvmla_dist.py --catalog catalog.json --store <dir> --secret-file <file> [--port 8443] [--cert c --key k]
       [--ttl 7200] [--test-faults]  (test only: resolve accepts fault=<mode> and the link misbehaves accordingly)"""
import argparse
import hashlib
import hmac
import json
import os
import ssl
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

A = argparse.ArgumentParser()
A.add_argument("--catalog", required=True)
A.add_argument("--store", required=True)
A.add_argument("--secret-file", required=True)
A.add_argument("--port", type=int, default=8443)
A.add_argument("--bind", default="0.0.0.0")
A.add_argument("--cert")
A.add_argument("--key")
A.add_argument("--ttl", type=int, default=7200)
A.add_argument("--test-faults", action="store_true")
O = A.parse_args()
CAT = json.load(open(O.catalog))
SECRET = open(O.secret_file, "rb").read().strip()
assert len(SECRET) >= 32, "secret too short"
FILES = {}  # id -> (path, sha256)
for key, img in CAT["images"].items():
    for ch in ("current", "previous"):
        p = img[ch]
        path = os.path.join(O.store, p["file"])
        got = hashlib.sha256(open(path, "rb").read()).hexdigest()
        assert got == p["sha256"], "store file %s does not match the catalog" % p["file"]
        FILES[p["sha256"][:24]] = (path, p["sha256"])
COUNT = {}
LOCK = threading.Lock()


def sign(fid, exp, fault=""):
    return hmac.new(SECRET, ("%s|%s|%s" % (fid, exp, fault)).encode(), hashlib.sha256).hexdigest()[:40]


def decide(q):
    """the compatibility rules - kept on the server"""
    distro = q.get("distro", "")
    ver = q.get("version", "")
    found = q.get("found", "")
    img = CAT["images"].get(distro)
    if not distro:
        return {"ok": False, "message": "This image does not name itself in /usr/lib/enigma.info: it cannot be identified."}
    if img is None:
        return {"ok": False, "message": "This image is '%s'. CineView MLA supports %s." % (distro, CAT["supported_text"])}
    probe = CAT["probe"]
    if len(found) != len(probe) or set(found) - set("01"):
        return {"ok": False, "message": "The installer is out of date. Please download the official installer again."}
    owners = [k for k, other in CAT["images"].items() if any(found[i] == "1" for i in other["markers"])]
    if owners != [distro]:
        return {"ok": False, "message": "enigma.info names %s, but the image's own files point to '%s': the image cannot "
                "be identified reliably." % (img["name"], " ".join(owners) or "no known image")}
    if not any(ver == t or ver.startswith(t + ".") for t in img["tested"]):
        return {"ok": False, "message": "%s %s has not been tested with CineView MLA, so it is not installed (tested: %s)."
                % (img["name"], ver, CAT["tested_text"])}
    ch = "previous" if q.get("channel") == "previous" else "current"
    p = img[ch]
    exp = int(time.time()) + O.ttl
    fid = p["sha256"][:24]
    fault = q.get("fault", "") if O.test_faults else ""
    url = "/v1/pkg/%s/%d/%s" % (fid, exp, sign(fid, exp, fault)) + ("?fault=" + fault if fault else "")
    return {"ok": True, "image": img["name"], "support": "%s %s is supported (tested on %s %s)" % (
        img["name"], ver, img["name"], " / ".join(img["tested"])), "python": img["python"], "version": p["version"],
        "file": p["file"], "sha256": p["sha256"], "url": url}


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "cvmla-dist"
    sys_version = ""

    def log_message(self, fmt, *a):  # no IP logging; path only
        sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), self.requestline.split("?")[0]))

    def js(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urllib.parse.urlsplit(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        if u.path == "/v1/probe":
            return self.js({"paths": CAT["probe"]})
        if u.path == "/v1/resolve":
            return self.js(decide(q))
        parts = u.path.split("/")
        if len(parts) == 6 and parts[1:3] == ["v1", "pkg"]:
            fid, exp, sig = parts[3], parts[4], parts[5]
            fault = q.get("fault", "") if O.test_faults else ""
            if fid not in FILES or not exp.isdigit() or not hmac.compare_digest(sig, sign(fid, exp, fault)):
                return self.js({"error": "not found"}, 404)
            if int(exp) < time.time() or fault == "gone" and COUNT.setdefault(("gone", fid), 0) == 0:
                COUNT[("gone", fid)] = 1  # test: the first link handed out for this file has expired, a new one works
                return self.js({"error": "link expired"}, 410)
            return self.send_pkg(FILES[fid][0], fault, sig)
        return self.js({"error": "not found"}, 404)

    def send_pkg(self, path, fault, sig):
        with LOCK:
            COUNT[sig] = COUNT.get(sig, 0) + 1
            n = COUNT[sig]
        data = open(path, "rb").read()
        if fault == "corrupt" or (fault == "corruptonce" and n == 1):
            data = data[:1000] + bytes([data[1000] ^ 0xFF]) + data[1001:]
        start = 0
        rng = self.headers.get("Range", "")
        if rng.startswith("bytes=") and fault != "norange":
            start = int(rng[6:].split("-")[0] or 0)
        if start >= len(data):
            self.send_response(416)
            self.send_header("Content-Range", "bytes */%d" % len(data))
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        body = data[start:]
        self.send_response(206 if start else 200)
        if start:
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, len(data) - 1, len(data)))
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Accept-Ranges", "none" if fault == "norange" else "bytes")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        cut = stall = None
        if (fault in ("drop", "norange") and n == 1) or (fault == "flaky" and n <= 2):
            cut = int(len(body) * 0.35)
        if fault == "dead":
            cut = 0
        if fault == "stall" and n == 1:
            stall = int(len(body) * 0.30)
        sent = 0
        try:
            while sent < len(body):
                if cut is not None and sent >= cut:
                    self.connection.shutdown(2)
                    return
                if stall is not None and sent >= stall:
                    time.sleep(40)
                    self.connection.shutdown(2)
                    return
                self.wfile.write(body[sent:sent + 65536])
                sent += 65536
                if fault == "slow":
                    time.sleep(65536 / 1.5e6)
        except OSError:
            return


S = ThreadingHTTPServer((O.bind, O.port), H)
if O.cert:
    c = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    c.load_cert_chain(O.cert, O.key)
    S.socket = c.wrap_socket(S.socket, server_side=True)
S.serve_forever()
