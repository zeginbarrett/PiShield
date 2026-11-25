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
  ],
  [
    "family",
    "Family / adult content",
    "Optional adult-content DNS list; not comprehensive parental controls.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/nsfw-onlydomains.txt"
  ],
  [
    "gambling",
    "Gambling",
    "Optional gambling-site filtering.",
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/gambling.mini-onlydomains.txt"
  ]
];
(()=>{'use strict';
const $=id=>document.getElementById(id),node=(tag,value,cl)=>{const e=document.createElement(tag);if(value!==undefined)e.textContent=value;if(cl)e.className=cl;return e;};
const own='PiShield privacy v1.3: ',legacy='PiShield v0.3 scoped profile';
const legacyNames={tv:'PiShield Smart TVs',family:'PiShield Family',gambling:'PiShield Gambling'};
const on=x=>x===true||x===1, ids=x=>Array.isArray(x?.groups)?x.groups.map(Number):[];
const ipv4=s=>/^\d{1,3}(\.\d{1,3}){3}$/.test(s)&&s.split('.').every(x=>String(Number(x))===x&&Number(x)<=255)&&Number(s.split('.')[0])>0&&Number(s.split('.')[0])<224&&!s.startsWith('127.');
const mac=s=>/^([a-f0-9]{2}:){5}[a-f0-9]{2}$/i.test(s);
const same=(a,b)=>String(a).toLowerCase()===String(b).toLowerCase();
const existing=(s,ip)=>s.clients.find(c=>same(c.client,ip));
const groupsFor=(s,ip)=>existing(s,ip)?ids(existing(s,ip)):[0];
function init(){const root=$('psdf');if(!root||!document.body.classList.contains('logged-in'))return;
let selected='',busy=false,observed=new Set();const base=document.body.dataset.apiurl,csrf=document.querySelector('meta[name="csrf-token"]')?.content;
async function api(path,method='GET',data){if(!base||!csrf)throw Error('Missing authenticated API context. Sign in again.');const u=new URL(base.replace(/\/$/,'')+path,location.href);if(u.origin!==location.origin)throw Error('Unexpected API origin');const r=await fetch(u,{method,credentials:'same-origin',cache:'no-store',redirect:'error',headers:{'X-CSRF-TOKEN':csrf,...(data?{'Content-Type':'application/json'}:{})},...(data?{body:JSON.stringify(data)}:{}),signal:AbortSignal.timeout(20000)});if(r.status===204&&r.ok)return {};let j;try{j=await r.json()}catch{throw Error('API HTTP '+r.status+' (invalid response)')}if(!r.ok||j.error)throw Error('API HTTP '+r.status+': '+String(j.error?.message||j.error?.key||'request failed').slice(0,200));if(j.processed?.errors?.length)throw Error(String(j.processed.errors[0].error||'API rejected change').slice(0,200));return j;}
async function state(){const [g,l,c,d,b]=await Promise.all([api('/groups'),api('/lists'),api('/clients'),api('/domains'),api('/dns/blocking')]);if(!Array.isArray(g.groups)||!Array.isArray(l.lists)||!Array.isArray(c.clients)||!Array.isArray(d.domains))throw Error('Unrecognized API response');return {groups:g.groups,lists:l.lists,clients:c.clients,domains:d.domains,blocking:b.blocking};}
function inspect(s,p,ip){const l=s.lists.find(x=>x.address===p[3]&&x.type==='block');const members=groupsFor(s,ip);const applies=l&&on(l.enabled)&&ids(l).some(id=>members.includes(id)&&s.groups.some(g=>g.id===id&&on(g.enabled)));let g=s.groups.find(x=>x.name==='PiShield Privacy '+p[0]);let tag=own+p[0];let name='PiShield Privacy '+p[0];
// Reuse a legacy PiShield profile only if it owns this exact list and has no other policies.
if(l&&legacyNames[p[0]]&&l.comment===legacyNames[p[0]]){g=s.groups.find(x=>x.name===legacyNames[p[0]]);tag=legacy;name=legacyNames[p[0]];}
const groupOK=!g||(g.comment===tag&&Number.isInteger(g.id)&&g.id>0&&on(g.enabled));
const listOK=!l||(g&&ids(l).includes(g.id)&&ids(l).every(id=>id===0||id===g.id)&&(l.comment===own+p[0]||tag===legacy&&l.comment===name));
const exclusive=!g||(!s.lists.some(x=>x!==l&&ids(x).includes(g.id))&&!s.domains.some(x=>ids(x).includes(g.id)));
const managed=groupOK&&listOK&&exclusive;const assigned=!!g&&members.includes(g.id);const defaultApplies=!!l&&on(l.enabled)&&ids(l).includes(0)&&members.includes(0)&&s.groups.some(x=>x.id===0&&on(x.enabled));
return {l,g,tag,name,managed,assigned,applies:!!applies,defaultApplies};}
function validate(s,ip){if(!ipv4(ip)&&!(mac(ip)&&existing(s,ip)))throw Error('Enter a valid IPv4 address or select a configured MAC client.');if(ip===location.hostname||ip==='0.0.0.0'||ip.endsWith('.255'))throw Error('Choose a device, not the Pi or a broadcast address.');if(!existing(s,ip)&&s.clients.some(c=>!ipv4(c.client)))throw Error('Existing MAC, subnet or hostname policies may cover this address. Select its existing client entry first to avoid overriding them.');}
async function change(p,ip,add){let s=await state();validate(s,ip);let x=inspect(s,p,ip);if(!x.managed)throw Error('This list or assignment is owned by another policy. Existing configuration left unchanged.');if(!add){if(!x.g||!x.assigned)return 'No device assignment to remove.';const c=existing(s,ip),groups=ids(c).filter(id=>id!==x.g.id);if(!c||!groups.length)throw Error('Removing this filter would leave no existing assignments. No change made.');await api('/clients/'+encodeURIComponent(c.client),'PUT',{comment:c.comment??null,groups});s=await state();const result=existing(s,ip);if(!result||ids(result).includes(x.g.id)||groups.some(id=>!ids(result).includes(id)))throw Error('Removal not verified');return 'Filter removed for this device. Other existing filters may still block these domains.';}
if(x.defaultApplies)return 'This device already receives the filter through an existing network-wide policy.';
if(!x.g){await api('/groups','POST',{name:x.name,comment:x.tag,enabled:true});s=await state();x=inspect(s,p,ip);if(!x.g||!x.managed)throw Error('Could not verify internal filter assignment');}
if(!x.l){await api('/lists?type=block','POST',{address:p[3],comment:own+p[0],groups:[x.g.id],enabled:true});s=await state();x=inspect(s,p,ip);if(!x.l||!x.managed||!on(x.l.enabled))throw Error('Could not verify new filter list');}
if(!on(x.l.enabled)){// Re-enabling a shared disabled list would change other devices. Stop rather than silently do so.
if(ids(x.l).includes(0)||s.clients.some(c=>!same(c.client,ip)&&ids(c).includes(x.g.id)))throw Error('This disabled list is shared with other devices. Existing configuration left unchanged.');await api('/lists/'+encodeURIComponent(p[3])+'?type=block','PUT',{type:'block',comment:x.l.comment,enabled:true,groups:ids(x.l)});s=await state();x=inspect(s,p,ip);if(!x.managed||!on(x.l?.enabled))throw Error('Could not verify list enabled');}
let c=existing(s,ip),groups=c?ids(c):[0];if(!groups.length)throw Error('Existing client has no explicit policy; refusing to overwrite it');if(!groups.includes(x.g.id)){groups=[...groups,x.g.id];if(c)await api('/clients/'+encodeURIComponent(c.client),'PUT',{comment:c.comment??null,groups});else await api('/clients','POST',{client:ip,comment:'PiShield device',groups});}
s=await state();c=existing(s,ip);x=inspect(s,p,ip);if(!c||!x.managed||!x.applies||!x.assigned||groups.some(id=>!ids(c).includes(id)))throw Error('Device filter assignment not verified');return 'Filter saved for '+ip+'. Update Gravity to download new lists, then test device DNS.';}
function render(s){const grid=$('psdf-grid');grid.replaceChildren();$('psdf-selected').hidden=!selected;if(!selected)return;const c=existing(s,selected);$('psdf-title').textContent=(c?.comment&&c.comment!=='PiShield device'?c.comment+' · ':'')+selected;$('psdf-coverage').textContent=(c?'Configured device.':'Not yet configured; enabling the first filter registers this IP.')+' '+(observed.has(selected)?'DNS activity observed.':'No current DNS observation for this address.')+' Global DNS blocking: '+String(s.blocking??'unknown')+'. Saved settings are not proof of traffic enforcement.';
for(const p of CATALOG){const x=inspect(s,p,selected),card=node('section',undefined,'psdf-card');card.dataset.filter=p[0];card.append(node('h3',p[1]),node('p',p[2]));let label=x.defaultApplies?'On via existing network-wide policy':x.applies?'On for this device':x.assigned?'Assigned, but filter disabled':'Off for this device';if(!x.managed)label+=' · managed elsewhere';const status=node('strong',label);status.dataset.state=x.applies?'on':!x.managed||x.assigned?'warn':'off';card.append(status);if(x.l)card.append(node('small',String(x.l.number??'Unknown')+' list entries · '+(x.l.number>0?'test DNS to verify':'update Gravity to populate list')));const add=!(x.assigned&&x.applies);const btn=node('button',add?'Turn on for device':'Turn off for device','btn btn-default');btn.type='button';btn.disabled=!x.managed||(add&&x.defaultApplies);btn.onclick=()=>{const target=selected;if(confirm((add?'Enable ':'Remove ')+p[1]+' for '+target+'? '+(add?'Confirm this is the intended device, not a router or the Pi.':'Other overlapping filters may still apply.')))run(()=>change(p,target,add));};card.append(btn);if(x.assigned&&!x.applies&&x.managed){const remove=node('button','Remove inactive assignment','btn btn-default');remove.type='button';remove.onclick=()=>{const target=selected;if(confirm('Remove inactive '+p[1]+' assignment from '+target+'?'))run(()=>change(p,target,false));};card.append(remove);}const a=node('a','List source');a.href=p[3];a.target='_blank';a.rel='noopener noreferrer';card.append(a);grid.append(card);}}
async function refreshDevices(s){const select=$('psdf-devices');const [q,v]=await Promise.all([api('/queries/suggestions').catch(()=>({})),api('/clients/suggestions').catch(()=>({}))]);observed=new Set((q.suggestions?.client_ip||[]).filter(ipv4));const choices=new Map();for(const ip of observed)choices.set(ip,ip+' · observed DNS');for(const item of (v.clients||[])){if(typeof item.addresses!=='string')continue;for(const ip of item.addresses.split(',').map(x=>x.trim()).filter(ipv4)){const existingMAC=s.clients.find(c=>same(c.client,item.hwaddr));if(existingMAC){choices.set(existingMAC.client,existingMAC.client+' · '+(item.names||item.macVendor||ip));continue;}if(!choices.has(ip))choices.set(ip,ip+' · '+(item.names||item.macVendor||'observed client'));}}
for(const c of s.clients){if(ipv4(c.client)||mac(c.client))choices.set(c.client,c.client+(c.comment?' · '+c.comment:''));}select.replaceChildren(node('option','Choose a device'));select.options[0].value='';for(const [ip,name] of choices){const opt=node('option',name);opt.value=ip;select.append(opt);}if(choices.has(selected))select.value=selected;}
async function run(fn){if(busy)return;busy=true;root.querySelectorAll('button,input,select').forEach(e=>e.disabled=true);$('psdf-status').textContent='Saving or loading…';let msg='';try{msg=await fn()||'';}catch(e){msg='Stopped: '+e.message+' Existing completed changes may remain; reload to check.';}try{const s=await state();await refreshDevices(s);render(s);$('psdf-status').textContent=msg||'Choose a device or enter its reserved IP.';}catch(e){$('psdf-status').textContent=(msg?msg+' · ':'')+'Unable to load settings: '+e.message;$('psdf-grid').replaceChildren();}finally{busy=false;for(const id of ['psdf-devices','psdf-ip','psdf-load','psdf-refresh'])$(id).disabled=false;}}
function load(){const ip=$('psdf-ip').value.trim();run(async()=>{const s=await state();validate(s,ip);selected=ip;return 'Showing device '+ip;});}
$('psdf-devices').onchange=()=>{if(!$('psdf-devices').value)return;$('psdf-ip').value=$('psdf-devices').value;load();};$('psdf-load').onclick=load;$('psdf-refresh').onclick=()=>run(async()=> 'Devices refreshed.');$('psdf-ip').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();load();}};run(async()=> 'Choose a device or enter its reserved IP.');}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();})();
