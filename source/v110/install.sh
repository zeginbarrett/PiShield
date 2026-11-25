#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
root=/var/www/html/admin
[[ -f "$root/scripts/js/pishield-v100.js" && -f "$root/scripts/lua/sidebar.lp" ]] || { echo 'PiShield 1.0 required. For a fresh installation use the repository install.sh.'; exit 1; }
getent group pihole >/dev/null
# Do not accept a new integrity baseline on repeat installation.
install -d -o root -g root -m 0755 /opt/pishield-guard
install -d -o root -g pihole -m 0750 /var/lib/pishield-guard
install -d -o root -g root -m 0700 /etc/pishield-guard
python3 -m py_compile guard.py control.py patch.py
# Fix old command transport if necessary, using the bundled 1.0 maintenance files.
if ! grep -q 'x-pishield-command' "$root/pishield-ai-api.lp"; then
    python3 ../v101/patch.py
fi
python3 patch.py
install -m 0644 guard.py /opt/pishield-guard/guard.py
install -m 0755 control.py /usr/local/sbin/pishield-guard
for unit in pishield-guard.service pishield-guard.timer pishield-guard-firewall.service; do install -m 0644 "$unit" /etc/systemd/system/; done
# Baseline only on first install, after all tracked files have been installed.
if [[ ! -e /var/lib/pishield-guard/baseline.json ]]; then /usr/bin/python3 /opt/pishield-guard/guard.py --baseline; fi
systemctl daemon-reload
systemctl enable --now pishield-guard.timer
if ! systemctl start pishield-guard.service; then echo 'Host check failed. Inspect: sudo journalctl -u pishield-guard.service -n 30'; fi
printf '\nPiShield v1.1 installed. Open Host security in the sidebar.\nNo firewall enabled automatically. Existing DNS settings preserved.\n'
