#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
[[ -f /var/www/html/admin/pishield-privacy.lp && -f /var/www/html/admin/pishield-live.lp ]] || { echo 'PiShield 1.3.5 required; use full installer for earlier versions.'; exit 1; }
getent group pihole >/dev/null
python3 -m py_compile collect.py check.py patch.py
install -d -o root -g root -m 0755 /opt/pishield-intelligence
install -d -o root -g pihole -m 0750 /var/lib/pishield-intelligence
install -m 0644 collect.py /opt/pishield-intelligence/
install -m 0755 check.py /usr/local/sbin/pishield-device-check
install -m 0644 pishield-intelligence.service pishield-intelligence.timer /etc/systemd/system/
systemctl daemon-reload
systemctl start pishield-intelligence.service
python3 -c 'import json,time; x=json.load(open("/var/lib/pishield-intelligence/status.json")); assert abs(time.time()-x["updated"])<120'
python3 patch.py
systemctl enable --now pishield-intelligence.timer
printf '\nPiShield 2.0 installed. Open Network > Device Intelligence. Existing DNS, firewall and notifications unchanged. Review expected integrity changes before rebaselining.\n'
