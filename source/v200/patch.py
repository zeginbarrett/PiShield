from pathlib import Path
import os,re,shutil,stat,tempfile
base=Path(__file__).resolve().parent;root=Path('/var/www/html/admin');backs=Path('/var/backups/pishield')
if os.geteuid()!=0:root=Path(os.environ.get('PS200_TEST_WEBROOT',str(root)));backs=Path(os.environ.get('PS200_TEST_BACKUPS',str(backs)))
header=root/'scripts/lua/header.lp';side=root/'scripts/lua/sidebar.lp';js=root/'scripts/js/pishield-v100.js'
for p in (header,side,js,root/'pishield-privacy.lp',root/'pishield-device-privacy.lp',root/'scripts/js/pishield-device-filters.js',root/'scripts/js/pishield-live.js'):
    if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise SystemExit('Missing or unsafe PiShield 1.3.5 prerequisite: '+str(p))
h=header.read_text();s=side.read_text();j=js.read_text()
h,n=re.subn(r'pishield-v100\.js\?v=(135|200)\b','pishield-v100.js?v=200',h)
if n!=1:raise SystemExit('Unexpected dashboard header')
j,n=re.subn(r'PISHIELD / (?:v1\.3\.5|v2\.0)\b','PISHIELD / v2.0',j)
if n!=1:raise SystemExit('Unexpected dashboard version')
marker='<!-- PISHIELD INTELLIGENCE V200 -->'
if s.count(marker)>1:raise SystemExit('Unexpected intelligence marker')
if marker not in s:
    anchor='<li class="header text-uppercase">Network</li>'
    if s.count(anchor)!=1:raise SystemExit('Network section missing')
    s=s.replace(anchor,anchor+'\n'+marker+'\n'+"""<li class="ps092-nav ps093-nav<? if scriptname == 'pishield-intelligence' then ?> active<? end ?>"><a href="<?=webhome?>pishield-intelligence"><i class="fa fa-fw menu-icon fa-network-wired"></i> <span>Device Intelligence</span></a></li>""",1)
changes={header:h.encode(),side:s.encode(),js:j.encode()}
for dest,src in {'pishield-intelligence.lp':'page.lp','pishield-intelligence-api.lp':'endpoint.lp','scripts/js/pishield-intelligence.js':'ui.js','style/pishield-intelligence.css':'style.css'}.items():changes[root/dest]=(base/src).read_bytes()
# Preserve installed existing pages; add narrowly scoped preselection and cache-busting.
for dest,page,marker,anchor,insertion,version in [
    ('pishield-device-filters.js','pishield-privacy.lp','/* PS200 PRESET */',"run(async()=> 'Choose a device or enter its reserved IP.');","const preset=new URLSearchParams(location.search).get('ip');if(preset&&ipv4(preset)){$('psdf-ip').value=preset;load();}else run(async()=> 'Choose a device or enter its reserved IP.');",'135'),
    ('pishield-live.js','pishield-live.lp','/* PS200 PRESET */',None,None,'133')]:
    f=root/'scripts/js'/dest; text=f.read_text()
    if marker not in text:
        if anchor:
            if text.count(anchor)!=1:raise SystemExit('Device filter script differs; no changes made')
            text=text.replace(anchor,marker+insertion,1)
        else:
            hook="setPreset('dns');poll();"
            if text.count(hook)!=1:raise SystemExit('Unexpected live monitor initialization')
            text=text.replace(hook,marker+"const pre=new URLSearchParams(location.search).get('ip');if(pre&&/^[0-9a-fA-F:.]{1,45}$/.test(pre)){$('pslive-ip').value=pre;setPreset('device-dns');}else setPreset('dns');poll();",1)
        changes[f]=text.encode()
    pagepath=root/page; text=pagepath.read_text();text,n=re.subn(r'('+re.escape(dest)+r'\?v=)(?:'+version+r'|200)\b',r'\g<1>200',text)
    if n!=1:raise SystemExit('Unexpected existing page script version')
    changes[pagepath]=text.encode()
for p in changes:
    if p.is_symlink() or (p.exists() and not p.is_file()) or not p.resolve().is_relative_to(root.resolve()):raise SystemExit('Unsafe destination: '+str(p))
changes={p:b for p,b in changes.items() if not p.exists() or p.read_bytes()!=b}
if not changes:print('Intelligence already current');raise SystemExit(0)
backs.mkdir(parents=True,exist_ok=True);backup=Path(tempfile.mkdtemp(prefix='intelligence-v200-',dir=backs));backup.chmod(0o700)
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
print('Device intelligence installed. Web backup:',backup)
