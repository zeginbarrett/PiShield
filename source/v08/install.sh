#!/bin/bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run with sudo'; exit 1; }
root=/var/www/html/admin
sidebar="$root/scripts/lua/sidebar.lp"
state=/var/lib/pishield-action
[[ -f "$sidebar" && -f "$root/pishield-defense.lp" && -f "$root/pishield-ai.lp" && -r /etc/pihole/cli_pw ]] || { echo 'Requires working v0.7 and native CLI authentication. No changes made.'; exit 1; }
getent group pihole >/dev/null
python3 -m py_compile engine.py
python3 - "$sidebar" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
if '<!-- PISHIELD ACTION V08 -->' not in s and s.count('<li class="header text-uppercase">Group Management</li>')!=1:raise SystemExit('Unrecognized sidebar layout. No changes made.')
PY
mkdir -p /var/backups/pishield
backup=$(mktemp -d /var/backups/pishield/action-v08-XXXXXXXX); chmod 700 "$backup"
for f in scripts/lua/sidebar.lp pishield-action.lp pishield-action-api.lp scripts/js/pishield-action.js; do if [[ -f "$root/$f" ]]; then mkdir -p "$backup/$(dirname "$f")"; cp -a "$root/$f" "$backup/$f"; fi; done
install -d -m 755 /opt/pishield-action
install -d -o root -g pihole -m 0750 "$state"
if [[ ! -e "$state/request" ]]; then install -o root -g pihole -m 0660 /dev/null "$state/request"; fi
[[ -f "$state/request" && ! -L "$state/request" ]] || { echo 'Invalid mailbox'; exit 1; }
chown root:pihole "$state/request"; chmod 660 "$state/request"
install -m 644 engine.py /opt/pishield-action/engine.py
install -m 644 page.lp "$root/pishield-action.lp"
install -m 644 endpoint.lp "$root/pishield-action-api.lp"
install -m 644 ui.js "$root/scripts/js/pishield-action.js"
python3 - "$sidebar" <<'PY'
from pathlib import Path
import sys,os,tempfile
p=Path(sys.argv[1]);s=p.read_text();marker='<!-- PISHIELD ACTION V08 -->';anchor='<li class="header text-uppercase">Group Management</li>'
if marker not in s:
    s=s.replace(anchor,marker+'''\n                <li class="menu-system<? if scriptname == 'pishield-action' then ?> active<? end ?>"><a href="<?=webhome?>pishield-action"><i class="fa fa-fw menu-icon fa-shield-alt"></i> <span>Defense control</span></a></li>\n                '''+anchor,1)
    fd,t=tempfile.mkstemp(dir=p.parent)
    with os.fdopen(fd,'w') as f:f.write(s)
    os.chmod(t,0o644);os.replace(t,p)
PY
install -m 644 pishield-action.service /etc/systemd/system/pishield-action.service
install -m 644 pishield-action.timer /etc/systemd/system/pishield-action.timer
systemctl daemon-reload
systemctl enable --now pishield-action.timer
systemctl start --no-block pishield-action.service
printf '\nPiShield v0.8 installed. Backup: %s\nOpen /admin/pishield-action and select Active defense to enable filtering. Existing rules unchanged until activation.\n' "$backup"
