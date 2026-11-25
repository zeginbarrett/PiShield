#!/bin/bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run with sudo'; exit 1; }
python3 - <<'PY'
from pathlib import Path
import os,re,tempfile,shutil
root=Path(os.environ.get('PS093_WEBROOT','/var/www/html/admin'))
backroot=Path(os.environ.get('PS093_BACKUPS','/var/backups/pishield'))
side=root/'scripts/lua/sidebar.lp'; header=root/'scripts/lua/header.lp'
js=root/'scripts/js/pishield-pages-v093.js'; css=root/'style/pishield-pages-v093.css'; ai=root/'scripts/js/pishield-ai-v06.js'
for p in (side,header,ai,root/'pishield-defense.lp',root/'pishield-action.lp',root/'pishield-ai.lp',root/'pishield-sentinel.lp',root/'pishield-system.lp'):
    if not p.is_file() or p.is_symlink():raise SystemExit(f'Missing or unsafe file: {p}; no changes made')
for p in (js,css):
    if p.is_symlink():raise SystemExit(f'Unsafe file: {p}; no changes made')
start='<!-- PISHIELD V09 NAV BEGIN -->'; end='<!-- PISHIELD V09 NAV END -->'
s=side.read_text();h=header.read_text(); a=ai.read_text()
if s.count(start)!=1 or s.count(end)!=1 or s.index(start)>s.index(end):raise SystemExit('Expected v0.9 navigation; no changes made')
sections=[('Defense operations', [('pishield-action?view=control','Defense control','shield-alt'),('pishield-action?view=rules','Domain rules','lock'),('pishield-action?view=log','Action log','history'),('pishield-defense?view=investigations','Investigations','bell')]),('Intelligence',[('pishield-sentinel?view=learning','Behavioral learning','brain'),('pishield-sentinel?view=verification','Threat verification','search'),('pishield-ai?view=analysis','AI analysis','microchip'),('pishield-ai?view=reports','AI reports','file-alt'),('pishield-ai?view=settings','AI settings','cog')]),('Network',[('pishield-system?view=devices','Device discovery','network-wired'),('pishield-defense?view=trust','Device trust','user-shield'),('pishield-system?view=health','Network health','heartbeat')]),('Filtering',[('pishield#profiles','Filtering profiles','filter')]),('Maintenance',[('pishield-sentinel?view=recovery','Service recovery','tools'),('pishield-system?view=backups','Backups','save')])]
nav=[start]
for title,links in sections:
    nav.append(f'<li class="header text-uppercase">{title}</li>')
    for route,label,icon in links:nav.append(f'<li class="ps092-nav ps093-nav"><a href="<?=webhome?>{route}"><i class="fa fa-fw menu-icon fa-{icon}"></i> <span>{label}</span></a></li>')
nav.append(end)
s=s[:s.index(start)]+'\n'.join(nav)+s[s.index(end)+len(end):]
mark='<!-- PISHIELD V093 VIEWS BEGIN -->'; close='<!-- PISHIELD V093 VIEWS END -->'
if h.count(mark)!=h.count(close) or h.count(mark)>1:raise SystemExit('Unexpected view markers; no changes made')
h=re.sub(re.escape(mark)+r'.*?'+re.escape(close),'',h,flags=re.S)
anchor=re.search(r'<link\b[^\n]*?style/pishield-mobile-v09\.css[^\n]*?>',h)
if not anchor:raise SystemExit('Shared mobile stylesheet anchor missing; no changes made')
block='\n'+mark+'\n<link rel="stylesheet" href="<?=webhome?>style/pishield-pages-v093.css?v=093">\n<script defer src="<?=webhome?>scripts/js/pishield-pages-v093.js?v=093"></script>\n'+close+'\n'
h=h[:anchor.end()]+block+h[anchor.end():]
# Avoid an unsolicited history job when opening the saved reports or model settings view.
old="if(!busy&&!j.report&&!latest)submit('load');"
new="if(!busy&&!j.report&&!latest&&!['settings','reports'].includes(new URLSearchParams(location.search).get('view')))submit('load');"
if old in a:a=a.replace(old,new,1)
elif new not in a:raise SystemExit('Unexpected AI UI version; no changes made')
javascript=r'''(()=>{'use strict';
const routes={
 'pishield-action':{default:'control',views:{control:['Defense control',[1,2]],rules:['Domain rules',[3]],log:['Action log',[4]]}},
 'pishield-defense':{default:'investigations',views:{investigations:['Investigations',[1,2,3]],trust:['Device trust',[4]]}},
 'pishield-ai':{default:'analysis',views:{analysis:['AI analysis',[1,2,3]],reports:['AI reports',[4,3]],settings:['AI settings',[1]]}},
 'pishield-sentinel':{default:'learning',views:{learning:['Behavioral learning',['Recorded coverage','Learned DNS baselines']],verification:['Threat verification',['Verified feed matches','Evidence-linked defensive recommendations']],recovery:['Service recovery',['Service recovery']]}},
 'pishield-system':{default:'devices',views:{devices:['Device discovery',['Network discovery']],health:['Network health',['Connection health']],backups:['Backups',['Configuration backups']]}}
};
const route=location.pathname.replace(/\/$/,'').split('/').pop().replace(/\.lp$/,''); const spec=routes[route]; if(!spec)return;
const view=new URLSearchParams(location.search).get('view')||spec.default;
if(view==='all'||!Object.hasOwn(spec.views,view))return;
function setup(){
 const content=document.querySelector('.content-wrapper .content')||document.querySelector('.content');if(!content)return;
 const [title,wanted]=spec.views[view];
 const boxes=[...content.querySelectorAll('.box-header > .box-title')].map(h=>({h,box:h.closest('.box'),name:h.textContent.trim().replace(/\s+/g,' ')})).filter(x=>x.box);
 const key=x=>/^\d+\s*\//.test(x.name)?Number(x.name.match(/^\d+/)[0]):x.name;
 const known=new Set(Object.values(spec.views).flatMap(v=>v[1]));
 const available=boxes.filter(x=>known.has(key(x))||(route==='pishield-defense'&&key(x)===5));
 const chosen=wanted.map(k=>available.find(x=>key(x)===k));
 // Fall back to the unchanged page if an upstream update changes any required section.
 if(chosen.some(x=>!x))return;
 const hidden=x=>x.classList.add('ps093-hidden');
 available.forEach(x=>{if(!chosen.includes(x)){hidden(x.box);if(x.box.parentElement?.tagName==='DETAILS')hidden(x.box.parentElement);}});
 const banner=content.querySelector('.ps-native-banner h2');if(banner)banner.textContent=title;
 else {const head=document.createElement('h2');head.className='ps093-title';head.textContent=title;content.prepend(head);}
 const visible=chosen[0].box.querySelector('.box-body');
 function moveStatus(ids){if(!visible)return;for(const id of ids){const n=document.getElementById(id);if(n)visible.prepend(n);}}
 if(route==='pishield-defense'&&view==='trust')moveStatus(['ps7-action','ps7-status']);
 if(route==='pishield-action'&&view==='rules')moveStatus(['ps8-result','ps8-status','ps8-mode']);
 if(route==='pishield-action'&&view==='log')moveStatus(['ps8-status']);
 if(route==='pishield-ai'&&view==='reports'){
   const history=chosen[0].box,answer=chosen[1].box;if(history.parentElement===answer.parentElement)history.after(answer);
   moveStatus(['ps6-connection']);
 }
 if(route==='pishield-ai'&&view==='settings'){
   for(const id of ['ps6-run','ps6-load']){const n=document.getElementById(id);if(n)hidden(n);}
   const w=document.getElementById('ps6-window');if(w?.parentElement)hidden(w.parentElement);
 }
 if(route==='pishield-system')for(const a of content.querySelectorAll('a[href="pishield-system"]'))a.href='pishield-system?view='+view;
 for(const a of document.querySelectorAll('.ps093-nav > a')){const u=new URL(a.href,location.href);if(u.pathname.replace(/\.lp$/,'')===location.pathname.replace(/\.lp$/,'')&&u.searchParams.get('view')===view){a.parentElement.classList.add('active');a.setAttribute('aria-current','page');}}
 document.title='PiShield | '+title;
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',setup,{once:true});else setup();
})();
'''
stylesheet='''/* PiShield task-specific views. Shared native scripts retain their required elements. */
.ps093-hidden {display:none !important;}
.ps093-title {margin: 8px 0 20px; color: #79fda6;}
.main-sidebar .ps093-nav > a {white-space: normal !important;}
.main-sidebar .ps093-nav > a > span {overflow-wrap: anywhere;}
'''
changes={side:s,header:h,ai:a,js:javascript,css:stylesheet}
backroot.mkdir(parents=True,exist_ok=True); backup=Path(tempfile.mkdtemp(prefix='pages-v093-',dir=backroot));backup.chmod(0o700)
existing=set()
for p in changes:
    if p.exists():
        existing.add(p); dest=backup/p.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
def write(p,text):
    fd,tmp=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'w') as f:f.write(text)
        os.chmod(tmp,0o644);os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
try:
    for p,text in changes.items():write(p,text)
    for p,text in changes.items():
        if p.read_text()!=text:raise IOError(f'Verification failed: {p}')
except BaseException:
    for p in changes:
        if p in existing:shutil.copy2(backup/p.relative_to(root),p)
        else:p.unlink(missing_ok=True)
    raise
print('PiShield v0.9.3 dedicated page views installed. Refresh with Ctrl+F5.')
print('Backup:',backup)
PY
