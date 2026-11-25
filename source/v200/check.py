#!/usr/bin/env python3
"""Explicit opt-in TCP reachability check for a single owned LAN device."""
import argparse, ipaddress, json, os, pathlib, socket, subprocess, tempfile, time, grp
D=pathlib.Path('/var/lib/pishield-intelligence'); PORTS=(22,23,80,443,445,3389,5555,8080)
LAN=(ipaddress.ip_network('10.0.0.0/8'),ipaddress.ip_network('172.16.0.0/12'),ipaddress.ip_network('192.168.0.0/16'))
def run():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('ip');p.add_argument('--confirm-owned',action='store_true',help='Confirm this is your device and you authorize a local reachability check');a=p.parse_args()
    if os.geteuid()!=0 or not a.confirm_owned:raise SystemExit('Run using sudo with --confirm-owned only for a device you own or administer.')
    try:target=ipaddress.IPv4Address(a.ip)
    except ValueError:raise SystemExit('A single local IPv4 address is required.')
    if not any(target in net for net in LAN):raise SystemExit('Only RFC1918 local addresses are accepted.')
    def ip_json(*args):return json.loads(subprocess.check_output(['ip','-j',*args],text=True,timeout=4))
    route=ip_json('route','get',str(target))[0];dev=route.get('dev');src=route.get('prefsrc');
    if route.get('gateway') or dev in ('lo','tailscale0',None) or not src or src==str(target):raise SystemExit('Target must be directly reachable on a local interface, not via a gateway or VPN.')
    records=ip_json('address','show','dev',dev);nets=[ipaddress.ip_interface(f"{x['local']}/{x['prefixlen']}").network for r in records for x in r.get('addr_info',[]) if x.get('family')=='inet']
    if not any(target in net and target not in (net.network_address,net.broadcast_address) for net in nets):raise SystemExit('Target must be a unicast address on a directly connected subnet.')
    if str(target) in {x.get('gateway') for x in ip_json('route','show','default')}:raise SystemExit('Select an endpoint, not the default gateway.')
    opened=[];unconfirmed=[]
    for port in PORTS:
        try:
            with socket.create_connection((str(target),port),timeout=.6):opened.append(port)
        except OSError:unconfirmed.append(port)
    path=D/'checks.json'
    try:old=json.loads(path.read_text())
    except (OSError,ValueError):old={}
    now=int(time.time());old={k:v for k,v in old.items() if isinstance(v,dict) and now-v.get('time',0)<7*86400};old[str(target)]={'time':now,'open':opened,'unconfirmed':unconfirmed};old=dict(sorted(old.items(),key=lambda x:-x[1]['time'])[:100]);fd,tmp=tempfile.mkstemp(dir=D)
    try:
        with os.fdopen(fd,'w') as f:json.dump(old,f);f.flush();os.fsync(f.fileno())
        os.chown(tmp,0,grp.getgrnam('pihole').gr_gid);os.chmod(tmp,0o640);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    print('TCP connection accepted:',opened or 'none observed');print('Unconfirmed:',unconfirmed);print('This is not a vulnerability scan; review unexpected services. The dashboard refreshes on the next collection.')
if __name__=='__main__':run()
