#!/bin/bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
case "${1:-}" in
 ssh-on)
   [[ $# == 2 ]] || { echo 'Usage: sudo pishield-proactive ssh-on TRUSTED_ADMIN_IP'; exit 1; }
   trusted=$(python3 -c 'import ipaddress,sys; print(ipaddress.ip_address(sys.argv[1]))' "$2")
   command -v fail2ban-client >/dev/null || { echo 'First run: sudo apt install fail2ban python3-systemd nftables'; exit 1; }
   p=/etc/fail2ban/jail.d/99-pishield-sshd.local
   [[ ! -e $p ]] || { echo 'Existing PiShield jail configuration; edit it manually.'; exit 1; }
   [[ ! -e /etc/fail2ban/jail.local ]] || { echo 'Existing jail.local detected; merge settings manually, see guide.'; exit 1; }
   umask 022
   cat > "$p" <<JAIL
[sshd]
enabled = true
backend = systemd
banaction = nftables
port = ssh
maxretry = 6
findtime = 10m
bantime = 15m
ignoreip = 127.0.0.1/8 ::1 $trusted
JAIL
   if ! fail2ban-client -t; then rm -f "$p"; echo 'Configuration rejected; removed PiShield drop-in.'; exit 1; fi
   if ! systemctl enable --now fail2ban.service || ! fail2ban-client reload || ! fail2ban-client status sshd; then
       rm -f "$p"; fail2ban-client reload || true; echo 'Failed to activate the PiShield jail; drop-in removed.'; exit 1
   fi
   echo 'SSH protection configured. Test a new login; current trusted address is excluded.';;
 updates-on)
   [[ $# == 1 ]] || exit 2
   command -v unattended-upgrade >/dev/null || { echo 'First run: sudo apt install unattended-upgrades'; exit 1; }
   p=/etc/apt/apt.conf.d/99-pishield-security
   [[ ! -e $p ]] || { echo 'Existing PiShield update policy; inspect it manually.'; exit 1; }
   umask 022
   cat > "$p" <<'APT'
// PiShield: opt-in Debian security archive only, no automatic reboot.
#clear Unattended-Upgrade::Allowed-Origins;
#clear Unattended-Upgrade::Origins-Pattern;
Unattended-Upgrade::Origins-Pattern { "origin=Debian,codename=${distro_codename}-security"; };
Unattended-Upgrade::Automatic-Reboot "false";
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT
   echo 'Review the effective policy and dry run before enabling timers.'
   apt-config dump | grep -E 'Unattended-Upgrade::(Allowed-Origins|Origins-Pattern|Automatic-Reboot)|APT::Periodic::(Update-Package-Lists|Unattended-Upgrade)' || true
   if ! unattended-upgrade --dry-run; then rm -f "$p"; echo 'Dry run failed; PiShield policy removed.'; exit 1; fi
   read -r -p 'Enable daily security updates (no automatic reboot)? [y/N] ' answer
   if [[ $answer != [yY] ]]; then rm -f "$p"; echo 'PiShield policy removed.'; exit 0; fi
   systemctl enable --now apt-daily.timer apt-daily-upgrade.timer
   echo 'Security update policy configured. Raspberry Pi vendor updates remain manual.';;
 check) systemctl start pishield-proactive.service; cat /var/lib/pishield-proactive/status.json; echo;;
 *) echo 'Usage: pishield-proactive check | ssh-on TRUSTED_ADMIN_IP | updates-on'; exit 2;;
esac
