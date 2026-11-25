import json, pathlib, subprocess, time, os, tempfile
STATE=pathlib.Path('/var/lib/pishield-intelligent'); PATH=STATE/'recovery.json'
TIMERS=['pishield-'+name+'.timer' for name in ('sentinel','defense','action','collect','backup')]
UNITS=['pishield-ai.service']+TIMERS+[u.replace('.timer','.service') for u in TIMERS]
def cmd(*a):return subprocess.run(a,capture_output=True,text=True,timeout=25)
def main():
    try: data=json.loads(PATH.read_text())
    except (OSError,ValueError):data={'last_attempt':{},'events':[]}
    now=int(time.time()); statuses={}; enabled=set()
    for u in UNITS:
        r=cmd('systemctl','show',u,'--property=LoadState,UnitFileState,ActiveState','--no-pager'); props=dict(l.split('=',1) for l in r.stdout.splitlines() if '=' in l)
        status=props.get('ActiveState','unknown');statuses[u]=status
        if props.get('UnitFileState')=='enabled' and status=='active':enabled.add(u)
        # Only recover enabled units that are actually failed; don't undo an intentional stop.
        if props.get('LoadState')=='loaded' and (props.get('UnitFileState')=='enabled' or u.replace('.service','.timer') in enabled) and status=='failed' and now-data['last_attempt'].get(u,0)>=600:
            data['last_attempt'][u]=now
            try:r=cmd('systemctl','restart','--no-block',u); result='restart queued' if r.returncode==0 else 'restart rejected: '+r.stderr[:160]
            except Exception as e:result='restart error: '+str(e)[:160]
            data['events'].append({'time':now,'unit':u,'result':result})
    data.update(updated=now,statuses=statuses,events=data['events'][-100:]); fd,t=tempfile.mkstemp(dir=STATE)
    with os.fdopen(fd,'w') as f:json.dump(data,f)
    os.replace(t,PATH)
if __name__=='__main__':main()
