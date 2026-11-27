#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
[[ -f /var/www/html/admin/pishield-intelligence.lp ]] || { echo 'PiShield 2.0 required; run the full repository installer first.'; exit 1; }
getent group pihole >/dev/null
python3 -m py_compile worker.py patch.py
python3 patch.py
install -d -o root -g root -m 0755 /opt/pishield-chat
install -m 0644 worker.py /opt/pishield-chat/worker.py
install -m 0644 pishield-chat.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable pishield-chat.service
systemctl restart pishield-chat.service
systemctl restart pishield-ai.service
sleep 2
systemctl is-active --quiet pishield-chat.service || { journalctl -u pishield-chat.service -n 15 --no-pager; exit 1; }
printf '\nPiShield 2.0.1 installed. Open Intelligence > Ask PiShield.\nNew manual and scheduled reports use plain English. No DNS or firewall changes.\nReview expected file-integrity changes before accepting a new baseline.\n'
