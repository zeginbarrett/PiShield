import pathlib,re,os,tempfile,sys,shutil
ROOT=pathlib.Path(os.environ.get('PS9_WEB','/var/www/html/admin')); SENT=pathlib.Path(os.environ.get('PS9_SENT','/opt/pishield-sentinel/sentinel.py')); SIDE=ROOT/'scripts/lua/sidebar.lp'
BEGIN='<!-- PISHIELD V09 NAV BEGIN -->'; END='<!-- PISHIELD V09 NAV END -->'

def atomic(p,s):
    fd,t=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'w') as f:f.write(s)
        os.chmod(t,0o644);os.replace(t,p)
    finally:
        if os.path.exists(t):os.unlink(t)

def sidebar(s):
    for a,b in [(BEGIN,END),('<!-- PISHIELD BEGIN -->','<!-- PISHIELD END -->'),('<!-- SENTINEL NAV BEGIN -->','<!-- SENTINEL NAV END -->')]:
        if s.count(a)!=s.count(b) or s.count(a)>1:raise ValueError('Unexpected sidebar markers: '+a)
        s=re.sub(re.escape(a)+r'.*?'+re.escape(b)+r'\n?', '',s,flags=re.S)
    # Earlier installers added individual flat list items. Remove only exact custom routes.
    s=re.sub(r'<li\b(?:(?!<li\b).)*?<a\s+href="<\?=webhome\?>pishield(?:[-#][a-z0-9-]+)?"(?:(?!<li\b).)*?</li>', '',s,flags=re.S|re.I)
    s=re.sub(r'<!-- PISHIELD (?:ACTION V08|DEFENSE V07) -->','',s)
    s=re.sub(r'<li class="header text-uppercase">(?:PiShield|Sentinel)</li>', '',s,flags=re.I)
    anchor='<li class="header text-uppercase">Group Management</li>'
    if s.count(anchor)!=1:raise ValueError('Native Group Management anchor missing')
    parts=[BEGIN]
    for title,links in [ ('Defense operations',[('pishield-action','Defense control','shield-alt'),('pishield-defense','Investigations & device trust','bell')]),('Intelligence',[('pishield-sentinel','Learning & verification','brain'),('pishield-ai','AI reports & model','microchip')]),('Network',[('pishield-system','Network discovery & health','wifi')]),('Filtering',[('pishield#profiles','Filtering profiles','user-shield')]) ]:
        parts.append('<li class="header text-uppercase">'+title+'</li>')
        for route,label,icon in links:
            parts.append('<li><a href="<?=webhome?>'+route+'"><i class="fa fa-fw menu-icon fa-'+icon+'"></i> <span>'+label.replace('&','&amp;')+'</span></a></li>')
    parts.append(END)
    return s.replace(anchor,'\n'.join(parts)+'\n'+anchor,1)

def sentinel(s):
    if '# PISHIELD V09 ENRICH' in s:return s
    needle="    # Commit telemetry before potentially slow model execution."
    if s.count(needle)!=1:raise ValueError('Sentinel collector layout differs')
    s=s.replace(needle,"    # PISHIELD V09 ENRICH\n    import intelligence\n    intelligence.enrich(db,q,report,now,event)\n"+needle)
    s=s.replace('No exploit instructions. Be concise.', 'Use learned baselines and feed verification when present. Recommend only evidence-linked defensive steps. No exploit instructions. Be concise.')
    start=s.index("    body='<section class=\"ps-native-banner\"");end=s.index('    if WEB.exists()',start)
    s=s[:start]+'''    body='<section class="ps-native-banner"><div class="ps-native-kicker">PISHIELD // INTELLIGENT DEFENSE</div><h2>Learning &amp; verification</h2><p>Last analysis: '+esc(stamp(now))+' · Scheduled every 15 minutes</p></section>'
    body+=box('Recorded coverage',table(['Metric','Value'],[['Stored queries analyzed',len(q)],['Matching stored rows',total],['Latest stored DNS record',stamp(newest)],['AI status',status],['Defense mode',report.get('defense_state',{}).get('mode','unknown')],['Feed verification',report['feed_verification']['status']]])+'<p>'+esc(report['coverage_note'])+'</p><p><a class="btn btn-primary" href="pishield-ai">Open AI reports &amp; model</a> <a class="btn btn-default" href="pishield-action">Open defense controls</a></p>')
    body+=box('Learned DNS baselines',table(['Reported client','Queries','Prior windows','Median','Elevated'],[(b['client'],b['queries'],b['prior_windows'],b['median'], 'Review' if b['elevated'] else 'No rate alert') for b in report['learned_baselines']])+'<p>Requires 12 prior active windows for rate alerts. Clients may be aggregated by the router. A rate change is not proof of compromise.</p>')
    body+=box('Verified feed matches',table(['Domain','Recorded queries','Managed list IDs'],[(m['domain'],m['queries'],m['list_ids']) for m in report['feed_verification']['matches']])+'<p>'+esc(report['feed_verification']['scope'])+'</p>')
    body+=box('Evidence-linked defensive recommendations',table(['Subject','Reason','Recommended action'],[(r.get('domain',r.get('client')),r['reason'],r['action']) for r in report['recommendations']])+'<p>Model suggestions never become filtering rules automatically. Use Defense control for approved changes.</p>')
    try:
        recovery=json.loads(pathlib.Path('/var/lib/pishield-intelligent/recovery.json').read_text())
        body+=box('Service recovery',table(['Service','State'],list(recovery['statuses'].items()))+table(['Time','Service','Action'],[(stamp(r['time']),r['unit'],r['result']) for r in recovery['events'][-10:][::-1]])+'<p>Failed enabled monitoring units only; deliberately stopped units and DNS engine are not restarted.</p>')
    except (OSError,ValueError,KeyError):body+=box('Service recovery','<p>Awaiting first recovery check.</p>')
''' +s[end:]
    compile(s,str(SENT),'exec');return s

def defense(s):
    # Collapse repeated information, retain data elements for native JS and full inspection.
    if 'PISHIELD V09 COLLAPSE' in s:return s
    lines=[]
    for line in s.splitlines():
        if '<h3 class="box-title">05 / DNS clients &amp; analysis history' in line:
            line='<details><!-- PISHIELD V09 COLLAPSE --><summary>Additional DNS client and analysis history</summary>'+line+'</details>'
        lines.append(line)
    return '\n'.join(lines)+'\n'

def main():
    p=ROOT/'pishield-defense.lp'; h=ROOT/'scripts/lua/header.lp'; hs=h.read_text()
    tag='<!-- PISHIELD V09 MOBILE -->'
    link=tag+'\n<link rel="stylesheet" href="<?=webhome?>style/pishield-mobile-v09.css">\n'
    if tag not in hs:
        closes=list(re.finditer(r'</head\s*>',hs,re.I))
        if len(closes)==1:
            pos=closes[0].start(); hs=hs[:pos]+link+hs[pos:]
        elif not closes:
            # Native v6 shared header leaves closing head to the caller.
            # Prefer the known theme anchor, outside any Lua code.
            anchor='<!-- PISHIELD THEME END -->'
            if hs.count(anchor)==1:
                pos=hs.index(anchor)+len(anchor); hs=hs[:pos]+'\n'+link+hs[pos:]
            elif 'pishield-brand-v053.css' in hs and re.search(r'<head\b[^>]*>',hs,re.I):
                hs=hs.rstrip()+'\n'+link
            else:
                raise ValueError('Unknown shared header layout; no changes made')
        else:
            raise ValueError('Multiple closing head tags; no changes made')
    if hs.count(tag)!=1 or hs.count('style/pishield-mobile-v09.css')!=1:
        raise ValueError('Duplicate or incomplete mobile style injection')
    changes={SIDE:sidebar(SIDE.read_text()),SENT:sentinel(SENT.read_text()),p:defense(p.read_text()),h:hs}
    if sys.argv[1:]==['--check']:return
    for path,txt in changes.items():
        if path.is_symlink():raise ValueError('Unsafe path '+str(path))
    for path,txt in changes.items():atomic(path,txt)
if __name__=='__main__':main()
