#!/bin/bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Use sudo'; exit 1; }
[[ -f /var/www/html/admin/pishield.lp ]] && grep -q 'PiShield extension v0.4' /var/www/html/admin/pishield.lp || { echo 'Install v0.4 first.'; exit 1; }
install -d -m 755 /opt/pishield-sentinel
install -d -m 700 /var/lib/pishield-sentinel
for f in sentinel.py patch.py brand.js brand.css logo.svg; do install -m 644 "$f" /opt/pishield-sentinel/; done
python3 /opt/pishield-sentinel/patch.py
if [[ ! -e /etc/pishield-sentinel.json ]]; then
  umask 077
  printf '%s\n' '{"ai_enabled":true,"model":"qwen3.5:4b"}' >/etc/pishield-sentinel.json
fi
if [[ ! -e /var/lib/pishield-sentinel/threat-domains.txt ]]; then touch /var/lib/pishield-sentinel/threat-domains.txt; chmod 600 /var/lib/pishield-sentinel/threat-domains.txt; fi
if [[ ! -e /var/www/html/admin/pishield-sentinel.lp ]]; then
  cat >/var/www/html/admin/pishield-sentinel.lp <<'PAGE'
<!-- PiShield Sentinel v0.5 generated -->
<? mg.include('scripts/lua/header_authenticated.lp','r') ?>
<div class="box box-primary"><div class="box-body"><h2>Sentinel is initializing</h2><p>First recorded DNS analysis is running. Refresh to load the result.</p></div></div>
<? mg.include('scripts/lua/footer.lp','r') ?>
PAGE
  chmod 644 /var/www/html/admin/pishield-sentinel.lp
fi
install -m 644 pishield-sentinel.service pishield-sentinel.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now pishield-sentinel.timer
systemctl start --no-block pishield-sentinel.service
printf '%s\n' 'Sentinel v0.5.1 installed. Refresh /admin/pishield-sentinel. No DNS or blocklist changes.'
