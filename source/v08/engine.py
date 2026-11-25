#!/usr/bin/env python3
import collections, contextlib, datetime, fcntl, grp, json, os, pathlib, re, sqlite3, subprocess, tempfile, time, urllib.request, urllib.parse
STATE=pathlib.Path('/var/lib/pishield-action'); GRAV=pathlib.Path('/etc/pihole/gravity.db'); DNS=pathlib.Path('/etc/pihole/pihole-FTL.db')
FEEDS={'mini':'https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/tif.mini-onlydomains.txt','medium':'https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/tif.medium-onlydomains.txt'}
TAG='PiShield Sentinel v0.8 managed'; PERIOD=8*3600

def now():return int(time.time())
def stamp(t):return datetime.datetime.fromtimestamp(t).astimezone().isoformat(timespec='seconds') if t else None
def load(p,default):
    try:return json.loads(p.read_text())
    except (OSError,ValueError):return default

def save(p,value,shared=False):
    fd,tmp=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f,ensure_ascii=True)
        if shared:os.chown(tmp,0,grp.getgrnam('pihole').gr_gid);os.chmod(tmp,0o640)
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def domain(s):
    s=s.lower().rstrip('.')
    if len(s)>253 or not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?',s):raise ValueError('Enter an exact DNS hostname, not a URL, IP, wildcard or regex')
    if s.endswith(('.local','.localhost','.lan','.home.arpa','.invalid','.test')):raise ValueError('Local and reserved names are not supported')
    return s

class API:
    def __init__(self):self.sid=None;self.csrf=None
    def call(self,method,path,data=None):
        headers={'Accept':'application/json'}
        if self.sid:headers['X-FTL-SID']=self.sid;headers['X-FTL-CSRF']=self.csrf or ''
        if data is not None:headers['Content-Type']='application/json'
        req=urllib.request.Request('http://127.0.0.1/api'+path,data=None if data is None else json.dumps(data).encode(),headers=headers,method=method)
        # Do not follow redirects carrying local API credentials.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        with opener.open(req,timeout=12) as r:
            b=r.read(8_000_001)
            if len(b)>8_000_000:raise ValueError('Oversize API response')
            return json.loads(b) if b else {}
    def __enter__(self):
        pw=pathlib.Path('/etc/pihole/cli_pw').read_text().strip()
        s=self.call('POST','/auth',{'password':pw}).get('session',{})
        self.sid=s.get('sid');self.csrf=s.get('csrf')
        if not self.sid or not s.get('valid'):raise RuntimeError('Native API authentication failed; check CLI password setting')
        return self
    def __exit__(self,*args):
        if self.sid:
            with contextlib.suppress(Exception):self.call('DELETE','/auth')
    def lists(self):return self.call('GET','/lists?type=block')['lists']
    def rules(self,kind):return self.call('GET','/domains/'+kind+'/exact')['domains']

def owned(r):return r.get('comment')==TAG or str(r.get('comment','')).startswith(TAG+' | expires=')
def encoded(s):return urllib.parse.quote(s,safe='')
def list_path(url):return '/lists/'+encoded(url)+'?type=block'
def rule_path(kind,d):return '/domains/'+kind+'/exact/'+encoded(d)
def expiry(r):
    m=re.fullmatch(re.escape(TAG)+r' \| expires=(\d+)',str(r.get('comment','')))
    return int(m[1]) if m else None

def record(cfg,action,detail):
    cfg['log']=(cfg.get('log',[])+[{'time':stamp(now()),'action':action,'detail':detail}])[-400:]
    save(STATE/'config.json',cfg)

def native_reload():
    subprocess.run(['/usr/local/bin/pihole','reloadlists'],check=True,timeout=40,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def apply_mode(a,cfg,mode):
    wanted=FEEDS.get({'active':'mini','aggressive':'medium'}.get(mode))
    rows=a.lists(); matching={r['address']:r for r in rows if r.get('address') in FEEDS.values()}
    if wanted in matching and not owned(matching[wanted]):raise ValueError('Requested feed already exists outside PiShield ownership; existing list left unchanged')
    # Enable replacement before disabling old managed feed. Never touch existing external rules.
    if wanted:
        r=matching.get(wanted)
        if r is None:
            a.call('POST','/lists?type=block',{'address':wanted,'comment':TAG,'groups':[0],'enabled':True})
            record(cfg,'FEED ADDED',wanted)
        elif not r.get('enabled'):
            a.call('PUT',list_path(wanted),{'comment':TAG,'groups':r.get('groups',[0]),'enabled':True,'type':'block'})
            record(cfg,'FEED ENABLED',wanted)
    for url,r in matching.items():
        if url!=wanted and owned(r) and r.get('enabled'):
            a.call('PUT',list_path(url),{'comment':TAG,'groups':r.get('groups',[0]),'enabled':False,'type':'block'})
            record(cfg,'FEED DISABLED',url)
    if mode=='observe':
        for r in a.rules('deny'):
            if owned(r) and r.get('enabled'):
                a.call('DELETE',rule_path('deny',r['domain']));record(cfg,'RULE REMOVED',r['domain']+' — observation mode')
    cfg['mode']=mode;cfg['refresh_due']=bool(wanted);cfg['reload_pending']=True;save(STATE/'config.json',cfg)

def add_rule(a,cfg,kind,d,seconds=0):
    d=domain(d)
    if kind=='deny' and cfg.get('mode')=='observe':raise ValueError('Activate defense before adding a Sentinel deny rule')
    rules=a.rules(kind)
    if any(r.get('domain')==d for r in rules):raise ValueError('Exact rule already exists; unchanged')
    if kind=='deny' and any(r.get('domain')==d and r.get('enabled') for r in a.rules('allow')):raise ValueError('Existing exact allow rule takes precedence; unchanged')
    comment=TAG+(' | expires='+str(now()+seconds) if seconds else '')
    a.call('POST','/domains/'+kind+'/exact',{'domain':d,'comment':comment,'groups':[0],'enabled':True})
    if not any(r.get('domain')==d and r.get('comment')==comment for r in a.rules(kind)):raise RuntimeError('Rule creation not verified')
    cfg['reload_pending']=True;record(cfg,'ALLOW ADDED' if kind=='allow' else 'DENY ADDED',d+(' (expires '+stamp(now()+seconds)+')' if seconds else ' (manual approval)'))

def remove_rule(a,cfg,kind,d):
    d=domain(d);r=next((x for x in a.rules(kind) if x.get('domain')==d and owned(x)),None)
    if not r:raise ValueError('No PiShield-owned exact rule found; existing rules unchanged')
    a.call('DELETE',rule_path(kind,d));cfg['reload_pending']=True;record(cfg,'RULE REMOVED',kind+' '+d)

def request():
    try:
        raw=(STATE/'request').read_bytes()[:2048].decode();p=raw.split('\n')
        if len(p)==5 and p[-1]=='END' and re.fullmatch(r'[A-Za-z0-9-]{8,80}',p[0]):return p[:4]
    except (OSError,UnicodeError):pass
    return None

def act(a,cfg,action,subject,value):
    if action=='mode' and subject in ('observe','active','aggressive') and value=='yes':apply_mode(a,cfg,subject);record(cfg,'MODE',subject)
    elif action=='refresh' and subject=='now' and value=='yes':
        if cfg.get('mode')=='observe':raise ValueError('No managed feed active')
        cfg['refresh_due']=True;record(cfg,'REFRESH REQUESTED','Managed feed')
    elif action=='allow' and value=='yes':add_rule(a,cfg,'allow',subject)
    elif action=='deny' and value in ('permanent','3600','86400'):add_rule(a,cfg,'deny',subject,0 if value=='permanent' else int(value))
    elif action=='remove' and value in ('allow','deny'):remove_rule(a,cfg,value,subject)
    else:raise ValueError('Invalid request')

def gravity_refresh(cfg):
    # Native gravity rebuild retains all existing list subscriptions. Avoid shell interpolation.
    cfg['last_attempt']=now();save(STATE/'config.json',cfg)
    subprocess.run(['/usr/local/bin/pihole','-g'],check=True,timeout=240,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    cfg['refresh_due']=False;cfg['last_refresh']=now();record(cfg,'GRAVITY REBUILT','Native list rebuild completed; feed download status shown separately')

def read_db(p):
    db=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=4);db.execute('PRAGMA query_only=ON');return db

def match(rows):
    ids=[r['id'] for r in rows if r.get('enabled') and r.get('number',0)>0]
    if not ids:return [],0
    with contextlib.closing(read_db(DNS)) as d:
        q=d.execute('SELECT domain,client,status FROM queries WHERE timestamp>=? ORDER BY timestamp DESC LIMIT 20000',(now()-86400,)).fetchall()
    counts=collections.Counter(str(x[0]).lower().rstrip('.') for x in q); hits=set()
    with contextlib.closing(read_db(GRAV)) as g:
        for chunk in range(0,len(counts),400):
            names=list(counts)[chunk:chunk+400]
            if names:
                sql='SELECT DISTINCT domain FROM gravity WHERE adlist_id IN ('+','.join('?'*len(ids))+') AND domain IN ('+','.join('?'*len(names))+')'
                hits.update(x[0] for x in g.execute(sql,ids+names))
    return [{'domain':d,'queries':counts[d]} for d in sorted(hits,key=lambda d:(-counts[d],d))[:100]],len(q)

def run():
    cfg=load(STATE/'config.json',{'mode':'observe','log':[]}); error=None; rows=[]; rules=[]; hits=[]; scanned=0; blocking=None; api_ok=False
    req=request()
    try:
        with API() as a:
            api_ok=True
            # Process explicit requests once; persist outcome before publishing.
            if req and req[0]!=cfg.get('last_action',{}).get('id'):
                rid,action,subject,value=req
                try:act(a,cfg,action,subject,value);result='Request applied to native configuration'
                except Exception as e:result='Failed: '+str(e)[:240];record(cfg,'ACTION ERROR',result)
                cfg['last_action']={'id':rid,'message':result};save(STATE/'config.json',cfg)
            for r in a.rules('deny'):
                exp=expiry(r)
                if exp and exp<=now():remove_rule(a,cfg,'deny',r['domain']);record(cfg,'EXPIRED',r['domain'])
            rows=[r for r in a.lists() if owned(r) and r.get('address') in FEEDS.values()]
            for k in ('allow','deny'):
                rules.extend({'domain':r['domain'],'kind':k,'enabled':r.get('enabled'),'expires':stamp(expiry(r))} for r in a.rules(k) if owned(r))
            blocking=a.call('GET','/dns/blocking').get('blocking')
        if cfg.get('reload_pending'):
            native_reload();cfg['reload_pending']=False;save(STATE/'config.json',cfg)
        if any(r.get('enabled') for r in rows) and (cfg.get('refresh_due') or now()-cfg.get('last_refresh',0)>=PERIOD) and now()-cfg.get('last_attempt',0)>=300:
            gravity_refresh(cfg)
            with API() as a:rows=[r for r in a.lists() if owned(r) and r.get('address') in FEEDS.values()]
        hits,scanned=match(rows)
    except Exception as e:error=type(e).__name__+': '+str(e)[:240]
    snapshot={'updated':stamp(now()),'mode':cfg.get('mode','observe'),'api_ok':api_ok,'blocking':blocking,'feeds':[{k:r.get(k) for k in ('address','enabled','number','status','date_updated','groups')} for r in rows],'rules':rules,'matches':hits,'scanned':scanned,'last_refresh':stamp(cfg.get('last_refresh')),'last_attempt':stamp(cfg.get('last_attempt')),'last_action':cfg.get('last_action',{}),'log':list(reversed(cfg.get('log',[]))),'error':error,'reload_pending':cfg.get('reload_pending',False)}
    save(STATE/'status.json',snapshot,True)
    print('PiShield action engine:',snapshot['mode'], 'managed feeds',len(rows),'matches',len(hits),'error',error,flush=True)

if __name__=='__main__':
    with (STATE/'lock').open('a') as f:
        try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit(0)
        run()
