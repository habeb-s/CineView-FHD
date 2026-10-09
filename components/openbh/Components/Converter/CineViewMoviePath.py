# -*- coding: utf-8 -*-
import os
from Components.Converter.Converter import Converter
from Components.Element import cached

class CineViewMoviePath(Converter):
    def __init__(self, type):
        Converter.__init__(self, type)
        self.mode = (type or "Full").strip().lower()

    def _reference(self):
        ref = getattr(self.source, "service", None)
        if callable(ref):
            try:
                ref = ref()
            except Exception:
                ref = None
        if ref:
            return ref
        for name in ("getCurrentServiceReference", "getCurrentServiceRef", "getCurrentService"):
            fn = getattr(self.source, name, None)
            if callable(fn):
                try:
                    ref = fn()
                    if ref:
                        return ref
                except Exception:
                    pass
        return None

    @cached
    def getText(self):
        ref = self._reference()
        if not ref:
            return ""
        try:
            path = ref.getPath() or ""
        except Exception:
            path = ""
        if not path:
            return ""
        clean = path.rstrip("/")
        if self.mode == "filename":
            return os.path.basename(clean)
        if self.mode in ("directory", "dir", "path"):
            return os.path.dirname(clean)
        return path

    text = property(getText)
