# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import os
import re

from enigma import eConsoleAppContainer, quitMainloop
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ProgressBar import ProgressBar

PLUGIN_VERSION = "2.3.4"
OWNER = "habeb-s/CineView-FHD"
BASE_RAW = "https://raw.githubusercontent.com/%s/main" % OWNER
MANIFEST_URL = BASE_RAW + "/update.json"
TMP_MANIFEST = "/tmp/cineview-update.json"
TMP_IPK = "/tmp/cineview-update.ipk"


def _version_tuple(value):
    nums = re.findall(r"\d+", value or "")
    return tuple([int(x) for x in nums[:4]])


def _image_key():
    try:
        data = open("/etc/image-version", "r").read().lower()
    except Exception:
        data = ""
    if "openatv" in data:
        return "openatv"
    if "openvix" in data:
        return "openvix"
    if "openbh" in data:
        return "openbh"
    return None


class CineViewUpdater(Screen):
    skin = """
    <screen name="CineViewUpdater" position="center,center" size="1180,560" title="CineView FHD Updater">
        <widget name="title" position="60,45" size="1060,55" font="Regular;38" halign="center" />
        <widget name="current" position="80,135" size="1020,45" font="Regular;30" />
        <widget name="status" position="80,215" size="1020,80" font="Regular;28" halign="center" valign="center" />
        <widget name="progress" position="120,330" size="940,34" />
        <widget name="percent" position="120,375" size="940,45" font="Regular;28" halign="center" />
        <eLabel position="80,485" size="28,28" backgroundColor="#0066cc" />
        <widget name="blue" position="120,474" size="500,48" font="Regular;28" />
        <eLabel position="770,485" size="28,28" backgroundColor="#aa0000" />
        <widget name="red" position="810,474" size="290,48" font="Regular;28" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self["title"] = Label("CineView FHD - Online Update")
        self["current"] = Label("Installed version: %s" % PLUGIN_VERSION)
        self["status"] = Label("Press BLUE to check for updates")
        self["progress"] = ProgressBar()
        self["progress"].setValue(0)
        self["percent"] = Label("0%")
        self["blue"] = Label("Check / Update")
        self["red"] = Label("Close")
        self.container = None
        self.remote = None
        self.busy = False

        self["actions"] = ActionMap(
            ["ColorActions", "OkCancelActions"],
            {
                "blue": self.checkUpdate,
                "cancel": self.close,
                "red": self.close,
            },
            -1,
        )

    def _run(self, cmd, done, capture=False):
        self.container = eConsoleAppContainer()
        if capture:
            try:
                self.container.dataAvail.append(self._data)
            except Exception:
                pass
        try:
            self.container.appClosed.append(done)
        except Exception:
            pass
        self.container.execute(cmd)

    def _data(self, data):
        try:
            if not isinstance(data, str):
                data = data.decode("utf-8", "ignore")
        except Exception:
            return
        matches = re.findall(r"(\d{1,3})%", data)
        if matches:
            value = min(100, int(matches[-1]))
            self["progress"].setValue(value)
            self["percent"].setText("%d%%" % value)

    def checkUpdate(self):
        if self.busy:
            return
        self.busy = True
        self["status"].setText("Checking for updates...")
        self["progress"].setValue(0)
        self["percent"].setText("0%")
        cmd = "rm -f %s; wget -q --no-check-certificate -O %s '%s'" % (
            TMP_MANIFEST, TMP_MANIFEST, MANIFEST_URL
        )
        self._run(cmd, self._manifestDone)

    def _manifestDone(self, retval):
        if retval != 0 or not os.path.exists(TMP_MANIFEST):
            self.busy = False
            self["status"].setText("Unable to check for updates")
            self.session.open(MessageBox, "Update check failed. Check internet connection.", MessageBox.TYPE_ERROR, timeout=6)
            return
        try:
            self.remote = json.load(open(TMP_MANIFEST, "r"))
            remote_version = str(self.remote.get("version", "0"))
        except Exception:
            self.busy = False
            self.session.open(MessageBox, "Invalid update information.", MessageBox.TYPE_ERROR, timeout=6)
            return

        if _version_tuple(remote_version) <= _version_tuple(PLUGIN_VERSION):
            self.busy = False
            self["status"].setText("No update available")
            self["progress"].setValue(100)
            self["percent"].setText("100%")
            self.session.open(MessageBox, "No update available.\nYou already have the latest CineView FHD version (%s)." % PLUGIN_VERSION, MessageBox.TYPE_INFO, timeout=6)
            return

        key = _image_key()
        package = (self.remote.get("packages") or {}).get(key or "")
        if not package:
            self.busy = False
            self.session.open(MessageBox, "This Enigma2 image is not supported by the updater.", MessageBox.TYPE_ERROR, timeout=7)
            return

        tag = package.get("tag")
        filename = package.get("file")
        if not tag or not filename:
            self.busy = False
            self.session.open(MessageBox, "Update package information is incomplete.", MessageBox.TYPE_ERROR, timeout=7)
            return

        self["status"].setText("New version %s found - downloading..." % remote_version)
        self["progress"].setValue(1)
        self["percent"].setText("1%")
        url = "https://github.com/%s/releases/download/%s/%s" % (OWNER, tag, filename)
        cmd = "rm -f %s; wget --no-check-certificate --progress=bar:force -O %s '%s' 2>&1" % (TMP_IPK, TMP_IPK, url)
        self._run(cmd, self._downloadDone, capture=True)

    def _downloadDone(self, retval):
        if retval != 0 or not os.path.exists(TMP_IPK) or os.path.getsize(TMP_IPK) < 1024:
            self.busy = False
            self["status"].setText("Download failed")
            self.session.open(MessageBox, "CineView FHD update download failed.", MessageBox.TYPE_ERROR, timeout=7)
            return
        self["progress"].setValue(100)
        self["percent"].setText("100%")
        self["status"].setText("Installing update...")
        cmd = "opkg install --force-reinstall '%s'" % TMP_IPK
        self._run(cmd, self._installDone)

    def _installDone(self, retval):
        self.busy = False
        try:
            os.remove(TMP_IPK)
        except Exception:
            pass
        if retval != 0:
            self["status"].setText("Installation failed")
            self.session.open(MessageBox, "CineView FHD update installation failed.", MessageBox.TYPE_ERROR, timeout=8)
            return
        remote_version = str((self.remote or {}).get("version", ""))
        self["status"].setText("Update installed successfully - restarting Enigma2")
        self.session.openWithCallback(
            self._restart,
            MessageBox,
            "CineView FHD %s installed successfully.\nEnigma2 will restart now." % remote_version,
            MessageBox.TYPE_INFO,
            timeout=4,
        )

    def _restart(self, *args):
        quitMainloop(3)


def main(session, **kwargs):
    session.open(CineViewUpdater)


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="CineView FHD Updater",
            description="Check and install CineView FHD updates",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon=None,
            fnc=main,
        ),
        PluginDescriptor(
            name="CineView FHD Updater",
            description="Check and install CineView FHD updates",
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,
            fnc=main,
        ),
    ]
