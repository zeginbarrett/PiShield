from pathlib import Path
import os, sys, shutil, tempfile, json, re
root=Path(os.environ.get('PS100_WEBROOT','/var/www/html/admin'))
backroot=Path(os.environ.get('PS100_BACKUPS','/var/backups/pishield'))
base=Path(__file__).parent
header=root/'scripts/lua/header.lp'
css=root/'style/pishield-v100.css';js=root/'scripts/js/pishield-v100.js'
paths=[header,css,js]
for p in paths:
    if p.is_symlink() or (p.exists() and not p.is_file()):raise SystemExit(f'Unsafe file: {p}')
for p in (header,root/'scripts/lua/header_authenticated.lp',root/'scripts/lua/sidebar.lp',root/'index.lp',root/'pishield-ai-api.lp',root/'pishield-action-api.lp',root/'pishield-defense-api.lp',root/'scripts/js/pishield-pages-v093.js'):
    if not p.is_file() or p.is_symlink():raise SystemExit(f'Missing v0.9.3 file: {p}; no changes made')
def atomic(p, data, mode=0o644):
    fd,t=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.chmod(t,mode);os.replace(t,p)
    finally:
        if os.path.exists(t):os.unlink(t)
def restore(b):
    manifest=json.loads((b/'manifest.json').read_text())
    if manifest.get('root')!=str(root) or set(manifest.get('files',{}))!={str(p.relative_to(root)) for p in paths}:raise SystemExit('Backup does not match this installation')
    for p in paths:
        k=str(p.relative_to(root)); meta=manifest['files'][k]
        if meta['exists']:atomic(p,(b/k).read_bytes(),meta['mode'])
        else:p.unlink(missing_ok=True)
    print('Restored web files from',b)
if sys.argv[1:]==['--rollback']:
    pointer=backroot/'v100-latest.json'
    if not pointer.is_file():raise SystemExit('No v1.0 backup pointer found')
    name=json.loads(pointer.read_text())['backup']
    if not re.fullmatch(r'v100-[A-Za-z0-9_-]+',name):raise SystemExit('Invalid backup name')
    b=backroot/name
    if b.is_symlink() or not b.is_dir():raise SystemExit('Backup missing or unsafe')
    restore(b);pointer.unlink();raise SystemExit(0)
if sys.argv[1:]:raise SystemExit('Unknown option')
h=header.read_text();begin='<!-- PISHIELD V100 BEGIN -->';end='<!-- PISHIELD V100 END -->'
if h.count(begin)!=h.count(end) or h.count(begin)>1:raise SystemExit('Unexpected v1.0 markers; no changes made')
h=re.sub(r'\n?'+re.escape(begin)+r'.*?'+re.escape(end)+r'\n?', '',h,flags=re.S)
# Inject after the shared v0.9.3 CSS/JS block; the native header may not close head itself.
anchor='<!-- PISHIELD V093 VIEWS END -->'
if h.count(anchor)!=1:raise SystemExit('Expected v0.9.3 header marker missing; no changes made')
block='\n'+begin+'\n<link rel="stylesheet" href="<?=webhome?>style/pishield-v100.css?v=100">\n<script defer src="<?=webhome?>scripts/js/pishield-v100.js?v=100"></script>\n'+end+'\n'
h=h.replace(anchor,anchor+block,1)
changes={header:h.encode(),css:(base/'style.css').read_bytes(),js:(base/'ui.js').read_bytes()}
if all(p.is_file() and p.read_bytes()==d for p,d in changes.items()):print('PiShield v1.0 already installed; no changes made.');raise SystemExit(0)
backroot.mkdir(parents=True,exist_ok=True);backup=Path(tempfile.mkdtemp(prefix='v100-',dir=backroot));backup.chmod(0o700)
manifest={'root':str(root),'files':{}}
for p in paths:
    rel=str(p.relative_to(root)); exists=p.exists();manifest['files'][rel]={'exists':exists,'mode':p.stat().st_mode&0o777 if exists else 0o644}
    if exists:
        dest=backup/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
(backup/'manifest.json').write_text(json.dumps(manifest));
try:
    for p,data in changes.items():atomic(p,data)
    for p,data in changes.items():
        if p.read_bytes()!=data:raise IOError('Write verification failed: '+str(p))
    atomic(backroot/'v100-latest.json',json.dumps({'backup':backup.name}).encode(),0o600)
except BaseException:
    restore(backup);raise
print('PiShield v1.0 installed. Backup:',backup)
print('Refresh /admin/ using Ctrl+F5. No DNS, AI, or firewall settings changed.')
