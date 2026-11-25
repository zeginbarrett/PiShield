#!/usr/bin/env python3
"""Read-only bounded device and system metrics. No probes or routing changes."""
import collections, datetime, grp, ipaddress, json, os, pathlib, sqlite3, subprocess, tempfile, time
D=pathlib.Path('/var/lib/pishield-intelligence'); DB=pathlib.Path('/etc/pihole/pihole-FTL.db')
LOCAL={1,4,5,9,10,11}; EXTERNAL={6,7,8,18}; CAP=30000
CATEGORIES=[('Viewing recognition / ACR',('samba.tv','samsungacr.com')),('Sony measurement',('ndmdhs.com','ssm1.internet.sony.tv','ssm2.internet.sony.tv','ssm3.internet.sony.tv','social.biv.sony.tv')),('Advertising',('doubleclick.net','googlesyndication.com','googleadservices.com','samsungads.com','lgsmartad.com','amazon-adsystem.com')),('Analytics / telemetry',('google-analytics.com','app-measurement.com','analytics.google.com','logs.roku.com','device-metrics-us.amazon.com','vortex.data.microsoft.com','telemetry.microsoft.com'))]
UNITS=['pihole-FTL.service','pishield-guard.timer','pishield-proactive.timer','pishield-proactive-notify.timer','pishield-privacy.timer','pishield-live.service','pishield-sentinel.timer','pishield-action.timer','tailscaled.service','ntfy.service','ssh.service','fail2ban.service','apt-daily-upgrade.timer']
def command(args,timeout=4):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=timeout,env={**os.environ,'LC_ALL':'C'});return p.stdout.strip() if p.returncode==0 else ''
def ip(value):
    try:return str(ipaddress.ip_address(value))
    except (ValueError,TypeError):return None
def classify(d):
    for label,suffixes in CATEGORIES:
        if any(d==s or d.endswith('.'+s) for s in suffixes):return label
    return None
def db_rows(now,db=DB):
    with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True,timeout=3) as c:
        c.execute('PRAGMA query_only=ON');deadline=time.monotonic()+7;c.set_progress_handler(lambda:int(time.monotonic()>deadline),10000)
        rows=c.execute('SELECT timestamp,client,domain,status FROM queries WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC LIMIT ?', (now-86400,now,CAP+1)).fetchall()
    return rows[:CAP],len(rows)>CAP

def summarize(rows,now,capped=False):
    clients={}; oldest=min((r[0] for r in rows),default=None)
    for stamp,client,domain,status in rows:
        address=ip(client)
        if address is None:continue
        if address not in clients:
            if len(clients)>=500:continue
            clients[address]={'ip':address,'queries':0,'local_blocks':0,'external_blocks':0,'tracking':0,'tracking_local_blocks':0,'last':0,'recent':0,'previous':0,'categories':collections.Counter(),'domains':collections.Counter()}
        x=clients[address];x['queries']+=1;x['last']=max(x['last'],stamp);x['local_blocks']+=status in LOCAL;x['external_blocks']+=status in EXTERNAL
        if stamp>now-3600:x['recent']+=1
        elif stamp>now-7*3600:x['previous']+=1
        d=str(domain).lower().rstrip('.');cat=classify(d)
        if cat:
            x['tracking']+=1;x['tracking_local_blocks']+=status in LOCAL;x['categories'][cat]+=1;x['domains'][d[:253]]+=1
    for x in clients.values():
        x['top_tracking']=[{'domain':d,'requests':n} for d,n in x.pop('domains').most_common(12)]
        x['coverage']=round(100*x['tracking_local_blocks']/x['tracking']) if x['tracking'] else None
        x['anomaly']=not capped and oldest is not None and oldest<=now-7*3600 and x['previous']>=30 and x['recent']>=max(100,4*x['previous']/6)
    return {'sample':len(rows),'capped':capped,'oldest':oldest,'devices':sorted(clients.values(),key=lambda x:-x['queries'])}
def read_json(p):
    try:return json.loads(pathlib.Path(p).read_text())
    except (OSError,ValueError):return {}
def collect(now):
    result={'updated':now,'errors':{},'services':{},'network':{},'health':{},'dns':None}
    try:
        rows,capped=db_rows(now);result['dns']=summarize(rows,now,capped)
    except (OSError,sqlite3.Error,ValueError) as e:result['errors']['dns']=type(e).__name__
    for unit in UNITS:
        try:
            # is-active returns nonzero for inactive, but stdout still identifies state.
            p=subprocess.run(['systemctl','is-active',unit],capture_output=True,text=True,timeout=2);result['services'][unit]=p.stdout.strip() or 'unknown'
        except (OSError,subprocess.TimeoutExpired):result['services'][unit]='unknown'
    try:
        routes=json.loads(command(['ip','-j','route','show','default']) or '[]');addrs=json.loads(command(['ip','-j','address','show']) or '[]');neighbors=json.loads(command(['ip','-j','neigh','show']) or '[]')
        result['network']={'routes':[{'gateway':r.get('gateway'),'interface':r.get('dev')} for r in routes][:10],'interfaces':[{'name':a['ifname'],'state':a.get('operstate'),'addresses':[b.get('local') for b in a.get('addr_info',[]) if b.get('scope')=='global']} for a in addrs][:30],'neighbors':[{'ip':r.get('dst'),'mac':r.get('lladdr'),'interface':r.get('dev'),'state':r.get('state')} for r in neighbors if ip(r.get('dst')) and r.get('lladdr')][:300],'ipv4_forwarding':pathlib.Path('/proc/sys/net/ipv4/ip_forward').read_text().strip()=='1'}
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired) as e:result['errors']['network']=type(e).__name__
    # Only summarize non-Pi DNS destinations visible in the existing short-lived packet buffer.
    live=read_json('/run/pishield-live/status.json');local={a for i in result['network'].get('interfaces',[]) for a in i.get('addresses',[]) if a};neighbors={n['ip'] for n in result['network'].get('neighbors',[])};hints=collections.Counter()
    if isinstance(live.get('updated'),(int,float)) and abs(now-live['updated'])<15:
        for row in live.get('rows',[]):
            if row.get('protocol')=='DNS' and row.get('dport')==53 and row.get('src') in neighbors-local and row.get('dst') not in local and ip(row.get('dst')):
                hints[row['src']]+=1
        result['dns_destination_hints']=dict(hints)
    result['checks']=read_json(D/'checks.json')
    p=read_json('/var/lib/pishield-proactive/status.json');g=read_json('/var/lib/pishield-guard/status.json');result['health']={'proactive_updated':p.get('updated'),'guard_updated':g.get('updated'),'power':p.get('power',{}),'storage':{k:p.get('storage',{}).get(k) for k in ('root_used_percent','messages')},'firewall':g.get('firewall',{}).get('state'),'security_updates':g.get('updates',{}).get('security_marked'),'update_cache':g.get('updates',{}).get('cache_updated')}
    return result

def main():
    data=collect(int(time.time()));fd,tmp=tempfile.mkstemp(dir=D)
    try:
        with os.fdopen(fd,'w') as f:json.dump(data,f,separators=(',',':'));f.flush();os.fsync(f.fileno())
        os.chown(tmp,0,grp.getgrnam('pihole').gr_gid);os.chmod(tmp,0o640);os.replace(tmp,D/'status.json')
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
if __name__=='__main__':main()
