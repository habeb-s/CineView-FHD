import hashlib, json, os, re, ssl, sys, time, urllib.error, urllib.request
# CineView MLA installer helper: HTTPS with certificate verification ALWAYS on (never disabled).
# exit: 0 ok | 2 SHA256 mismatch | 3 refused / not found / link expired | 4 network | 5 certificate not verifiable


def ctx():
    c = ssl.create_default_context()
    if not c.cert_store_stats().get("x509_ca"):  # image CA bundle not in OpenSSL's default place: add it, still verified
        for f in ("/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt", "/etc/ssl/cert.pem"):
            if os.path.isfile(f):
                try:
                    c.load_verify_locations(f)
                except Exception:
                    pass
        try:
            import certifi
            c.load_verify_locations(certifi.where())
        except Exception:
            pass
    return c


def code(e):
    r = getattr(e, "reason", None)
    if isinstance(e, ssl.SSLCertVerificationError) or isinstance(r, ssl.SSLCertVerificationError):
        return 5
    if isinstance(e, urllib.error.HTTPError):
        return 3 if e.code in (403, 404, 410) else 4
    return 4


def get(url):
    last = 4
    for n in range(3):
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=20, context=ctx()).read().decode())
            break
        except Exception as e:
            last = code(e)
            if last == 5:
                return 5
            time.sleep(2 * (n + 1))
    else:
        return last
    for p in d.get("paths", []):
        if re.match(r"^[A-Za-z0-9_/]+$", p):
            print("P=" + p)
    for k, v in d.items():
        if k != "paths" and re.match(r"^[a-z0-9_]+$", k):
            print("%s=%s" % (k.upper(), str(int(v) if isinstance(v, bool) else v).replace("\n", " ")))
    return 0


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def fetch(url, out, want, tries, tmo):
    last = 4
    for n in range(1, tries + 1):
        try:
            have = os.path.getsize(out) if os.path.exists(out) else 0
            req = urllib.request.Request(url, headers={"Range": "bytes=%d-" % have} if have else {})
            try:
                r = urllib.request.urlopen(req, timeout=tmo, context=ctx())  # timeout = idle time, not total time
            except urllib.error.HTTPError as e:
                if e.code != 416:
                    raise
                r = None  # the file is already complete
            if r is not None:
                mode = "ab" if have and r.status == 206 else "wb"
                expect = int(r.headers.get("Content-Length") or -1)
                got = 0
                with open(out, mode) as f:
                    for b in iter(lambda: r.read(1 << 16), b""):
                        f.write(b)
                        got += len(b)
                if expect >= 0 and got < expect:  # connection closed early: keep the part, the next attempt resumes
                    raise ConnectionError("incomplete")
            if sha(out) == want:
                return 0
            os.remove(out)  # complete but not the official file: the next attempt starts from zero
            last = 2
        except Exception as e:
            last = code(e)
            if last in (3, 5):
                return last
        if n < tries:
            sys.stderr.write("  [..] Download interrupted - trying again (%d of %d)\n" % (n + 1, tries))
            sys.stderr.flush()
            time.sleep(3 * n)
    return last


if __name__ == "__main__":
    if sys.argv[1] == "get":
        sys.exit(get(sys.argv[2]))
    sys.exit(fetch(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6])))
