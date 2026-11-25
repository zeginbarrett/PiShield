#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
python3 -m py_compile patch.py
python3 patch.py
printf '\nPiShield 1.3.4 installed. Open Filtering > Device filtering & privacy.\nNo DNS policies, firewall, or notification settings changed during installation. Review expected file-integrity changes before accepting a new baseline.\n'
