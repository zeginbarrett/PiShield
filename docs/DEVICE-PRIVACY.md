# Device Privacy Monitor (1.3.1)

Install on a working 1.3 system with `sudo bash pishield-v131.sh` (the full installer includes this step). Open **Filtering → Device Privacy Monitor**. Select a client from the observed IP list, or type its address. Use **Load activity** to view the recent DNS sample. Live mode refreshes a 15-minute or one-hour window every 30 seconds when the page is visible. 24-hour and seven-day views read retained disk history and may lag. Each load reads at most 5,000 records in 10 pages; the display shows up to 150 domains and 150 newest requests. CSV export includes the loaded sample only and stays in the browser. Protect the CSV as private network information.

The monitor displays local and upstream blocked DNS results, distinct domains, category hints and actual native DNS status/reply values. Category hints come from curated domain suffixes and native gravity list IDs when available, not from inspection of traffic contents. Unrecognized domains remain unclassified. Other DNS results do not prove a successful connection. No packet capture, decryption, data-volume measurement or full connection monitoring is performed. No external analysis service is contacted.

## Sony Bravia

Open **Privacy & data protection**, enable **Sony Bravia**, keep scope **Selected devices only**, and assign the TV's existing client entry. Update Gravity / download lists. The dedicated exact-domain list contains a small subset of Sony telemetry and Samba TV viewing-recognition endpoints documented by [PCTestAdmin](https://github.com/PCTestAdmin/tv-blocklist). It deliberately excludes firmware and app update domains; it does not cover every rotating hostname. General Smart TV / ACR overlaps it. Other lists can continue blocking after disabling a filter. Test streaming, updates and sign-in. Disable TV viewing-recognition and optional data collection in the TV's privacy settings too.

Set the TV DNS to the Pi's LAN IP if you want individually identifiable requests. Reserve the TV address on your router or use a correctly configured static IP outside the dynamic pool. Avoid using a public secondary DNS. Verify the TV appears under its own IP in Query Log (not just the router). IPv6, encrypted DNS and direct IP traffic may bypass these filters. If no requests appear, do not conclude that the device is not sending data.

## Rules and scope

Use Manage clients to configure the device with an exact IP entry and assign groups. To limit a rule to one device, create a dedicated group and assign only that device, keeping its other desired memberships. Click Block or Allow next to a recorded domain, choose an existing enabled group assigned to that exact client, review the scope and confirm. The tool refuses to overwrite existing exact rules; manage or undo them in Domain rules. Default applies to other default-group clients as well. Other group members may also be affected; the displayed explicit-client count does not include unconfigured devices or overlapping selectors. Check the live DNS results after applying a rule.

All existing network, firewall and ntfy settings remain unchanged. The installer backs up changed files. The new list is off by default. Do not accept changed file-integrity fingerprints automatically; review the expected files first.
