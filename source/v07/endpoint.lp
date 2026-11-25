<?
-- PiShield defense API. Pi-hole supplies HTTP headers; write JSON body only.
local ri=mg.request_info
local function respond(s) mg.write(s) end
if ri.is_authenticated ~= true then respond('{"error":"Authentication required"}'); return end
-- FTL serves .lp templates only for GET/HEAD. Commands use a dedicated
-- authenticated, CSRF-protected header; ordinary GET requests never write.
local function header(name)
  for k,v in pairs(ri.http_headers or {}) do
    if string.lower(k)==name then return v end
  end
  return nil
end
if ri.request_method~='GET' then respond('{"error":"Unsupported method"}');return end
local body=header('x-pishield-command')
if body==nil then
  local f=io.open('/var/lib/pishield-defense/status.json','r')
  if not f then respond('{"error":"Collector has not published a snapshot yet"}'); return end
  local s=f:read('*a'); f:close(); respond(s); return
end
local site=header('sec-fetch-site')
if site and site~='same-origin' then respond('{"error":"Cross-origin command rejected"}');return end
if type(body)~='string' or #body>1024 or #body==0 then respond('{"error":"Invalid request"}');return end
local token=header('x-csrf-token')
if type(ri.csrf_token)~='string' or #ri.csrf_token==0 or token~=ri.csrf_token then respond('{"error":"CSRF validation failed; reload and log in again"}');return end
local id=mg.get_var(body,'id') or ''
if mg.get_var(ri.query_string or '', 'pscmd')~=id then respond('{"error":"Invalid request ID"}');return end
local action=mg.get_var(body,'action') or ''
local subject=mg.get_var(body,'subject') or ''
local value=mg.get_var(body,'value') or ''
if #id<8 or #id>80 or not id:match('^[%w%-]+$') or #subject>24 or not subject:match('^[a-f0-9:]+$') or not ((action=='trust' and (value=='trusted' or value=='unknown' or value=='restricted')) or (action=='ack' and (value=='yes' or value=='no'))) then respond('{"error":"Invalid parameters"}');return end
local f=io.open('/var/lib/pishield-defense/request','w')
if not f then respond('{"error":"Mailbox unavailable"}');return end
f:write(id,'\n',action,'\n',subject,'\n',value,'\nEND');f:close();respond('{"accepted":true}')
?>
