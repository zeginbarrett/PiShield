#!/usr/bin/env python3
"""Bounded, local host and DNS security checks. No network calls or model execution."""
import collections, datetime, grp, hashlib, json, os, pathlib, re, sqlite3, stat, subprocess, tempfile, time
STATE=pathlib.Path('/var/lib/pishield-guard'); WEB=pathlib.Path('/var/www/html/admin'); DNS=pathlib.Path('/etc/pihole/pihole-FTL.db')

def run(args,timeout=12):
    r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=timeout,env={**os.environ,'LC_ALL':'C'})
    if r.returncode: raise RuntimeError(f'{args[0]} exited {r.returncode}')
    return r.stdout

def save(path,data,shared=False):
    fd,t=tempfile.mkstemp(dir=STATE)
    try:
        with os.fdopen(fd,'w') as f:json.dump(data,f,ensure_ascii=True);f.flush();os.fsync(f.fileno())
        if shared:os.chown(t,0,grp.getgrnam('pihole').gr_gid);os.chmod(t,0o640)
        os.replace(t,path)
    finally:
        if os.path.exists(t):os.unlink(t)

def tracked():
    files={pathlib.Path("/usr/local/sbin/pishield-guard")}
    for pat in ('pishield*.lp','scripts/js/pishield*.js','style/pishield*.css','scripts/lua/header.lp','scripts/lua/sidebar.lp','scripts/lua/header_authenticated.lp','index.lp','login.lp'):
        files.update(WEB.glob(pat))
    files.update(pathlib.Path('/etc/systemd/system').glob('pishield-*.service'));files.update(pathlib.Path('/etc/systemd/system').glob('pishield-*.timer'))
    for d in pathlib.Path('/opt').glob('pishield-*'):
        if d.is_dir() and not d.is_symlink(): files.update(d.glob('*.py'));files.update(d.glob('*.sh'))
    return sorted(files)[:500]

def fingerprint(p):
    try:
        st=p.lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_size>8_000_000:return {'unsafe_type_or_size':True}
        fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as f:
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):return {'unsafe_type_or_size':True}
            b=f.read(8_000_001)
        if len(b)>8_000_000:return {'unsafe_type_or_size':True}
        return {'sha256':hashlib.sha256(b).hexdigest(),'mode':stat.S_IMODE(st.st_mode),'uid':st.st_uid,'gid':st.st_gid}
    except OSError:return {'unreadable':True}

def inventory():return {str(p):fingerprint(p) for p in tracked()}

def changes(old,new):
    return [{'path':p,'change':'added' if p not in old else 'missing' if p not in new else 'changed'} for p in sorted(set(old)|set(new)) if old.get(p)!=new.get(p)]

def dns_signals(rows):
    clients=collections.defaultdict(lambda:[0,0,0,0])
    for _,domain,client,reply in rows:
        d=str(domain).lower().rstrip('.'); c=str(client); v=clients[c];v[0]+=1
        if reply==2:v[1]+=1 # FTL reply type NXDOMAIN
        labels=d.split('.');long=any(len(x)>=45 for x in labels)
        if long:v[2]+=1
        if len(d)>=120:v[3]+=1
    out=[]
    for c,(n,nx,ll,whole) in sorted(clients.items(),key=lambda x:-x[1][0])[:30]:
        signals=[]
        if n>=1500:signals.append('High DNS volume in 15 minutes')
        if nx>=50 and nx/n>=.45:signals.append('High NXDOMAIN share')
        if ll>=20 or whole>=10:signals.append('Repeated long DNS names; possible encoded data or normal service traffic')
        if signals:out.append({'client':c,'queries':n,'nxdomain':nx,'long_labels':ll,'long_names':whole,'signals':signals})
    return out

def dns_check(now):
    with sqlite3.connect(DNS.as_uri()+'?mode=ro',uri=True,timeout=4) as c:
        c.execute('PRAGMA query_only=ON');c.execute('PRAGMA busy_timeout=4000')
        deadline=time.monotonic()+5;c.set_progress_handler(lambda:int(time.monotonic()>deadline),10000)
        rows=c.execute('SELECT timestamp,domain,client,reply_type FROM queries WHERE timestamp>=? AND timestamp<=? ORDER BY timestamp DESC LIMIT 20001',(now-900,now)).fetchall()
    return {'sample':min(len(rows),20000),'capped':len(rows)>20000,'signals':dns_signals(rows[:20000]),'latest':rows[0][0] if rows else None}

def ssh_check():
    lines=run(['journalctl','-u','ssh.service','-u','sshd.service','--since','15 min ago','-n','2000','--no-pager','-o','cat']).splitlines()
    # Count log messages, not unique attempts. Never publish raw log text or credentials.
    failed=sum(bool(re.search(r'Failed (?:password|publickey)|authentication failure|Invalid user|maximum authentication attempts exceeded',l,re.I)) for l in lines)
    return {'failure_messages':failed,'journal_lines':len(lines),'possibly_capped':len(lines)>=2000}

def listeners():
    lines=run(['ss','-H','-lntu']).splitlines();out=[]
    for l in lines[:250]:
        x=l.split()
        if len(x)>=5:out.append({'protocol':x[0],'local':x[4]})
    return out

def updates():
    s=run(['apt-get','-s','-o','Debug::NoLocking=true','upgrade'],30)
    rows=[]
    for l in s.splitlines():
        if l.startswith('Inst '):rows.append({'package':l.split()[1],'security':bool(re.search(r'(?:Debian-Security|Raspbian-Security|[\w-]+-security)',l,re.I))})
    mtimes=[p.stat().st_mtime for p in pathlib.Path('/var/lib/apt/lists').glob('*InRelease') if p.is_file()]
    return {'total':len(rows),'security_marked':sum(r['security'] for r in rows),'packages':rows[:100],'cache_updated':max(mtimes,default=None)}

def firewall():
    if not pathlib.Path('/usr/sbin/nft').exists():return {'state':'not installed'}
    p=subprocess.run(['/usr/sbin/nft','list','table','inet','pishield_guard'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,timeout=5,env={**os.environ,'LC_ALL':'C'})
    status='active' if p.returncode==0 else 'not active' if 'No such file or directory' in p.stderr else 'unavailable'
    return {'state':status,'persistent':pathlib.Path('/etc/pishield-guard/firewall.nft').is_file()}

def main():
    now=int(time.time());data={'updated':datetime.datetime.now().astimezone().isoformat(timespec='seconds'),'scope':'Pi host and recorded DNS only','errors':{}}
    for k,fn in [('dns',lambda:dns_check(now)),('ssh',ssh_check),('listeners',listeners),('firewall',firewall)]:
        try:data[k]=fn()
        except Exception as e:data['errors'][k]=type(e).__name__+': '+str(e)[:180]
    # Cache the package simulation for six hours; no network/apt update performed.
    try:
        p=STATE/'updates.json';cached=json.loads(p.read_text()) if p.exists() else {}
        if now-cached.get('checked',0)>21600:
            cached={'checked':now,**updates()};save(p,cached)
        data['updates']=cached
    except Exception as e:data['errors']['updates']=type(e).__name__+': '+str(e)[:180]
    try:
        old=json.loads((STATE/'baseline.json').read_text());new=inventory();d=changes(old,new);data['integrity']={'tracked':len(old),'changes':d[:100],'total_changes':len(d)}
    except Exception as e:data['errors']['integrity']=type(e).__name__+': '+str(e)[:180]
    save(STATE/'status.json',data,True)

if __name__=='__main__':
    import sys
    if sys.argv[1:]==['--baseline']:
        save(STATE/'baseline.json',inventory());print('Trusted file baseline recorded. Only rebaseline after reviewing changes.')
    elif not sys.argv[1:]:main()
    else:raise SystemExit('Unknown argument')
