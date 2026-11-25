#!/usr/bin/env python3
"""Local, bounded, read-only exact gravity matches. No attribution of causality."""
import collections, grp, json, os, pathlib, sqlite3, tempfile, time
D=pathlib.Path('/var/lib/pishield-privacy'); DNS=pathlib.Path('/etc/pihole/pihole-FTL.db'); GRAV=pathlib.Path('/etc/pihole/gravity.db'); CATALOG=pathlib.Path(__file__).with_name('catalog.json')
def connection(p):
    c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=3);c.execute('PRAGMA query_only=ON');deadline=time.monotonic()+12;c.set_progress_handler(lambda:int(time.monotonic()>deadline),10000);return c

def collect(now, dns=DNS, gravity=GRAV, catalog=None):
    catalog=catalog or json.loads(CATALOG.read_text()); urls={x[3]:x[0] for x in catalog}
    with connection(dns) as c:
        # FTL status 1 = blocked by gravity, exact queried name only; CNAME/regex excluded.
        rows=c.execute('SELECT domain FROM queries WHERE timestamp BETWEEN ? AND ? AND status=1 ORDER BY timestamp DESC LIMIT 20001',(now-86400,now)).fetchall()
    counts=collections.Counter(str(x[0]).lower().rstrip('.') for x in rows[:20000]);out={};
    with connection(gravity) as g:
        ad={i:urls[a] for i,a in g.execute('SELECT id,address FROM adlist WHERE enabled=1 AND type=0') if a in urls};out={v:0 for v in ad.values()};names=list(counts)
        if ad:
            for start in range(0,len(names),400):
                chunk=names[start:start+400];sql='SELECT DISTINCT domain,adlist_id FROM gravity WHERE adlist_id IN ('+','.join('?'*len(ad))+') AND domain IN ('+','.join('?'*len(chunk))+')'
                for domain,aid in g.execute(sql,[*ad,*chunk]):out[ad[aid]]+=counts[domain]
    return {'updated':now,'sample':min(20000,len(rows)),'capped':len(rows)>20000,'counts':out}
def main():
    try:data=collect(int(time.time()))
    except (OSError,sqlite3.Error,ValueError) as e:data={'error':'Counter unavailable: '+type(e).__name__}
    fd,t=tempfile.mkstemp(dir=D)
    try:
        with os.fdopen(fd,'w') as f:json.dump(data,f);f.flush();os.fsync(f.fileno())
        os.chown(t,0,grp.getgrnam('pihole').gr_gid);os.chmod(t,0o640);os.replace(t,D/'status.json')
    finally:
        if os.path.exists(t):os.unlink(t)
if __name__=='__main__':main()
