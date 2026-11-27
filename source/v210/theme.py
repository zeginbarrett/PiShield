"""Only declarative, bounded theme settings. Never evaluate CSS or code from the model."""
import json, os, pathlib, tempfile
DIR=pathlib.Path('/var/lib/pishield-theme')
DEFAULT={'palette':'green','density':'normal','corners':'rounded','text':'normal','columns':'normal'}
OPTIONS={'palette':('green','blue','yellow','purple','red','cyan','gray'),'density':('compact','normal','comfortable'),'corners':('square','rounded','soft'),'text':('normal','large'),'columns':('normal','wide')}
def validate(value):
    if not isinstance(value,dict) or set(value)!=set(OPTIONS) or any(not isinstance(value[k],str) or value[k] not in opts for k,opts in OPTIONS.items()):raise ValueError('Invalid design settings')
    return dict(value)
def current():
    try:
        with (DIR/'theme.json').open('rb') as f:raw=f.read(4097)
        if len(raw)>4096:raise ValueError()
        return validate(json.loads(raw))
    except (OSError,ValueError):return DEFAULT.copy()
def save(value):
    value=validate(value);fd,tmp=tempfile.mkstemp(dir=DIR)
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f);f.flush();os.fsync(f.fileno())
        os.chmod(tmp,0o640);os.replace(tmp,DIR/'theme.json')
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
