# Phone alerts (1.2.1)

Install the update with `sudo bash pishield-v121.sh` on an existing 1.2 installation. Keep your existing private ntfy HTTPS endpoint and publish-only token in `/etc/pishield-proactive/ntfy.json`. No setup is repeated. See [initial setup](PROACTIVE-DEFENSE.md) if needed. Test with `sudo python3 /opt/pishield-proactive/notify.py --test`.

Alerts are grouped by severity and checked every five minutes:

- Critical (ntfy priority 5): missing tracked files or inactive host firewall. Legitimate maintenance can also trigger these warnings.
- High (4): repeated SSH authentication failures, tracked-file changes, potential DNS tunneling patterns, managed threat-feed domain matches and storage warnings. A feed match is a recorded lookup, not proof of successful malicious communication. Feed matches are limited to one alert per local calendar day and use the existing bounded 24-hour sample.
- Warning (3): unusual DNS activity, new observed neighbors, power or disk warnings, and defense-action errors.
- Information (2): security-marked package updates, recorded DNS rule/feed/mode changes and successful list rebuilds. These are configuration actions, not verified blocked attacks.

A daily report runs on the first successful notification check at or after 08:00 local time. The first report may arrive immediately after installation if it is already past 08:00. It includes recorded event counts, available DNS request totals and a subset of local-list denial statuses (ads included), feed matches, recorded actions, firewall and health. Data is bounded by retained logs and snapshots; failed reads are marked unavailable. No traffic inspection or proof of compromise is implied.

Messages contain fixed descriptions and counts, not IPs, domains, device names, raw logs or tokens. New alerts use persisted deduplication; retries may duplicate delivery if the process stops after server acceptance but before saving state. The first upgrade uses the previous notification checkpoint, with at most 15 minutes of recent historical alerts; later delivery considers up to 24 hours. The phone must remain reachable through your private notification service. No delivery is possible while the Pi or notification service is offline.

Check logs: `sudo journalctl -u pishield-proactive-notify.service -n 20 --no-pager`. A successful test proves delivery, not attack detection. Review expected file changes after the update before rebaselining. The patch changes only the notifier and its service; the dashboard remains in the 1.2 release family. Backups are stored in `/var/backups/pishield/notifications-v121-*`.
