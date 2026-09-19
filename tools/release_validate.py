#!/usr/bin/env python3
import base64,collections,glob,hashlib,io,os,re,shutil,subprocess,sys,tarfile,tempfile,xml.etree.ElementTree as ET
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
SMART=os.path.join(ROOT,'cineview-smart-install.sh')
def fail(x): print('FAIL:',x); raise SystemExit(1)
def checkxml(root,label):
    bad=[]; dup=[]
    for p in glob.glob(root+'/**/*.xml',recursive=True):
        try:r=ET.parse(p).getroot()
        except Exception as e:bad.append((p,str(e)));continue
        ns=[x.get('name') for x in r.findall('.//screen') if x.get('name')]
        ds=[n for n,c in collections.Counter(ns).items() if c>1]
        if ds:dup.append((p,ds))
    print('%s bad=%d dup=%d'%(label,len(bad),len(dup)))
    if bad or dup: fail('%s XML'%label)
def digest(root):
    h=hashlib.sha256()
    for p in sorted(x for x in glob.glob(root+'/**',recursive=True) if os.path.isfile(x) and '__pycache__' not in x):
        h.update(os.path.relpath(p,root).encode()); h.update(open(p,'rb').read())
    return h.hexdigest()
lines=open(SMART,'rb').read().splitlines()
idx=next(i for i,x in enumerate(lines) if x.strip()==b'__CINEVIEW_PAYLOAD_BELOW__')
blob=base64.b64decode(b''.join(lines[idx+1:]))
tmp=tempfile.mkdtemp(prefix='cv-release-')
try:
    with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as tf: tf.extractall(tmp)
    skin=tmp+'/usr/share/enigma2/CineView_FHD'
    plug=tmp+'/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl'
    checkxml(skin,'EXTRACTED')
    if "VERSION='2.1.0'" not in open(plug+'/plugin.py',errors='ignore').read(): fail('version')
    if os.path.exists(plug+'/openatv_v5.py'): fail('legacy openatv_v5')
    rc=subprocess.call([sys.executable,plug+'/openatv_compat.py',skin])
    if rc!=0: fail('adapter first rc='+str(rc))
    checkxml(skin,'ADAPTER1')
    a=digest(tmp)
    rc=subprocess.call([sys.executable,plug+'/openatv_compat.py',skin])
    if rc not in (0,3): fail('adapter second rc='+str(rc))
    checkxml(skin,'ADAPTER2')
    if a!=digest(tmp): fail('adapter not idempotent')
    main=open(skin+'/skin.xml',errors='ignore').read()
    for n in ('PluginBrowser','PluginBrowserList','PluginBrowserGrid','QuickMenu'):
        m=re.search(r'<screen\b(?=[^>]*\bname=["\']%s["\'])[^>]*>'%n,main)
        if not m or 'size="1920,1080"' not in m.group(0): fail(n+' not FullHD')
    for tok in ('IsSDAndWidescreen','IsSDAndNotWidescreen','IsVideoAVC','IsVideoHEVC','IsVideoMPEG2'):
        if '<convert type="ServiceInfo">%s</convert>'%tok in main: fail('legacy '+tok)
    py=[p for p in glob.glob(tmp+'/usr/lib/enigma2/python/**/*.py',recursive=True) if 'CineView' in os.path.basename(p) or '/CineViewControl/' in p]
    for p in py: subprocess.check_call([sys.executable,'-m','py_compile',p])
    print('PYTHON=%d OK'%len(py))
    print('PAYLOAD_SHA256='+hashlib.sha256(blob).hexdigest())
    print('RELEASE_VALIDATE_OK')
finally: shutil.rmtree(tmp,ignore_errors=True)
