#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
[[ -f /opt/pishield-chat/worker.py && -f /var/www/html/admin/pishield-chat.lp ]] || { echo 'Install PiShield 2.0.1 first.'; exit 1; }
python3 -m py_compile worker.py patch.py approve.py actions.py theme.py
install -d -m 0750 -o root -g pihole /var/lib/pishield-theme
install -d -m 0700 -o root -g root /var/lib/pishield-workshop
install -d -m 0755 -o root -g root /opt/pishield-chat
backup=$(mktemp -d /var/backups/pishield/workshop-service-XXXXXXXX); chmod 700 "$backup"
cp -p /opt/pishield-chat/worker.py "$backup/worker.py"
cp -p /etc/systemd/system/pishield-chat.service "$backup/pishield-chat.service"
for f in worker.py actions.py approve.py theme.py; do install -m 0644 -o root -g root "$f" /opt/pishield-chat/; done
cat > /usr/local/sbin/pishield-approve <<'EOF'
#!/bin/sh
exec /usr/bin/python3 -I /opt/pishield-chat/approve.py "$@"
EOF
chmod 0755 /usr/local/sbin/pishield-approve
install -m 0644 -o root -g root pishield-chat.service /etc/systemd/system/pishield-chat.service
systemctl daemon-reload
rollback(){ install -m 0644 "$backup/worker.py" /opt/pishield-chat/worker.py; install -m 0644 "$backup/pishield-chat.service" /etc/systemd/system/pishield-chat.service; systemctl daemon-reload; systemctl restart pishield-chat.service; }
# Python isolated mode excludes script directory; explicitly use a fixed module path in approval helper.
if ! systemctl restart pishield-chat.service; then rollback; exit 1; fi
sleep 2
if ! systemctl is-active --quiet pishield-chat.service; then rollback; journalctl -u pishield-chat.service -n 12 --no-pager; exit 1; fi
if ! python3 patch.py; then rollback; exit 1; fi
printf '\nPiShield 2.1 installed. Open Intelligence > AI Chat or Tool Workshop.\nNo network policies changed. Review expected integrity changes.\n'
