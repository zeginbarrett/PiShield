# Changelog

## 1.2.1
- Added critical, high, warning and informational phone notifications.
- Added alerts for managed threat-feed matches, possible DNS tunneling and recorded defense actions.
- Added a daily report at 08:00 local time, deduplication and a manual delivery test.
- Retained private notification credentials and existing firewall/DNS settings. Alert evidence is not proof of compromise.

## 1.2.0
- Added five-minute power, storage, neighbor and IPv6 checks.
- Added bounded security event history and a 24-hour summary.
- Redesigned Host security status cards and tables.
- Added optional Fail2ban SSH protection, Debian security-only update configuration and authenticated ntfy notifications.
- Existing firewall and DNS settings are preserved. No network-wide traffic inspection or IP reputation feed.

## 1.1.0
- Added host security checks every five minutes: DNS warning signs, SSH failures, listening sockets, file integrity and cached package updates.
- Added optional nftables host firewall, with a three-minute rollback trial and explicit confirmation for persistence.
- Added a dedicated Host security page, version indicator and restricted monitoring service.
- The Pi remains a DNS server, not an inline network firewall. No automatic package installation or traffic interception.

## 1.0.0 — Initial public release
- Complete Raspberry Pi installer.
- Desktop and mobile dashboard, DNS history charts, and system checks.
- Local model support, scheduled analysis, and security reports.
- Defense modes, managed threat feeds, domain rules, and device trust.
- Working command handling and selected-mode highlighting.
- Private remote access instructions.

New installations start in observation mode. The full fresh-install sequence still needs testing on a separate physical Pi.
