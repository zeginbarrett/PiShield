#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
[[ -f /var/www/html/admin/pishield-live.lp && -f /opt/pishield-live/capture.py && -f /etc/systemd/system/pishield-live.service ]] || { echo 'PiShield 1.3.2 required; use full install.sh first.'; exit 1; }
getent group pihole >/dev/null
python3 -m py_compile capture.py patch.py
command -v tcpdump >/dev/null || { echo 'Install tcpdump first.'; exit 1; }
install -d -m 0700 /var/backups/pishield
backup=$(mktemp -d /var/backups/pishield/live-service-v133-XXXXXXXX)
chmod 700 "$backup"
cp -p /opt/pishield-live/capture.py /etc/systemd/system/pishield-live.service "$backup/"
rollback(){ install -m 0644 "$backup/capture.py" /opt/pishield-live/; install -m 0644 "$backup/pishield-live.service" /etc/systemd/system/; systemctl daemon-reload; systemctl restart pishield-live.service; }
trap 'rollback' ERR
install -m 0644 capture.py /opt/pishield-live/
install -m 0644 pishield-live.service /etc/systemd/system/
systemctl daemon-reload
systemctl restart pishield-live.service
ready=0
for i in {1..12}; do
  if systemctl is-active --quiet pishield-live.service && python3 -c 'import json,time; d=json.load(open("/run/pishield-live/status.json")); assert d.get("schema")==2 and abs(time.time()-d["updated"])<5' 2>/dev/null; then ready=1; break; fi
  sleep 1
done
if [[ $ready != 1 ]]; then journalctl -u pishield-live.service -n 12 --no-pager; rollback; exit 1; fi
python3 patch.py
trap - ERR
printf '\nPiShield 1.3.3 installed. Refresh Live Network Monitor.\nCapture presets are display filters, not firewall changes. Existing DNS settings unchanged.\nService backup: %s\n' "$backup"
