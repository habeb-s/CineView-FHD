# Receiver helper (copied to /tmp/cvmla by the device scripts): set key=value lines in /etc/enigma2/settings while
# Enigma2 is STOPPED (atomic replace + fsync).  usage: python3 setcfg.py config.a.b=value [...]
import sys
p='/etc/enigma2/settings'; kv=dict(a.split('=',1) for a in sys.argv[1:])
lines=open(p).read().splitlines(); seen=set(); out=[]
for l in lines:
    k=l.split('=',1)[0]
    if k in kv: out.append(f'{k}={kv[k]}'); seen.add(k)
    else: out.append(l)
out+= [f'{k}={v}' for k,v in kv.items() if k not in seen]
open(p+'.tmp','w').write('\n'.join(out)+'\n')
import os; f=os.open(p+'.tmp',os.O_RDONLY); os.fsync(f); os.close(f); os.replace(p+'.tmp',p); print('set',kv)
