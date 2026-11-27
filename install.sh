#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
root=/var/www/html/admin
state=/var/lib/pishield-install
[[ $EUID == 0 ]] || { echo 'Run: sudo bash install.sh'; exit 1; }
[[ $# == 0 ]] || { echo 'Usage: sudo bash install.sh'; exit 2; }
command -v apt-get >/dev/null && command -v systemctl >/dev/null || { echo 'Requires Raspberry Pi OS / Debian with systemd.'; exit 1; }
if [[ -f "$root/scripts/js/pishield-v100.js" ]]; then
  echo 'Existing PiShield dashboard detected. Applying 2.0.1.'
  if [[ ! -f "$root/pishield-guard.lp" ]]; then bash pishield-v110.sh; fi
  if [[ ! -f "$root/pishield-proactive-api.lp" || ! -f /opt/pishield-proactive/monitor.py ]]; then bash pishield-v120.sh; fi
  bash pishield-v121.sh
  if [[ ! -f "$root/pishield-privacy.lp" || ! -f /opt/pishield-privacy/monitor.py ]]; then bash pishield-v130.sh; fi
  if [[ ! -f "$root/pishield-device-privacy.lp" ]]; then bash pishield-v131.sh; fi
  if [[ ! -f "$root/pishield-live.lp" || ! -f /opt/pishield-live/capture.py ]]; then bash pishield-v132.sh; fi
  if ! grep -Eq 'pishield-v100\.js\?v=(133|134|135|200|201)\b' "$root/scripts/lua/header.lp"; then bash pishield-v133.sh; fi
  if ! grep -Eq 'pishield-v100\.js\?v=(134|135|200|201)\b' "$root/scripts/lua/header.lp"; then bash pishield-v134.sh; fi
  if ! grep -Eq 'pishield-v100\.js\?v=(135|200|201)\b' "$root/scripts/lua/header.lp"; then bash pishield-v135.sh; fi
  if ! grep -Eq 'pishield-v100\.js\?v=(200|201)\b' "$root/scripts/lua/header.lp"; then bash pishield-v200.sh; fi
  bash pishield-v201.sh
  exec bash pishield-v100.sh --check
fi
if [[ -f "$root/scripts/js/pishield-pages-v093.js" && ! -d "$state" ]]; then
  bash pishield-v100.sh
  bash pishield-v110.sh
  bash pishield-v120.sh
  bash pishield-v121.sh
  bash pishield-v130.sh
  bash pishield-v131.sh
  bash pishield-v132.sh
  bash pishield-v133.sh
  bash pishield-v134.sh
  bash pishield-v135.sh
  bash pishield-v200.sh
  exec bash pishield-v201.sh
fi
if [[ -f "$root/pishield.lp" && ! -d "$state" ]]; then
  echo 'Existing older PiShield installation detected. Do not overwrite it with the fresh-install sequence.'
  echo 'Complete the documented incremental upgrade or restore a backup first.'
  exit 1
fi
for f in components/*.sh pishield-v100.sh; do bash -n "$f"; done
printf '%s\n' 'PiShield 2.0.1 modifies the installed Pi-hole web interface and adds background services.' 'Review the source and create a system backup before proceeding.'
read -r -p 'Continue? [y/N] ' answer
[[ "$answer" == [yY] ]] || exit 0
apt-get update
apt-get install -y ca-certificates curl git python3 iproute2 iputils-ping iw tar lshw bind9-dnsutils
if ! command -v pihole >/dev/null; then
  tmp=$(mktemp)
  trap 'rm -f "$tmp"' EXIT
  curl -fL --proto '=https' https://install.pi-hole.net -o "$tmp"
  bash "$tmp"
  rm -f "$tmp"; trap - EXIT
fi
command -v pihole >/dev/null && [[ -f "$root/scripts/lua/header_authenticated.lp" ]] || { echo 'Pi-hole installation did not complete.'; exit 1; }
versions=$(pihole version)
printf '%s\n' "$versions"
if ! grep -qE 'Core version is v6\.' <<< "$versions"; then echo 'Requires Pi-hole v6. No PiShield changes made.'; exit 1; fi
if ! grep -q 'Web version is v6.6.1' <<< "$versions"; then
  echo 'Warning: web templates differ from the tested v6.6.1 release. Compatibility checks may stop the install.'
  read -r -p 'Try anyway? [y/N] ' answer; [[ "$answer" == [yY] ]] || exit 1
fi
install -d -m 700 "$state" /var/backups/pishield
if [[ ! -e "$state/preinstall" ]]; then
  backup=$(mktemp -d /var/backups/pishield/full-install-XXXXXXXX)
  chmod 700 "$backup"
  tar -czf "$backup/web-before.tar.gz" -C /var/www/html admin
  printf '%s\n' "$backup" > "$state/preinstall"
  echo "Original web interface backup: $backup"
fi
stage() {
  local name=$1; shift
  if [[ -f "$state/$name.done" ]]; then echo "Already completed: $name"; return; fi
  echo "=== Installing $name ==="
  "$@"
  touch "$state/$name.done"
}
stage v03 bash components/pishield-v03.sh
stage v04 bash components/pishield-v04.sh
stage v051 bash components/pishield-v051.sh
stage brand bash components/pishield-brand-v053.sh
stage layout bash components/pishield-layout-v054.sh
stage v06 bash components/pishield-v06.sh
stage v07 bash components/pishield-v07.sh
stage v08 bash components/pishield-v08.sh
# Fresh installs begin in observation mode. Users enable additional feeds explicitly.
install -d -m 700 /var/lib/pishield-intelligent
if [[ ! -e "$state/v091.done" ]]; then touch /var/lib/pishield-intelligent/activation-requested; fi
stage v091 bash components/pishield-v091.sh
stage v092 bash components/pishield-layout-v092.sh
stage v093 bash components/pishield-pages-v093.sh
stage v100 bash pishield-v100.sh
stage v101 bash update-v101.sh
stage v110 bash pishield-v110.sh
stage v120 bash pishield-v120.sh
stage v121 bash pishield-v121.sh
stage v130 bash pishield-v130.sh
stage v131 bash pishield-v131.sh
stage v132 bash pishield-v132.sh
stage v133 bash pishield-v133.sh
stage v134 bash pishield-v134.sh
stage v135 bash pishield-v135.sh
stage v200 bash pishield-v200.sh
stage v201 bash pishield-v201.sh
printf '\nPiShield 2.0.1 installed. Open http://<YOUR-PI-IP>/admin/\n'
echo 'Select Active defense to enable the managed threat feeds. Configure the optional Ollama bridge using docs/LOCAL-AI.md.'
hostname -I || true
bash pishield-v100.sh --check
