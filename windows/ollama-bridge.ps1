param([switch]$Run,[switch]$RemoveStartup,[string]$PiUser,[string]$PiAddress)
$ErrorActionPreference='Stop'
$task='PiShield Ollama Bridge'
$dest=Join-Path $env:LOCALAPPDATA 'PiShield'
$key=Join-Path $env:USERPROFILE '.ssh\pishield_bridge'
if($RemoveStartup){Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue; Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue; exit}
if(-not $PiUser){$PiUser=Read-Host 'Raspberry Pi SSH username'}
if(-not $PiAddress){$PiAddress=Read-Host 'Raspberry Pi IP or hostname'}
if($PiUser -notmatch '^[a-z_][a-z0-9_-]*$' -or $PiAddress -notmatch '^[a-zA-Z0-9][a-zA-Z0-9.-]*$'){throw 'Invalid username or IPv4/hostname'}
$target="$PiUser@$PiAddress"
if($Run){while($true){& ssh.exe -NT -i $key -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -R '127.0.0.1:11435:127.0.0.1:11434' $target; Start-Sleep -Seconds 15}}
New-Item -ItemType Directory -Force (Split-Path $key),$dest | Out-Null
if(-not(Test-Path $key)){Write-Host 'Create a dedicated key; press Enter twice for an empty passphrase if unattended reconnection is desired.'; & ssh-keygen.exe -t ed25519 -f $key -C 'pishield-bridge'; if($LASTEXITCODE){throw 'Key generation failed'}}
$pub=(Get-Content "$key.pub" -Raw).Trim()
if($pub -notmatch '^ssh-ed25519 [A-Za-z0-9+/=]+(?: .*)?$'){throw 'Unexpected public key format'}
Write-Host 'Confirm the Pi host key fingerprint before accepting it; then sign in to the Pi.'
& scp.exe "$key.pub" "${target}:pishield_bridge.pub"
if($LASTEXITCODE){throw 'Public key transfer failed'}
Write-Host 'In your Pi SSH session, run this entire single line:'
Write-Host 'mkdir -p ~/.ssh; chmod 700 ~/.ssh; touch ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys; key=$(tr -d "\r" < ~/pishield_bridge.pub); line="restrict,port-forwarding,permitlisten=\"127.0.0.1:11435\",command=\"/bin/false\" $key"; grep -qxF -- "$line" ~/.ssh/authorized_keys || printf "%s\n" "$line" >> ~/.ssh/authorized_keys'
if((Read-Host 'Type YES after registering the public key') -cne 'YES'){exit}
# Test public key authentication and the tunnel in a foreground process before installing the task.
Write-Host 'Optional manual connection test. Press Ctrl+C to close it before starting the scheduled task.'
Write-Host "Manual test: ssh -NT -i `"$key`" -o IdentitiesOnly=yes -o BatchMode=yes -o ExitOnForwardFailure=yes -R 127.0.0.1:11435:127.0.0.1:11434 $target"
$copy=Join-Path $dest 'ollama-bridge.ps1'
if($PSCommandPath -ne $copy){Copy-Item $PSCommandPath $copy -Force}
$arguments='-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+$copy+'" -Run -PiUser '+$PiUser+' -PiAddress '+$PiAddress
$action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments
$trigger=New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $task -Action $action -Trigger $trigger -Settings $settings -User "$env:USERDOMAIN\$env:USERNAME" -Force | Out-Null
Start-ScheduledTask -TaskName $task
Write-Host 'Bridge task started. On the Pi, check: curl -fsS http://127.0.0.1:11435/api/tags'
