# Receiver temperature "CPU: --°C" - fix (CineView MLA 1.0.2), 2026-10-09

**Receiver:** Octagon SF8008 4K Supreme (machinebuild sf8008, chipset HiSilicon Hi3798MV200), OpenATV 7.6.0
(build 20260821), Python 3.13.12, skin CineView_FHD_MLA 1.0.1~openatv.py313.

**Root cause:** the converter behind the InfoBar / Second InfoBar / Event View label (golden `CineViewCPUTemp`,
built as `CineViewMLACPUTemp`) read only `/sys/class/thermal/thermal_zone0/temp`, `/proc/stb/sensors/temp0/value`
and `/proc/stb/fp/temp_sensor`. None exists on this receiver; its driver reports the temperature as
`Tsensor: temperature = 48 degree` in `/proc/hisi/msp/pm_cpu`. The converter returned nothing -> `CPU: --°C`
(before_infobar_cpu_dashes.jpg).

**Fix:** `tools/mla/patches/cputemp.py` (swapped in by `build.py`): golden paths first (unchanged reading where they
worked), then other thermal zones, `/proc/stb/sensors/temp/value`, `/proc/stb/fp/temp_sensor_avs`, HiSilicon
`/proc/hisi/msp/pm_cpu|pm_temp`; every source probed by existence; plausible values only; `CPU: N/A` when no valid
reading. Same label format, position, size and 5 s poll.

**Packages:** 1.0.2 = each 1.0.1 package with only this module (+ version.json, control version) changed - all three
images and all Python lines; Smart Installer 1.3.2 installs 1.0.2, `ROLLBACK=1` returns to 1.0.1.

**Device test (Octagon):** 1.0.2~openatv.py313 installed through the installer; GUI restarted (no recording running);
InfoBar 45°C = sensor 45 (3 samples), Second InfoBar 46°C = sensor 46, Event View 45°C = sensor 45; Enigma2 debug
log: 0 Tracebacks, 0 crash logs; temporary debug-log settings removed afterwards (settings = backup).
Backup on the receiver: /home/root/cineview-backup-20261009-cputemp/.
