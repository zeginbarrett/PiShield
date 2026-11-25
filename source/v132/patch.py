from pathlib import Path
import os,re,shutil,stat,tempfile
base=Path(__file__).resolve().parent;root=Path('/var/www/html/admin');backs=Path('/var/backups/pishield')
if os.geteuid()!=0:root=Path(os.environ.get('PS132_TEST_WEBROOT',str(root)));backs=Path(os.environ.get('PS132_TEST_BACKUPS',str(backs)))
header=root/'scripts/lua/header.lp';side=root/'scripts/lua/sidebar.lp';js=root/'scripts/js/pishield-v100.js'
for p in (header,side,js,root/'pishield-device-privacy.lp'):
    if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise SystemExit('Missing or unsafe PiShield 1.3.1 prerequisite: '+str(p))
h=header.read_text();s=side.read_text();j=js.read_text()
h,n=re.subn(r'pishield-v100\.js\?v=(131|132)\b','pishield-v100.js?v=132',h)
if n!=1:raise SystemExit('Unexpected dashboard header')
j,n=re.subn(r'PISHIELD / v1\.3\.[12]\b','PISHIELD / v1.3.2',j)
if n!=1:raise SystemExit('Unexpected dashboard version')
marker='<!-- PISHIELD LIVE V132 -->';anchor='<li class="header text-uppercase">Network</li>'
if s.count(marker)>1:raise SystemExit('Unexpected live marker')
if marker not in s:
    line=next((l for l in s.splitlines() if 'href="<?=webhome?>pishield-device-privacy"' in l),None)
    if not line:raise SystemExit('Device monitor menu missing')
    # Prefer Network section; fallback to adjacent device privacy menu.
    addition=marker+'\n<li class="ps092-nav ps093-nav<? if scriptname == \'pishield-live\' then ?> active<? end ?>"><a href="<?=webhome?>pishield-live"><i class="fa fa-fw menu-icon fa-chart-line"></i> <span>Live Network Monitor</span></a></li>'
    if s.count(anchor)==1:s=s.replace(anchor,anchor+'\n'+addition,1)
    else:s=s.replace(line,line+'\n'+addition,1)
changes={header:h.encode(),side:s.encode(),js:j.encode()}
for dest,src in {'pishield-live.lp':'page.lp','pishield-live-api.lp':'endpoint.lp','scripts/js/pishield-live.js':'ui.js','style/pishield-live.css':'style.css'}.items():changes[root/dest]=(base/src).read_bytes()
for p in changes:
    if p.is_symlink() or (p.exists() and not p.is_file()) or not p.resolve().is_relative_to(root.resolve()):raise SystemExit('Unsafe destination: '+str(p))
changes={p:b for p,b in changes.items() if not p.exists() or p.read_bytes()!=b}
if not changes:print('Live monitor already current');raise SystemExit(0)
backs.mkdir(parents=True,exist_ok=True);backup=Path(tempfile.mkdtemp(prefix='live-v132-',dir=backs));backup.chmod(0o700)
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
print('Live monitor installed. Web backup:',backup)
