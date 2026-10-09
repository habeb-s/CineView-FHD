# -*- coding: utf-8 -*-
# by digiteng...07.2021,
# 08.2021(stb lang support),
# 09.2021 mini fixes
# © Provided that digiteng rights are protected, all or part of the code can be used, modified...
# russian and py3 support by sunriser...
# downloading in the background while zaping...
# by beber...03.2022,
# 03.2022 specific for EMC plugin ...
#
# for emc plugin,
# <widget source="Service" render="LukaPosterXEMC" position="100,100" size="185,278" />

from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, eTimer, loadJPG, eEPGCache
from ServiceReference import ServiceReference
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.CurrentService import CurrentService
from Components.Sources.EventInfo import EventInfo
from Components.Sources.Event import Event
from Components.Renderer.LukaPosterXDownloadThread import LukaPosterXDownloadThread
from six import text_type

import os
import sys
import re
import time
import socket
from re import search, sub, I, S, escape

PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True
    import queue
    import html
    html_parser = html
    from _thread import start_new_thread
    from urllib.error import HTTPError, URLError
    from urllib.request import urlopen
    from urllib.parse import quote_plus
else:
    import Queue
    from thread import start_new_thread
    from urllib2 import HTTPError, URLError
    from urllib2 import urlopen
    from urllib import quote_plus
    from HTMLParser import HTMLParser
    html_parser = HTMLParser()


try:
    from urllib import unquote, quote
except ImportError:
    from urllib.parse import unquote, quote


epgcache = eEPGCache.getInstance()
try:
    from Components.config import config
    lng = config.osd.language.value
except:
    lng = None
    pass


# def isMountedInRW(path):
    # testfile = path + '/tmp-rw-test'
    # os.system('touch ' + testfile)
    # if os.path.exists(testfile):
        # os.system('rm -f ' + testfile)
        # return True
    # return False


def isMountedInRW(mount_point):
    with open("/proc/mounts", "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) > 1 and parts[1] == mount_point:
                return True
    return False


# Share the exact same persistent CineView poster cache used by InfoBar/EPG.
try:
    from Components.Renderer.CineViewPosterX import CACHE_ROOT as path_folder
except Exception:
    path_folder = "/tmp/CINEVIEW/poster"
if not os.path.exists(path_folder):
    os.makedirs(path_folder)


if PY3:
    pdbemc = queue.LifoQueue()
else:
    pdbemc = Queue.LifoQueue()


def quoteEventName(eventName):
    try:
        text = eventName.decode('utf8').replace(u'\x86', u'').replace(u'\x87', u'').encode('utf8')
    except:
        text = eventName
    return quote_plus(text, safe="+")


REGEX = re.compile(
    r'[\(\[].*?[\)\]]|'                    # Parentesi tonde o quadre
    r':?\s?odc\.\d+|'                      # odc. con o senza numero prima
    r'\d+\s?:?\s?odc\.\d+|'                # numero con odc.
    r'[:!]|'                               # due punti o punto esclamativo
    r'\s-\s.*|'                            # trattino con testo successivo
    r',|'                                  # virgola
    r'/.*|'                                # tutto dopo uno slash
    r'\|\s?\d+\+|'                         # | seguito da numero e +
    r'\d+\+|'                              # numero seguito da +
    r'\s\*\d{4}\Z|'                        # * seguito da un anno a 4 cifre
    r'[\(\[\|].*?[\)\]\|]|'                # Parentesi tonde, quadre o pipe
    r'(?:\"[\.|\,]?\s.*|\"|'               # Testo tra virgolette
    r'\.\s.+)|'                            # Punto seguito da testo
    r'Премьера\.\s|'                       # Specifico per il russo
    r'[хмтдХМТД]/[фс]\s|'                  # Pattern per il russo con /ф o /с
    r'\s[сС](?:езон|ерия|-н|-я)\s.*|'      # Stagione o episodio in russo
    r'\s\d{1,3}\s[чсЧС]\.?\s.*|'           # numero di parte/episodio in russo
    r'\.\s\d{1,3}\s[чсЧС]\.?\s.*|'         # numero di parte/episodio in russo con punto
    r'\s[чсЧС]\.?\s\d{1,3}.*|'             # Parte/Episodio in russo
    r'\d{1,3}-(?:я|й)\s?с-н.*',            # Finale con numero e suffisso russo
    re.DOTALL)


def intCheck():
    try:
        response = urlopen("http://google.com", None, 5)
        response.close()
    except HTTPError:
        return False
    except URLError:
        return False
    except socket.timeout:
        return False
    return True


def remove_accents(string):
    if not isinstance(string, text_type):
        string = text_type(string, 'utf-8')
    string = sub(u"[àáâãäå]", 'a', string)
    string = sub(u"[èéêë]", 'e', string)
    string = sub(u"[ìíîï]", 'i', string)
    string = sub(u"[òóôõö]", 'o', string)
    string = sub(u"[ùúûü]", 'u', string)
    string = sub(u"[ýÿ]", 'y', string)
    return string


def unicodify(s, encoding='utf-8', norm=None):
    if not isinstance(s, text_type):
        s = text_type(s, encoding)
    if norm:
        from unicodedata import normalize
        s = normalize(norm, s)
    return s


def str_encode(text, encoding="utf8"):
    if not PY3:
        if isinstance(text, text_type):
            return text.encode(encoding)
    return text


def cutName(eventName=""):
    if eventName:
        eventName = eventName.replace('"', '').replace('.', '').replace(' | ', '')  # .replace('Х/Ф', '').replace('М/Ф', '').replace('Х/ф', '')
        eventName = eventName.replace('(18+)', '').replace('18+', '').replace('(16+)', '').replace('16+', '').replace('(12+)', '')
        eventName = eventName.replace('12+', '').replace('(7+)', '').replace('7+', '').replace('(6+)', '').replace('6+', '')
        eventName = eventName.replace('(0+)', '').replace('0+', '').replace('+', '')
        eventName = eventName.replace('المسلسل العربي', '')
        eventName = eventName.replace('مسلسل', '')
        eventName = eventName.replace('برنامج', '')
        eventName = eventName.replace('فيلم وثائقى', '')
        eventName = eventName.replace('حفل', '')
        return eventName
    return ""


def getCleanTitle(eventitle=""):
    # save_name = sub('\\(\d+\)$', '', eventitle)
    # save_name = sub('\\(\d+\/\d+\)$', '', save_name)  # remove episode-number " (xx/xx)" at the end
    # # save_name = sub('\ |\?|\.|\,|\!|\/|\;|\:|\@|\&|\'|\-|\"|\%|\(|\)|\[|\]\#|\+', '', save_name)
    save_name = eventitle.replace(' ^`^s', '').replace(' ^`^y', '')
    return save_name


def dataenc(data):
    if PY3:
        data = data.decode("utf-8")
    else:
        data = data.encode("utf-8")
    return data


def sanitize_filename(filename):
    # Replace spaces with underscores and remove invalid characters (like ':')
    sanitized = sub(r'[^\w\s-]', '', filename)  # Remove invalid characters
    # sanitized = sanitized.replace(' ', '_')      # Replace spaces with underscores
    # sanitized = sanitized.replace('-', '_')      # Replace dashes with underscores
    return sanitized.strip()


def convtext(text=''):
    try:
        if text is None:
            print('return None original text: ' + str(type(text)))
            return
        if text == '':
            print('text is an empty string')
        else:
            print('original text:' + text)
            text = text.lower()
            print('lowercased text:' + text)
            text = text.lstrip()

            # text = cutName(text)
            # text = getCleanTitle(text)

            if text.endswith("the"):
                text = "the " + text[:-4]

            # Modifiche personalizzate
            if 'giochi olimpici parigi' in text:
                text = 'olimpiadi di parigi'
            if 'bruno barbieri' in text:
                text = text.replace('bruno barbieri', 'brunobarbierix')
            if "anni '60" in text:
                text = "anni 60"
            if 'tg regione' in text:
                text = 'tg3'
            if 'studio aperto' in text:
                text = 'studio aperto'
            if 'josephine ange gardien' in text:
                text = 'josephine ange gardien'
            if 'elementary' in text:
                text = 'elementary'
            if 'squadra speciale cobra 11' in text:
                text = 'squadra speciale cobra 11'
            if 'criminal minds' in text:
                text = 'criminal minds'
            if 'i delitti del barlume' in text:
                text = 'i delitti del barlume'
            if 'senza traccia' in text:
                text = 'senza traccia'
            if 'hudson e rex' in text:
                text = 'hudson e rex'
            if 'ben-hur' in text:
                text = 'ben-hur'
            if 'alessandro borghese - 4 ristoranti' in text:
                text = 'alessandroborgheseristoranti'
            if 'alessandro borghese: 4 ristoranti' in text:
                text = 'alessandroborgheseristoranti'
            if 'amici di maria' in text:
                text = 'amicidimariadefilippi'

            cutlist = ['x264', '720p', '1080p', '1080i', 'pal', 'german', 'english', 'ws', 'dvdrip', 'unrated',
                       'retail', 'web-dl', 'dl', 'ld', 'mic', 'md', 'dvdr', 'bdrip', 'bluray', 'dts', 'uncut', 'anime',
                       'ac3md', 'ac3', 'ac3d', 'ts', 'dvdscr', 'complete', 'internal', 'dtsd', 'xvid', 'divx', 'dubbed',
                       'line.dubbed', 'dd51', 'dvdr9', 'dvdr5', 'h264', 'avc', 'webhdtvrip', 'webhdrip', 'webrip',
                       'webhdtv', 'webhd', 'hdtvrip', 'hdrip', 'hdtv', 'ituneshd', 'repack', 'sync', '1^tv', '1^ tv',
                       '1^ visione rai', '1^ visione', ' - prima tv', ' - primatv', 'prima visione',
                       'film -', 'first screening',  # 'de filippi',
                       'live:', 'new:', 'film:', 'première diffusion', 'nouveau:', 'en direct:',
                       'premiere:', 'estreno:', 'nueva emisión:', 'en vivo:'
                       ]
            for word in cutlist:
                text = text.replace(word, '')
            text = ' '.join(text.split())
            print(text)

            text = cutName(text)
            text = getCleanTitle(text)

            text = text.partition("-")[0]  # Mantieni solo il testo prima del primo "-"

            # Pulizia finale
            text = text.replace('.', ' ').replace('-', ' ').replace('_', ' ').replace('+', '').replace('1/2', 'mezzo')

            # Rimozione pattern specifici
            if search(r'[Ss][0-9]+[Ee][0-9]+', text):
                text = sub(r'[Ss][0-9]+[Ee][0-9]+.*[a-zA-Z0-9_]+', '', text, flags=S | I)
            text = sub(r'\(.*\)', '', text).rstrip()
            text = text.partition("(")[0]
            text = sub(r"\\s\d+", "", text)
            text = text.partition(":")[0]
            text = sub(r'(odc.\s\d+)+.*?FIN', '', text)
            text = sub(r'(odc.\d+)+.*?FIN', '', text)
            text = sub(r'(\d+)+.*?FIN', '', text)
            text = sub('FIN', '', text)
            # remove episode number in arabic series
            text = sub(r' +ح', '', text)
            # remove season number in arabic series
            text = sub(r' +ج', '', text)
            # remove season number in arabic series
            text = sub(r' +م', '', text)

            # # Rimuovi accenti e normalizza
            text = remove_accents(text)
            print('remove_accents text: ' + text)

            # Forzature finali
            text = text.replace('XXXXXX', '60')
            text = text.replace('brunobarbierix', 'bruno barbieri - 4 hotel')
            text = text.replace('alessandroborgheseristoranti', 'alessandro borghese - 4 ristoranti')
            text = text.replace('il ritorno di colombo', 'colombo')
            text = text.replace('amicidimariadefilippi', 'amici di maria')
            # text = sanitize_filename(text)
            # print('sanitize_filename text: ' + text)
            return text.capitalize()
    except Exception as e:
        print('convtext error: ' + str(e))
        pass


class PosterDBEMC(LukaPosterXDownloadThread):
    def __init__(self):
        LukaPosterXDownloadThread.__init__(self)
        self.logdbg = None
        self.pstcanal = None

    def run(self):
        # self.logDB("[QUEUE] : Initialized")
        while True:
            canal = pdbemc.get()
            # self.logDB("[QUEUE] : {} : {}-{} ({})".format(canal[0], canal[1], canal[2], canal[5]))
            self.pstcanal = convtext(canal[5])
            if self.pstcanal != 'None' or self.pstcanal is not None:
                dwn_poster = path_folder + '/' + self.pstcanal + ".jpg"
            else:
                print('none type xxxxxxxxxx- posterx')
                return
            if os.path.exists(dwn_poster):
                os.utime(dwn_poster, (time.time(), time.time()))
            '''
            # if lng == "fr":
                # if not os.path.exists(dwn_poster):
                    # val, log = self.search_molotov_google(dwn_poster, canal[5], canal[4], canal[3], canal[0])
                    # # self.logDB(log)
                # if not os.path.exists(dwn_poster):
                    # val, log = self.search_programmetv_google(dwn_poster, canal[5], canal[4], canal[3], canal[0])
                    # # self.logDB(log)
            '''
            if not os.path.exists(dwn_poster):
                val, log = self.search_tmdb(dwn_poster, self.pstcanal, canal[4], canal[3])
                # self.logDB(log)
            if not os.path.exists(dwn_poster):
                val, log = self.search_tvdb(dwn_poster, self.pstcanal, canal[4], canal[3])
                # self.logDB(log)
            if not os.path.exists(dwn_poster):
                val, log = self.search_fanart(dwn_poster, self.pstcanal, canal[4], canal[3])
                # self.logDB(log)
            if not os.path.exists(dwn_poster):
                val, log = self.search_imdb(dwn_poster, self.pstcanal, canal[4], canal[3])
                # self.logDB(log)
            if not os.path.exists(dwn_poster):
                val, log = self.search_google(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                # self.logDB(log)
            pdbemc.task_done()

    def logDB(self, logmsg):
        import traceback
        try:
            with open("/tmp/LukaPosterXEMC.log", "a") as w:
                w.write("%s\n" % logmsg)
        except Exception as e:
            print('logDB error:', str(e))
            traceback.print_exc()


threadDBemc = PosterDBEMC()
threadDBemc.start()


class LukaPosterXEMC(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        try:
            self.online = intCheck()
        except:
            self.online = False

        self.canal = [None, None, None, None, None, None]
        self.poster_file = None
        self.media_path = None
        self.title = None
        self.generation = 0

        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.showPoster)
        except:
            self.timer.callback.append(self.showPoster)

    def applySkin(self, desktop, parent):
        attribs = []
        for (attrib, value,) in self.skinAttributes:
            attribs.append((attrib, value))
        self.skinAttributes = attribs
        return Renderer.applySkin(self, desktop, parent)

    def _hide(self):
        try:
            if self.instance:
                self.instance.hide()
        except:
            pass

    def _normalise(self, text):
        if not text:
            return ""
        try:
            text = str(text).lower()
        except:
            return ""

        text = text.replace("_", " ").replace(".", " ")
        text = re.sub(r'\[[^\]]*\]', ' ', text)
        text = re.sub(r'\([^)]*\)', ' ', text)
        text = text.split(" | ", 1)[0]

        stop = re.search(
            r'\b(?:s\d{1,2}e\d{1,3}|2160p|1080p|720p|480p|'
            r'bluray|blu ray|web[- ]?dl|webrip|uhd|remux|hdr|dv|'
            r'x264|x265|h264|h265|hevc|10bit|truehd|atmos|aac|dts|fhd)\b',
            text,
            flags=re.I
        )
        if stop:
            text = text[:stop.start()]

        year = re.search(r'\b(?:19|20)\d{2}\b', text)
        if year:
            text = text[:year.end()]

        text = re.sub(r'[-]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip(' -_')

    def _referenceable(self, title):
        if not title:
            return False
        t = title.strip()
        if len(t) < 3:
            return False
        if sum(1 for c in t if c.isalpha()) < 3:
            return False
        bad = {"video","movie","recording","record","clip","stream","unknown","untitled","test","media","sample","instant record","normal recording"}
        if t.lower() in bad:
            return False
        return True

    def _key(self, text):
        if not text:
            return ""
        return ''.join(c.lower() for c in str(text) if c.isalnum())

    def _title_from_path(self, path):
        if not path:
            return ""
        base = os.path.basename(path)
        base = os.path.splitext(base)[0]
        base = re.sub(r'^\d{8}\s+\d{4}\s+-\s+[^-]+-\s+', '', base)
        return self._normalise(base)

    def _sidecar(self, media):
        if not media:
            return None
        root = os.path.splitext(media)[0]
        for ext in (".jpg", ".jpeg"):
            fn = root + ext
            if os.path.exists(fn):
                return fn
        return None

    def _find_downloaded(self, title):
        if not title:
            return None
        wanted = self._key(title)
        if len(wanted) < 3:
            return None
        try:
            files = os.listdir(path_folder)
        except:
            return None

        best = None
        best_mtime = 0

        for fn in files:
            if fn.startswith("__frame__"):
                continue
            if not fn.lower().endswith((".jpg", ".jpeg")):
                continue
            stem = os.path.splitext(fn)[0]
            key = self._key(stem)
            if not key:
                continue

            exact = (key == wanted)
            near = (len(wanted) >= 6 and (wanted in key or key in wanted))

            if exact or near:
                full = os.path.join(path_folder, fn)

                # Internet posters must be portrait.  This rejects old
                # landscape video-frame fallbacks that used the same filename.
                try:
                    from PIL import Image
                    with Image.open(full) as im:
                        w, h = im.size
                    if not w or not h or h < int(w * 1.10):
                        continue
                except:
                    continue

                try:
                    mt = os.path.getmtime(full)
                except:
                    mt = 0
                if exact:
                    return full
                if mt >= best_mtime:
                    best = full
                    best_mtime = mt
        return best

    def _internet_poster_direct(self, title):
        """Fetch a real portrait poster directly from IMDb suggestion data."""
        if not title:
            return None
        try:
            import requests
            from io import BytesIO
            from PIL import Image

            q = str(title).strip()
            api = "https://v3.sg.media-imdb.com/suggestion/x/%s.json" % quote_plus(q)
            data = requests.get(api, headers={"User-Agent": "Mozilla/5.0"}, timeout=12).json()
            rows = data.get("d") or []

            wanted_year = None
            ym = re.search(r'\b((?:19|20)\d{2})\b', q)
            if ym:
                wanted_year = ym.group(1)

            base = re.sub(r'\b(?:19|20)\d{2}\b', ' ', q)
            base = re.sub(r'[^a-z0-9]+', ' ', base.lower()).strip()

            ranked = []
            for row in rows[:12]:
                rid = str(row.get("id") or "")
                if not rid.startswith("tt"):
                    continue
                label = str(row.get("l") or "")
                image = (row.get("i") or {}).get("imageUrl")
                if not label or not image:
                    continue

                label_key = re.sub(r'[^a-z0-9]+', ' ', label.lower()).strip()
                year = str(row.get("y") or "")
                score = 0
                if label_key == base:
                    score += 100
                elif base and (base in label_key or label_key in base):
                    score += 70
                if wanted_year and year == wanted_year:
                    score += 40
                ranked.append((score, image, label, year))

            if not ranked:
                return None

            ranked.sort(key=lambda x: x[0], reverse=True)
            score, image_url, label, year = ranked[0]
            if score < 70:
                return None

            bounded = re.sub(r'\._V1_[^/]*?\.jpg(?:\?.*)?$', '._V1_FMjpg_UY900_.jpg', image_url)
            body = requests.get(bounded, headers={"User-Agent": "Mozilla/5.0"}, timeout=15).content
            if not body or len(body) < 1500:
                return None

            im = Image.open(BytesIO(body))
            im.load()
            if im.mode != "RGB":
                im = im.convert("RGB")
            im.thumbnail((600, 900), Image.Resampling.LANCZOS)

            # Poster must be portrait; reject backdrops/frames.
            if im.height < int(im.width * 1.10):
                return None

            os.makedirs(path_folder, exist_ok=True)
            target = os.path.join(path_folder, self._key(title) + ".jpg")
            im.save(target, "JPEG", quality=88, optimize=True)

            try:
                with open("/tmp/CineViewEMCPoster.log", "a") as w:
                    w.write("IMDB_DIRECT_OK: %s -> %s (%s)\n" % (title, label, year))
            except:
                pass
            return target
        except Exception as e:
            try:
                with open("/tmp/CineViewEMCPoster.log", "a") as w:
                    w.write("IMDB_DIRECT_FAIL: %s | %s\n" % (title, e))
            except:
                pass
            return None

    def _frame_target(self, title, media):
        stem = self._key(title) or self._key(os.path.basename(os.path.splitext(media)[0]))
        if not stem:
            stem = "emc_frame"
        return os.path.join(path_folder, "__frame__" + stem + ".jpg")

    def _extract_frame(self, media, out_file):
        import subprocess, shutil
        if not media or not os.path.exists(media):
            return None

        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg and os.path.exists("/usr/bin/ffmpeg"):
            ffmpeg = "/usr/bin/ffmpeg"
        if not ffmpeg and os.path.exists("/bin/ffmpeg"):
            ffmpeg = "/bin/ffmpeg"
        if not ffmpeg:
            return None

        os.makedirs(os.path.dirname(out_file), exist_ok=True)

        for ss in ("15", "8", "3"):
            try:
                cmd = [
                    ffmpeg, "-y",
                    "-ss", ss,
                    "-i", media,
                    "-frames:v", "1",
                    "-q:v", "3",
                    out_file
                ]
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate(timeout=20)
                if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
                    return out_file
            except:
                pass
        return None

    def _load(self, filename):
        if not filename or not os.path.exists(filename):
            self._hide()
            return False
        try:
            self.instance.setPixmap(loadJPG(filename))
            self.instance.setScale(1)
            self.instance.show()
            return True
        except:
            self._hide()
            return False

    def changed(self, what):
        self.generation += 1
        generation = self.generation
        self.poster_file = None
        self.media_path = None
        self.title = None
        self._hide()

        if what[0] == self.CHANGED_CLEAR:
            return

        path = ""
        event_name = ""
        ext_desc = ""
        short_desc = ""
        begin = None
        channel = None

        try:
            if isinstance(self.source, ServiceEvent):
                event = getattr(self.source, "event", None)
                service = getattr(self.source, "service", None)
                if event:
                    try: begin = event.getBeginTime()
                    except: pass
                    try: event_name = event.getEventName() or ""
                    except: pass
                    try: ext_desc = event.getExtendedDescription() or ""
                    except: pass
                    try: short_desc = event.getShortDescription() or ""
                    except: pass
                if service:
                    try: path = service.getPath() or ""
                    except: pass

            elif isinstance(self.source, CurrentService):
                try:
                    ref = self.source.getCurrentServiceReference()
                    if ref:
                        path = ref.getPath() or ""
                except:
                    pass
            else:
                return
        except:
            return

        title = self._normalise(event_name)
        if not self._referenceable(title):
            title = self._title_from_path(path)

        try:
            base = os.path.basename(os.path.splitext(path)[0])
            m = re.search(r'^\d{8}\s+\d{4}\s+-\s+(.+?)\s+-\s+(.+)$', base)
            if m:
                channel = m.group(1).strip()
                if not self._referenceable(title):
                    title = self._normalise(m.group(2))
        except:
            pass

        self.media_path = path
        self.title = title

        # 1) local sidecar next to media
        sidecar = self._sidecar(path)
        if sidecar:
            self.poster_file = sidecar
            self.timer.start(10, True)
            return

        # 2) previously downloaded internet poster
        downloaded = self._find_downloaded(title)
        if downloaded:
            self.poster_file = downloaded
            self.timer.start(10, True)
            return

        # 3) online poster fetch first
        if self._referenceable(title) and self.online:
            self.canal = [channel or "local", begin, title, ext_desc, short_desc, title]
            start_new_thread(self.waitPoster, (generation, title, path, begin, ext_desc, short_desc, channel))
            return

        # 4) only fallback to frame if not referenceable / offline
        start_new_thread(self._frame_fallback, (generation, title, path))
        return

    def waitPoster(self, generation, title, media, begin, ext_desc, short_desc, channel):
        # Primary provider: direct IMDb title/year match.
        direct = self._internet_poster_direct(title)
        if generation != self.generation:
            return
        if direct and os.path.exists(direct) and os.path.getsize(direct) > 1500:
            self.poster_file = direct
            try:
                self.timer.start(10, True)
            except:
                pass
            return

        # Secondary provider: CineView's proven EPG providers
        # (TVMaze -> IMDb -> iTunes).
        try:
            from Components.Renderer import CineViewPosterX as CVPoster
            epg_cached = CVPoster._poster_path(title)
            if not (os.path.exists(epg_cached) and os.path.getsize(epg_cached) > 1500):
                CVPoster._download(title)
            if generation != self.generation:
                return
            if os.path.exists(epg_cached) and os.path.getsize(epg_cached) > 1500:
                self.poster_file = epg_cached
                try:
                    self.timer.start(10, True)
                except:
                    pass
                try:
                    with open("/tmp/CineViewEMCPoster.log", "a") as w:
                        w.write("ONLINE_POSTER_OK: %s -> %s\n" % (title, epg_cached))
                except:
                    pass
                return
        except Exception as e:
            try:
                with open("/tmp/CineViewEMCPoster.log", "a") as w:
                    w.write("CINEVIEW_PROVIDER_FAIL: %s | %s\n" % (title, e))
            except:
                pass

        # Keep the legacy EMC providers as a secondary fallback.
        try:
            pdbemc.put([channel or "local", begin, title, ext_desc, short_desc, title])
        except:
            pass

        for _ in range(20):  # ~10 sec
            if generation != self.generation:
                return
            found = self._find_downloaded(title)
            if found:
                self.poster_file = found
                try:
                    self.timer.start(10, True)
                except:
                    pass
                return
            time.sleep(0.5)

        # If all internet providers fail, use a video frame.
        if generation != self.generation:
            return
        target = self._frame_target(title, media)
        made = self._extract_frame(media, target)
        if generation != self.generation:
            return
        if made and os.path.exists(made):
            self.poster_file = made
            try:
                self.timer.start(10, True)
            except:
                pass
        else:
            self._hide()

    def _frame_fallback(self, generation, title, media):
        time.sleep(0.2)
        if generation != self.generation:
            return
        target = self._frame_target(title, media)
        made = self._extract_frame(media, target)
        if generation != self.generation:
            return
        if made and os.path.exists(made):
            self.poster_file = made
            try:
                self.timer.start(10, True)
            except:
                pass
        else:
            self._hide()

    def showPoster(self):
        if self.poster_file and os.path.exists(self.poster_file):
            self._load(self.poster_file)
            return

        if self.title:
            downloaded = self._find_downloaded(self.title)
            if downloaded:
                self.poster_file = downloaded
                self._load(downloaded)
                return

        self._hide()

    def logPoster(self, logmsg):
        try:
            with open("/tmp/CineViewEMCPoster.log", "a") as w:
                w.write("%s\n" % logmsg)
        except:
            pass

