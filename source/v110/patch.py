from pathlib import Path
import os,re,shutil,tempfile,stat
base=Path(__file__).resolve().parent
root=Path('/var/www/html/admin'); backs=Path('/var/backups/pishield')
if os.geteuid()!=0:
    root=Path(os.environ.get('PS110_TEST_WEBROOT',str(root)));backs=Path(os.environ.get('PS110_TEST_BACKUPS',str(backs)))
side=root/'scripts/lua/sidebar.lp';head=root/'scripts/lua/header.lp';js=root/'scripts/js/pishield-v100.js'
for p in (side,head,js):
    if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise SystemExit('Missing or unsafe prerequisite: '+str(p))
s=side.read_text();h=head.read_text();j=js.read_text()
marker='<!-- PISHIELD GUARD V110 -->'
anchor='<li class="header text-uppercase">Defense operations</li>'
if s.count(anchor)!=1:raise SystemExit('Unexpected sidebar layout; no web changes')
if marker not in s:s=s.replace(anchor,anchor+'\n'+marker+'\n<li class="ps092-nav ps093-nav<? if scriptname == \'pishield-guard\' then ?> active<? end ?>"><a href="<?=webhome?>pishield-guard"><i class="fa fa-fw menu-icon fa-shield-alt"></i> <span>Host security</span></a></li>',1)
if not re.search(r'PISHIELD / v1\.(?:0(?:\.1)?|1)\b',j):raise SystemExit('Unexpected dashboard version')
j=re.sub(r'PISHIELD / v1\.(?:0(?:\.1)?|1)\b','PISHIELD / v1.1',j)
if 'pishield-v100.js?v=' not in h:raise SystemExit('Unexpected dashboard header')
h=re.sub(r'pishield-v100\.js\?v=(?:100|101|110)\b','pishield-v100.js?v=110',h)
changes={side:s.encode(),head:h.encode(),js:j.encode(),root/'pishield-guard.lp':(base/'page.lp').read_bytes(),root/'pishield-guard-api.lp':(base/'endpoint.lp').read_bytes(),root/'scripts/js/pishield-guard.js':(base/'ui.js').read_bytes()}
for p in changes:
    if p.is_symlink() or (p.exists() and not p.is_file()) or not p.resolve().is_relative_to(root.resolve()):raise SystemExit('Unsafe destination: '+str(p))
changes={p:b for p,b in changes.items() if not p.exists() or p.read_bytes()!=b}
if not changes: print('Web files already current');raise SystemExit(0)
backs.mkdir(parents=True,exist_ok=True);backup=Path(tempfile.mkdtemp(prefix='guard-v110-',dir=backs));backup.chmod(0o700)
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
