#!/usr/bin/env python3
"""Optional authenticated ntfy delivery; sends generic event categories only."""
import json, pathlib, os, tempfile, urllib.parse, urllib.request, time, re
D=pathlib.Path('/var/lib/pishield-proactive'); C=pathlib.Path('/etc/pishield-proactive/ntfy.json')
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**k):return None

def send():
    if not C.exists():return
    config=json.loads(C.read_text());url=config['url'];token=config['token'];p=urllib.parse.urlsplit(url)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment or not re.fullmatch(r'/[A-Za-z0-9_-]{1,100}',p.path) or not re.fullmatch(r'[A-Za-z0-9._~-]{10,512}',token):raise ValueError('Invalid ntfy configuration')
    status=json.loads((D/'status.json').read_text());now=int(time.time());sent=D/'notified.json'
    # On first activation, deliver only events from the last 15 minutes.
    try:last=int(json.loads(sent.read_text())['through'])
    except FileNotFoundError:last=now-900
    events=[x for x in status.get('events',[]) if last<x['time']<=now]
    if not events:return
    # No client identifiers, domains, hostnames, log messages or IPs sent.
    titles=sorted(set(x['title'] for x in events))
    message='PiShield: '+', '.join(titles)+'. Review your private dashboard.'
    r=urllib.request.Request(url,data=message.encode(),headers={'Authorization':'Bearer '+token,'Title':'PiShield security notice','Content-Type':'text/plain; charset=utf-8'},method='POST')
    with urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect()).open(r,timeout=12) as res:
        if not 200<=res.status<300:raise RuntimeError('Delivery not confirmed')
    fd,t=tempfile.mkstemp(dir=D)
    try:
        with os.fdopen(fd,'w') as f:json.dump({'through':max(x['time'] for x in events)},f)
        os.replace(t,sent)
    finally:
        if os.path.exists(t):os.unlink(t)
if __name__=='__main__':
    try:send()
    except Exception as e:raise SystemExit('Notification failed: '+type(e).__name__)
