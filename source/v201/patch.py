from pathlib import Path
import os,re,shutil,stat,tempfile
base=Path(__file__).resolve().parent
root=Path('/var/www/html/admin'); opt=Path('/opt'); backs=Path('/var/backups/pishield')
if os.geteuid()!=0:
    root=Path(os.environ.get('PS201_TEST_WEBROOT',str(root))); opt=Path(os.environ.get('PS201_TEST_OPT',str(opt))); backs=Path(os.environ.get('PS201_TEST_BACKUPS',str(backs)))
header=root/'scripts/lua/header.lp'; sidebar=root/'scripts/lua/sidebar.lp'; dash=root/'scripts/js/pishield-v100.js'; page=root/'pishield-ai.lp'; ui=root/'scripts/js/pishield-ai-v06.js'; manual=opt/'pishield-ai/worker.py'; sentinel=opt/'pishield-sentinel/sentinel.py'
for p in (header,sidebar,dash,page,ui,manual,sentinel):
    if not p.is_file() or p.is_symlink() or not any(p.resolve().is_relative_to(x.resolve()) for x in (root,opt)):raise SystemExit('Missing or unsafe prerequisite: '+str(p))
h=header.read_text();s=sidebar.read_text();j=dash.read_text();p=page.read_text();u=ui.read_text();m=manual.read_text();t=sentinel.read_text()
h,n=re.subn(r'pishield-v100\.js\?v=(200|201)\b','pishield-v100.js?v=201',h)
if n!=1:raise SystemExit('PiShield 2.0 required')
j,n=re.subn(r'PISHIELD / v2\.0(?:\.1)?\b','PISHIELD / v2.0.1',j)
if n!=1:raise SystemExit('Unexpected dashboard version')
marker='<!-- PISHIELD CHAT V201 -->'
if marker not in s:
    anchor='<li class="header text-uppercase">Intelligence</li>'
    if s.count(anchor)!=1:raise SystemExit('Intelligence menu missing')
    s=s.replace(anchor,anchor+'\n'+marker+'\n'+'''<li class="ps092-nav ps093-nav<? if scriptname == 'pishield-chat' then ?> active<? end ?>"><a href="<?=webhome?>pishield-chat"><i class="fa fa-fw menu-icon fa-comments"></i> <span>Ask PiShield</span></a></li>''',1)
if marker not in p:
    a='<pre id="ps6-answer"'; i=p.find(a)
    if i<0 or p.count(a)!=1:raise SystemExit('Unexpected report template')
    e=p.index('</pre>',i)+len('</pre>'); old=p[i:e]
    p=p[:i]+marker+'<link rel="stylesheet" href="<?=webhome?>style/pishield-chat.css?v=201"><div class="psc-plain"><div id="ps6-plain"></div><a class="btn btn-primary" href="pishield-chat">Ask about the latest report</a><details><summary>Original AI report / technical text</summary>'+old+'</details></div>'+p[e:]
if '/* PS201 PLAIN */' not in u:
    anchor='function display(r,a){'
    if u.count(anchor)!=1:raise SystemExit('Unexpected AI script')
    u=u.replace(anchor,(base/'plain.js').read_text()+'\n'+anchor+'plain(r,a);',1)
# Append to fixed prompt strings using exact known anchor; no rewrite of data or model config.
plain=' Write for a home user in plain English. No Markdown tables or jargon. Start with: In short. Then: What PiShield noticed. Then: What you should do. At most three practical steps. Explain any unfamiliar terms. Make clear when the retained data covers less than the selected window or most requests appear under the router. Never describe DNS requests as actual uploads or blocked requests as attacks. Keep technical domain names only when they matter.'
if 'Write for a home user in plain English.' not in m:
    anchor='Give a readable concise report.'
    if m.count(anchor)!=1:raise SystemExit('Manual report prompt differs')
    m=m.replace(anchor,anchor+plain,1)
if 'Write for a home user in plain English.' not in t:
    anchor='No exploit instructions. Be concise.'
    if t.count(anchor)!=1:raise SystemExit('Scheduled report prompt differs')
    t=t.replace(anchor,anchor+plain,1)
compile(m,str(manual),'exec');compile(t,str(sentinel),'exec')
changes={header:h.encode(),sidebar:s.encode(),dash:j.encode(),page:p.encode(),ui:u.encode(),manual:m.encode(),sentinel:t.encode()}
for dest,src in {'pishield-chat.lp':'page.lp','pishield-chat-api.lp':'endpoint.lp','scripts/js/pishield-chat.js':'ui.js','style/pishield-chat.css':'style.css'}.items():changes[root/dest]=(base/src).read_bytes()
for f in changes:
    if f.is_symlink() or (f.exists() and not f.is_file()) or not any(f.resolve().is_relative_to(x.resolve()) for x in (root,opt)):raise SystemExit('Unsafe destination '+str(f))
changes={f:b for f,b in changes.items() if not f.exists() or f.read_bytes()!=b}
if not changes:print('Chat already current');raise SystemExit(0)
backs.mkdir(parents=True,exist_ok=True); backup=Path(tempfile.mkdtemp(prefix='chat-v201-',dir=backs));backup.chmod(0o700)
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
print('AI pages and prompts updated. Backup:',backup)
