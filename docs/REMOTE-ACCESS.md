# Access PiShield from your phone

On your local Wi-Fi, open `http://PI_IP/admin/` using the Pi's actual address. For access away from home, use a private VPN, not a public port-forward.

## Tailscale (optional)

Review the official [Tailscale installation instructions](https://tailscale.com/download/linux). On your Pi:

```sh
curl -fsSL https://tailscale.com/install.sh -o /tmp/tailscale-install.sh
sh /tmp/tailscale-install.sh
sudo tailscale up --accept-dns=false
```

Follow the authentication URL and sign in to your own account. To use private HTTPS access, run:

```sh
sudo tailscale serve --bg http://127.0.0.1:80
tailscale serve status
```

Enable HTTPS certificates/MagicDNS in your Tailscale account if prompted. Install Tailscale on your Android or iPhone, sign in to the same private tailnet, and open the HTTPS address printed by `tailscale serve status`, adding `/admin/`. Keep the dashboard password enabled and restrict tailnet access to trusted devices. Do **not** enable Tailscale Funnel or public forwarding.

Your Pi and its internet connection must remain on. Your PC is needed only for AI inference if it hosts Ollama. Remote dashboard access does not automatically route phone DNS through PiShield; that is a separate Tailscale DNS configuration.
