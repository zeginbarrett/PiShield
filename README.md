# PiShield v1.0 — Network Defense Console

PiShield is an independent, fork-style derivative of [Pi-hole](https://github.com/pi-hole/pi-hole), using its DNS engine and modifying its [web interface](https://github.com/pi-hole/web). It is not an official Pi-hole product or a replacement DNS engine. The GitHub repository is standalone rather than a GitHub-generated fork.

PiShield adds local AI-assisted DNS analysis, network discovery, behavioral baselines, managed malware/phishing feeds, domain rules, device trust, security history, service recovery, and a responsive green-on-black console.

**Release status:** experimental v1.0. Developed incrementally on Raspberry Pi 4, 64-bit Raspberry Pi OS Lite (Debian 13), Pi-hole Core 6.6, Web 6.6.1 and FTL 6.9. A combined clean-device installation and full mobile/enforcement testing have not been verified.

## Quick start

Flash Raspberry Pi OS Lite (64-bit) with Raspberry Pi Imager. Enable SSH and create your own user. Give the Pi a stable LAN address through a router DHCP reservation or static configuration.

On your Pi:

```bash
sudo apt update
sudo apt install -y git curl
git clone https://github.com/zeginbarrett/PiShield.git
cd PiShield
sudo bash install.sh
```

Review scripts before running as root. The installer uses the official interactive Pi-hole installer if needed, then applies PiShield's components. On a compatible existing Pi-hole installation, back up your configuration first. Open `http://<PI-LAN-IP>/admin/` and use your existing Pi-hole admin password. No personal credentials are bundled.

For an existing PiShield 0.9.3 installation, run `sudo bash pishield-v100.sh` instead. Check with `sudo bash pishield-v100.sh --check`. Roll back the v1.0 UI patch using `sudo bash pishield-v100.sh --rollback`.

## What it does

- DNS advertising and tracker blocking via Pi-hole.
- Managed threat feeds and observation/active/aggressive defense modes.
- Temporary and permanent domain rules, allowlist exceptions, audit trail and rollback.
- Device discovery, trust labels, connection health and DNS history.
- Local Ollama analysis, persistent reports and 15-minute scheduled monitoring.
- Behavioral baselines, threat verification, recommendations and service recovery.
- Mobile-friendly dashboard and separate feature pages.

Activate additional threat filtering in **Defense control**. AI recommendations need review; an AI judgment alone does not establish compromise. Device trust labels do not isolate devices. DNS monitoring is not full traffic inspection; a router forwarding DNS may obscure individual devices. Existing filtering works while the AI computer is offline.

## Local AI and remote access

See [AI setup](docs/LOCAL-AI.md) and [phone access](docs/REMOTE-ACCESS.md). The AI host can keep Ollama bound to localhost; an SSH reverse tunnel carries requests from the Pi. Keep dashboard and Ollama private.

## Screenshots

See [gallery](docs/SCREENSHOTS.md).

## Attribution and licensing

This project builds on Pi-hole Core, FTL and the Pi-hole web interface. Upstream source and license terms are available in the [Pi-hole organization](https://github.com/pi-hole). The web interface is EUPL-licensed; its existing copyright notices and license files must be retained when modified or redistributed. PiShield does not claim ownership of upstream code or trademarks. This repository contains extension installers rather than a vendored upstream copy. Upstream upgrades may overwrite modified templates; review compatibility before updating.

## Security and limitations

Keep admin authentication enabled. Never publish the dashboard, private SSH keys, DNS logs, or Ollama API directly to the internet. DNS-level defenses do not replace endpoint security or a firewall. Back up before installation and test DNS resolution and blocking before setting your entire network to use the Pi. The repository is a development release, not a guarantee of security.
