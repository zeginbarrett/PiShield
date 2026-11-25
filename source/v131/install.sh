#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
[[ -f /opt/pishield-privacy/monitor.py && -f /var/www/html/admin/pishield-privacy.lp ]] || { echo 'PiShield 1.3 required; run pishield-v130.sh or full install.sh first.'; exit 1; }
python3 patch.py
printf '\nPiShield 1.3.1 installed. Open Filtering > Device Privacy Monitor or Sony Bravia on Privacy & data protection.\nNo DNS, firewall or notification configuration changed. New Sony filter is off until enabled and Gravity updated.\nReview expected file-integrity changes before accepting a new baseline.\n'
