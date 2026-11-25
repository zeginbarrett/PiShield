#!/bin/bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run with sudo'; exit 1; }
root=/var/www/html/admin
for f in "$root/scripts/lua/sidebar.lp" "$root/scripts/lua/header.lp" "$root/pishield-defense.lp" "$root/pishield-action.lp" "$root/pishield-ai.lp" "$root/pishield-system.lp" /opt/pishield-sentinel/sentinel.py /opt/pishield-action/engine.py /var/lib/pishield-action/request; do [[ -f "$f" && ! -L "$f" ]] || { echo "Missing or unsafe v0.8 file: $f; no changes made"; exit 1; }; done
python3 -m py_compile intelligence.py recover.py patch.py activate.py
python3 patch.py --check
backup=$(mktemp -d /var/backups/pishield/intelligent-v09-XXXXXXXX); chmod 700 "$backup"
cp -a "$root/scripts/lua/sidebar.lp" "$root/scripts/lua/header.lp" "$root/pishield-defense.lp" /opt/pishield-sentinel/sentinel.py /etc/systemd/system/pishield-sentinel.timer "$backup/"
install -d -m 755 /opt/pishield-intelligent
install -d -m 700 /var/lib/pishield-intelligent
install -m 644 intelligence.py /opt/pishield-sentinel/intelligence.py
install -m 644 recover.py /opt/pishield-intelligent/recover.py
install -m 644 mobile.css "$root/style/pishield-mobile-v09.css"
python3 patch.py
install -m 644 pishield-sentinel.timer pishield-recovery.service pishield-recovery.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now pishield-sentinel.timer pishield-recovery.timer
systemctl restart pishield-sentinel.timer
systemctl start --no-block pishield-recovery.service
python3 activate.py
systemctl start --no-block pishield-action.service
systemctl start --no-block pishield-sentinel.service
printf '\nPiShield v0.9.1 installed. Backup: %s\nOpen /admin/pishield-sentinel and /admin/pishield-action. Check native feed status before assuming protection.\n' "$backup"
