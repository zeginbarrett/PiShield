#!/usr/bin/env python3
"""Private, evidence-based notifications. No automatic enforcement or raw logs."""
import collections, datetime as dt, hashlib, json, os, pathlib, re, sqlite3, tempfile, time, urllib.parse, urllib.request, sys
D=pathlib.Path('/var/lib/pishield-proactive'); C=pathlib.Path('/etc/pishield-proactive/ntfy.json'); G=pathlib.Path('/var/lib/pishield-guard/status.json'); A=pathlib.Path('/var/lib/pishield-action/status.json'); DB=pathlib.Path('/etc/pihole/pihole-FTL.db')
LEVELS={'critical':5,'high':4,'warning':3,'info':2}
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**k):return None

def read(p,default=None):
    try:
        with p.open() as f: return json.load(f)
    except FileNotFoundError:return default

def fresh(p,now,age=900):
    try:
        x=read(p,{})
        return x if abs(now-dt.datetime.fromisoformat(x['updated']).timestamp())<=age else None
    except (OSError,ValueError,TypeError,KeyError):return None

def number(x):return max(0,min(x,10**9)) if type(x) is int else 0

def config():
    c=read(C);u=c['url'];t=c['token'];p=urllib.parse.urlsplit(u)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment or not re.fullmatch(r'/[A-Za-z0-9_-]{1,100}',p.path) or not re.fullmatch(r'[A-Za-z0-9._~-]{10,512}',t):raise ValueError('Invalid ntfy configuration')
    return u,t

def deliver(c,level,title,body):
    u,t=c; req=urllib.request.Request(u,data=body.encode(),headers={'Authorization':'Bearer '+t,'Title':title,'Priority':str(LEVELS[level]),'Tags':{'critical':'rotating_light','high':'warning','warning':'warning','info':'shield'}[level],'Content-Type':'text/plain; charset=utf-8'},method='POST')
    with urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect()).open(req,timeout=12) as res:
        if not 200<=res.status<300:raise RuntimeError('Delivery not confirmed')

def save(p,x):
    fd,t=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(x,f);f.flush();os.fsync(f.fileno())
        os.replace(t,p)
    finally:
        if os.path.exists(t):os.unlink(t)

def ident(*a):return hashlib.sha256(json.dumps(a,sort_keys=True).encode()).hexdigest()
def parse_time(x):
    try:return int(dt.datetime.fromisoformat(x).timestamp())
    except (ValueError,TypeError):return 0

# Only fixed text and numeric counts leave the Pi. Never transmit raw event detail.
def event_message(e,g):
    key=str(e.get('key','')).split(':',1)[0]; g=g or {}; integ=g.get('integrity',{}); ssh=g.get('ssh',{}); dns=g.get('dns',{}); signals=dns.get('signals',[])
    if key=='integrity':
        missing=sum(x.get('change')=='missing' for x in integ.get('changes',[]))
        n=number(integ.get('total_changes'))
        if missing:return 'critical',f'{missing} tracked file(s) missing in the current snapshot. Review immediately; a legitimate update may also explain this.'
        return 'high',(f'Tracked files differ from the saved baseline ({n} currently reported). ' if integ else 'A tracked-file change was recorded; current count unavailable. ')+'Check expected updates before treating this as tampering.'
    if key=='ssh':return 'high','Repeated SSH authentication failures recorded (at least five log messages in a 15-minute sample). Not proof of a successful login.'
    if key=='dns':
        if any(number(x.get('long_labels'))>=20 or number(x.get('long_names'))>=10 for x in signals):return 'high','Repeated long DNS names: possible DNS tunneling or legitimate encoded service traffic. Investigate the reported clients.'
        return 'warning','Unusual DNS volume or failed lookups recorded. Investigate before assuming compromise.'
    fixed={'device':('warning','New network neighbor observed. Check whether it is one of your devices; randomized MAC addresses may be normal.'),'firewall':('critical','Host firewall reported inactive. Check its status; network traffic may still be protected by your router.'),'storage':('high','Storage or USB warnings recorded. Check the drive and power supply.'),'undervoltage':('warning','Undervoltage recorded since boot. Check the power supply.'),'throttling':('warning','Active throttling or thermal limit reported.'),'disk':('warning','Root filesystem at least 90% used.'),'updates':('info','Security-marked package upgrades available in the cached package list.')}
    return fixed.get(key)

ACTIONS={'DENY ADDED':'DNS deny rule added to configuration','ALLOW ADDED':'DNS allow rule added to configuration','RULE REMOVED':'DNS rule removed','EXPIRED':'Temporary DNS rule expired','FEED ADDED':'Managed threat feed added','FEED ENABLED':'Managed threat feed enabled','FEED DISABLED':'Managed threat feed disabled','MODE':'Defense mode changed','GRAVITY REBUILT':'DNS list rebuild completed','ACTION ERROR':'Defense action reported an error'}

def collect(status,g,a,hist,now,after):
    out=[]
    for e in hist.get('events',[]):
        t=e.get('time',0)
        if type(t) is not int or not after<t<=now:continue
        m=event_message(e,g)
        if m:out.append((ident('event',e.get('key'),t),t,*m))
    if a and a.get('api_ok') and not a.get('error'):
        hits=a.get('matches',[])
        if hits:
            # Existing engine reports a bounded rolling 24h sample, not successful connections.
            day=dt.datetime.fromtimestamp(now).date().isoformat()
            out.append((ident('feed',day),now,'high',f'{len(hits)} distinct domain(s) matched enabled managed threat feeds in the retained 24-hour DNS sample. A lookup does not prove a connection or compromise.'))
    if a:
        for e in a.get('log',[]):
            t=parse_time(e.get('time')); action=e.get('action')
            if not after<t<=now or action not in ACTIONS:continue
            out.append((ident('action',t,action,e.get('detail')),t,'warning' if action=='ACTION ERROR' else 'info',ACTIONS[action]+'. Configuration changes are not proof of blocked attacks.'))
    return out

def dns_totals(now):
    try:
        with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True,timeout=3) as c:
            c.execute('PRAGMA query_only=ON'); deadline=time.monotonic()+5;c.set_progress_handler(lambda:int(time.monotonic()>deadline),10000)
            rows=c.execute('SELECT status,count(*) FROM queries WHERE timestamp>? AND timestamp<=? GROUP BY status',(now-86400,now)).fetchall()
        # Explicit subset used elsewhere in PiShield: local gravity/exact/regex denials; not attacks.
        return sum(n for _,n in rows),sum(n for s,n in rows if s in (1,4,5,9,10,11))
    except (OSError,sqlite3.Error):return None

def daily(status,g,a,hist,now):
    counts=collections.Counter();
    for e in hist.get('events',[]):
        if now-86400<e.get('time',0)<=now:
            m=event_message(e,g)
            if m:counts[m[0]]+=1
    lines=['Last 24 hours (recorded events): '+', '.join(f'{k} {counts[k]}' for k in LEVELS)+'.']
    d=dns_totals(now)
    lines.append(f'DNS requests: {d[0]:,}; local-list denials (subset): {d[1]:,}.' if d is not None else 'DNS totals unavailable.')
    if a and a.get('api_ok') and not a.get('error'):lines.append(f'Managed threat-feed domain matches (bounded sample): {len(a.get("matches",[]))}.')
    else:lines.append('Threat-feed status unavailable.')
    if a:lines.append(f'Defense action log entries: {sum(now-86400<parse_time(x.get("time"))<=now for x in a.get("log",[]) if x.get("action") in ACTIONS)} (includes configuration changes).')
    if g:lines.append('Host firewall: '+({'active':'active','not active':'inactive'}.get(g.get('firewall',{}).get('state'),'unknown'))+'.')
    else:lines.append('Host checks unavailable or stale.')
    if status:
        p=status.get('power',{});s=status.get('storage',{}); lines.append('Power: '+('warning recorded' if p.get('undervoltage') or p.get('previous_undervoltage') or p.get('throttled') else 'no reported undervoltage/throttling' if p else 'unknown')+'.')
        if isinstance(s.get('root_used_percent'),(int,float)):lines.append(f'Root storage used: {s["root_used_percent"]:.1f}%.')
        if status.get('errors'):lines.append('Some monitoring checks were unavailable.')
    else:lines.append('Proactive checks unavailable or stale.')
    return '\n'.join(lines)+'\nDNS denials and warning counts are not confirmed attacks.'

def main():
    if not C.exists():return
    c=config();now=int(time.time())
    if sys.argv[1:]==['--test']:deliver(c,'info','PiShield | Test','Private notification delivery is working.');return
    if sys.argv[1:]:raise ValueError('Unknown argument')
    path=D/'notifications-v121.json';state=read(path,None)
    if state is None:
        old=read(D/'notified.json',{}) or {};state={'since':max(now-900,min(now,old.get('through',now-900))),'sent':{},'daily':''}
        save(path,state)
    state['sent']={k:v for k,v in state.get('sent',{}).items() if v>now-2*86400}
    after=max(now-86400,state['since']);status=fresh(D/'status.json',now);g=fresh(G,now);a=fresh(A,now);hist=read(D/'history.json',{}) or {}
    events=collect(status,g,a,hist,now,after);groups=collections.defaultdict(dict)
    for k,t,level,msg in events:
        if k not in state['sent']:groups[level][k]=msg
    for level in LEVELS:
        group=groups[level]
        if not group:continue
        messages=collections.Counter(group.values());lines=[(f'{n} x ' if n>1 else '')+m for m,n in messages.items()];body='\n'.join(lines[:12]);
        if len(lines)>12:body+=f'\n{len(lines)-12} additional categories; see dashboard.'
        deliver(c,level,'PiShield | '+level.upper(),body+'\nReview your private dashboard.');state['sent'].update({k:now for k in group});save(path,state)
    local=dt.datetime.fromtimestamp(now);day=local.date().isoformat()
    if local.hour>=8 and state.get('daily')!=day:
        deliver(c,'info','PiShield | Daily security report',daily(status,g,a,hist,now));state['daily']=day;save(path,state)
    save(path,state)
if __name__=='__main__':
    try:main()
    except Exception as e:raise SystemExit('Notification failed: '+type(e).__name__)
