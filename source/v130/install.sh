#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
[[ -f /opt/pishield-proactive/monitor.py && -f /var/www/html/admin/pishield-proactive-api.lp ]] || { echo 'PiShield 1.2 required; use full repository install.sh for a new installation.'; exit 1; }
getent group pihole >/dev/null
python3 -m py_compile monitor.py patch.py
python3 patch.py
install -d -m 0755 -o root -g root /opt/pishield-privacy
install -d -m 0750 -o root -g pihole /var/lib/pishield-privacy
install -m 0644 monitor.py catalog.json /opt/pishield-privacy/
install -m 0644 pishield-privacy.service pishield-privacy.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now pishield-privacy.timer
systemctl start pishield-privacy.service
printf '\nPiShield v1.3 installed. Open Filtering > Privacy & data protection.\nNew filters are OFF; existing DNS and firewall settings unchanged.\nReview expected integrity changes before accepting a new baseline.\n'
