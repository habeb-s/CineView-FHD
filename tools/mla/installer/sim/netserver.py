#!/usr/bin/env python3
"""Test distribution point with faulty network behaviours (for installer download tests only).
URL: /<mode>/packages/<image>/<file>  served from <dist>/packages/<image>/<file>.  Range requests are honoured
(resume) except in mode 'norange'.  Per (mode, file) the server counts requests to script first-attempt failures.
modes: ok | slow (~1.5 MB/s) | drop (1st request cut after 35 %) | stall (1st request stalls after 30 %, longer than
the client timeout) | dropnorange (1st request cut, later requests ignore Range) | corrupt (always 1 byte changed)
| corruptonce (1st complete download corrupt) | 404 | flaky (1st and 2nd request cut) | dead (every request cut)
usage: netserver.py <dist dir> <port>"""
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DIST, PORT = sys.argv[1], int(sys.argv[2])
COUNT = {}
LOCK = threading.Lock()


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *a):
        sys.stderr.write("%s %s\n" % (self.command, self.path))

    def do_GET(self):
        parts = self.path.lstrip("/").split("/", 1)
        if len(parts) != 2:
            return self.send_error(404)
        run, rel = parts
        mode = run.split("-")[0]
        path = os.path.join(DIST, rel)
        if mode == "404" or not os.path.isfile(path):
            return self.send_error(404, "Not Found")
        with LOCK:
            k = (run, rel)
            COUNT[k] = COUNT.get(k, 0) + 1
            nreq = COUNT[k]
        data = open(path, "rb").read()
        if mode == "corrupt" or (mode == "corruptonce" and nreq == 1):
            data = data[:1000] + bytes([data[1000] ^ 0xFF]) + data[1001:]
        start = 0
        rng = self.headers.get("Range")
        honour = not (mode == "dropnorange" and nreq > 1)
        if rng and honour and rng.startswith("bytes="):
            start = int(rng[6:].split("-")[0] or 0)
        if start >= len(data):
            self.send_response(416)
            self.send_header("Content-Range", "bytes */%d" % len(data))
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        body = data[start:]
        if start:
            self.send_response(206)
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, len(data) - 1, len(data)))
        else:
            self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Accept-Ranges", "none" if not honour else "bytes")
        self.end_headers()
        cut = None
        if (mode in ("drop", "dropnorange") and nreq == 1) or (mode == "flaky" and nreq <= 2):
            cut = int(len(body) * 0.35)
        if mode == "dead":  # headers, then the connection drops before any data - no progress is ever made
            cut = 0
        stall = int(len(body) * 0.30) if mode == "stall" and nreq == 1 else None
        chunk = 64 * 1024
        sent = 0
        try:
            while sent < len(body):
                if cut is not None and sent >= cut:
                    self.connection.shutdown(2)
                    return
                if stall is not None and sent >= stall:
                    time.sleep(40)  # longer than the client's idle timeout used in the test
                    self.connection.shutdown(2)
                    return
                self.wfile.write(body[sent:sent + chunk])
                sent += chunk
                if mode == "slow":
                    time.sleep(chunk / 1.5e6)
        except (BrokenPipeError, ConnectionResetError, OSError):
            return


ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
