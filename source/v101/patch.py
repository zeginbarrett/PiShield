"""PiShield 1.0.1: safe web-only upgrade with backup and atomic writes."""
from pathlib import Path
import os, shutil, tempfile, stat
base = Path(__file__).resolve().parents[1]
root = Path('/var/www/html/admin')
backroot = Path('/var/backups/pishield')
# The only overrides are for unprivileged local fixture testing.
if os.geteuid() != 0:
    root = Path(os.environ.get('PS101_TEST_WEBROOT', str(root)))
    backroot = Path(os.environ.get('PS101_TEST_BACKUPS', str(backroot)))
paths = {
    'pishield-ai-api.lp': 'v06/endpoint.lp',
    'scripts/js/pishield-ai-v06.js': 'v06/ui.js',
    'pishield-defense-api.lp': 'v07/endpoint.lp',
    'scripts/js/pishield-defense.js': 'v07/ui.js',
    'pishield-action-api.lp': 'v08/endpoint.lp',
    'scripts/js/pishield-action.js': 'v08/ui.js',
}
changes = {}
for dest, src in paths.items():
    target = root/dest
    if not target.is_file() or target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
        raise SystemExit(f'Missing or unsafe installed file: {target}; no changes made')
    data = (base/src).read_bytes()
    old = target.read_text()
    if dest.endswith('.lp') and ('mg.request_info' not in old or '/var/lib/pishield-' not in old):
        raise SystemExit(f'Unexpected endpoint: {target}; no changes made')
    if dest.endswith('.js') and ('pishield-' not in old or 'fetch(' not in old):
        raise SystemExit(f'Unexpected client: {target}; no changes made')
    changes[target] = data
for rel in ('style/pishield-v100.css','scripts/js/pishield-v100.js'):
    target = root/rel
    if not target.is_file() or target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
        raise SystemExit(f'PiShield 1.0 required: {target}; no changes made')
    old = target.read_text()
    if rel.endswith('.css'):
        if '.ps1-dashboard' not in old:raise SystemExit('Unexpected dashboard CSS; no changes made')
        marker = '/* PISHIELD V101 MODE BEGIN */'
        end = '/* PISHIELD V101 MODE END */'
        if old.count(marker)!=old.count(end) or old.count(marker)>1:raise SystemExit('Unexpected mode CSS markers; no changes made')
        if marker in old: old=old[:old.index(marker)]+old[old.index(end)+len(end):]
        block=(base/'v100/style.css').read_text().split(marker,1)[1].split(end,1)[0]
        new=old.rstrip()+'\n\n'+marker+block+end+'\n'
    else:
        if 'PISHIELD / v1.0' not in old:raise SystemExit('Unexpected dashboard JS; no changes made')
        new=old.replace("'PISHIELD / v1.0'","'PISHIELD / v1.0.1'")
    changes[target]=new.encode()
# Bust the explicitly-versioned shared CSS/JS URLs. Other scripts use native fileversion().
header=root/'scripts/lua/header.lp'
if not header.is_file() or header.is_symlink() or not header.resolve().is_relative_to(root.resolve()):raise SystemExit('Missing header; no changes made')
h=header.read_text()
for filename in ('pishield-v100.css','pishield-v100.js'):
    if filename+'?v=100' not in h and filename+'?v=101' not in h:raise SystemExit('Unexpected v1.0 header; no changes made')
    h=h.replace(filename+'?v=100',filename+'?v=101')
changes[header]=h.encode()
changes={p:d for p,d in changes.items() if p.read_bytes()!=d}
if not changes:
    print('PiShield 1.0.1 already installed; no changes made.');raise SystemExit(0)
backroot.mkdir(parents=True,exist_ok=True)
backup=Path(tempfile.mkdtemp(prefix='v101-',dir=backroot)); backup.chmod(0o700)
for p in changes:
    b=backup/p.relative_to(root); b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,b)
def atomic(path,data):
    mode=stat.S_IMODE(path.stat().st_mode); fd,tmp=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.chmod(tmp,mode);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
written=[]
try:
    for p,d in changes.items():atomic(p,d);written.append(p)
except BaseException:
    for p in written:atomic(p,(backup/p.relative_to(root)).read_bytes())
    raise
print('PiShield 1.0.1 applied. Backup:',backup)
print('Refresh the AI and Defense Control pages (Ctrl+F5). No DNS restart or mode change.')
