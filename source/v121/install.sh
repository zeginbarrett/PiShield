#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
[[ -f /opt/pishield-proactive/notify.py && -f /etc/systemd/system/pishield-proactive-notify.service ]] || { echo 'PiShield 1.2 required; use install.sh for a fresh install'; exit 1; }
getent group pihole >/dev/null
python3 -m py_compile notify.py
backup=$(mktemp -d /var/backups/pishield/notifications-v121-XXXXXXXX)
chmod 700 "$backup"
cp -p /opt/pishield-proactive/notify.py /etc/systemd/system/pishield-proactive-notify.service "$backup/"
systemctl stop pishield-proactive-notify.timer
systemctl stop pishield-proactive-notify.service
rollback() {
  install -m 0644 "$backup/notify.py" /opt/pishield-proactive/notify.py
  install -m 0644 "$backup/pishield-proactive-notify.service" /etc/systemd/system/pishield-proactive-notify.service
  systemctl daemon-reload
  systemctl start pishield-proactive-notify.timer
}
trap 'rollback' ERR
install -m 0644 notify.py /opt/pishield-proactive/notify.py
install -m 0644 pishield-proactive-notify.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now pishield-proactive-notify.timer
trap - ERR
printf 'PiShield notification update 1.2.1 installed. Backup: %s\n' "$backup"
echo 'Existing ntfy configuration and firewall unchanged. Test: sudo python3 /opt/pishield-proactive/notify.py --test'
