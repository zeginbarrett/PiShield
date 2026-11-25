#!/usr/bin/env python3
import collections, datetime, hashlib, ipaddress, json, os, pathlib, re, sqlite3, tempfile, time, grp
STATE=pathlib.Path('/var/lib/pishield-defense')
SENT=pathlib.Path('/var/lib/pishield-sentinel/sentinel.sqlite3')
DNS=pathlib.Path('/etc/pihole/pihole-FTL.db')
FEED=SENT.parent/'threat-domains.txt'
AI=pathlib.Path('/var/lib/pishield-ai/status.json')
MAC=re.compile(r'(?:[0-9a-f]{2}:){5}[0-9a-f]{2}')
DOMAIN=re.compile(r'(?=.{1,253}$)[a-z0-9_-]+(?:\.[a-z0-9_-]+)+')

def read(p,default):
    try:return json.loads(p.read_text())
    except (OSError,ValueError):return default

def save(p,obj,shared=False):
    fd,tmp=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(obj,f,ensure_ascii=True)
        if shared:os.chown(tmp,0,grp.getgrnam('pihole').gr_gid);os.chmod(tmp,0o640)
        else:os.chmod(tmp,0o600)
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def stamp(t):return datetime.datetime.fromtimestamp(t).astimezone().isoformat(timespec='seconds') if t else None

def connect(path):
    db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=5);db.execute('PRAGMA query_only=ON');return db

def feed_domains():
    if not FEED.exists():return set(), 'No administrator threat list configured'
    if FEED.stat().st_size>25_000_000:raise ValueError('Threat list exceeds 25 MB')
    items=set()
    with FEED.open() as f:
        for line in f:
            s=line.split('#',1)[0].strip().lower().rstrip('.')
            if DOMAIN.fullmatch(s):items.add(s)
    return items, f'{len(items):,} administrator-supplied exact domain entries'

def collect(now=None):
    now=int(time.time()) if now is None else now
    trust=read(STATE/'trust.json',{}); ack=read(STATE/'ack.json',{}); errors=[]
    cutoff=now-86400; devices=[]; events=[]; runs=[]; matching=[]; clients=[]; total=0; newest=None; scanned=0; db_ok=False; sent_ok=False; feed_ok=False
    try:feed,feed_status=feed_domains();feed_ok=bool(feed)
    except (OSError,ValueError) as e:feed=set();feed_status='Unavailable';errors.append('Threat list: '+str(e))
    try:
        with connect(DNS) as db:
            db.execute('BEGIN');total=db.execute('SELECT count(*) FROM queries WHERE timestamp BETWEEN ? AND ?',(cutoff,now)).fetchone()[0]
            rows=db.execute('SELECT timestamp,domain,client,status FROM queries WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC LIMIT 50000',(cutoff,now)).fetchall()
            newest=db.execute('SELECT max(timestamp) FROM queries').fetchone()[0]; scanned=len(rows)
        hits=collections.defaultdict(lambda:{'count':0,'clients':collections.Counter(),'last':0,'statuses':collections.Counter()}); cc=collections.Counter()
        for t,d,c,s in rows:
            d=str(d).lower().rstrip('.');c=str(c);cc[c]+=1
            if d in feed:
                h=hits[d];h['count']+=1;h['clients'][c]+=1;h['last']=max(h['last'],t);h['statuses'][str(s)]+=1
        for d,h in sorted(hits.items(),key=lambda x:-x[1]['count'])[:100]:
            matching.append({'domain':d,'count':h['count'],'clients':h['clients'].most_common(20),'last':stamp(h['last']),'statuses':dict(h['statuses'])})
        clients=cc.most_common(50);db_ok=True
    except (sqlite3.Error,OSError,ValueError,TypeError) as e:errors.append('DNS history: '+str(e))
    try:
        with connect(SENT) as db:
            raw=db.execute('SELECT t,kind,subject,detail FROM events WHERE t>=? ORDER BY t DESC LIMIT 250',(now-30*86400,)).fetchall()
            for t,k,s,d in raw:
                eid=hashlib.sha256(json.dumps([t,k,s,d]).encode()).hexdigest()[:24]
                events.append({'id':eid,'time':stamp(t),'t':t,'kind':k,'subject':s,'detail':d,'acknowledged':eid in ack})
            for mac,ip,first,last in db.execute('SELECT mac,ip,first_seen,last_seen FROM devices ORDER BY last_seen DESC LIMIT 500'):
                if not MAC.fullmatch(mac):continue
                devices.append({'mac':mac,'ip':ip,'first':stamp(first),'last':stamp(last),'trust':trust.get(mac,'unknown')})
            for t,r,s in db.execute('SELECT t,report,ai_status FROM runs ORDER BY t DESC LIMIT 32'):
                try: n=json.loads(r).get('queries')
                except (ValueError,AttributeError):n=None
                runs.append({'time':stamp(t),'t':t,'status':s,'queries':n})
        sent_ok=True
    except (sqlite3.Error,OSError,ValueError,TypeError) as e:errors.append('Sentinel history: '+str(e))
    # A score is a review-priority heuristic, not probability of compromise.
    recent=[e for e in events if e['t']>=cutoff];rate={e['subject'] for e in recent if e['kind']=='RATE CHANGE'}
    new={e['subject'] for e in recent if e['kind']=='NEW NEIGHBOR'}
    factors=[{'label':'Exact administrator threat-list matches (distinct domains)','count':len(matching),'points':min(60,20*len(matching))},{'label':'Rate changes (distinct reported clients)','count':len(rate),'points':min(25,5*len(rate))},{'label':'New neighbor observations (distinct addresses)','count':len(new),'points':min(15,3*len(new))}]
    valid=db_ok and sent_ok and bool(newest) and now-newest<3600 and bool(runs) and now-runs[0]['t']<3600
    score=sum(f['points'] for f in factors) if valid else None
    ai=read(AI,{});job=ai.get('job') or {}; updated=ai.get('updated');fresh=False
    try:fresh=abs(now-datetime.datetime.fromisoformat(updated).timestamp())<300
    except (ValueError,TypeError):pass
    return {'updated':stamp(now),'score':score,'factors':factors,'feed_status':feed_status,'feed_entries':len(feed),'feed_configured':feed_ok,'dns_ok':db_ok,'sentinel_ok':sent_ok,'matching_rows':total,'scanned':scanned,'latest_record':stamp(newest),'capped':total>scanned,'matches':matching,'events':events,'devices':devices,'clients':clients,'runs':runs,'ai':{'fresh':fresh,'models':ai.get('models',[]) if fresh else [],'model':ai.get('selected'),'job':job.get('phase'),'error':ai.get('connection_error'),'updated':updated},'errors':errors,'note':'Last 24 hours of stored DNS data, newest 50,000 records. The score measures review priority, not compromise probability. Ordinary ad blocks and failed lookups do not contribute. Router forwarding can combine clients; neighbor observations do not prove current connectivity. No automatic blocking.'}

def process():
    try:raw=(STATE/'request').read_bytes()[:1024].decode('utf-8')
    except (OSError,UnicodeError):return
    parts=raw.split('\n')
    if len(parts)!=5 or parts[-1]!='END':return
    rid,action,subject,value,_=parts
    if not re.fullmatch(r'[a-zA-Z0-9-]{8,80}',rid) or rid==read(STATE/'last.json',{}).get('id'):return
    msg='Invalid action or unknown subject'; snap=read(STATE/'status.json',{})
    if action=='trust' and MAC.fullmatch(subject) and value in ('trusted','unknown','restricted') and any(x['mac']==subject for x in snap.get('devices',[])):
        d=read(STATE/'trust.json',{});d[subject]=value;save(STATE/'trust.json',d);msg='Device trust label saved (label only; not a firewall rule)'
    elif action=='ack' and re.fullmatch(r'[a-f0-9]{24}',subject) and value in ('yes','no') and any(x['id']==subject for x in snap.get('events',[])):
        d=read(STATE/'ack.json',{});d={k:v for k,v in d.items() if isinstance(v,(float,int)) and v>time.time()-30*86400}
        if value=='yes':d[subject]=time.time()
        else:d.pop(subject,None)
        save(STATE/'ack.json',d);msg='Alert review state saved'
    save(STATE/'last.json',{'id':rid,'message':msg})

def main():
    process(); result=collect();result['last_action']=read(STATE/'last.json',{});save(STATE/'status.json',result,True)
    print('Active Defense:',result['scanned'],'recorded queries;',len(result['events']),'stored signals; score',result['score'],flush=True)
if __name__=='__main__':main()
