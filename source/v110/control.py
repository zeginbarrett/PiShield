#!/usr/bin/env python3
"""Explicit local-admin firewall controls; never invoked by the web server."""
import fcntl, json, os, pathlib, re, subprocess, sys, tempfile
ETC=pathlib.Path('/etc/pishield-guard'); STATE=pathlib.Path('/var/lib/pishield-guard'); CONF=ETC/'firewall.nft'; TRIAL=STATE/'trial.json'; NFT='/usr/sbin/nft'; UNIT='pishield-guard-firewall.service'; REVERT='pishield-guard-revert.timer'; SELF='/usr/local/sbin/pishield-guard'
def cmd(*a,check=True):return subprocess.run(a,check=check,timeout=25)
def exists():return subprocess.run([NFT,'list','table','inet','pishield_guard'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5).returncode==0
def atomic(p,s):
    fd,t=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'w') as f:f.write(s);f.flush();os.fsync(f.fileno())
        os.replace(t,p)
    finally:
        if os.path.exists(t):os.unlink(t)
def rules(iface):
    if not re.fullmatch(r'[a-zA-Z0-9_.:-]{1,15}',iface) or iface in ('lo','tailscale0') or not (pathlib.Path('/sys/class/net')/iface).exists():raise ValueError('Specify your actual LAN interface, e.g. wlan0 or eth0')
    return f'''table inet pishield_guard {{
 chain input {{
  type filter hook input priority 10; policy accept;
  iifname "lo" accept
  ct state established,related accept
  meta l4proto {{ icmp, ipv6-icmp }} accept
  udp sport 67 udp dport 68 accept
  udp sport 547 udp dport 546 accept
  iifname "{iface}" tcp dport {{ 22, 53, 80, 443 }} accept
  iifname "{iface}" udp dport {{ 53, 67, 5353, 547 }} accept
  iifname "tailscale0" tcp dport {{ 22, 53, 80, 443 }} accept
  iifname "tailscale0" udp dport 53 accept
  udp dport 41641 accept
  counter drop
 }}
}}
'''
def apply(text):
    # nft batch is atomic. Only this dedicated table is ever removed/replaced.
    if exists():text='delete table inet pishield_guard\n'+text
    fd,t=tempfile.mkstemp(dir=STATE)
    try:
        with os.fdopen(fd,'w') as f:f.write(text)
        cmd(NFT,'-c','-f',t);cmd(NFT,'-f',t)
    finally:os.unlink(t)
def remove():
    if exists():cmd(NFT,'delete','table','inet','pishield_guard')
def main(a):
    if os.geteuid()!=0:raise SystemExit('Run with sudo')
    if a==['baseline']:
        cmd('/usr/bin/python3','/opt/pishield-guard/guard.py','--baseline');return
    if a==['check']:
        cmd('systemctl','start','pishield-guard.service');print((STATE/'status.json').read_text());return
    if a==['firewall','status']:
        if not pathlib.Path(NFT).exists():print('nftables not installed');return
        print('Persistent configuration:',CONF.exists(),'Unconfirmed trial:',TRIAL.exists());cmd(NFT,'list','table','inet','pishield_guard',check=False);return
    if not a or a[0]!='firewall':raise SystemExit('Usage: pishield-guard check | baseline | firewall status | trial INTERFACE | confirm | off')
    if not pathlib.Path(NFT).exists():raise SystemExit('Install nftables first: sudo apt install nftables')
    with (STATE/'firewall.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if len(a)==3 and a[1]=='trial':
            if CONF.exists() or TRIAL.exists() or exists():raise SystemExit('Firewall already active or trial pending. Turn it off first.')
            text=rules(a[2]); atomic(TRIAL,json.dumps({'rules':text}))
            try:
                cmd('systemd-run','--quiet','--unit=pishield-guard-revert','--on-active=180s',SELF,'firewall','expire')
                apply(text)
            except BaseException:
                remove();TRIAL.unlink(missing_ok=True);cmd('systemctl','stop',REVERT,check=False);raise
            print('Firewall trial active for 180 seconds. Open a NEW SSH session and test DNS and phone access before confirming.');return
        if a==['firewall','confirm']:
            if not TRIAL.exists() or not exists():raise SystemExit('No active trial to confirm')
            atomic(CONF,json.loads(TRIAL.read_text())['rules'])
            try:cmd('systemctl','enable',UNIT)
            except BaseException:CONF.unlink(missing_ok=True);raise
            TRIAL.unlink();cmd('systemctl','stop',REVERT,check=False);print('Firewall confirmed and enabled for future boots.');return
        if a==['firewall','expire']:
            if TRIAL.exists():remove();TRIAL.unlink();print('Unconfirmed firewall trial reverted.')
            return
        if a==['firewall','restore']:
            if CONF.exists():apply(CONF.read_text())
            return
        if a==['firewall','off']:
            cmd('systemctl','disable',UNIT,check=False);CONF.unlink(missing_ok=True);remove();TRIAL.unlink(missing_ok=True);cmd('systemctl','stop',REVERT,check=False);print('PiShield host firewall removed. Other firewall rules unchanged.');return
        raise SystemExit('Invalid command')
if __name__=='__main__':main(sys.argv[1:])
