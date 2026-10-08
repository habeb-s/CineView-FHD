# -*- coding: utf-8 -*-
"""CineView MLA - OpenViX adapter: the EPG transform of the OpenBH adapter, unchanged.  OpenViX 6.9.002
(OpenViX/enigma2 d3f089af4e) and OpenBH 5.6.008 (BlackHole/enigma2 52dedddc314a) have byte-identical
Screens/EpgSelectionBase.py, EpgSelectionGrid.py, EpgSelectionSingle.py, EpgSelectionMulti.py and the same
Components/EpgList*.py skin attributes, so one transform serves both (no second copy of the rules)."""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location("mla_transform_openbh_for_openvix",
	os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "openbh", "transform.py"))
_bh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bh)
for _name in dir(_bh):
	if not _name.startswith("__"):
		globals()[_name] = getattr(_bh, _name)
