const CATALOG=[
  [
    "tv",
    "Smart TV / ACR",
    "General television advertising, viewing recognition and analytics; overlaps some vendor filters.",
    "https://raw.githubusercontent.com/PCTestAdmin/tv-blocklist/main/lists/hosts.txt"
  ],
  [
    "sony",
    "Sony Bravia",
    "Dedicated Sony measurement, advertising and Samba TV viewing-data endpoints. Exact names only; some entries overlap Smart TV / ACR.",
    "https://raw.githubusercontent.com/zeginbarrett/PiShield/main/lists/sony-bravia.txt"
  ],
  [
    "samsung",
    "Samsung",
    "Samsung device advertising and telemetry.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/native.samsung-onlydomains.txt"
  ],
  [
    "lg",
    "LG webOS",
    "LG television tracking and telemetry.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/native.lgwebos-onlydomains.txt"
  ],
  [
    "roku",
    "Roku",
    "Roku tracking endpoints.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/native.roku-onlydomains.txt"
  ],
  [
    "amazon",
    "Amazon / Fire TV",
    "Amazon device and service trackers.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/native.amazon-onlydomains.txt"
  ],
  [
    "windows",
    "Windows / Office",
    "Microsoft telemetry and trackers; test sign-in and updates.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/native.winoffice-onlydomains.txt"
  ],
  [
    "apple",
    "Apple devices",
    "Apple device and service trackers.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/native.apple-onlydomains.txt"
  ],
  [
    "xiaomi",
    "Xiaomi / smart home",
    "Xiaomi device trackers; not all IoT brands.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/native.xiaomi-onlydomains.txt"
  ],
  [
    "huawei",
    "Huawei devices",
    "Huawei device tracking.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/native.huawei-onlydomains.txt"
  ],
  [
    "oppo",
    "OPPO / Realme",
    "Mobile device trackers.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/native.oppo-realme-onlydomains.txt"
  ],
  [
    "vivo",
    "Vivo devices",
    "Mobile device trackers.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/native.vivo-onlydomains.txt"
  ],
  [
    "social",
    "TikTok fingerprinting",
    "Known TikTok tracking domains; not all social networks.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/native.tiktok-onlydomains.txt"
  ],
  [
    "tracking",
    "Data harvesting / ads",
    "General advertising, analytics and tracking; includes other unwanted domains.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/multi-onlydomains.txt"
  ],
  [
    "bypass",
    "DNS / VPN bypass (optional)",
    "Known encrypted DNS, VPN and proxy endpoints. May disrupt legitimate VPNs including remote access; do not enable without testing.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/doh-vpn-proxy-bypass-onlydomains.txt"
  ]
];
(()=>{'use strict';
const $=id=>document.getElementById(id), n=(tag,txt,cl)=>{const e=document.createElement(tag);if(txt!==undefined)e.textContent=txt;if(cl)e.className=cl;return e;};
function init(){const grid=$('pspriv-grid');if(!grid||!document.body.classList.contains('logged-in'))return;
const csrf=document.querySelector('meta[name="csrf-token"]')?.content||'',base=document.body.dataset.apiurl,web=document.body.dataset.webhome||'/admin/';
const own='PiShield privacy v1.3: ',groupName=p=>'PiShield Privacy '+p[0];let busy=false;
const enabled=x=>x===true||x===1;const ids=x=>Array.isArray(x?.groups)?x.groups.map(Number):[];
async function api(path,method='GET',data){if(!base||!csrf)throw Error('Missing authenticated API context; sign in again');const u=new URL(base.replace(/\/$/,'')+path,location.href);if(u.origin!==location.origin)throw Error('Unexpected API origin');const r=await fetch(u,{method,credentials:'same-origin',cache:'no-store',redirect:'error',headers:{'X-CSRF-TOKEN':csrf,...(data?{'Content-Type':'application/json'}:{})},...(data?{body:JSON.stringify(data)}:{}),signal:AbortSignal.timeout(20000)});if(!r.ok)throw Error('API HTTP '+r.status);return r.status===204?{}:r.json();}
async function state(){const [g,l,c,b]=await Promise.all([api('/groups'),api('/lists?type=block'),api('/clients'),api('/dns/blocking')]);if(!Array.isArray(g.groups)||!Array.isArray(l.lists)||!Array.isArray(c.clients))throw Error('Unexpected response');return {groups:g.groups,lists:l.lists,clients:c.clients,blocking:b.blocking};}
const group=(s,p)=>s.groups.find(x=>x.name===groupName(p));const list=(s,p)=>s.lists.find(x=>x.address===p[3]);
function owned(s,p){const g=group(s,p),l=list(s,p);return (!g||g.comment===own+p[0])&&(!l||l.comment===own+p[0]&&g&&ids(l).includes(g.id)&&ids(l).every(x=>x===0||x===g.id));}
async function ensure(s,p,scope){if(!owned(s,p))throw Error('Existing group/list belongs to another policy; manage it in native Lists / Groups. No changes made.');let g=group(s,p);if(!g){await api('/groups','POST',{name:[groupName(p)],comment:own+p[0],enabled:true});s=await state();g=group(s,p);}if(!g||g.comment!==own+p[0]||!Number.isInteger(g.id)||g.id<=0||!enabled(g.enabled))throw Error('Group not enabled or could not verify');let l=list(s,p);const groups=scope==='default'?[0,g.id]:[g.id];if(!l)await api('/lists?type=block','POST',{address:[p[3]],comment:own+p[0],groups,enabled:true});else{if(!owned(s,p))throw Error('List changed; reload first');await api('/lists/'+encodeURIComponent(p[3])+'?type=block','PUT',{comment:l.comment,enabled:true,groups,type:'block'});}const after=await state();l=list(after,p);if(!owned(after,p)||!enabled(l?.enabled)||ids(l).length!==groups.length||!groups.every(x=>ids(l).includes(x)))throw Error('Configuration not verified; review Lists');return 'List enabled in configuration. Run Update Gravity and test actual DNS filtering.';}
async function disable(p){const s=await state(),l=list(s,p);if(!l||!owned(s,p))throw Error('Not a managed list');await api('/lists/'+encodeURIComponent(p[3])+'?type=block','PUT',{comment:l.comment,enabled:false,groups:ids(l),type:'block'});const a=await state();if(enabled(list(a,p)?.enabled))throw Error('Disable not verified');return 'List disabled. Other overlapping blocklists can still block these domains.';}
async function assign(p,client,add){const s=await state(),g=group(s,p),l=list(s,p),c=s.clients.find(x=>x.client===client);if(!g||!l||!owned(s,p)||!c||!enabled(g.enabled))throw Error('Managed profile or client unavailable');const groups=ids(c);if(!groups.length)throw Error('Client has no explicit groups; review native Clients');if(add&&!groups.includes(g.id))groups.push(g.id);if(!add){const i=groups.indexOf(g.id);if(i>=0)groups.splice(i,1);if(!groups.length)throw Error('Removing would leave no groups; edit native Clients.');}await api('/clients/'+encodeURIComponent(client),'PUT',{comment:c.comment??'',groups});const a=await state(),actual=ids(a.clients.find(x=>x.client===client));if(actual.includes(g.id)!==add||groups.some(x=>!actual.includes(x))||actual.length!==groups.length)throw Error('Client groups not verified');return 'Client assignment saved; existing groups retained. Default-group scope applies independently.';}
async function counter(){try{const u=new URL('pishield-privacy-api',new URL(web,location.href));if(u.origin!==location.origin)throw Error();const r=await fetch(u,{cache:'no-store',credentials:'same-origin',signal:AbortSignal.timeout(5000)});const j=await r.json();if(!r.ok||j.error||!j.updated||Math.abs(Date.now()/1000-j.updated)>1200)throw Error();$('pspriv-count-note').textContent=`Last 24h: ${j.sample.toLocaleString()} recorded gravity-blocked queries sampled${j.capped?' (sample capped)':''}. Counts match current enabled lists; overlaps possible, not unique blocked requests attributable to a filter.`;return j.counts;}catch{$('pspriv-count-note').textContent='Block-match counters unavailable or stale. No values estimated.';return {};}}
async function run(fn){if(busy)return;busy=true;grid.querySelectorAll('button,select').forEach(e=>e.disabled=true);$('pspriv-status').textContent='Saving…';let message;try{message=await fn();}catch(e){message='Stopped: '+e.message+'; refresh and inspect any completed changes.';}busy=false;await refresh(message);}
async function refresh(message=''){if(busy)return;busy=true;grid.querySelectorAll('button,select').forEach(e=>e.disabled=true);try{const [s,counts]=await Promise.all([state(),counter()]);grid.replaceChildren();$('pspriv-status').textContent=(message?message+' · ':'')+'DNS blocking: '+String(s.blocking??'unknown')+'. Filters below show saved configuration, not verified end-to-end enforcement.';
for(const p of CATALOG){const g=group(s,p),l=list(s,p),managed=owned(s,p),on=enabled(l?.enabled),card=n('section',undefined,'pspriv-card');card.append(n('h3',p[1]),n('p',p[2]));const info=n('strong',!managed?'Existing external policy — manage in Lists':!l?'Not configured':on?(enabled(g?.enabled)?'Enabled in configuration':'Group disabled'):'Disabled');info.dataset.state=!managed||on&&!enabled(g?.enabled)?'warn':on?'on':'off';card.append(info);const num=n('p',typeof counts[p[0]]==='number'?counts[p[0]].toLocaleString()+' matching blocked requests':'— matching blocked requests','pspriv-metric');card.append(num);if(l)card.append(n('p','List entries: '+String(l.number??'unknown')+' · download status: '+String(l.status??'unknown')+(l.number===0?' · update Gravity':'')));const row=n('div',undefined,'pspriv-row'),scope=n('select');scope.setAttribute('aria-label',p[1]+' scope');for(const [v,t] of [['devices','Selected devices only'],['default','Default group + selected devices']]){const o=n('option',t);o.value=v;scope.append(o);}scope.value=ids(l).includes(0)?'default':'devices';const toggle=n('button',on?'Disable':'Enable','btn btn-default pspriv-toggle');toggle.type='button';toggle.setAttribute('aria-pressed',String(on));toggle.disabled=!managed;scope.disabled=!managed;toggle.onclick=()=>{if(confirm(on?'Disable this managed list?':'Enable '+p[1]+' for '+scope.selectedOptions[0].text+'? Test apps after updating Gravity.'))run(()=>on?disable(p):state().then(x=>ensure(x,p,scope.value)));};const change=n('button','Save scope','btn btn-default');change.type='button';change.disabled=!managed||!on;change.onclick=()=>{if(confirm('Change scope to '+scope.selectedOptions[0].text+'?'))run(()=>state().then(x=>ensure(x,p,scope.value)));};row.append(scope,toggle,change);card.append(row);
const assigned=g?s.clients.filter(c=>ids(c).includes(g.id)):[];card.append(n('p',assigned.length+' explicit client assignment(s)'));const d=n('details'),sum=n('summary','Device assignments and list source');d.append(sum);if(g&&l&&managed){const sel=n('select',undefined,'pspriv-clients');sel.setAttribute('aria-label','Select existing client for '+p[1]);for(const c of s.clients){if(typeof c.client!=='string')continue;const o=n('option',c.client+(ids(c).includes(g.id)?' (assigned)':''));o.value=c.client;sel.append(o);}const a=n('button','Assign','btn btn-default'),b=n('button','Remove assignment','btn btn-default');for(const x of [a,b]){x.type='button';x.disabled=!sel.options.length;}a.onclick=()=>{if(confirm('Assign '+sel.value+'? Confirm it is the intended device, not the router.'))run(()=>assign(p,sel.value,true));};b.onclick=()=>{if(confirm('Remove this device assignment?'))run(()=>assign(p,sel.value,false));};d.append(sel,a,b);}const link=n('a','View source list');link.href=p[3];link.target='_blank';link.rel='noopener noreferrer';d.append(n('p','Use Manage clients to add new devices and Domain exceptions to allow specific domains.'),link);card.append(d);grid.append(card);}
}catch(e){$('pspriv-status').textContent='Privacy controls unavailable: '+e.message;grid.replaceChildren();}finally{busy=false;}}
$('pspriv-refresh').onclick=()=>refresh();refresh();}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();})();
