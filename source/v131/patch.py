from pathlib import Path
import os, re, shutil, stat, tempfile
base=Path(__file__).resolve().parent;root=Path('/var/www/html/admin');backs=Path('/var/backups/pishield');opt=Path('/opt/pishield-privacy')
if os.geteuid()!=0:
    root=Path(os.environ.get('PS131_TEST_WEBROOT',str(root)));backs=Path(os.environ.get('PS131_TEST_BACKUPS',str(backs)));opt=Path(os.environ.get('PS131_TEST_OPT',str(opt)))
header=root/'scripts/lua/header.lp';side=root/'scripts/lua/sidebar.lp';js=root/'scripts/js/pishield-v100.js';catalog=opt/'catalog.json'
for p in (header,side,js,root/'pishield-privacy.lp',catalog):
    if not p.is_file() or p.is_symlink():raise SystemExit('Missing or unsafe PiShield 1.3 prerequisite: '+str(p))
h=header.read_text();s=side.read_text();j=js.read_text()
if not re.search(r'pishield-v100\.js\?v=(130|131)\b',h):raise SystemExit('Unexpected dashboard header')
h=re.sub(r'pishield-v100\.js\?v=(130|131)\b','pishield-v100.js?v=131',h)
j,n=re.subn(r'PISHIELD / v1\.3(?:\.1)?\b','PISHIELD / v1.3.1',j)
if n!=1:raise SystemExit('Unexpected dashboard version')
marker='<!-- PISHIELD DEVICE PRIVACY V131 -->';anchor='<li class="header text-uppercase">Filtering</li>'
if s.count(anchor)!=1 or s.count(marker)>1:raise SystemExit('Unexpected filtering sidebar')
if marker not in s:
    line=next((l for l in s.splitlines() if 'href="<?=webhome?>pishield-privacy"' in l),None)
    if not line:raise SystemExit('Privacy menu missing')
    s=s.replace(line,line+'\n'+marker+'\n<li class="ps092-nav ps093-nav<? if scriptname == \'pishield-device-privacy\' then ?> active<? end ?>"><a href="<?=webhome?>pishield-device-privacy"><i class="fa fa-fw menu-icon fa-search"></i> <span>Device Privacy Monitor</span></a></li>',1)
changes={header:h.encode(),side:s.encode(),js:j.encode(),catalog:(base/'catalog.json').read_bytes()}
for dest,src in {'pishield-privacy.lp':'privacy.lp','scripts/js/pishield-privacy.js':'privacy.js','pishield-device-privacy.lp':'page.lp','scripts/js/pishield-device-privacy.js':'ui.js','style/pishield-device-privacy.css':'style.css'}.items():changes[root/dest]=(base/src).read_bytes()
for p in changes:
    if p.is_symlink() or (p.exists() and not p.is_file()) or not (p.resolve().is_relative_to(root.resolve()) or p==catalog and p.resolve().is_relative_to(opt.resolve())):raise SystemExit('Unsafe destination: '+str(p))
changes={p:b for p,b in changes.items() if not p.exists() or p.read_bytes()!=b}
if not changes:print('Device privacy already current');raise SystemExit(0)
backs.mkdir(parents=True,exist_ok=True);backup=Path(tempfile.mkdtemp(prefix='device-privacy-v131-',dir=backs));backup.chmod(0o700)
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
        st=p.stat();old[p]=(p.read_bytes(),stat.S_IMODE(st.st_mode),st.st_uid,st.st_gid);b=backup/('catalog.json' if p==catalog else 'web/'+str(p.relative_to(root)));b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,b)
    else:old[p]=None
written=[]
try:
    for p,b in changes.items():
        atomic(p,b,*(old[p][1:] if old[p] else (0o644,None,None)));written.append(p)
except BaseException:
    for p in reversed(written):
        if old[p]:atomic(p,*old[p])
        else:p.unlink(missing_ok=True)
    raise
print('Device privacy installed. Backup:',backup)
