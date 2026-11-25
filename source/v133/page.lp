<? mg.include('scripts/lua/header_authenticated.lp','r') ?>
<link rel="stylesheet" href="<?=webhome?>style/pishield-live.css?v=133">
<div class="ps-native-banner"><div class="ps-native-kicker">PISHIELD / LIVE MONITOR</div><h2>Live Network Monitor</h2><p>Watch DNS and other visible IP packets. This Pi is not an inline network gateway.</p></div>
<div id="pslive" class="pslive"><div class="box"><div class="box-body">
<div class="pslive-presets" role="group" aria-label="Packet filter presets">
<button class="btn btn-default" type="button" data-preset="all">All visible IP</button>
<button class="btn btn-default" type="button" data-preset="dns">All DNS</button>
<button class="btn btn-default" type="button" data-preset="https">HTTPS / port 443</button>
<button class="btn btn-default" type="button" data-preset="icmp">ICMP / ping</button>
<button class="btn btn-default" type="button" data-preset="device">Device traffic</button>
<button class="btn btn-default" type="button" data-preset="device-dns">Device DNS</button>
</div>
<div class="pslive-tools"><label>Device IP <input id="pslive-ip" placeholder="Enter device IP" autocomplete="off"></label><label>Direction <select id="pslive-kind"><option value="all">Both</option><option>To DNS port</option><option>From DNS port</option></select></label><label>Port <input id="pslive-port" type="number" min="1" max="65535" placeholder="Any"></label><label>Find <input id="pslive-search" placeholder="Domain, IP or detail"></label><button class="btn btn-default" type="button" id="pslive-pause">Pause display</button><button class="btn btn-default" type="button" id="pslive-clear">Clear display</button><a class="btn btn-default" href="pishield-device-privacy">Device history</a></div><p id="pslive-scope" role="status"></p><p id="pslive-state" role="status">Connecting…</p><p class="pslive-note">Up to 300 DNS and 300 other IP packet summaries, retained for at most five minutes in RAM. Presets filter the display, not firewall rules. Pause and clear affect the display only. Port 443 is a hint, not proof of HTTPS. No decrypted payloads or raw packet files.</p></div></div>
<div class="box"><div class="box-body"><div class="pslive-metrics" id="pslive-metrics"></div><div class="pslive-scroll"><table class="table table-striped"><thead><tr><th>Time</th><th>Interface</th><th>Source</th><th>Destination</th><th>Protocol</th><th>Packet details</th></tr></thead><tbody id="pslive-rows"></tbody></table></div></div></div></div>
<script defer src="<?=webhome?>scripts/js/pishield-live.js?v=133"></script>
<? mg.include('scripts/lua/footer.lp','r') ?>
