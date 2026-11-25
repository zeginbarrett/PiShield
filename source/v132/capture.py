#!/usr/bin/env python3
"""Bounded rolling decoded DNS packet summaries; no raw packet archive."""
import collections,json,os,pathlib,re,selectors,signal,subprocess,tempfile,time,ipaddress
D=pathlib.Path('/run/pishield-live')
PAT=re.compile(r'^(\d+(?:\.\d+)?)\s+(?:(\S+)\s+(In|Out|P|B|M|Host)\s+)?(IP6?)\s+(\S+)\s+>\s+(\S+):\s*(.*)$')
def endpoint(s):
    host,sep,port=s.rpartition('.')
    if not sep or not port.isdecimal() or not 0<=int(port)<=65535:return None
    try:return str(ipaddress.ip_address(host)),int(port)
    except ValueError:return None

def parse(line):
    m=PAT.fullmatch(line.strip())
    if not m:return None
    ts,iface,direction,version,src,dst,detail=m.groups();a,b=endpoint(src),endpoint(dst)
    if not a or not b or 53 not in (a[1],b[1]):return None
    # Treat packet direction as a hint, not proof of a valid DNS message.
    return {'time':float(ts),'interface':iface or '?','src':a[0],'sport':a[1],'dst':b[0],'dport':b[1],'kind':'To DNS port' if b[1]==53 else 'From DNS port','detail':detail[:600]}

def snapshot(rows,total,started,limited):
    fd,p=tempfile.mkstemp(dir=D)
    try:
        with os.fdopen(fd,'w') as f:json.dump({'updated':time.time(),'started':started,'total':total,'limited':limited,'rows':list(rows)},f,separators=(',',':'))
        os.chmod(p,0o640);os.replace(p,D/'status.json')
    finally:
        if os.path.exists(p):os.unlink(p)

def main():
    rows=collections.deque(maxlen=300);total=0;limited=0;started=time.time();last=0;buf=b'';budget=0;window=time.monotonic()
    # No promiscuous mode, no reverse DNS lookups, no hex dumps or pcap files.
    cmd=['/usr/bin/tcpdump','-i','any','-p','-nn','-tt','-l','-s','1232','-B','256','port 53 and (udp or tcp)']
    # Debian may install tcpdump in /usr/sbin rather than /usr/bin.
    if not os.path.isfile(cmd[0]):cmd[0]='/usr/sbin/tcpdump'
    child=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=None,bufsize=0)
    sel=selectors.DefaultSelector();sel.register(child.stdout,selectors.EVENT_READ)
    def stop(*_):raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try:
        while True:
            if time.monotonic()-window>=1:window=time.monotonic();budget=0
            for key,_ in sel.select(timeout=.5):
                data=os.read(key.fd,65536)
                if not data:raise RuntimeError('tcpdump exited')
                lines=(buf+data).split(b'\n');buf=lines.pop()[-4096:]
                for line in lines:
                    if budget>=400:limited+=1;continue
                    budget+=1;row=parse(line[:4096].decode('utf-8','replace'))
                    if row:rows.append(row);total+=1
            if time.monotonic()-last>=1:
                while rows and rows[0]['time'] < time.time()-300:rows.popleft()
                snapshot(rows,total,started,limited);last=time.monotonic()
            if child.poll() is not None:raise RuntimeError('tcpdump exited')
    finally:
        sel.close();child.terminate()
        try:child.wait(timeout=3)
        except subprocess.TimeoutExpired:child.kill();child.wait()
if __name__=='__main__':main()
