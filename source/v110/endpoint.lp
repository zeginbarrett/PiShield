<?
if mg.request_info.is_authenticated ~= true then mg.write('{"error":"Authentication required"}'); return end
if mg.request_info.request_method ~= 'GET' then mg.write('{"error":"Unsupported method"}'); return end
local f=io.open('/var/lib/pishield-guard/status.json','r')
if not f then mg.write('{"error":"Host checks not ready"}'); return end
local s=f:read('*a'); f:close(); mg.write(s)
?>
