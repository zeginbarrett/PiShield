<?
-- Fixed-path mailbox, never execute commands or accept arbitrary paths.
local ri = mg.request_info
local function respond(s)
  mg.write(s)
end
if ri.is_authenticated ~= true then
  respond('{"error":"Authentication required"}')
  return
end
if ri.request_method == 'GET' then
  local f=io.open('/var/lib/pishield-ai/status.json','r')
  if not f then respond('{"error":"AI worker initializing or status unavailable"}'); return end
  local s=f:read('*a'); f:close(); respond(s); return
end
if ri.request_method ~= 'POST' then respond('{"error":"Unsupported method"}'); return end
local body=mg.read()
if type(body)~='string' or #body>2048 then respond('{"error":"Invalid request"}'); return end
local token=mg.get_var(body,'csrf')
if type(ri.csrf_token)~='string' or #ri.csrf_token==0 or token~=ri.csrf_token then respond('{"error":"CSRF validation failed"}'); return end
local id=mg.get_var(body,'id') or ''
local action=mg.get_var(body,'action') or ''
local hours=mg.get_var(body,'hours') or ''
local model=mg.get_var(body,'model') or ''
if #id<8 or #id>80 or not id:match('^[%w%-]+$') or (action~='run' and action~='load' and action~='save') or (hours~='1' and hours~='6' and hours~='24' and hours~='168') or #model>250 or model:find('[%c]') then respond('{"error":"Invalid job parameters"}');return end
local f=io.open('/var/lib/pishield-ai/request','w')
if not f then respond('{"error":"Request mailbox unavailable"}');return end
f:write(id,'\n',action,'\n',hours,'\n',model,'\nEND');f:close()
respond('{"accepted":true}')
?>
