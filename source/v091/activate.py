import pathlib,json,sys,fcntl,uuid,os
S=pathlib.Path('/var/lib/pishield-action'); M=pathlib.Path('/var/lib/pishield-intelligent/activation-requested')
if M.exists():print('Existing defense preference retained.');sys.exit(0)
with (S/'lock').open('a') as lock:
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:print('Defense engine busy; select Active defense in dashboard to enable feed blocking.');sys.exit(0)
    cfg=json.loads((S/'config.json').read_text()) if (S/'config.json').exists() else {}
    if cfg.get('mode','observe')!='observe':print('Existing active/aggressive mode retained.');M.touch();sys.exit(0)
    p=S/'request'; raw=p.read_text().split('\n')
    if len(raw)==5 and raw[-1]=='END' and raw[0]!=cfg.get('last_action',{}).get('id'):print('Another action is pending; use Defense control after completion.');sys.exit(0)
    with p.open('w') as f:f.write(str(uuid.uuid4())+'\nmode\nactive\nyes\nEND')
    M.touch();print('Active defense requested; verify actual feed and DNS status in Defense control.')
