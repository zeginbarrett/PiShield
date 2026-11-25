# Attribution and licensing

PiShield is an independent Pi-hole fork distributed as a patch and extension installer. It is not affiliated with, endorsed by, or a product of Pi-hole, LLC.

Upstream copyright: Copyright (C) 2017 Pi-hole, LLC (https://pi-hole.net). Upstream Core, FTL and web code are distributed under the European Union Public Licence (EUPL), with separate third-party licenses where specified. The upstream web license is included in `LICENSE`. PiShield derivative modifications are distributed under EUPL-1.2 to maintain compatibility with the upstream license. Original installed license files and copyright notices are retained; UI branding does not remove these rights.

Upstream projects: https://github.com/pi-hole/pi-hole ; https://github.com/pi-hole/FTL ; https://github.com/pi-hole/web. The installer downloads the upstream project separately rather than redistributing its full tree. The scripts in `components/` contain the installers; `source/` exposes the readable payloads for review. The separate components use external threat-list providers under those providers' own terms. See https://github.com/hagezi/dns-blocklists and https://github.com/PCTestAdmin/tv-blocklist.

PiShield includes an independently created emblem. Screenshots show development versions; no upstream endorsement is implied.

## Compatibility

The installers were developed against Pi-hole Core v6.6, Web v6.6.1 and FTL v6.9. The upstream installation is a required dependency and is installed automatically when absent. Internal service and API identifiers are retained for compatibility. Future upstream versions may need additional template changes.
