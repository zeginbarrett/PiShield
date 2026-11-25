#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
python3 patch.py
echo 'PiShield 1.2.2 installed. Refresh your browser (Ctrl+F5). DNS, firewall and notification settings unchanged.'
