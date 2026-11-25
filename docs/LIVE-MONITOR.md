# Live Network Monitor

Open **Network → Live Network Monitor** (or the adjacent device privacy menu if the Network section is absent). The monitor starts during installation and uses a restricted systemd service to decode TCP/UDP port 53 packet summaries with tcpdump. It listens on available interfaces without promiscuous mode. The authenticated dashboard refreshes every two seconds. Filter by an exact device IP, direction, or domain/detail text. For example, select the TV's IP and launch an app on the television to verify that DNS packets are arriving at the Pi. An empty view does not prove that a device is offline or sending no traffic.

The service keeps a rolling buffer of up to 300 summaries from the last five minutes in `/run`, with a rate cap. No raw capture files are created. The browser's pause and clear controls affect the display only. DNS packet summaries can include private domain names and answers; keep the dashboard private. TCP segments and truncated packets may be incomplete, and some packets may be skipped under load. Counts represent parsed packet summaries, not unique DNS queries or confirmed blocks. The device history page shows recorded DNS decisions.

This is not a gateway or packet-filtering firewall. The Pi can see only traffic delivered to its interfaces; it cannot see all device-to-router communications on a switched network. HTTPS, encrypted DNS and VPN contents are not decoded. For broader visibility use a compatible router, or an authorized mirrored switch port; for packet enforcement use a gateway/firewall.

Stop capture and remove the volatile buffer:

```sh
sudo systemctl disable --now pishield-live.service
```

Restart capture:

```sh
sudo systemctl enable --now pishield-live.service
```

Troubleshoot with `sudo journalctl -u pishield-live.service -n 30 --no-pager`. Existing DNS, firewall, notifications and privacy rules are unchanged. Review expected integrity changes after upgrading.
