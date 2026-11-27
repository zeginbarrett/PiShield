from pathlib import Path
import os,re,shutil,stat,tempfile
base=Path(__file__).resolve().parent
root=Path('/var/www/html/admin'); opt=Path('/opt'); backs=Path('/var/backups/pishield')
if os.geteuid()!=0:
    root=Path(os.environ.get('PS210_TEST_WEBROOT',str(root))); backs=Path(os.environ.get('PS210_TEST_BACKUPS',str(backs)))
header=root/'scripts/lua/header.lp'; sidebar=root/'scripts/lua/sidebar.lp'; dash=root/'scripts/js/pishield-v100.js'
for f in (header,sidebar,dash,root/'pishield-chat.lp'):
    if not f.is_file() or f.is_symlink() or not f.resolve().is_relative_to(root.resolve()):raise SystemExit('Missing or unsafe PiShield 2.0.1 prerequisite: '+str(f))
h=header.read_text();s=sidebar.read_text();j=dash.read_text()
h,n=re.subn(r'pishield-v100\.js\?v=(201|210)\b','pishield-v100.js?v=210',h)
if n!=1:raise SystemExit('PiShield 2.0.1 required')
j,n=re.subn(r'PISHIELD / v2\.(?:0\.1|1)\b','PISHIELD / v2.1',j)
if n!=1:raise SystemExit('Unexpected dashboard version')
marker='<!-- PISHIELD WORKSHOP V210 -->'
lines=s.splitlines(keepends=True); hits=[i for i,l in enumerate(lines) if 'href="<?=webhome?>pishield-chat"' in l]
if len(hits)!=1:raise SystemExit('Chat menu missing')
lines[hits[0]]=lines[hits[0]].replace('<span>Ask PiShield</span>','<span>AI Chat</span>')
s=''.join(lines)
if marker not in s:
    line=lines[hits[0]]
    s=s.replace(line,line+marker+'\n'+"""<li class="ps092-nav ps093-nav<? if scriptname == 'pishield-workshop' then ?> active<? end ?>"><a href="<?=webhome?>pishield-workshop"><i class="fa fa-fw menu-icon fa-tools"></i> <span>Tool Workshop</span></a></li>"""+'\n',1)
theme_marker='<!-- PISHIELD THEME V210 -->'
if theme_marker not in h:
    hook='<script defer src="<?=webhome?>scripts/js/pishield-v100.js?v=210"></script>'
    if h.count(hook)!=1:raise SystemExit('Theme header hook missing')
    h=h.replace(hook,hook+'\n'+theme_marker+'\n<link rel="stylesheet" href="<?=webhome?>style/pishield-theme.css?v=210">\n<script defer src="<?=webhome?>scripts/js/pishield-theme.js?v=210"></script>',1)
changes={header:h.encode(),sidebar:s.encode(),dash:j.encode()}
for dest,source in {'pishield-chat.lp':'page.lp','pishield-workshop.lp':'workshop.lp','pishield-chat-api.lp':'endpoint.lp','scripts/js/pishield-chat.js':'ui.js','style/pishield-chat.css':'style.css','pishield-theme-api.lp':'theme-api.lp','scripts/js/pishield-theme.js':'theme.js','style/pishield-theme.css':'theme.css'}.items():changes[root/dest]=(base/source).read_bytes()
for f in changes:
    if f.is_symlink() or (f.exists() and not f.is_file()) or not any(f.resolve().is_relative_to(x.resolve()) for x in (root,opt)):raise SystemExit('Unsafe destination '+str(f))
changes={f:b for f,b in changes.items() if not f.exists() or f.read_bytes()!=b}
if not changes:print('Chat already current');raise SystemExit(0)
backs.mkdir(parents=True,exist_ok=True); backup=Path(tempfile.mkdtemp(prefix='chat-v210-',dir=backs));backup.chmod(0o700)
old={}
for f in changes:
    if f.exists():
        st=f.stat();old[f]=(f.read_bytes(),stat.S_IMODE(st.st_mode),st.st_uid,st.st_gid); dest=backup/('web' if f.is_relative_to(root) else 'opt')/f.relative_to(root if f.is_relative_to(root) else opt);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
    else:old[f]=None
def atomic(f,b,mode,uid=None,gid=None):
    fd,tmp=tempfile.mkstemp(dir=f.parent)
    try:
        with os.fdopen(fd,'wb') as out:out.write(b);out.flush();os.fsync(out.fileno())
        os.chmod(tmp,mode)
        if uid is not None and os.geteuid()==0:os.chown(tmp,uid,gid)
        os.replace(tmp,f)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
written=[]
try:
    for f,b in changes.items():atomic(f,b,*(old[f][1:] if old[f] else (0o644,None,None)));written.append(f)
except BaseException:
    for f in reversed(written):
        if old[f]:atomic(f,*old[f])
        else:f.unlink(missing_ok=True)
    raise
print('Chat and Workshop installed. Backup:',backup)
