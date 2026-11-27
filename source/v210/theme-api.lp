<?
if mg.request_info.is_authenticated~=true or mg.request_info.request_method~='GET' then mg.write('{}');return end
local f=io.open('/var/lib/pishield-theme/theme.json','r')
if not f then mg.write('{}');return end
local s=f:read(4096);f:close();mg.write(s or '{}')
?>
