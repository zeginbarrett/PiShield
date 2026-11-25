#!/bin/bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run with sudo'; exit 1; }
python3 - <<'PY'
from pathlib import Path
import os, re, shutil, tempfile
root=Path(os.environ.get('PS_LAYOUT_WEBROOT','/var/www/html/admin'))
backroot=Path(os.environ.get('PS_LAYOUT_BACKUPS','/var/backups/pishield'))
sidebar=root/'scripts/lua/sidebar.lp'
header=root/'scripts/lua/header.lp'
style=root/'style/pishield-mobile-v09.css'
home=root/'index.lp'
for p in (sidebar,header,style,home):
    if not p.is_file() or p.is_symlink(): raise SystemExit(f'Expected v0.9.1 file missing or unsafe: {p}; no changes made')
s=sidebar.read_text(); h=header.read_text(); c=style.read_text(); i=home.read_text()
start='<!-- PISHIELD V09 NAV BEGIN -->'; end='<!-- PISHIELD V09 NAV END -->'
if s.count(start)!=1 or s.count(end)!=1 or s.index(start)>s.index(end): raise SystemExit('v0.9 navigation markers missing; no changes made')
a,b=s.index(start),s.index(end)+len(end)
nav=s[a:b]
for old,new in [('Investigations &amp; device trust','Investigations &amp; trust'),('Network discovery &amp; health','Devices &amp; health')]:
    nav=nav.replace('>'+old+'</span>','>'+new+'</span>')
# Scope the flex layout to the extension links; native tree menus retain their own behavior.
nav=nav.replace('<li><a href="<?=webhome?>pishield','<li class="ps092-nav"><a href="<?=webhome?>pishield')
if nav.count('class="ps092-nav"')!=6: raise SystemExit('Unexpected v0.9 navigation links; no changes made')
s=s[:a]+nav+s[b:]
# The existing shared header loads this sheet after the terminal theme.
h,n=re.subn(r'(style/pishield-mobile-v09\.css)(?:\?v=[\w.-]+)?(?=")',r'\1?v=092',h)
if n!=1: raise SystemExit('Expected one mobile stylesheet link; no changes made')
marker='/* BEGIN PISHIELD V092 LAYOUT */'; finish='/* END PISHIELD V092 LAYOUT */'
if c.count(marker)!=c.count(finish) or c.count(marker)>1: raise SystemExit('Unexpected CSS markers; no changes made')
c=re.sub(re.escape(marker)+r'.*?'+re.escape(finish), '', c, flags=re.S).rstrip()+'\n'+marker+'''
/* Expanded sidebar: allow long labels to wrap without truncation. */
@media (min-width: 768px) {
  body:not(.sidebar-collapse) .main-sidebar .sidebar-menu > li.ps092-nav > a {
    display: flex !important; align-items: center; gap: 9px; min-height: 39px;
    padding: 10px 12px !important; white-space: normal !important;
    height: auto !important; line-height: 1.4 !important; box-sizing: border-box;
  }
  body:not(.sidebar-collapse) .main-sidebar .sidebar-menu > li.ps092-nav > a > i { flex: 0 0 19px; margin: 0 !important; text-align: center; }
  body:not(.sidebar-collapse) .main-sidebar .sidebar-menu > li.ps092-nav > a > span { flex: 1 1 auto; min-width: 0; white-space: normal !important; overflow-wrap: anywhere; }
}
@media (max-width: 767px) {
  body .main-sidebar .sidebar-menu > li.ps092-nav > a {
    display: flex !important; align-items: center; gap: 9px; min-height: 42px;
    padding: 10px 12px !important; white-space: normal !important;
    height: auto !important; line-height: 1.4 !important; box-sizing: border-box;
  }
  body .main-sidebar .sidebar-menu > li.ps092-nav > a > i { flex: 0 0 19px; margin: 0 !important; }
  body .main-sidebar .sidebar-menu > li.ps092-nav > a > span { flex: 1 1 auto; min-width: 0; white-space: normal !important; overflow-wrap: anywhere; }
}
/* Compact dashboard header, preserve native chart dimensions and controls. */
body .content .ps-native-banner { padding: 16px 20px !important; margin-bottom: 14px !important; }
body .content .ps-native-banner h2 { margin: 5px 0 7px !important; line-height: 1.25; }
body .content .ps-native-banner p { margin-bottom: 10px !important; }
body .content .ps-native-banner .btn { max-width: 100%; white-space: normal; margin: 3px 6px 3px 0 !important; }
body .content .small-box .small-box-footer { white-space: normal; overflow-wrap: anywhere; }
@media (max-width: 767px) {
  body .content .ps-native-banner { padding: 13px !important; }
  body .content .ps-native-banner h2 { font-size: 21px !important; }
  body .content .box-header .box-title { white-space: normal; overflow-wrap: anywhere; }
  body .content .box-body .table-responsive { max-width: 100%; overflow-x: auto !important; }
}
@media (max-width: 420px) { body .content .small-box .icon { display: none; } }
'''+finish+'\n'
# Route only the known shortcuts, not arbitrary links or native controls.
for old,new in [ ('href="<?=webhome?>pishield#ai">AI ANALYST','href="<?=webhome?>pishield-ai">AI REPORTS'), ('href="<?=webhome?>pishield#overview">SECURITY OVERVIEW','href="<?=webhome?>pishield-action">DEFENSE CONTROL') ]:
    i=i.replace(old,new)
updates={sidebar:s,header:h,style:c,home:i}
backroot.mkdir(parents=True,exist_ok=True)
backup=Path(tempfile.mkdtemp(prefix='layout-v092-',dir=backroot))
for p in updates:
    dst=backup/p.relative_to(root); dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,dst)
def write(p,txt):
    fd,tmp=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'w') as f:f.write(txt)
        os.chmod(tmp,p.stat().st_mode & 0o777); os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
try:
    for p,txt in updates.items():write(p,txt)
    for p,txt in updates.items():
        if p.read_text()!=txt:raise IOError(f'Verification failed: {p}')
except BaseException:
    for p in updates:shutil.copy2(backup/p.relative_to(root),p)
    raise
print('PiShield v0.9.2 layout correction installed. Refresh with Ctrl+F5.')
print('Backup:',backup)
PY
