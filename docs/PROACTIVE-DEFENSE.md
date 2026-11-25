# Proactive defense (1.2)

Run `sudo bash pishield-v120.sh` on an existing 1.1 system. The full `install.sh` installs both versions on a new Pi. Open Host security and refresh. The existing firewall, DNS, model settings and network configuration are not changed.

The local checks run every five minutes. They record power/throttling flags, recent kernel USB/storage warnings, root filesystem space, observed local neighbors, IPv6 addresses and default route, and available security-control status. History is limited to 500 events and 30 days, and continuing warnings are grouped rather than counted as attacks. Devices are observed from the kernel neighbor cache only; unknown or randomized MAC addresses may be legitimate. This is not a full scan, SMART test or network-wide intrusion prevention. The initial nonempty neighbor sample is the baseline. The 24-hour summary is shown on Host security.

## Optional SSH protection

Keep your current SSH session open. Install the Debian packages, then configure a short ban period and your trusted **current** admin IP (replace the example IP). Package installation may already enable the distribution's default SSH jail. If you have other Fail2ban settings, review those first; the helper refuses an existing jail.local and does not overwrite its own drop-in.

```sh
sudo apt install fail2ban python3-systemd nftables
sudo pishield-proactive ssh-on 192.168.1.202
sudo fail2ban-client status sshd
```

Test a new login. The default PiShield rule bans six failed attempts within ten minutes for 15 minutes, with only loopback and the specified admin address excluded. Fail2ban uses its own firewall rules; the PiShield host firewall remains intact. An administrator can unban an address using `sudo fail2ban-client set sshd unbanip ADDRESS`. To remove the PiShield policy, delete `/etc/fail2ban/jail.d/99-pishield-sshd.local` and run `sudo fail2ban-client reload`; the distribution's default jail may remain active. Use key-based SSH after verifying a second login; the installer does not change your login settings.

## Optional automatic Debian security updates

Review existing unattended-upgrades policy before enabling this feature. Installing the package can enable the distribution's default policy. The helper creates a separate apt configuration, displays the effective policy, performs a dry run and asks for approval before enabling timers. It limits unattended upgrades to the Debian security archive, not all Raspberry Pi vendor packages. Package upgrades can restart services, so back up and choose a suitable maintenance time. It never schedules an automatic reboot.

```sh
sudo apt update
sudo apt install unattended-upgrades
sudo pishield-proactive updates-on
```

Check `/var/log/unattended-upgrades/` periodically. Removing `/etc/apt/apt.conf.d/99-pishield-security` restores the remaining apt policy, which may still enable unattended upgrades. The dashboard reports configuration and timer status, not successful patch installation. Other software, firmware and kernel updates need separate review.

## Optional phone alerts

Use an ntfy server you trust, a **private authenticated topic** and a publish-only access token. Subscribe using the ntfy app on your phone. Do not use an unprotected public topic. The notifier sends only generic categories (e.g. storage warning), never device addresses, domains or raw logs. No third-party service is contacted until you configure it.

```sh
sudo install -m 600 /dev/null /etc/pishield-proactive/ntfy.json
sudo nano /etc/pishield-proactive/ntfy.json
```

Enter JSON using your own HTTPS server, private topic and token:

```json
{"url":"https://YOUR-NTFY-SERVER/YOUR-PRIVATE-TOPIC","token":"YOUR-PUBLISH-TOKEN"}
```

Run `sudo systemctl start pishield-proactive-notify.service` to process recent recorded warnings; no message is sent when there are no new warnings. Check `sudo journalctl -u pishield-proactive-notify.service -n 20 --no-pager` for delivery errors. Delete the root-only config to stop alerts. The dashboard's configured indicator is not a delivery receipt.

## Verify

```sh
sudo systemctl status pishield-proactive.timer --no-pager
sudo pishield-proactive check
sudo pishield-guard firewall status
```

The existing file integrity baseline is deliberately preserved. Review the upgrade-related changes against trusted repository files before using `sudo pishield-guard baseline`. The web-file backup is printed by the installer. No new reputation feed or network-wide IP blocking is provided; the Pi is not the gateway.
