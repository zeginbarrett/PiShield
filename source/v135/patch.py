from pathlib import Path
import os,re,shutil,stat,tempfile
base=Path(__file__).resolve().parent;root=Path('/var/www/html/admin');backs=Path('/var/backups/pishield')
if os.geteuid()!=0:root=Path(os.environ.get('PS135_TEST_WEBROOT',str(root)));backs=Path(os.environ.get('PS135_TEST_BACKUPS',str(backs)))
header=root/'scripts/lua/header.lp';side=root/'scripts/lua/sidebar.lp';js=root/'scripts/js/pishield-v100.js'
for p in (header,side,js,root/'pishield-privacy.lp',root/'pishield-device-privacy.lp'):
    if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise SystemExit('Missing or unsafe PiShield 1.3.4 prerequisite: '+str(p))
h=header.read_text();s=side.read_text();j=js.read_text()
h,n=re.subn(r'pishield-v100\.js\?v=(134|135)\b','pishield-v100.js?v=135',h)
if n!=1:raise SystemExit('Unexpected dashboard header')
j,n=re.subn(r'PISHIELD / v1\.3(?:\.[45])\b','PISHIELD / v1.3.5',j)
if n!=1:raise SystemExit('Unexpected dashboard version')
# Keep the native group administration intact; remove only the obsolete custom menu item.
lines=s.splitlines(keepends=True); hits=[i for i,l in enumerate(lines) if 'href="<?=webhome?>pishield-privacy"' in l]
if len(hits)!=1:raise SystemExit('Unexpected privacy menu')
lines[hits[0]]=re.sub(r'<span>[^<]*</span>','<span>Device filtering &amp; privacy</span>',lines[hits[0]],count=1)
s=''.join(l for l in lines if 'href="<?=webhome?>pishield#profiles"' not in l)
changes={header:h.encode(),side:s.encode(),js:j.encode()}
for dest,src in {'pishield-privacy.lp':'page.lp','scripts/js/pishield-device-filters.js':'ui.js','style/pishield-device-filters.css':'style.css','pishield-device-privacy.lp':'monitor.lp','scripts/js/pishield-device-privacy.js':'monitor.js'}.items():changes[root/dest]=(base/src).read_bytes()
for p in changes:
    if p.is_symlink() or (p.exists() and not p.is_file()) or not p.resolve().is_relative_to(root.resolve()):raise SystemExit('Unsafe destination: '+str(p))
changes={p:b for p,b in changes.items() if not p.exists() or p.read_bytes()!=b}
if not changes:print('Device filters already current');raise SystemExit(0)
backs.mkdir(parents=True,exist_ok=True);backup=Path(tempfile.mkdtemp(prefix='device-filters-v135-',dir=backs));backup.chmod(0o700)
def atomic(p,b,mode,uid=None,gid=None):
    fd,t=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
        os.chmod(t,mode)
        if uid is not None and os.geteuid()==0:os.chown(t,uid,gid)
        os.replace(t,p)
    finally:
        if os.path.exists(t):os.unlink(t)
old={}
for p in changes:
    if p.exists():
        st=p.stat();old[p]=(p.read_bytes(),stat.S_IMODE(st.st_mode),st.st_uid,st.st_gid);b=backup/p.relative_to(root);b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,b)
    else:old[p]=None
written=[]
try:
    for p,b in changes.items():atomic(p,b,*(old[p][1:] if old[p] else (0o644,None,None)));written.append(p)
except BaseException:
    for p in reversed(written):
        if old[p]:atomic(p,*old[p])
        else:p.unlink(missing_ok=True)
    raise
print('Device filters installed. Web backup:',backup)
