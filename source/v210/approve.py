#!/usr/bin/python3
"""Owner-only approval for one fixed operation; never executes model text."""
import os, pathlib, sys, json, time, subprocess, fcntl, re, stat
sys.path.insert(0,"/opt/pishield-chat")
from actions import ACTIONS
D=pathlib.Path('/run/pishield-chat'); S=pathlib.Path('/var/lib/pishield-workshop')
def load(path):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as f:
        st=os.fstat(f.fileno())
        if st.st_uid!=0 or st.st_mode&0o022 or not stat.S_ISREG(st.st_mode):raise ValueError('Unsafe proposal or receipt')
        raw=f.read(8193)
    if len(raw)>8192:raise ValueError('Invalid file size')
    return json.loads(raw)
def check(p,ident):
    if not isinstance(p,dict) or set(p)!={'id','action','mode','reason','created'} or p['id']!=ident or not re.fullmatch(r'[A-Za-z0-9-]{8,80}',ident):raise ValueError('No matching proposal')
    if type(p['created']) not in (int,float) or not 0<=time.time()-p['created']<=600:raise ValueError('Proposal expired; request another')
    if p['action'] not in ACTIONS or ACTIONS[p['action']][0]!=p['mode']:raise ValueError('Action not permitted')
    return ACTIONS[p['action']]
def main():
    if os.geteuid()!=0 or not sys.stdin.isatty():raise ValueError('Run via sudo in an interactive SSH terminal')
    if len(sys.argv)!=2:raise ValueError('Usage: sudo pishield-approve REQUEST_ID')
    ident=sys.argv[1];p=load(D/'proposal.json');mode,label,cmd=check(p,ident)
    with (S/'lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        receipt=S/(ident+'.json')
        if receipt.exists():raise ValueError('Already consumed; request a new approval')
        print('Action:',label,'\nExact command:', ' '.join(cmd),'\nRequest:',ident)
        if input('Type APPROVE to run this exact action: ')!='APPROVE':raise ValueError('Cancelled')
        if load(D/'proposal.json')!=p:raise ValueError('Proposal changed; review again')
        check(p,ident)
        # Consume before running, so failures never automatically replay.
        with receipt.open('x') as f:json.dump({'id':ident,'action':p['action'],'status':'started','time':time.time()},f)
        try:
            result=subprocess.run(cmd,stdin=subprocess.DEVNULL,timeout=900,check=False,cwd='/',env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/bin','LANG':'C','DEBIAN_FRONTEND':'noninteractive'})
            status='completed' if result.returncode==0 else 'failed (exit '+str(result.returncode)+')'
        except (OSError,subprocess.TimeoutExpired):status='failed or timed out; check terminal'
        rec={'id':ident,'action':p['action'],'status':status,'time':time.time()}
        receipt.write_text(json.dumps(rec));tmp=S/'latest.tmp';tmp.write_text(json.dumps(rec));os.replace(tmp,S/'latest.json');print(status)
if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError) as e:raise SystemExit(str(e))
