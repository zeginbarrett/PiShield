#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
[[ -f /var/www/html/admin/pishield-guard.lp && -f /opt/pishield-guard/guard.py ]] || { echo 'PiShield 1.1 required. For a fresh installation use the repository install.sh.'; exit 1; }
getent group pihole >/dev/null
python3 -m py_compile monitor.py notify.py patch.py
install -d -o root -g root -m 0755 /opt/pishield-proactive
install -d -o root -g pihole -m 0750 /var/lib/pishield-proactive
install -d -o root -g root -m 0700 /etc/pishield-proactive
python3 patch.py
install -m 0644 monitor.py notify.py /opt/pishield-proactive/
install -m 0755 control.sh /usr/local/sbin/pishield-proactive
for unit in pishield-proactive.service pishield-proactive.timer pishield-proactive-notify.service pishield-proactive-notify.timer; do install -m 0644 "$unit" /etc/systemd/system/; done
systemctl daemon-reload
systemctl enable --now pishield-proactive.timer pishield-proactive-notify.timer
systemctl start pishield-proactive.service
printf '\nPiShield v1.2 installed. Refresh Host security.\nFirewall, network settings and DNS unchanged. Optional controls: docs/PROACTIVE-DEFENSE.md\n'
echo 'The prior file-integrity baseline is preserved. Review expected upgrade changes before accepting a new baseline.'
