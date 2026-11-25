from pathlib import Path
import os,re,shutil,tempfile,stat
base=Path(__file__).resolve().parent;root=Path('/var/www/html/admin');backs=Path('/var/backups/pishield')
if os.geteuid()!=0:root=Path(os.environ.get('PS120_TEST_WEBROOT',str(root)));backs=Path(os.environ.get('PS120_TEST_BACKUPS',str(backs)))
page=root/'pishield-guard.lp';head=root/'scripts/lua/header.lp';js=root/'scripts/js/pishield-v100.js'
for p in (page,head,js):
    if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise SystemExit('Missing or unsafe prerequisite: '+str(p))
s=page.read_text();h=head.read_text();j=js.read_text();start='<!-- PISHIELD PROACTIVE V120 -->';end='<!-- PISHIELD PROACTIVE V120 END -->';anchor='<div class="box box-primary"><div class="box-header with-border"><h3 class="box-title">DNS warning signs</h3>'
if s.count(start)!=s.count(end) or s.count(start)>1:raise SystemExit('Unexpected proactive markup')
if start in s:s=s[:s.index(start)]+s[s.index(end)+len(end):].lstrip('\n')
if s.count(anchor)!=1:raise SystemExit('Unexpected host security layout')
s=s.replace(anchor,(base/'panel.html').read_text()+anchor,1)
if not re.search(r'PISHIELD / v1\.(?:1|2)\b',j):raise SystemExit('PiShield 1.1 dashboard required')
j=re.sub(r'PISHIELD / v1\.(?:1|2)\b','PISHIELD / v1.2',j)
if not re.search(r'pishield-v100\.js\?v=(110|120)\b',h):raise SystemExit('Unexpected header version')
h=re.sub(r'pishield-v100\.js\?v=(110|120)\b','pishield-v100.js?v=120',h)
changes={page:s.encode(),head:h.encode(),js:j.encode(),root/'pishield-proactive-api.lp':(base/'proactive.lp').read_bytes(),root/'style/pishield-proactive.css':(base/'style.css').read_bytes(),root/'scripts/js/pishield-proactive.js':(base/'ui.js').read_bytes()}
for p in changes:
    if p.is_symlink() or (p.exists() and not p.is_file()) or not p.resolve().is_relative_to(root.resolve()):raise SystemExit('Unsafe destination: '+str(p))
changes={p:b for p,b in changes.items() if not p.exists() or p.read_bytes()!=b}
if not changes:print('Web files already current');raise SystemExit(0)
backs.mkdir(parents=True,exist_ok=True);backup=Path(tempfile.mkdtemp(prefix='proactive-v120-',dir=backs));backup.chmod(0o700)
def atomic(p,b,mode):
    fd,t=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
        os.chmod(t,mode);os.replace(t,p)
    finally:
        if os.path.exists(t):os.unlink(t)
old={p:(p.read_bytes(),stat.S_IMODE(p.stat().st_mode)) if p.exists() else None for p in changes}
for p,m in old.items():
    if m is not None:
        b=backup/p.relative_to(root);b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,b)
written=[]
try:
    for p,b in changes.items():atomic(p,b,old[p][1] if old[p] else 0o644);written.append(p)
except BaseException:
    for p in reversed(written):
        if old[p]:atomic(p,*old[p])
        else:p.unlink(missing_ok=True)
    raise
print('Web backup:',backup)
