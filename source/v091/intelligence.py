"""Local defensive evidence enrichment; never execute model output."""
import collections, contextlib, json, pathlib, sqlite3, statistics, time
GRAV=pathlib.Path('/etc/pihole/gravity.db')
ACTION=pathlib.Path('/var/lib/pishield-action/status.json')
URLS={'https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/tif.mini-onlydomains.txt','https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/tif.medium-onlydomains.txt'}
TAG='PiShield Sentinel v0.8 managed'

def enrich(db, rows, report, now, event):
    counts=collections.Counter(str(r[1]).lower().rstrip('.') for r in rows)
    baseline=[]
    for client,n in collections.Counter(str(r[2]) for r in rows).most_common(20):
        prior=[r[0] for r in db.execute('SELECT n FROM counts WHERE client=? AND t>=? AND t<? ORDER BY t DESC LIMIT 672',(client,now-7*86400,now-60))]
        median=statistics.median(prior) if prior else None
        baseline.append({'client':client,'queries':n,'prior_windows':len(prior),'median':median,'elevated':bool(len(prior)>=12 and not report['capped'] and n>=50 and n>=3*max(1,median))})
    report['learned_baselines']=baseline
    report['feed_verification']={'status':'unavailable','matches':[],'scope':'Exact matches in enabled PiShield-managed gravity lists; not independent confirmation of infection.'}
    try:
        with contextlib.closing(sqlite3.connect(GRAV.as_uri()+'?mode=ro',uri=True,timeout=5)) as g:
            g.execute('PRAGMA query_only=ON')
            ids=[x[0] for x in g.execute('SELECT id,address,comment FROM adlist WHERE enabled=1') if x[1] in URLS and x[2]==TAG]
            if ids:
                names=list(counts); hits=collections.defaultdict(set)
                for i in range(0,len(names),300):
                    chunk=names[i:i+300]
                    sql='SELECT domain,adlist_id FROM gravity WHERE adlist_id IN ('+','.join('?'*len(ids))+') AND domain IN ('+','.join('?'*len(chunk))+')'
                    for d,idx in g.execute(sql,ids+chunk):hits[d].add(idx)
                matches=[{'domain':d,'queries':counts[d],'list_ids':sorted(hits[d])} for d in sorted(hits,key=lambda x:(-counts[x],x))[:50]]
                report['feed_verification'].update(status='matched enabled managed lists',matches=matches,enabled_lists=len(ids))
                for m in matches[:20]:event('MANAGED FEED MATCH',m['domain'],str(m['queries'])+' recorded queries; exact feed match; verify native blocking and group membership')
            else:report['feed_verification']['status']='no enabled PiShield-managed feeds'
    except Exception as e:report['feed_verification']['status']='verification error: '+str(e)[:150]
    try:
        a=json.loads(ACTION.read_text());report['defense_state']={k:a.get(k) for k in ('mode','blocking','updated','last_refresh','error','reload_pending')}
    except (OSError,ValueError):report['defense_state']={'mode':'unknown'}
    report['recommendations']=[{'domain':m['domain'],'reason':'Exact managed threat feed match; verify enforcement in Defense Control.','action':'Review existing protection; do not create duplicate rules.'} for m in report['feed_verification']['matches'][:20]]
    for b in baseline:
        if b['elevated']:report['recommendations'].append({'client':b['client'],'reason':'Query count elevated relative to learned median.','action':'Investigate client in query log; no automatic block.'})
    return report
