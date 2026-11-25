from pathlib import Path
import os, re, shutil, stat, tempfile
base = Path(__file__).resolve().parent
root = Path('/var/www/html/admin')
backs = Path('/var/backups/pishield')
if os.geteuid() != 0:
    root = Path(os.environ.get('PS122_TEST_WEBROOT', str(root)))
    backs = Path(os.environ.get('PS122_TEST_BACKUPS', str(backs)))
header = root/'scripts/lua/header.lp'
js = root/'scripts/js/pishield-v100.js'
for p in (header, js):
    if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):
        raise SystemExit('Missing or unsafe prerequisite: '+str(p))
h = header.read_text(); j = js.read_text()
start = '<!-- PISHIELD COMPACT V122 -->'; end = '<!-- PISHIELD COMPACT V122 END -->'
if h.count(start) != h.count(end) or h.count(start)>1:
    raise SystemExit('Unexpected layout markers')
if start in h:
    h = h[:h.index(start)] + h[h.index(end)+len(end):].lstrip('\n')
# Locate the exact shared script tag rather than assume the native closing-head placement.
pattern = r'<script\s+defer\s+src="<\?=webhome\?>scripts/js/pishield-v100\.js\?v=(?:100|101|110|120|122)"\s*></script>'
m = list(re.finditer(pattern, h))
if len(m) != 1: raise SystemExit('Unexpected shared dashboard script')
block = '\n'+start+'\n<link rel="stylesheet" href="<?=webhome?>style/pishield-compact.css?v=122">\n<script defer src="<?=webhome?>scripts/js/pishield-compact.js?v=122"></script>\n'+end+'\n'
h = h[:m[0].end()] + block + h[m[0].end():].lstrip('\n')
h = re.sub(r'pishield-v100\.js\?v=(?:100|101|110|120|122)\b', 'pishield-v100.js?v=122', h)
j, n = re.subn(r'PISHIELD / v1\.(?:2(?:\.[12])?)\b', 'PISHIELD / v1.2.2', j)
if n != 1: raise SystemExit('PiShield 1.2 dashboard required')
changes = {header:h.encode(), js:j.encode(), root/'style/pishield-compact.css':(base/'layout.css').read_bytes(), root/'scripts/js/pishield-compact.js':(base/'layout.js').read_bytes()}
for p in changes:
    if p.is_symlink() or (p.exists() and not p.is_file()) or not p.resolve().is_relative_to(root.resolve()):
        raise SystemExit('Unsafe destination: '+str(p))
changes = {p:b for p,b in changes.items() if not p.exists() or p.read_bytes()!=b}
if not changes: print('PiShield compact layout already current'); raise SystemExit(0)
backs.mkdir(parents=True, exist_ok=True)
backup=Path(tempfile.mkdtemp(prefix='compact-v122-',dir=backs)); backup.chmod(0o700)
def atomic(p,b,mode):
    fd,t=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f: f.write(b);f.flush();os.fsync(f.fileno())
        os.chmod(t,mode);os.replace(t,p)
    finally:
        if os.path.exists(t):os.unlink(t)
old={p:(p.read_bytes(),stat.S_IMODE(p.stat().st_mode)) if p.exists() else None for p in changes}
for p,m in old.items():
    if m is not None:
        b=backup/p.relative_to(root);b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,b)
written=[]
try:
    for p,b in changes.items(): atomic(p,b,old[p][1] if old[p] else 0o644);written.append(p)
except BaseException:
    for p in reversed(written):
        if old[p]:atomic(p,*old[p])
        else:p.unlink(missing_ok=True)
    raise
print('Compact layout installed. Web backup:', backup)
