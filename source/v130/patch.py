from pathlib import Path
import os, re, shutil, stat, tempfile
base=Path(__file__).resolve().parent;root=Path('/var/www/html/admin');backs=Path('/var/backups/pishield')
if os.geteuid()!=0:root=Path(os.environ.get('PS130_TEST_WEBROOT',str(root)));backs=Path(os.environ.get('PS130_TEST_BACKUPS',str(backs)))
header=root/'scripts/lua/header.lp';sidebar=root/'scripts/lua/sidebar.lp';js=root/'scripts/js/pishield-v100.js'
for p in (header,sidebar,js):
    if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise SystemExit('Missing or unsafe prerequisite: '+str(p))
h=header.read_text();s=sidebar.read_text();j=js.read_text()
start='<!-- PISHIELD COMPACT V122 -->';end='<!-- PISHIELD COMPACT V122 END -->'
if h.count(start)!=h.count(end) or h.count(start)>1:raise SystemExit('Unexpected compact markers')
if start in h:h=h[:h.index(start)]+h[h.index(end)+len(end):].lstrip('\n')
pattern=r'<script\s+defer\s+src="<\?=webhome\?>scripts/js/pishield-v100\.js\?v=(?:120|122|130)"\s*></script>'
m=list(re.finditer(pattern,h))
if len(m)!=1:raise SystemExit('PiShield 1.2 dashboard required')
block='\n'+start+'\n<link rel="stylesheet" href="<?=webhome?>style/pishield-compact.css?v=130">\n<script defer src="<?=webhome?>scripts/js/pishield-compact.js?v=130"></script>\n'+end+'\n'
h=h[:m[0].end()]+block+h[m[0].end():].lstrip('\n')
h=re.sub(r'pishield-v100\.js\?v=(?:120|122|130)\b','pishield-v100.js?v=130',h)
j,n=re.subn(r'PISHIELD / v1\.(?:2(?:\.[12])?|3)\b','PISHIELD / v1.3',j)
if n!=1:raise SystemExit('Unexpected dashboard version')
marker='<!-- PISHIELD PRIVACY V130 -->';anchor='<li class="header text-uppercase">Filtering</li>'
if s.count(anchor)!=1 or s.count(marker)>1:raise SystemExit('Unexpected filtering sidebar')
if marker not in s:s=s.replace(anchor,anchor+'\n'+marker+'\n<li class="ps092-nav ps093-nav<? if scriptname == \'pishield-privacy\' then ?> active<? end ?>"><a href="<?=webhome?>pishield-privacy"><i class="fa fa-fw menu-icon fa-user-shield"></i> <span>Privacy &amp; data protection</span></a></li>',1)
changes={header:h.encode(),sidebar:s.encode(),js:j.encode()}
for dest,src in {'pishield-privacy.lp':'page.lp','pishield-privacy-api.lp':'endpoint.lp','scripts/js/pishield-privacy.js':'ui.js','style/pishield-privacy.css':'style.css','scripts/js/pishield-compact.js':'layout.js','style/pishield-compact.css':'layout.css'}.items():changes[root/dest]=(base/src).read_bytes()
for p in changes:
    if p.is_symlink() or (p.exists() and not p.is_file()) or not p.resolve().is_relative_to(root.resolve()):
        raise SystemExit('Unsafe destination: '+str(p))
changes = {p:b for p,b in changes.items() if not p.exists() or p.read_bytes()!=b}
if not changes: print('PiShield privacy already current'); raise SystemExit(0)
backs.mkdir(parents=True, exist_ok=True)
backup=Path(tempfile.mkdtemp(prefix='privacy-v130-',dir=backs)); backup.chmod(0o700)
def atomic(p,b,mode):
    fd,t=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f: f.write(b);f.flush();os.fsync(f.fileno())
        os.chmod(t,mode);os.replace(t,p)
    finally:
        if os.path.exists(t):os.unlink(t)
old={p:(p.read_bytes(),stat.S_IMODE(p.stat().st_mode)) if p.exists() else None for p in changes}
for p,m in old.items():
    if m is not None:
        b=backup/p.relative_to(root);b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,b)
written=[]
try:
    for p,b in changes.items(): atomic(p,b,old[p][1] if old[p] else 0o644);written.append(p)
except BaseException:
    for p in reversed(written):
        if old[p]:atomic(p,*old[p])
        else:p.unlink(missing_ok=True)
    raise
print('Privacy layout installed. Web backup:', backup)
