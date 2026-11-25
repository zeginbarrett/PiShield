# PiShield 2.0: Device Intelligence

Open **Network → Device Intelligence**. Select a recorded DNS client or observed neighbor. The page consolidates existing privacy, packet, AI, and DNS history controls. The source collector is read-only, runs every five minutes, and records bounded aggregates from up to 30,000 DNS rows in the previous 24 hours. Oldest retained sample time and caps are displayed. DNS counts are not packet volume or confirmed attacks.

## What is available

- Device identity hints from client names and vendor suggestions, IP and MAC neighbor observations, and last recorded DNS timestamps. A neighbor cache is not an authoritative device census or physical topology.
- Recognized tracking categories and top tracking domains, local versus upstream block counts, and a percentage of recognized tracking queries denied locally. Unclassified domains are not assumed harmless. This is not a comprehensive privacy rating.
- A conservative volume-spike check comparing the last hour to the prior six hours; requires enough history and is suppressed for capped samples. The existing security monitoring and phone notifications remain separate and unchanged.
- Direct links to device filtering, DNS history and live packets, and links to AI and domain controls. IPv4 is required for newly registered device filters.
- List entry counts and native download status, system service/timer states, host health, and network interfaces/default route/forwarding readiness. The native Gravity update schedule remains unchanged; run Update Gravity if a list is missing entries.
- Possible alternate-DNS destination hints from visible port-53 packets in the existing live monitor buffer. On a switched network the Pi usually cannot see client-to-router unicast traffic, DoH or all bypasses. No observation does not mean no bypass.

## Optional service exposure check

Only for an individual device you own or administer, from your authenticated SSH terminal:

```sh
sudo pishield-device-check 192.168.1.50 --confirm-owned
```

The helper accepts only a directly connected private IPv4 endpoint (not the default gateway, Pi or VPN-routed target), attempts a TCP connection to eight common ports, and records accepted versus unconfirmed connections. No banner collection, exploit, password attempt or automatic scan. Results appear on the next intelligence snapshot. A reachable service is not necessarily vulnerable; an unconfirmed port is not necessarily closed.

## Scope and limitations

This release includes the earlier privacy, live monitor, local AI, host firewall, phone alert, backups and recovery features. It does not install a root web shell, change router/DHCP settings, enable IP forwarding, create an inline gateway, enforce per-device internet schedules, or capture/decrypt arbitrary payloads. Use SSH for system administration. To enforce packet-level policies or reliably measure device flows, deploy a suitable gateway with a reviewed network topology; port mirroring can provide visibility but not enforcement. No automatic policy changes are made. The dashboard and snapshots are authenticated; keep access private. Review expected file-integrity changes before accepting a new baseline.

## Install

On 1.3.5, run `sudo bash pishield-v200.sh`. On a fresh system or earlier version use the full `install.sh`. Refresh your browser. If collection fails, use `sudo journalctl -u pishield-intelligence.service -n 30 --no-pager`. Stop new monitoring with `sudo systemctl disable --now pishield-intelligence.timer`; existing DNS protections are unaffected.
