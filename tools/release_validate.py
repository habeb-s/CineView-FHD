#!/usr/bin/env python3
import base64, collections, glob, hashlib, io, os, re, shutil, subprocess, sys, tarfile, tempfile, xml.etree.ElementTree as ET

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
SMART=os.path.join(ROOT,'cineview-smart-install.sh')
PARITY=os.path.join(ROOT,'tools','validate_openbh_atv_parity.py')

def fail(x):
    print('FAIL:',x)
    raise SystemExit(1)

def checkxml(root,label):
    bad=[]; dup=[]
    for p in glob.glob(root+'/**/*.xml',recursive=True):
        try:
            r=ET.parse(p).getroot()
        except Exception as e:
            bad.append((p,str(e))); continue
        ns=[x.get('name') for x in r.findall('.//screen') if x.get('name')]
        ds=[n for n,c in collections.Counter(ns).items() if c>1]
        if ds: dup.append((p,ds))
    print('%s bad=%d dup=%d'%(label,len(bad),len(dup)))
    if bad or dup: fail('%s XML'%label)

def digest(root):
    h=hashlib.sha256()
    for p in sorted(x for x in glob.glob(root+'/**',recursive=True) if os.path.isfile(x) and '__pycache__' not in x):
        h.update(os.path.relpath(p,root).encode())
        h.update(open(p,'rb').read())
    return h.hexdigest()

def apply_twice(base, label, adapter_name):
    stage=tempfile.mkdtemp(prefix='cv-%s-'%label.lower())
    shutil.copytree(base,stage,dirs_exist_ok=True)
    skin=stage+'/usr/share/enigma2/CineView_FHD'
    plug=stage+'/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl'
    adapter=plug+'/'+adapter_name
    rc=subprocess.call([sys.executable,adapter,skin])
    if rc!=0: fail('%s adapter first rc=%s'%(label,rc))
    checkxml(skin,label+'-ADAPTER1')
    a=digest(stage)
    rc=subprocess.call([sys.executable,adapter,skin])
    if rc not in (0,3): fail('%s adapter second rc=%s'%(label,rc))
    checkxml(skin,label+'-ADAPTER2')
    if a!=digest(stage): fail('%s adapter not idempotent'%label)
    return stage

def one_screen(path,name):
    r=ET.parse(path).getroot()
    xs=[x for x in r.iter('screen') if x.get('name')==name]
    if len(xs)!=1: fail('%s count=%d'%(name,len(xs)))
    return xs[0]

lines=open(SMART,'rb').read().splitlines()
idx=next(i for i,x in enumerate(lines) if x.strip()==b'__CINEVIEW_PAYLOAD_BELOW__')
blob=base64.b64decode(b''.join(lines[idx+1:]))
base=tempfile.mkdtemp(prefix='cv-release-base-')
atv=bh=None
try:
    with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as tf:
        tf.extractall(base)
    skin=base+'/usr/share/enigma2/CineView_FHD'
    plug=base+'/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl'
    checkxml(skin,'EXTRACTED')

    ptxt=open(plug+'/plugin.py',errors='ignore').read()
    vm=re.search(r'\bVERSION\s*=\s*["\x27](\d+(?:\.\d+)+)["\x27]',ptxt)
    if not vm:
        fail('plugin version marker')
    print('PLUGIN_VERSION='+vm.group(1))

    for required in ('openatv_compat.py','openbh_compat.py'):
        if not os.path.isfile(plug+'/'+required): fail('missing '+required)
    smart_text=open(SMART,errors='ignore').read()
    if 'openbh_compat.py' not in smart_text or '*openbh*|*openblackhole*)' not in smart_text:
        fail('OpenBH activation hook missing from smart installer')

    py=[p for p in glob.glob(base+'/usr/lib/enigma2/python/**/*.py',recursive=True)
        if 'CineView' in os.path.basename(p) or '/CineViewControl/' in p]
    for p in py:
        subprocess.check_call([sys.executable,'-m','py_compile',p])
    print('PYTHON=%d OK'%len(py))

    atv=apply_twice(base,'OPENATV','openatv_compat.py')
    bh=apply_twice(base,'OPENBH','openbh_compat.py')

    atv_skin=atv+'/usr/share/enigma2/CineView_FHD'
    bh_skin=bh+'/usr/share/enigma2/CineView_FHD'

    subprocess.check_call([
        sys.executable, PARITY,
        '--skin-dir', skin,
        '--openatv-adapter', plug+'/openatv_compat.py',
        '--openbh-adapter', plug+'/openbh_compat.py',
        '--strict',
    ])
    print('PARITY_STRICT_OK')

    # Public full-screen layouts approved on OpenATV and ported to OpenBH.
    for root,label in ((atv_skin,'OPENATV'),(bh_skin,'OPENBH')):
        main=root+'/skin.xml'
        for n in ('PluginBrowser','PluginBrowserList','PluginBrowserGrid','QuickMenu'):
            x=one_screen(main,n)
            if x.get('position')!='0,0' or x.get('size')!='1920,1080':
                fail('%s %s not FullHD'%(label,n))

    # OpenBH-only panels must not regress to their old small native-dialog sizes.
    bhmain=bh_skin+'/skin.xml'
    for n in ('DeliteGreenPanel','DeliteBluePanel','DeliteSetupFp','BhSetupGreen'):
        x=one_screen(bhmain,n)
        if x.get('size')!='1820,880':
            fail('OPENBH %s not CineView-size'%n)

    for root,label in ((atv_skin,'OPENATV'),(bh_skin,'OPENBH')):
        for p in glob.glob(root+'/skin*.xml'):
            txt=open(p,errors='ignore').read()
            if 'render="PosterX"' in txt or "render='PosterX'" in txt:
                fail('%s legacy PosterX in %s'%(label,os.path.basename(p)))

    print('PAYLOAD_SHA256='+hashlib.sha256(blob).hexdigest())
    print('RELEASE_VALIDATE_OK')
finally:
    for p in (atv,bh,base):
        if p: shutil.rmtree(p,ignore_errors=True)
