#!/bin/bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run with sudo'; exit 1; }
root=/var/www/html/admin
state=/var/lib/pishield-ai
sent=/opt/pishield-sentinel/sentinel.py
[[ -f "$sent" && -f "$root/pishield.lp" && -f "$root/scripts/js/pishield.js" ]] || { echo 'Expected PiShield v0.4 and Sentinel v0.5.1. Nothing changed.'; exit 1; }
getent group pihole >/dev/null
python3 -m py_compile worker.py
# Prepare all template changes and check Sentinel integration before touching files.
python3 - <<'PY'
from pathlib import Path
p=Path('/opt/pishield-sentinel/sentinel.py');s=p.read_text()
marker='# PISHIELD V06 MODEL OVERRIDE'
if marker not in s and s.count("cfg=json.loads(CONFIG.read_text()); minutes=15;")!=1:
    raise SystemExit('Sentinel source layout not recognized. Nothing changed.')
PY
backup=$(mktemp -d /var/backups/pishield/ai-v06-XXXXXXXX)
chmod 700 "$backup"
cp -a "$root/scripts/lua/sidebar.lp" "$root/index.lp" "$root/scripts/js/pishield.js" "$sent" "$backup/"
for f in pishield-ai.lp pishield-ai-api.lp scripts/js/pishield-ai-v06.js; do if [[ -e "$root/$f" ]]; then mkdir -p "$backup/$(dirname "$f")"; cp -a "$root/$f" "$backup/$f"; fi; done
install -d -m 755 /opt/pishield-ai
install -d -o root -g pihole -m 0750 "$state"
if [[ ! -e "$state/request" ]]; then install -o root -g pihole -m 0660 /dev/null "$state/request"; fi
[[ -f "$state/request" && ! -L "$state/request" ]] || { echo 'Invalid mailbox'; exit 1; }
chown root:pihole "$state/request"; chmod 660 "$state/request"
install -m 644 worker.py /opt/pishield-ai/worker.py
install -m 644 page.lp "$root/pishield-ai.lp"
install -m 644 endpoint.lp "$root/pishield-ai-api.lp"
install -m 644 ui.js "$root/scripts/js/pishield-ai-v06.js"
python3 - <<'PY'
from pathlib import Path
import re, os, tempfile
root=Path('/var/www/html/admin')
def atomic(p,s):
    fd,t=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'w') as f:f.write(s)
        os.chmod(t,0o644);os.replace(t,p)
    finally:
        if os.path.exists(t):os.unlink(t)
for name in ('scripts/lua/sidebar.lp','index.lp'):
    p=root/name;s=p.read_text();s=s.replace('pishield#ai','pishield-ai');atomic(p,s)
p=root/'scripts/js/pishield.js';s=p.read_text();marker='// PISHIELD V06 AI REDIRECT'
if marker not in s:
    s='''// PISHIELD V06 AI REDIRECT
(()=>{const route=()=>{if(location.hash.toLowerCase()==='#ai'){location.replace((document.body?.dataset.webhome||'/admin/')+'pishield-ai');}};route();window.addEventListener('hashchange',route);})();
'''+s
    atomic(p,s)
p=Path('/opt/pishield-sentinel/sentinel.py');s=p.read_text();marker='# PISHIELD V06 MODEL OVERRIDE'
if marker not in s:
    s=s.replace("now=int(time.time()); cfg=json.loads(CONFIG.read_text()); minutes=15; since=now-minutes*60", """now=int(time.time()); cfg=json.loads(CONFIG.read_text()); minutes=15; since=now-minutes*60
    # PISHIELD V06 MODEL OVERRIDE
    try:
        model_override=json.loads(pathlib.Path('/var/lib/pishield-ai/model.json').read_text()).get('model')
        if isinstance(model_override,str) and model_override: cfg['model']=model_override
    except (OSError,ValueError,AttributeError): pass""")
    compile(s,str(p),'exec');atomic(p,s)
PY
install -m 644 pishield-ai.service /etc/systemd/system/pishield-ai.service
systemctl daemon-reload
systemctl enable pishield-ai.service
systemctl restart pishield-ai.service
printf '\nPiShield v0.6 installed. Backup: %s\n' "$backup"
printf 'Open /admin/pishield-ai (log in first). No DNS restart required.\n'
