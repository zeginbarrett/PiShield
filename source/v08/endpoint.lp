<?
local ri=mg.request_info
local function respond(s) mg.write(s) end
if ri.is_authenticated~=true then respond('{"error":"Authentication required"}');return end
if ri.request_method=='GET' then
 local f=io.open('/var/lib/pishield-action/status.json','r')
 if not f then respond('{"error":"Engine is initializing; refresh shortly"}');return end
 local s=f:read('*a');f:close();respond(s);return
end
if ri.request_method~='POST' then respond('{"error":"Unsupported method"}');return end
local body=mg.read()
if type(body)~='string' or #body>2048 then respond('{"error":"Invalid request"}');return end
local token=mg.get_var(body,'csrf')
if type(ri.csrf_token)~='string' or #ri.csrf_token==0 or token~=ri.csrf_token then respond('{"error":"CSRF validation failed"}');return end
local id=mg.get_var(body,'id') or ''
local action=mg.get_var(body,'action') or ''
local subject=mg.get_var(body,'subject') or ''
local value=mg.get_var(body,'value') or ''
if #id<8 or #id>80 or not id:match('^[%w%-]+$') or #subject>253 or not subject:match('^[a-zA-Z0-9%.%-]+$') or #value>16 or not value:match('^[a-z0-9]+$') or not (action=='mode' or action=='refresh' or action=='allow' or action=='deny' or action=='remove') then respond('{"error":"Invalid parameters"}');return end
local f=io.open('/var/lib/pishield-action/request','w')
if not f then respond('{"error":"Request mailbox unavailable"}');return end
f:write(id,'\n',action,'\n',subject,'\n',value,'\nEND');f:close();respond('{"accepted":true}')
?>
