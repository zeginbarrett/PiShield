<?
if mg.request_info.is_authenticated ~= true then mg.write('{"error":"Authentication required"}'); return end
if mg.request_info.request_method ~= 'GET' then mg.write('{"error":"Unsupported method"}'); return end
local f=io.open('/run/pishield-live/status.json','r')
if not f then mg.write('{"error":"Capture is stopped or starting"}'); return end
local s=f:read(2000000); f:close(); mg.write(s)
?>
