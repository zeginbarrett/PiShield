#!/usr/bin/env python3
"""Local monitoring; no traffic capture, firewall changes or remote requests."""
import collections, datetime, grp, hashlib, json, os, pathlib, re, subprocess, tempfile, time
D=pathlib.Path('/var/lib/pishield-proactive'); GUARD=pathlib.Path('/var/lib/pishield-guard/status.json')
def command(args,timeout=8):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=timeout,env={**os.environ,'LC_ALL':'C'})
    if p.returncode: raise RuntimeError(f'{args[0]} exit {p.returncode}')
    return p.stdout

def read(path,default):
    try:return json.loads(path.read_text())
    except (OSError,ValueError):return default

def write(path,obj,shared=False):
    fd,t=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(obj,f,ensure_ascii=True);f.flush();os.fsync(f.fileno())
        if shared:os.chown(t,0,grp.getgrnam('pihole').gr_gid);os.chmod(t,0o640)
        os.replace(t,path)
    finally:
        if os.path.exists(t):os.unlink(t)

def power():
    s=command(['vcgencmd','get_throttled']).strip();m=re.fullmatch(r'throttled=(0x[0-9a-fA-F]+)',s)
    if not m:raise ValueError('Unexpected firmware response')
    x=int(m[1],16)
    return {'raw':m[1],'undervoltage':bool(x&1),'throttled':bool(x&4),'previous_undervoltage':bool(x&(1<<16)),'previous_throttling':bool(x&(1<<18)),'temperature_limit':bool(x&8)}

def storage():
    pattern=re.compile(r'\b(?:I/O error|Buffer I/O|EXT4-fs error|FAT-fs.*error|blk_update_request|USB disconnect|reset (?:high|super|full)-speed USB|uas_eh_|read-only filesystem)\b',re.I)
    lines=command(['journalctl','-k','--since','15 min ago','-n','3000','--no-pager','-o','cat'],12).splitlines()
    matches=[l[:220] for l in lines if pattern.search(l)]
    v=os.statvfs('/');total=v.f_blocks*v.f_frsize;avail=v.f_bavail*v.f_frsize
    return {'messages':len(matches),'recent':matches[-12:],'root_free_bytes':avail,'root_used_percent':round(100*(1-avail/total),1) if total else None,'possibly_capped':len(lines)>=3000}

def neighbors(rows):
    found={}
    for r in rows:
        mac=str(r.get('lladdr','')).lower();st=r.get('state',[]);st=[st] if isinstance(st,str) else st
        if r.get('dev') in ('lo','tailscale0') or not re.fullmatch(r'(?:[0-9a-f]{2}:){5}[0-9a-f]{2}',mac) or not set(st)&{'REACHABLE','STALE','DELAY','PROBE','PERMANENT'}:continue
        if int(mac[:2],16)&1 or mac=='00:00:00:00:00:00':continue
        found.setdefault(mac,{'mac':mac,'addresses':[],'interface':str(r.get('dev',''))})['addresses'].append(str(r.get('dst',''))[:80])
    return list(found.values())[:500]

def devices(now):
    rows=neighbors(json.loads(command(['ip','-j','neigh','show'])));old=read(D/'devices.json',{});known=old.get('known',{});initialized=bool(old.get('initialized'));new=[]
    for r in rows:
        mac=r['mac']
        if initialized and mac not in known:new.append(r)
        known[mac]=now
    known=dict(sorted(known.items(),key=lambda x:x[1],reverse=True)[:2000]);write(D/'devices.json',{'initialized':initialized or bool(rows),'known':known})
    return {'observed':rows,'new':new,'known_count':len(known),'baseline_ready':initialized or bool(rows)}

def audit():
    routes=json.loads(command(['ip','-j','-6','route','show','default']));addrs=json.loads(command(['ip','-j','-6','addr','show','scope','global']));interfaces=[]
    for r in addrs:
        if r.get('addr_info'):interfaces.append({'interface':r.get('ifname'),'addresses':[a.get('local') for a in r['addr_info'] if a.get('local')]})
    return {'default_route':bool(routes),'interfaces':interfaces,'note':'IPv6 addresses do not prove internet exposure or client DNS coverage.'}

def enabled(unit):
    p=subprocess.run(['systemctl','is-enabled',unit],capture_output=True,text=True,timeout=5);return p.stdout.strip()=='enabled'
def controls():
    result={'ssh_protection':'not verified','auto_updates_configured':pathlib.Path('/etc/apt/apt.conf.d/99-pishield-security').is_file(),'apt_daily_upgrade_enabled':enabled('apt-daily-upgrade.timer'),'alerts_configured':pathlib.Path('/etc/pishield-proactive/ntfy.json').is_file()}
    try:
        s=command(['fail2ban-client','status','sshd']);result['ssh_protection']='sshd jail active';m=re.search(r'Currently banned:\s*(\d+)',s);result['ssh_banned']=int(m[1]) if m else None
    except Exception:pass
    return result

def candidates(data):
    out=[]
    def add(key,title,detail=''):out.append({'key':key,'title':title,'detail':detail})
    p=data.get('power',{});s=data.get('storage',{});g=data.get('guard',{});ssh=g.get('ssh',{});integrity=g.get('integrity',{})
    if p.get('undervoltage') or p.get('previous_undervoltage'):add('undervoltage','Power supply warning','Undervoltage recorded since boot')
    if p.get('throttled') or p.get('temperature_limit'):add('throttling','Performance throttling','Firmware reports active throttling or thermal limit')
    if s.get('messages',0):add('storage','Storage / USB warning',str(s['messages'])+' matching kernel messages in 15 minutes')
    if (s.get('root_used_percent') or 0)>=90:add('disk','Root filesystem nearly full',str(s['root_used_percent'])+'% used')
    if ssh.get('failure_messages',0)>=5:add('ssh','Repeated SSH authentication failures',str(ssh['failure_messages'])+' log messages in 15 minutes')
    if integrity.get('total_changes',0):add('integrity','Tracked files changed',str(integrity['total_changes'])+' files differ from saved baseline')
    if g.get('dns',{}).get('signals'):add('dns','DNS activity warning','Review Host security for the recorded indicators')
    if g.get('updates',{}).get('security_marked',0):add('updates','Security-marked upgrades available',str(g['updates']['security_marked'])+' packages in cached simulation')
    if g.get('firewall',{}).get('state')=='not active':add('firewall','Host firewall not active','Check your firewall configuration')
    for d in data.get('devices',{}).get('new',[]):add('device:'+d['mac'],'New observed neighbor',d['mac']+' · '+', '.join(d['addresses']))
    return out

def record(old,active,now):
    history=[e for e in old.get('events',[]) if e.get('time',0)>now-30*86400];last={e['key']:e['time'] for e in history};prior=set(old.get('active',[]));added=[]
    for e in active:
        k=e['key']
        if k not in prior or now-last.get(k,0)>=86400:
            x={**e,'time':now};history.append(x);added.append(x)
    return {'events':history[-500:],'active':[e['key'] for e in active]},added

def main():
    now=int(time.time());data={'updated':datetime.datetime.now().astimezone().isoformat(timespec='seconds'),'errors':{}}
    for k,fn in [('power',power),('storage',storage),('devices',lambda:devices(now)),('ipv6',audit),('controls',controls)]:
        try:data[k]=fn()
        except Exception as e:data['errors'][k]=type(e).__name__+': '+str(e)[:140]
    g=read(GUARD,{})
    try:
        if abs(now-datetime.datetime.fromisoformat(g['updated']).timestamp())<700:data['guard']=g
        else:raise ValueError('stale')
    except (ValueError,KeyError,TypeError):data['errors']['guard']='Host security snapshot stale or unavailable'
    history,added=record(read(D/'history.json',{}),candidates(data),now);write(D/'history.json',history)
    data['events']=history['events'][-100:][::-1];data['last24h']=dict(collections.Counter(e['title'] for e in history['events'] if e['time']>=now-86400));data.pop('guard',None)
    write(D/'status.json',data,True)
if __name__=='__main__':main()
