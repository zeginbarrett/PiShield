#!/usr/bin/env python3
"""Bounded volatile DNS details and other visible IP packet metadata."""
import collections, json, os, pathlib, re, selectors, signal, subprocess, tempfile, time, ipaddress
D=pathlib.Path('/run/pishield-live')
PAT=re.compile(r'^(\d+(?:\.\d+)?)\s+(?:(\S+)\s+(In|Out|P|B|M|Host)\s+)?(IP6?)\s+(\S+)\s+>\s+(\S+):\s*(.*)$')

def endpoint(s):
    try:return str(ipaddress.ip_address(s)),None
    except ValueError:pass
    host,sep,port=s.rpartition('.')
    if not sep or not port.isdecimal() or not 0<=int(port)<=65535:return None
    try:return str(ipaddress.ip_address(host)),int(port)
    except ValueError:return None

def parse(line,stream):
    m=PAT.fullmatch(line.strip())
    if not m:return None
    ts,iface,direction,version,src,dst,detail=m.groups();a,b=endpoint(src),endpoint(dst)
    if not a or not b:return None
    if stream=='dns':
        if 53 not in (a[1],b[1]):return None
        protocol='DNS';kind='To DNS port' if b[1]==53 else 'From DNS port';summary=detail[:600]
    else:
        # tcpdump -q metadata only. Do not retain arbitrary protocol-decoder text.
        if 53 in (a[1],b[1]):return None
        if re.match(r'tcp(?:\s|,|$)',detail,re.I):protocol='TCP'
        elif re.match(r'udp(?:\s|,|$)',detail,re.I):protocol='UDP'
        elif re.match(r'icmp6?(?:\s|,|$)',detail,re.I):protocol='ICMP'
        else:protocol='IP'
        kind='Metadata';summary=protocol+' packet (metadata only)'
    return {'time':float(ts),'interface':iface or '?','src':a[0],'sport':a[1],'dst':b[0],'dport':b[1],'kind':kind,'protocol':protocol,'detail':summary}

def snapshot(rows,totals,started,limited):
    fd,p=tempfile.mkstemp(dir=D)
    try:
        with os.fdopen(fd,'w') as f:json.dump({'schema':2,'updated':time.time(),'started':started,'total':sum(totals.values()),'totals':totals,'limited':sum(limited.values()),'rows':sorted((r for q in rows.values() for r in q),key=lambda x:x['time'])},f,separators=(',',':'))
        os.chmod(p,0o640);os.replace(p,D/'status.json')
    finally:
        if os.path.exists(p):os.unlink(p)

def main():
    streams={'dns':['-s','1232','port 53 and (udp or tcp)'],'metadata':['-q','-s','128','(ip or ip6) and not (port 53 and (udp or tcp))']}
    rows={k:collections.deque(maxlen=300) for k in streams};totals={k:0 for k in streams};limited={k:0 for k in streams};buffers={k:b'' for k in streams};budget={k:0 for k in streams};started=time.time();last=0;window=time.monotonic()
    exe=next((p for p in ('/usr/bin/tcpdump','/usr/sbin/tcpdump') if os.path.isfile(p)),None)
    if not exe:raise RuntimeError('tcpdump missing')
    children=[];sel=selectors.DefaultSelector()
    def stop(*_):raise SystemExit(0)
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try:
        for k,args in streams.items():
            child=subprocess.Popen([exe,'-i','any','-p','-nn','-tt','-l','-B','256',*args],stdout=subprocess.PIPE,stderr=None,bufsize=0);children.append(child);sel.register(child.stdout,selectors.EVENT_READ,k)
        while True:
            if time.monotonic()-window>=1:window=time.monotonic();budget={k:0 for k in streams}
            for key,_ in sel.select(timeout=.5):
                k=key.data;data=os.read(key.fd,65536)
                if not data:raise RuntimeError(k+' capture exited')
                lines=(buffers[k]+data).split(b'\n');buffers[k]=lines.pop()[-4096:]
                for line in lines:
                    if budget[k]>=400:limited[k]+=1;continue
                    budget[k]+=1;row=parse(line[:4096].decode('utf-8','replace'),k)
                    if row:rows[k].append(row);totals[k]+=1
            if any(c.poll() is not None for c in children):raise RuntimeError('Capture process exited')
            if time.monotonic()-last>=1:
                for k,q in rows.items():rows[k]=collections.deque((r for r in q if r['time']>=time.time()-300),maxlen=300)
                snapshot(rows,totals,started,limited);last=time.monotonic()
    finally:
        sel.close()
        for child in children:
            if child.poll() is None:child.terminate()
        for child in children:
            try:child.wait(timeout=3)
            except subprocess.TimeoutExpired:child.kill();child.wait()
if __name__=='__main__':main()
