#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
[[ -f /var/www/html/admin/pishield-device-privacy.lp ]] || { echo 'PiShield 1.3.1 required; use full install.sh first.'; exit 1; }
getent group pihole >/dev/null
python3 -m py_compile capture.py patch.py
if ! command -v tcpdump >/dev/null; then apt-get update; apt-get install -y tcpdump; fi
install -d -o root -g root -m 0755 /opt/pishield-live
install -m 0644 capture.py /opt/pishield-live/
install -m 0644 pishield-live.service /etc/systemd/system/
python3 patch.py
systemctl daemon-reload
systemctl enable pishield-live.service
systemctl restart pishield-live.service
sleep 2
systemctl is-active --quiet pishield-live.service || { journalctl -u pishield-live.service -n 12 --no-pager; exit 1; }
printf '\nPiShield 1.3.2 installed. Open Live Network Monitor.\nStop capture: sudo systemctl disable --now pishield-live.service\nReview expected file-integrity changes before accepting a new baseline.\n'
