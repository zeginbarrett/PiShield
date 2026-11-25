#!/bin/bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run with sudo'; exit 1; }
root=/var/www/html/admin
sidebar="$root/scripts/lua/sidebar.lp"
state=/var/lib/pishield-defense
[[ -f "$sidebar" && -f "$root/pishield-ai.lp" && -f /opt/pishield-sentinel/sentinel.py ]] || { echo 'Requires working PiShield v0.6 and Sentinel. No changes made.'; exit 1; }
getent group pihole >/dev/null
python3 -m py_compile collector.py
python3 - "$sidebar" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text(); marker='<!-- PISHIELD DEFENSE V07 -->'
if marker not in s and s.count('<li class="header text-uppercase">Group Management</li>') != 1:
    raise SystemExit('Unrecognized sidebar layout. No changes made.')
PY
backup=$(mktemp -d /var/backups/pishield/defense-v07-XXXXXXXX)
chmod 700 "$backup"
for f in scripts/lua/sidebar.lp pishield-defense.lp pishield-defense-api.lp scripts/js/pishield-defense.js; do if [[ -f "$root/$f" ]]; then mkdir -p "$backup/$(dirname "$f")"; cp -a "$root/$f" "$backup/$f"; fi; done
install -d -m 755 /opt/pishield-defense
install -d -o root -g pihole -m 0750 "$state"
if [[ ! -e "$state/request" ]]; then install -o root -g pihole -m 0660 /dev/null "$state/request"; fi
[[ -f "$state/request" && ! -L "$state/request" ]] || { echo 'Invalid mailbox'; exit 1; }
chown root:pihole "$state/request"; chmod 660 "$state/request"
install -m 644 collector.py /opt/pishield-defense/collector.py
install -m 644 page.lp "$root/pishield-defense.lp"
install -m 644 endpoint.lp "$root/pishield-defense-api.lp"
install -m 644 ui.js "$root/scripts/js/pishield-defense.js"
python3 - "$sidebar" <<'PY'
from pathlib import Path
import sys,os,tempfile
p=Path(sys.argv[1]);s=p.read_text();marker='<!-- PISHIELD DEFENSE V07 -->';anchor='<li class="header text-uppercase">Group Management</li>'
if marker not in s:
    s=s.replace(anchor,marker+'''\n                <li class="menu-system<? if scriptname == 'pishield-defense' then ?> active<? end ?>"><a href="<?=webhome?>pishield-defense"><i class="fa fa-fw menu-icon fa-shield-alt"></i> <span>Active defense</span></a></li>\n                '''+anchor,1)
    fd,t=tempfile.mkstemp(dir=p.parent)
    with os.fdopen(fd,'w') as f:f.write(s)
    os.chmod(t,0o644);os.replace(t,p)
PY
install -m 644 pishield-defense.service /etc/systemd/system/pishield-defense.service
install -m 644 pishield-defense.timer /etc/systemd/system/pishield-defense.timer
systemctl daemon-reload
systemctl enable --now pishield-defense.timer
systemctl start pishield-defense.service
printf '\nPiShield Active Defense v0.7 installed. Backup: %s\nOpen /admin/pishield-defense. No DNS changes.\n' "$backup"
