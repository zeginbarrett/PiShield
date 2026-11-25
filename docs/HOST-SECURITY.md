# Host security

The Host security page checks the Pi every five minutes. It reports recent DNS warning signs, SSH authentication failure messages, listening TCP/UDP sockets, changes to tracked PiShield files, and available package updates. The package check uses the local APT cache (simulated upgrade every six hours); it does not refresh indexes or install packages. Refresh package indexes with `sudo apt update` and review updates before installing them. Security labels are inferred from repository names, not a complete CVE inventory.

The DNS check uses at most 20,000 stored queries from the past 15 minutes. High query counts, failed lookups and long names are investigation leads, not proof of compromise or tunneling. Router-forwarded DNS can hide individual devices. SSH counts are log messages, not distinct login attempts. No raw SSH logs are exposed in the dashboard.

## Optional firewall for the Pi

The firewall is **off by default**. It protects the Pi's own incoming connections, not traffic routed by your router or between other devices. It creates only its own `inet pishield_guard` nftables table. Existing rules may still restrict access. No output or forwarding rules are changed.

Before enabling, identify the interface used by your home network (`ip -br address`). Keep a local keyboard/monitor available if possible. The trial permits standard DNS, SSH and web ports on the specified LAN interface and Tailscale interface, DHCP and necessary ICMP, and standard Tailscale UDP transport. Other new incoming connections are dropped. Custom ports and other interfaces may stop working. LAN devices on the trusted interface still have access to permitted ports; use strong authentication and keep the router's public port forwarding disabled.

Install nftables if necessary, but do not enable or replace an existing firewall service solely for this feature:

```bash
sudo apt install nftables
sudo pishield-guard firewall trial wlan0
```

Replace `wlan0` with the correct interface. The trial automatically reverts after 180 seconds unless confirmed. While the trial is active, **open a new SSH session** and test DNS, the dashboard, and phone access (including remote VPN access if used). If anything fails, let the trial expire. Only if all tests succeed, run:

```bash
sudo pishield-guard firewall confirm
```

Confirmation enables persistence across reboots. Remove the PiShield firewall at any time:

```bash
sudo pishield-guard firewall off
```

This removes the dedicated table and disables its boot restoration, without changing other firewall rules. A firewall manager that flushes the whole ruleset can remove the table; check its status afterwards. Do not assume the trial timer can recover from all kernel, systemd, or power failures. If an unconfirmed trial is interrupted by reboot, use `firewall off` to clear the leftover trial marker.

## Checks and integrity baseline

```bash
sudo pishield-guard check
sudo pishield-guard firewall status
sudo journalctl -u pishield-guard.service -n 30 --no-pager
```

The installer records a first-install baseline of selected web files, PiShield scripts, and systemd units. Later changes (including legitimate upgrades) are reported. After reviewing legitimate changes, explicitly accept the new baseline with `sudo pishield-guard baseline`. This is local change detection, not a remote attestation system and not protection against an attacker who already controls root.

The new monitoring service runs with a restricted systemd sandbox, no external network access, and a memory limit. Existing DNS filtering and model services are unchanged. The existing 15-minute analysis schedule is preserved.

## Limits

A Pi used as a Wi-Fi DNS server cannot inspect every packet on a switched network. Full intrusion prevention, device quarantine, outbound filtering and segmentation require a router/gateway or supported traffic mirror. This release does not claim to prevent all zero-day attacks. Keep all devices patched and limit exposed services.
