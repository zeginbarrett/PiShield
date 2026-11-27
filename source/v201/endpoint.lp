<?
local ri=mg.request_info
local function response(s) mg.write(s) end
if ri.is_authenticated~=true or ri.request_method~='GET' then response('{"error":"Authentication required"}');return end
local function header(name)
 for k,v in pairs(ri.http_headers or {}) do if string.lower(k)==name then return v end end
end
local body=header('x-pishield-command')
if not body then
 local f=io.open('/run/pishield-chat/status.json','r');if not f then response('{"error":"Chat service starting or unavailable"}');return end
 local s=f:read(1000000);f:close();response(s);return
end
local site=header('sec-fetch-site');local token=header('x-csrf-token')
if (site and site~='same-origin') or type(ri.csrf_token)~='string' or #ri.csrf_token==0 or token~=ri.csrf_token then response('{"error":"Request authorization failed"}');return end
if #body>7000 or body:find('[%c]') then response('{"error":"Request too large or invalid"}');return end
local id=mg.get_var(body,'id') or ''
if #id<8 or #id>80 or not id:match('^[%w%-]+$') or mg.get_var(ri.query_string or '', 'pscmd')~=id then response('{"error":"Invalid request ID"}');return end
local f=io.open('/run/pishield-chat/request','w');if not f then response('{"error":"Chat mailbox unavailable"}');return end
f:write(id,'\n',body,'\nEND');f:close();response('{"accepted":true}')
?>
