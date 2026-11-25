<? mg.include('scripts/lua/header_authenticated.lp','r') ?>
<link rel="stylesheet" href="<?=webhome?>style/pishield-device-filters.css?v=134">
<div id="psdf" class="psdf">
<h2>Device filtering &amp; privacy</h2><p>Choose a device, then turn its protections on or off. PiShield manages the internal assignments for you.</p>
<div class="box"><div class="box-body"><div class="psdf-tools"><label>Observed or configured device <select id="psdf-devices"><option value="">Choose a device</option></select></label><label>Device IP or existing client <input id="psdf-ip" placeholder="Enter device IP" autocomplete="off"></label><button type="button" class="btn btn-primary" id="psdf-load">Load device</button><button type="button" class="btn btn-default" id="psdf-refresh">Refresh devices</button><a class="btn btn-default" href="gravity">Update Gravity / download lists</a><a class="btn btn-default" href="pishield-device-privacy">Device activity</a></div><p id="psdf-status" role="status">Loading devices…</p><p>Use a reserved IP for a new device. Do not select the router or the Pi. The device must use PiShield for DNS. Existing network-wide rules stay in place. <a href="groups/lists">Review existing lists</a> or <a href="groups/domains">domain exceptions</a>.</p></div></div>
<div id="psdf-selected" hidden><h3 id="psdf-title"></h3><p id="psdf-coverage"></p><div id="psdf-grid" class="psdf-grid"></div></div>
</div><script defer src="<?=webhome?>scripts/js/pishield-device-filters.js?v=134"></script>
<? mg.include('scripts/lua/footer.lp','r') ?>
