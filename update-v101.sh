#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ $EUID == 0 ]] || { echo 'Run: sudo bash update-v101.sh'; exit 1; }
[[ $# == 0 ]] || { echo 'Usage: sudo bash update-v101.sh'; exit 2; }
python3 source/v101/patch.py
