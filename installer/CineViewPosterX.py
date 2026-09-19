# -*- coding: utf-8 -*-
from __future__ import print_function

# CineView FHD native poster renderer.
# Unique renderer name avoids conflicts with PosterX packages shipped by images.

import os
import re
import threading

from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, eTimer, loadJPG, eEPGCache
import NavigationInstance

CACHE_ROOT = "/tmp/CINEVIEW/poster"
API_SINGLE = "https://api.tvmaze.com/singlesearch/shows"
API_SEARCH = "https://api.tvmaze.com/search/shows"
API_ITUNES = "https://itunes.apple.com/search"
API_IMDB = "https://v3.sg.media-imdb.com/suggestion/x/%s.json"
UA = "CineView-FHD/2.0.2 (Enigma2 native poster renderer)"
LOG_PATH = "/tmp/CINEVIEW/poster.log"
MAX_POSTER_PIXELS = 4000000
MAX_POSTER_EDGE = 2600

def _jpeg_dimensions(data):
    """Read JPEG SOF dimensions without decoding pixel data."""
    try:
        if not data or data[:2] != b"\xff\xd8":
            return None
        i = 2
        n = len(data)
        sof = {0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}
        while i + 9 < n:
            if data[i] != 0xFF:
                i += 1
                continue
            while i < n and data[i] == 0xFF:
                i += 1
            if i >= n:
                break
            marker = data[i]
            i += 1
            if marker in (0xD8,0xD9):
                continue
            if i + 1 >= n:
                break
            seglen = (data[i] << 8) | data[i+1]
            if seglen < 2 or i + seglen > n:
                break
            if marker in sof and seglen >= 7:
                h = (data[i+3] << 8) | data[i+4]
                w = (data[i+5] << 8) | data[i+6]
                return (w,h)
            i += seglen
    except Exception:
        pass
    return None

def _safe_dimensions(dims):
    if not dims:
        return False
    w,h = dims
    return w > 0 and h > 0 and max(w,h) <= MAX_POSTER_EDGE and (w*h) <= MAX_POSTER_PIXELS

def _safe_jpeg_file(path):
    try:
        with open(path, "rb") as f:
            head = f.read(262144)
        dims = _jpeg_dimensions(head)
        if not _safe_dimensions(dims):
            _log("reject-cache path=%s dims=%s" % (path, dims))
            try:
                os.unlink(path)
            except Exception:
                pass
            return False
        return True
    except Exception:
        return False


_epg = eEPGCache.getInstance()
_lock = threading.Lock()
_pending = set()
_callbacks = {}


def _mkdir(path):
    try:
        os.makedirs(path)
    except OSError:
        pass


def _clean_title(text):
    text = (text or "").replace("\x86", "").replace("\x87", "").strip()
    text = re.sub(r'(?i)\s*[\[(]?(?:ep\.?|episode|odc\.?|sezon|season|s\d+e\d+)\s*\d*[^\])]*[\])]?\s*$', '', text)
    text = re.sub(r'\s+', ' ', text).strip(' -:|')
    return text


def _safe_name(title):
    value = _clean_title(title).lower()
    value = re.sub(r'[^\w .()\-]+', ' ', value, flags=re.UNICODE)
    value = re.sub(r'\s+', ' ', value).strip()
    return value[:180] or "unknown"


def _poster_path(title):
    _mkdir(CACHE_ROOT)
    return os.path.join(CACHE_ROOT, _safe_name(title) + ".jpg")


def _log(msg):
    try:
        _mkdir("/tmp/CINEVIEW")
        with open(LOG_PATH, "a") as f:
            f.write(msg.replace("\\n", " ")[:900] + "\\n")
    except Exception:
        pass


def _queries(title):
    q = _clean_title(title)
    out = []
    for value in (
        q,
        re.sub(r"\\s*[:|\\-]\\s*[^:|\\-]+$", "", q).strip(),
        re.sub(r"\\([^)]*\\)|\\[[^]]*\\]", "", q).strip(),
    ):
        value = re.sub(r"\\s+", " ", value).strip(" -:|")
        if value and value not in out:
            out.append(value)
    return out


def _http_get(url, params=None, timeout=7.0, want_json=False):
    try:
        import requests
        r = requests.get(
            url,
            params=params,
            headers={"User-Agent": UA, "Accept": "application/json" if want_json else "image/jpeg,*/*;q=0.8"},
            timeout=timeout,
        )
        if not r.ok:
            return None
        return r.json() if want_json else r.content
    except Exception:
        pass

    try:
        try:
            from urllib.parse import urlencode
            from urllib.request import Request, urlopen
        except ImportError:
            from urllib import urlencode
            from urllib2 import Request, urlopen
        if params:
            url = url + ("&" if "?" in url else "?") + urlencode(params)
        req = Request(url, headers={"User-Agent": UA, "Accept": "application/json" if want_json else "image/jpeg,*/*;q=0.8"})
        res = urlopen(req, timeout=timeout)
        body = res.read()
        if want_json:
            import json
            if not isinstance(body, str):
                body = body.decode("utf-8", "ignore")
            return json.loads(body)
        return body
    except Exception:
        return None


def _quote(value):
    try:
        from urllib.parse import quote
    except ImportError:
        from urllib import quote
    try:
        return quote(value.encode("utf-8") if not isinstance(value, str) else value)
    except Exception:
        try:
            return quote(value)
        except Exception:
            return value


def _imdb_bounded_url(url):
    """Ask IMDb's own CDN for a receiver-safe poster instead of the original."""
    if not url:
        return None
    scaled = re.sub(r'\._V1_[^/]*?\.jpg(?:\?.*)?$', '._V1_FMjpg_UY900_.jpg', url)
    return scaled if scaled != url else url


def _imdb_artwork(q):
    # IMDb suggestion understands localized movie/series titles and needs no API key.
    data = _http_get(API_IMDB % _quote(q), timeout=6.0, want_json=True) or {}
    for row in (data.get("d") or [])[:8]:
        if not str(row.get("id") or "").startswith("tt"):
            continue
        image = row.get("i") or {}
        url = image.get("imageUrl")
        if url:
            return _imdb_bounded_url(url)
    return None


def _itunes_artwork(q):
    # Apple Search covers movies as well as TV and needs no API key.
    # Try common storefronts because EPG titles are frequently localized.
    for country in ("US", "GB", "PL", "DE", "FR", "IT", "ES"):
        for media, entity in (("movie", "movie"), ("tvShow", "tvSeason")):
            data = _http_get(
                API_ITUNES,
                params={"term": q, "media": media, "entity": entity, "limit": 5, "country": country},
                timeout=6.0,
                want_json=True,
            ) or {}
            for row in (data.get("results") or [])[:5]:
                url = row.get("artworkUrl100") or row.get("artworkUrl60")
                if url:
                    # Apple's image CDN accepts larger requested dimensions.
                    url = re.sub(r"/\\d+x\\d+bb\\.", "/600x900bb.", url)
                    return url
    return None


def _image_url(title):
    queries = _queries(title)
    if not queries:
        return None

    # TVMaze is excellent for series/episodes.
    for q in queries:
        data = _http_get(API_SINGLE, params={"q": q}, timeout=6.0, want_json=True) or {}
        image = data.get("image") or {}
        url = image.get("medium") or image.get("original")
        if url:
            _log("provider=tvmaze title=%s query=%s" % (title, q))
            return url
        rows = _http_get(API_SEARCH, params={"q": q}, timeout=6.0, want_json=True) or []
        for row in rows[:5]:
            show = (row or {}).get("show") or {}
            image = show.get("image") or {}
            url = image.get("medium") or image.get("original")
            if url:
                _log("provider=tvmaze-search title=%s query=%s" % (title, q))
                return url

    # Localized EPG movie names often do not exist in TVMaze. IMDb's
    # suggestion endpoint maps localized titles to the canonical title and poster.
    for q in queries:
        url = _imdb_artwork(q)
        if url:
            _log("provider=imdb title=%s query=%s" % (title, q))
            return url

    # Final no-key fallback for movie/TV storefront artwork.
    for q in queries:
        url = _itunes_artwork(q)
        if url:
            _log("provider=itunes title=%s query=%s" % (title, q))
            return url

    _log("provider=none title=%s queries=%s" % (title, " | ".join(queries)))
    return None


def _notify(title):
    # Worker threads must never touch Enigma2 GUI/C++ objects.
    # Each renderer instance already polls from its own eTimer on the GUI thread.
    with _lock:
        _callbacks.pop(title, None)
        _pending.discard(title)


def _download(title):
    path = _poster_path(title)
    tmp = path + ".part"

    def fetch_safe(url):
        if not url:
            return None
        body = _http_get(url, timeout=9.0, want_json=False)
        if not body or len(body) <= 1500:
            return None
        dims = _jpeg_dimensions(body[:262144])
        if _safe_dimensions(dims):
            return body
        _log("reject-download title=%s dims=%s url=%s" % (title, dims, url))
        return None

    try:
        url = _image_url(title)
        body = fetch_safe(url)

        # IMDb can return poster originals far larger than an STB ever needs.
        # If the selected provider is oversized, use iTunes' bounded 600x900 art.
        if body is None:
            for q in _queries(title):
                small = _itunes_artwork(q)
                body = fetch_safe(small)
                if body is not None:
                    _log("provider=itunes-safe title=%s query=%s" % (title, q))
                    break

        if body is not None:
            _mkdir(CACHE_ROOT)
            with open(tmp, "wb") as f:
                f.write(body)
            os.rename(tmp, path)
    except Exception:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass
    _notify(title)


def _queue(title, obj):
    title = _clean_title(title)
    if not title:
        return
    with _lock:
        bucket = _callbacks.setdefault(title, [])
        if obj not in bucket:
            bucket.append(obj)
        if title in _pending:
            return
        _pending.add(title)
    t = threading.Thread(target=_download, args=(title,))
    t.daemon = True
    t.start()


def _current_ref():
    try:
        return NavigationInstance.instance.getCurrentlyPlayingServiceReference()
    except Exception:
        return None


def _source_event(source):
    try:
        return getattr(source, "event", None)
    except Exception:
        return None


def _source_ref(source):
    for method in ("getCurrentService", "getCurrentServiceRef"):
        try:
            fn = getattr(source, method, None)
            if fn:
                ref = fn()
                if ref is not None:
                    return ref
        except Exception:
            pass
    try:
        ref = getattr(source, "service", None)
        if ref is not None:
            return ref
    except Exception:
        pass
    return _current_ref()


def _lookup_event(ref, slot):
    if ref is None:
        return None
    try:
        rows = _epg.lookupEvent(['IBDCTESX', (ref.toString(), 0, -1, -1)]) or []
        slot = max(0, int(slot))
        if slot < len(rows):
            row = rows[slot]
            if row and len(row) >= 5:
                return row[4] or ""
    except Exception:
        pass
    try:
        ev = _epg.lookupEventTime(ref, -1, 1 if int(slot) else 0)
        return ev and (ev.getEventName() or "") or ""
    except Exception:
        return ""


class CineViewPosterX(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.nexts = 0
        self._title = ""
        self._timer = eTimer()
        self._timer.callback.append(self._poll)
        self._polls = 0

    def applySkin(self, desktop, parent):
        attrs = []
        for key, value in self.skinAttributes:
            if key == "nexts":
                try:
                    self.nexts = int(value)
                except Exception:
                    self.nexts = 0
            else:
                attrs.append((key, value))
        self.skinAttributes = attrs
        return Renderer.applySkin(self, desktop, parent)

    def _resolve_title(self):
        ev = _source_event(self.source)
        if ev is not None and self.nexts == 0:
            try:
                name = ev.getEventName() or ""
                if name:
                    return name
            except Exception:
                pass
        return _lookup_event(_source_ref(self.source), self.nexts)

    def changed(self, what):
        if not self.instance:
            return
        if what[0] == self.CHANGED_CLEAR:
            self.instance.hide()
            self._timer.stop()
            return

        title = _clean_title(self._resolve_title())
        if not title:
            self.instance.hide()
            return

        self._title = title
        path = _poster_path(title)
        if os.path.exists(path) and os.path.getsize(path) > 1500:
            if _safe_jpeg_file(path):
                self._show(path)
                return

        self.instance.hide()
        _queue(title, self)
        self._polls = 0
        self._timer.start(500, True)

    def _wake(self):
        try:
            self._polls = 0
            self._timer.start(50, True)
        except Exception:
            pass

    def _poll(self):
        if not self.instance or not self._title:
            return
        path = _poster_path(self._title)
        if os.path.exists(path) and os.path.getsize(path) > 1500:
            if _safe_jpeg_file(path):
                self._show(path)
                return
        self._polls += 1
        with _lock:
            pending = self._title in _pending
        if pending and self._polls < 180:
            self._timer.start(500, True)

    def _show(self, path):
        try:
            pix = loadJPG(path)
            if pix:
                self.instance.setPixmap(pix)
                self.instance.setScale(1)
                self.instance.show()
            else:
                self.instance.hide()
        except Exception:
            self.instance.hide()

    def destroy(self):
        try:
            self._timer.stop()
        except Exception:
            pass
        try:
            with _lock:
                for title, bucket in list(_callbacks.items()):
                    if self in bucket:
                        bucket.remove(self)
                    if not bucket:
                        _callbacks.pop(title, None)
        except Exception:
            pass
        Renderer.destroy(self)
