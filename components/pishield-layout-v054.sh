#!/bin/bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run with sudo'; exit 1; }
python3 - <<'PY'
from pathlib import Path
import os,re,tempfile,shutil
r=Path(os.getenv('PISHIELD_WEBROOT','/var/www/html/admin'))
b=Path(os.getenv('PISHIELD_BACKUPS','/var/backups/pishield'))
h=r/'scripts/lua/header.lp'; a=r/'scripts/lua/header_authenticated.lp'; c=r/'style/pishield-brand-v053.css'
for p in (h,a,c,r/'img/pishield-art-v053.png'):
    if not p.is_file() or p.is_symlink(): raise SystemExit(f'Missing v0.5.3 file: {p}; no changes made')
header=h.read_text(); auth=a.read_text(); css=c.read_text()
if 'pishield-brand-v053.css' not in header or 'ps-brand-header' not in auth: raise SystemExit('Expected v0.5.3 branding not found; no changes made')
# Add a readable wordmark only to the expanded header; preserve native navigation.
pat=r'(<span\s+class="logo-lg"[^>]*>)(.*?)(</span>)'
def lockup(m):
    inner=re.sub(r'<span class="ps-brand-wordmark">.*?</span>', '', m[2],flags=re.S)
    # The wordmark is a sibling of the image, not a nested span, for repeat-safe replacement.
    inner=re.sub(r'<strong class="ps-brand-wordmark">.*?</strong>', '',inner,flags=re.S)
    if 'ps-brand-header' not in inner: raise SystemExit('Header image missing; no changes made')
    return m[1]+inner+'<strong class="ps-brand-wordmark">PiShield</strong>'+m[3]
auth,n=re.subn(pat,lockup,auth,count=1,flags=re.S)
if n!=1: raise SystemExit('Expanded header not found; no changes made')
header=re.sub(r'(pishield-brand-v053\.css)(?:\?v=[\w.-]+)?',r'\1?v=054',header)
marker='/* BEGIN PISHIELD 054 LAYOUT */'
css=css.split(marker,1)[0].rstrip()+'\n'+marker+'''
/* One compact brand lockup; no duplicate artwork in the status panel. */
body .main-header a.logo .logo-lg {text-align:center!important;white-space:nowrap!important;line-height:50px!important;}
body .main-header a.logo .logo-lg img.ps-brand-header {width:48px!important;height:48px!important;display:inline-block!important;vertical-align:middle!important;object-fit:contain!important;border-radius:50%!important;margin:0 8px 0 0!important;}
body .main-header a.logo .logo-lg .ps-brand-wordmark {display:inline-block!important;font-size:21px!important;line-height:1!important;letter-spacing:.035em!important;font-weight:700!important;vertical-align:middle!important;color:#79fda6!important;}
body .main-header a.logo .logo-mini img.ps-brand-header {width:40px!important;height:40px!important;border-radius:50%!important;}
body .main-sidebar .sidebar .user-panel {display:block!important;min-height:0!important;height:auto!important;padding:14px 15px 15px!important;overflow:visible!important;}
body .main-sidebar .sidebar .user-panel .image {display:none!important;}
body .main-sidebar .sidebar .user-panel .info {display:block!important;float:none!important;position:static!important;box-sizing:border-box!important;width:100%!important;min-width:0!important;max-width:none!important;padding:0!important;margin:0!important;font-size:12px!important;line-height:1.65!important;white-space:normal!important;overflow:visible!important;overflow-wrap:normal!important;}
body .main-sidebar .sidebar .user-panel .info p {font-size:11px!important;letter-spacing:.13em!important;text-transform:uppercase!important;color:#79fda6!important;margin:0 0 7px!important;}
body .main-sidebar .sidebar .user-panel .info > br {display:none!important;}
body .main-sidebar .sidebar .user-panel .info > span {display:block!important;width:100%!important;min-height:20px!important;line-height:20px!important;white-space:nowrap!important;overflow:visible!important;overflow-wrap:normal!important;}
body .main-sidebar .sidebar .user-panel .info > span i {display:inline-block!important;width:19px!important;text-align:center!important;margin-right:5px!important;}
@media(min-width:768px){body.sidebar-mini.sidebar-collapse .main-sidebar:not(:hover) .sidebar .user-panel {display:none!important;min-height:0!important;padding:0!important;}}
/* END PISHIELD 054 LAYOUT */
'''
updates={h:header,a:auth,c:css}
b.mkdir(parents=True,exist_ok=True); backup=Path(tempfile.mkdtemp(prefix='brand-v054-',dir=b))
for p in updates:
    dest=backup/p.relative_to(r);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
def write(p,s):
    fd,tmp=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'w') as f:f.write(s)
        os.chmod(tmp,0o644);os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
try:
    for p,s in updates.items():write(p,s)
    for p,s in updates.items():
        if p.read_text()!=s:raise IOError(f'Verification failed: {p}')
except BaseException:
    for p in updates:shutil.copy2(backup/p.relative_to(r),p)
    raise
print('PiShield v0.5.4 layout installed. Refresh with Ctrl+F5.')
print('Backup:',backup)
PY
