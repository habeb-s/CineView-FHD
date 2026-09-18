# -*- coding: utf-8 -*-
from __future__ import print_function

# CineView FHD 2.0 native PosterX renderer.
# Independent from other skins/plugins. Temporary cache only.

import os
import re
import time
import threading

from Components.Renderer.Renderer import Renderer
try:
    from Components.Sources.Event import Event
except Exception:
    Event = ()
try:
    from Components.Sources.EventInfo import EventInfo
except Exception:
    EventInfo = ()
try:
    from Components.Sources.ServiceEvent import ServiceEvent
except Exception:
    ServiceEvent = ()
try:
    from Components.Sources.CurrentService import CurrentService
except Exception:
    CurrentService = ()

from enigma import ePixmap, eTimer, loadJPG, eEPGCache
import NavigationInstance

CACHE_ROOT = "/tmp/CINEVIEW/poster"
API_SEARCH = "https://api.tvmaze.com/singlesearch/shows"
UA = "CineView-FHD/2.0 (Enigma2 poster renderer)"

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


def _notify(title):
    with _lock:
        objs = list(_callbacks.pop(title, []))
        _pending.discard(title)
    for obj in objs:
        try:
            obj._wake()
        except Exception:
            pass


def _download(title):
    path = _poster_path(title)
    tmp = path + ".part"
    try:
        import requests
        r = requests.get(
            API_SEARCH,
            params={"q": _clean_title(title)},
            headers={"User-Agent": UA, "Accept": "application/json"},
            timeout=(2.5, 5.0),
        )
        if r.ok:
            data = r.json() or {}
            image = data.get("image") or {}
            url = image.get("original") or image.get("medium")
            if url:
                img = requests.get(url, headers={"User-Agent": UA}, timeout=(2.5, 7.0))
                ctype = (img.headers.get("content-type") or "").lower()
                if img.ok and len(img.content) > 1500 and ("image" in ctype or url.lower().endswith((".jpg", ".jpeg"))):
                    _mkdir(CACHE_ROOT)
                    with open(tmp, "wb") as f:
                        f.write(img.content)
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


def _lookup_event(ref, slot):
    if ref is None:
        return None
    try:
        rows = _epg.lookupEvent(['IBDCTESX', (ref.toString(), 0, -1, -1)]) or []
        slot = max(0, int(slot))
        if slot >= len(rows):
            return None
        row = rows[slot]
        if not row or len(row) < 7:
            return None
        return {"title": row[4] or ""}
    except Exception:
        return None


class PosterX(Renderer):
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

        ref = None
        try:
            if ServiceEvent and isinstance(self.source, ServiceEvent):
                ref = self.source.getCurrentService()
            elif CurrentService and isinstance(self.source, CurrentService):
                ref = self.source.getCurrentServiceRef()
        except Exception:
            ref = None
        if ref is None:
            ref = _current_ref()

        item = _lookup_event(ref, self.nexts)
        return (item or {}).get("title", "")

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
            self._show(path)
            return
        self._polls += 1
        if self._polls < 30:
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
