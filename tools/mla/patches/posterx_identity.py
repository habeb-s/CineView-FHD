
# ======================================================================================================
# CineView MLA (P5) — unified poster identity, appended by tools/mla/build.py to CineViewMLAPosterX.py.
# Every poster widget (InfoBar, SecondInfoBar, EventView, EPG, ChannelSelection) resolves the EVENT, not
# just its title: Components.CineViewMLAPosterMatch.identify() -> title+kind+year key, provider candidates
# are scored, and only a reliable match is cached/shown.  Generic programmes and unreliable/ambiguous
# matches show the neutral default poster instead of a wrong one.  Decisions are logged to poster.log.
# ======================================================================================================
import json as _mla_json
import time as _mla_time

from Components.CineViewMLAPosterMatch import identify as _mla_identify, choose as _mla_choose, \
    imdb_candidates as _mla_imdb, tvmaze_candidates as _mla_tvmaze, itunes_candidates as _mla_itunes

_MLA_DEFAULT = "/usr/share/enigma2/CineView_FHD_MLA/mla_assets/poster_default.jpg"
_MLA_NEG_TTL = 12 * 3600
_mla_alias = {}  # norm title -> best identity key resolved in this session (fills screens lacking year/kind)


def _mla_safe(key):
    value = re.sub(r'[^\w .()~\-]+', ' ', key, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', value).strip()[:200] or "unknown"


def _mla_path(key):
    _mkdir(CACHE_ROOT)
    return os.path.join(CACHE_ROOT, "id", _mla_safe(key) + ".jpg")


def _mla_neg_path(key):
    return os.path.join(CACHE_ROOT, "id", _mla_safe(key) + ".none")


def _mla_negative(key):
    try:
        return _mla_time.time() - os.path.getmtime(_mla_neg_path(key)) < _MLA_NEG_TTL
    except OSError:
        return False


def _mla_cached(ident):
    """Cached file for this identity; an identity without year/kind may use the richer identity another
    screen resolved for the same title (same event seen with its description)."""
    p = _mla_path(ident["key"])
    if os.path.exists(p) and os.path.getsize(p) > 1500 and _safe_jpeg_file(p):
        return p
    if not ident["kind"] and not ident["year"]:
        alias = _mla_alias.get(ident["norm"])
        if alias:
            p = _mla_path(alias)
            if os.path.exists(p) and os.path.getsize(p) > 1500 and _safe_jpeg_file(p):
                return p
    return None


def _mla_candidates(ident):
    q = ident["title"]
    out = []
    data = _http_get(API_IMDB % _quote(q), timeout=6.0, want_json=True) or {}
    out += _mla_imdb(data)
    if ident["kind"] != "movie":
        out += _mla_tvmaze(_http_get(API_SEARCH, params={"q": q}, timeout=6.0, want_json=True) or [])
    if not out:
        for media, entity in (("movie", "movie"), ("tvShow", "tvSeason")):
            if ident["kind"] and ident["kind"] != ("movie" if media == "movie" else "series"):
                continue
            out += _mla_itunes(_http_get(API_ITUNES, params={"term": q, "media": media, "entity": entity, "limit": 5, "country": "US"}, timeout=6.0, want_json=True) or {}, media)
    return out


def _mla_fetch(url):
    body = _http_get(_imdb_bounded_url(url) if "media-amazon" in (url or "") else url, timeout=9.0, want_json=False)
    if not body or len(body) <= 1500:
        return None
    try:
        from io import BytesIO
        from PIL import Image
        src = Image.open(BytesIO(body))
        src.load()
        if src.mode != "RGB":
            src = src.convert("RGB")
        src.thumbnail((600, 900), Image.Resampling.LANCZOS)
        if src.width < 40 or src.height < 40:
            return None
        out = BytesIO()
        src.save(out, format="JPEG", quality=88, optimize=True)
        return out.getvalue()
    except Exception as e:
        _log("image-normalise-failed url=%s err=%s" % (url, e))
        return None


def _mla_download(ident):
    key = ident["key"]
    try:
        cands = _mla_candidates(ident)
        best, conf, why = _mla_choose(ident, cands)
        body = _mla_fetch(best["url"]) if best else None
        if best and body is None and best["provider"] == "imdb":
            why += " (download failed)"
        if body is not None:
            path = _mla_path(key)
            _mkdir(os.path.dirname(path))
            with open(path + ".part", "wb") as f:
                f.write(body)
            os.rename(path + ".part", path)
            meta = {"key": key, "provider": best["provider"], "id": best.get("id"), "title": best["title"],
                "year": best.get("year"), "kind": best.get("kind"), "confidence": round(conf, 2), "time": int(_mla_time.time())}
            with open(path[:-4] + ".json", "w") as f:
                _mla_json.dump(meta, f)
        else:
            _mkdir(os.path.join(CACHE_ROOT, "id"))
            open(_mla_neg_path(key), "w").write(why[:300])
        _log("identity key=%s title=%s kind=%s year=%s candidates=%d -> %s" % (key, ident["title"], ident["kind"], ident["year"], len(cands), why))
    except Exception as e:
        _log("identity-error key=%s err=%s" % (key, e))
    _notify(key)


def _mla_queue(ident, obj):
    key = ident["key"]
    with _lock:
        bucket = _callbacks.setdefault(key, [])
        if obj not in bucket:
            bucket.append(obj)
        if key in _pending:
            return
        _pending.add(key)
    t = threading.Thread(target=_mla_download, args=(ident,))
    t.daemon = True
    t.start()


def _mla_event_texts(ev):
    try:
        return ev.getEventName() or "", ev.getShortDescription() or "", ev.getExtendedDescription() or "", ev.getBeginTime()
    except Exception:
        return "", "", "", 0


def _mla_engine_enabled():
    # Not merged as the default until it is device-tested (user decision 18:51): opt-in per receiver via
    # /etc/enigma2/cineview_mla/runtime.json {"poster_engine": "identity"}; anything else = legacy engine.
    try:
        return _mla_json.load(open("/etc/enigma2/cineview_mla/runtime.json")).get("poster_engine") == "identity"
    except Exception:
        return False


_CineViewMLAPosterXBase = CineViewMLAPosterX


class _CineViewMLAPosterXIdentity(_CineViewMLAPosterXBase):
    def _resolve_event(self):
        ev = _source_event(self.source)
        ref = _source_ref(self.source)
        if ev is not None and self.nexts == 0:
            return ev
        if ev is not None and self.nexts > 0 and ref is not None:
            try:
                t = ev.getBeginTime() + ev.getDuration()
                nxt = None
                for _i in range(self.nexts):
                    nxt = _epg.lookupEventTime(ref, t)
                    if nxt is None:
                        break
                    t = nxt.getBeginTime() + nxt.getDuration()
                if nxt is not None:
                    return nxt
            except Exception:
                pass
        if ref is not None:
            try:
                return _epg.lookupEventTime(ref, -1, 1 if self.nexts else 0)
            except Exception:
                return None
        return None

    def _show_default(self):
        if os.path.exists(_MLA_DEFAULT):
            self._show(_MLA_DEFAULT)
        else:
            self.instance.hide()

    def changed(self, what):
        if not self.instance:
            return
        if what[0] == self.CHANGED_CLEAR or not self._enabled():
            self.instance.hide()
            self._timer.stop()
            self._title = ""
            return
        ev = self._resolve_event()
        name, short, ext, begin = _mla_event_texts(ev) if ev is not None else ("", "", "", 0)
        if not name:
            self.instance.hide()
            self._title = ""
            return
        ident = _mla_identify(name, short, ext, now_year=_mla_time.localtime().tm_year + 1)
        self._ident = ident
        self._title = ident["key"]
        if ident["generic"]:
            self._timer.stop()
            self._show_default()
            return
        path = _mla_cached(ident)
        if path:
            self._timer.stop()
            if ident["kind"] or ident["year"]:
                _mla_alias[ident["norm"]] = ident["key"]
            self._show(path)
            return
        self._show_default()
        if _mla_negative(ident["key"]):
            self._timer.stop()
            return
        _mla_queue(ident, self)
        self._polls = 0
        self._timer.start(500, True)

    def _poll(self):
        if not self.instance or not self._title:
            return
        ident = getattr(self, "_ident", None)
        if ident is None or ident["key"] != self._title:
            return
        path = _mla_cached(ident)
        if path:
            if ident["kind"] or ident["year"]:
                _mla_alias[ident["norm"]] = ident["key"]
            self._show(path)
            return
        self._polls += 1
        with _lock:
            pending = self._title in _pending
        if pending and self._polls < 180:
            self._timer.start(500, True)


if _mla_engine_enabled():
    CineViewMLAPosterX = _CineViewMLAPosterXIdentity
    _log("engine=identity (runtime.json)")
