# Harness: real OpenATV 8.0 config.py (commit 45414bc) + real CineViewControl.apply_timeout logic.
import sys, types, importlib.util
import os
ATV=os.environ.get('ATV80','/path/to/openatv-enigma2@45414bc')+'/lib/python'
def stub(name, **attrs):
    m=types.ModuleType(name); m.__dict__.update(attrs); sys.modules[name]=m; return m
stub('enigma', getPrevAsciiCode=lambda:0, eTimer=object, eEnv=types.SimpleNamespace(resolve=lambda s:s))
stub('Tools'); stub('Tools.Directories', SCOPE_CONFIG=0, fileAccess=lambda *a,**k:True, resolveFilename=lambda s,f='':'/tmp/'+f)
stub('Tools.NumericalTextInput', NumericalTextInput=object)
stub('Components'); stub('Components.Harddisk', harddiskmanager=types.SimpleNamespace())
spec=importlib.util.spec_from_file_location('Components.config', ATV+'/Components/config.py')
cfg=importlib.util.module_from_spec(spec); sys.modules['Components.config']=cfg
import builtins; builtins._=lambda s:s; builtins.ngettext=lambda a,b,n:a if n==1 else b
spec.loader.exec_module(cfg)
config=cfg.config
# Exact definitions from UsageConfig.py@45414bc lines 386-392
config.usage=cfg.ConfigSubsection()
config.usage.show_second_infobar=cfg.ConfigSelection(default="1",choices=[("0","Off"),("1","Event Info"),("2","2nd InfoBar INFO"),("3","2nd InfoBar ECM")])
# user's saved setting (snapshot settings-gui.txt): show_second_infobar=2
config.usage.show_second_infobar.value="2"
# CineViewControl choices/default (plugin.py ensure_config)
for secondtimeout in ['20','5','10','15','30','60','0']:
    config.usage.show_second_infobar.value="2"
    before=config.usage.show_second_infobar.value
    # apply_timeout(False) body, verbatim semantics:
    config.usage.show_second_infobar.value=secondtimeout
    print(f"secondtimeout={secondtimeout:>3}  show_second_infobar: {before} -> {config.usage.show_second_infobar.value}")
