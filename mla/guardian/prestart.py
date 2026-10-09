# CineView MLA - start of the boot guardian from Python's start-up hook.
#
# Why: the images give Enigma2 add-ons ONE pre-start hook, the single file /usr/bin/enigma2_pre_start.sh that
# enigma2.sh runs before every start (OpenATV 7.6 / 8.0, OpenBH 5.6 / 6.0, OpenViX 6.9 - checked in each image's
# enigma2.sh).  Only one package can own a file, so CineView MLA no longer uses it: another add-on may own it,
# and CineView neither replaces nor edits nor disables it.
# How: site-packages/cineview_mla_guardian.pth (a standard Python "site" start-up file, the same mechanism as the
# images' own distutils-precedence.pth) runs this file only inside the enigma2 process, during Python
# initialisation (Py_Initialize in enigma2's python.cpp), i.e. before StartEnigma reads the settings and loads the
# skin - the moment the guardian needs.  Every other Python program returns at once in the .pth line.
# Never blocks or breaks the Enigma2 start: the guardian runs with a time limit and every error is only logged.
import os
import subprocess
import time

G = "/usr/share/enigma2/CineView_FHD_MLA/mla/guardian/guardian.sh"
if os.access(G, os.X_OK):
	env = dict(os.environ)
	env.pop("LD_PRELOAD", None)  # enigma2.sh preloads libopen for enigma2 itself; the guardian does not need it
	env.setdefault("PATH", "/usr/sbin:/usr/bin:/sbin:/bin")
	env["CVMLA_GUARDIAN_HOOK"] = "python"
	try:
		subprocess.run([G], env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=150, check=False)
	except Exception as e:  # noqa: BLE001 - nothing may stop Enigma2 from starting
		try:
			with open("/etc/enigma2/cineview_mla/history.log", "a") as f:
				f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + "start-up hook: guardian not completed: %s\n" % e)
		except OSError:
			pass
