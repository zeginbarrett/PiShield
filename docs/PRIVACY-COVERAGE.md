# Privacy coverage across devices

PiShield is a DNS filter and monitor for TVs, streaming devices, phones, tablets, computers and smart-home devices that use it for DNS. Choose an observed device or its reserved IP under **Filtering → Device filtering & privacy**. Select only your intended device; never assign a router or the Pi as an individual device. No manual group creation is required. Each device can have different filters. No new filters are activated on install.

| Device or purpose | Available filters |
| --- | --- |
| Sony Bravia | Sony measurement, advertising and Samba TV viewing-data endpoints; general Smart TV / ACR |
| Samsung, LG webOS, Roku, Fire TV | Vendor telemetry/trackers and general TV/ACR |
| Windows | Windows / Office telemetry |
| Apple | Apple devices and service trackers |
| Android and smart home | Xiaomi, Huawei, OPPO / Realme, Vivo; generic tracking list for other devices |
| Any DNS client | Data harvesting / ads, TikTok fingerprinting, optional family and gambling filtering |
| Optional restrictive policy | Known DNS / VPN bypass domains; can disrupt legitimate services and remote access |

## Understand the status

- **On — list loaded:** an enabled list with loaded entries applies to the selected client's policy and DNS blocking is enabled. This is configuration evidence, not a live enforcement test.
- **Waiting for list download:** an enabled list applies but has zero or unknown entries. Open Download lists / Update Gravity and inspect the result. Refresh devices afterward.
- **Off for this device:** the specific list has no active assignment. Other lists or exact/regex rules may still block the same domains.
- **Inherited from Default policy:** the device already receives that list through Default. A device-specific switch cannot override it. Existing shared policies are preserved; changing them can affect other devices.
- **Inactive:** blocking disabled or unconfirmed, or an assignment has a disabled filter.

## Verify on a TV or other device

Configure the device to use the Pi's LAN IP as its DNS resolver, or configure your router to advertise the Pi directly. A forwarding router may hide device identity. Check the selected device has observed DNS requests. Enable the desired filters and download new lists. Open **Device activity** to jump to the selected IPv4 address in Device Privacy Monitor. Check actual blocked requests, DNS destination categories, historical results and export a CSV if needed. Test streaming, updates and sign-in. Domain exceptions are available. See [Device filters](DEVICE-FILTERS.md), [Device Privacy Monitor](DEVICE-PRIVACY.md), and [Live Network Monitor](LIVE-PRESETS.md).

DNS records and visible packet metadata do not reveal all data transmitted, encrypted contents, successful uploads or other traffic not visible to the Pi. Categories are hints. HTTPS and direct-IP or encrypted-DNS traffic can bypass DNS controls. List entries can overlap; loaded domain counts are not per-device block counts. These tools reduce known tracking and advertising, not all data harvesting.
