<!-- PiShield AI v0.6 -->
<? mg.include('scripts/lua/header_authenticated.lp','r') ?>
<section class="ps-native-banner"><div class="ps-native-kicker">PISHIELD // INTELLIGENCE TERMINAL</div><h2>DNS Threat Analysis</h2><p>Server-side Ollama bridge · Recorded DNS history · Read-only recommendations</p></section>
<div class="box box-primary"><div class="box-header with-border"><h3 class="box-title">01 / AI configuration</h3></div><div class="box-body">
<p id="ps6-connection" role="status">Connecting to Sentinel backend…</p>
<div class="row"><div class="col-md-8"><label for="ps6-model">Local AI model</label><select id="ps6-model" class="form-control"><option>Loading models…</option></select></div><div class="col-md-4"><label for="ps6-window">History window</label><select id="ps6-window" class="form-control"><option value="1">Last hour</option><option value="6">Last 6 hours</option><option value="24" selected>Last 24 hours</option><option value="168">Last 7 days</option></select></div></div>
<p>Model selection is saved for scheduled analysis. Up to 20,000 stored records per manual run; coverage is reported. Data stays on your Pi and Windows Ollama host.</p>
<button class="btn btn-primary" id="ps6-run" disabled>Run AI analysis</button> <button class="btn btn-default" id="ps6-load" disabled>Load DNS history</button> <button class="btn btn-default" id="ps6-save" disabled>Save model</button> <button class="btn btn-default" id="ps6-rescan">Refresh connection</button>
<p id="ps6-job" role="status" style="margin-top:15px">Waiting for backend.</p></div></div>
<div class="box box-primary"><div class="box-header with-border"><h3 class="box-title">02 / Recorded DNS intelligence</h3></div><div class="box-body"><p id="ps6-coverage">No data loaded.</p><div class="row" id="ps6-tables"></div></div></div>
<div class="box box-primary"><div class="box-header with-border"><h3 class="box-title">03 / AI security report</h3></div><div class="box-body"><pre id="ps6-answer" style="white-space:pre-wrap;overflow-wrap:anywhere;min-height:100px">No report selected.</pre><button id="ps6-export" class="btn btn-default" disabled>Export report</button></div></div>
<div class="box box-primary"><div class="box-header with-border"><h3 class="box-title">04 / Stored reports</h3></div><div class="box-body"><p>Manual and scheduled reports (latest entries). Select a report to view it above.</p><div id="ps6-history"></div></div></div>
<script src="<?=pihole.fileversion('scripts/js/pishield-ai-v06.js')?>"></script>
<? mg.include('scripts/lua/footer.lp','r') ?>
