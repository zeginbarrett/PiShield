import os,pathlib,re,shutil,sys,tempfile,time
R=pathlib.Path('/var/www/html/admin'); P=pathlib.Path('/opt/pishield-sentinel'); B=pathlib.Path('/var/backups/pishield')
def atomic(p,s):
    p.parent.mkdir(parents=True,exist_ok=True); fd,t=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'w') as f:f.write(s)
        os.chmod(t,0o644);os.replace(t,p)
    finally:
        if os.path.exists(t):os.unlink(t)
def strip(s,a,b):
    if s.count(a)!=s.count(b) or s.count(a)>1:raise ValueError('Unexpected patch markers')
    return re.sub(re.escape(a)+'.*?'+re.escape(b)+r'\n?', '',s,flags=re.S)
def block(tag,body):return '<!-- SENTINEL '+tag+' BEGIN -->\n'+body+'\n<!-- SENTINEL '+tag+' END -->\n'
header=R/'scripts/lua/header.lp'; side=R/'scripts/lua/sidebar.lp'; index=R/'index.lp'
for x in (header,side,index):
    if not x.is_file() or x.is_symlink():raise SystemExit('Missing or unsafe native file: '+str(x))
h=strip(header.read_text(),'<!-- SENTINEL BRAND BEGIN -->','<!-- SENTINEL BRAND END -->');s=strip(side.read_text(),'<!-- SENTINEL NAV BEGIN -->','<!-- SENTINEL NAV END -->'); i=strip(index.read_text(),'<!-- SENTINEL HOME BEGIN -->','<!-- SENTINEL HOME END -->')
if sys.argv[1:]==['remove']:
    for path,value in ((header,h),(side,s),(index,i)): atomic(path,value)
    for name in ('scripts/js/pishield-sentinel-brand.js','style/pishield-sentinel.css','img/pishield-sentinel.svg','pishield-sentinel.lp'):
        path=R/name
        if path.exists() and not path.is_symlink(): path.unlink()
    print('Sentinel web integration removed. Earlier PiShield customizations retained.')
    sys.exit(0)
# Preserve the full original donation block for easy restoration; hide using CSS/JS rather than deleting upstream credits.
# Reuse the v0.4 theme and homepage markers and the native Group Management line.
# Insertion points are deliberately outside earlier PiShield-managed blocks.
checks={
    'header theme end': (h,'<!-- PISHIELD THEME END -->'),
    'homepage banner end': (i,'<!-- PISHIELD HOME END -->'),
}
for label,(source,token) in checks.items():
    if source.count(token)!=1:
        raise SystemExit(f'Cannot find unique {label} (found {source.count(token)}). No web changes made.')
if 'pishield-terminal.css' not in h or 'pishield#ai' not in i:
    raise SystemExit('v0.4 theme or homepage not found. No web changes made.')
# Locate the existing extension block if present; otherwise use the verified native sidebar section.
nav_match=list(re.finditer(r'(?m)^[ \t]*<!-- PISHIELD BEGIN -->[^\n]*\n',s))
if len(nav_match)==1:
    nav_pos=nav_match[0].start()
else:
    native=list(re.finditer(r'(?mi)^[ \t]*<li\b[^>]*class=["\'][^"\']*\bheader\b[^"\']*["\'][^>]*>\s*Group Management\s*</li>[^\n]*',s))
    if len(native)!=1 or not re.search(r'pishield(?:#|\.lp|["\'])',s,re.I):
        raise SystemExit(f'Cannot locate existing PiShield navigation or unique Group Management section (found {len(native)}). No web changes made.')
    nav_pos=native[0].start()
def after_marker(source,token,value):
    pos=source.index(token)+len(token)
    if source[pos:pos+1]=='\n': pos+=1
    return source[:pos]+('' if source[pos-1:pos]=='\n' else '\n')+value+source[pos:]
h=after_marker(h,'<!-- PISHIELD THEME END -->',block('BRAND', '''<link rel="stylesheet" href="<?=pihole.fileversion('style/pishield-sentinel.css')?>">
<script defer src="<?=pihole.fileversion('scripts/js/pishield-sentinel-brand.js')?>"></script>'''))
s=s[:nav_pos]+block('NAV','''<li class="header text-uppercase">Sentinel</li>
<li class="menu-main<? if scriptname == 'pishield-sentinel' then ?> active<? end ?>"><a href="<?=webhome?>pishield-sentinel"><i class="fa fa-fw menu-icon fa-shield-alt"></i> <span>Autonomous defense</span></a></li>''')+s[nav_pos:]
i=after_marker(i,'<!-- PISHIELD HOME END -->',block('HOME','<div class="box box-primary"><div class="box-body"><strong>SENTINEL // BACKGROUND MONITOR</strong> &nbsp; <a class="btn btn-default" href="<?=webhome?>pishield-sentinel">Open persistent security reports</a></div></div>'))
updates={header:h,side:s,index:i,R/'scripts/js/pishield-sentinel-brand.js':(P/'brand.js').read_text(),R/'style/pishield-sentinel.css':(P/'brand.css').read_text(),R/'img/pishield-sentinel.svg':(P/'logo.svg').read_text()}
for p in updates:
    if p.is_symlink():raise SystemExit('Unsafe path '+str(p))
original={p:p.read_text() if p.exists() else None for p in updates}
B.mkdir(exist_ok=True,parents=True,mode=0o700); backup=pathlib.Path(tempfile.mkdtemp(prefix='sentinel-v05-',dir=B))
for p,v in original.items():
    if v is not None:
        target=backup/p.relative_to(R);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
try:
    for p,v in updates.items():atomic(p,v)
except BaseException:
    for p,v in original.items():
        if v is None:p.unlink(missing_ok=True)
        else:atomic(p,v)
    raise
print('Web integration installed; original files backed up to',backup)
