# Local AI setup (optional)

PiShield works without AI. DNS filtering and configured threat feeds continue even when the model host is offline. Model output is advisory and does not itself authorize blocking.

## 1. Prepare the model host

Install [Ollama](https://ollama.com/download) on a computer you own. In its terminal:

```sh
ollama pull qwen3.5:4b
ollama list
```

Choose any installed chat-capable model that fits your hardware. Keep Ollama bound to its default loopback address, `127.0.0.1:11434`. Do not expose it to the internet. No `OLLAMA_ORIGINS` change is required for the server-side bridge.

On Windows, verify the server is running:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

On Linux/macOS:

```sh
curl -fsS http://127.0.0.1:11434/api/tags
```

## 2. Connect the model host to the Pi

On the computer running Ollama (not on the Pi), replace `PI_USER` and `PI_IP` with your own SSH username and Pi address:

```sh
ssh -NT -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -R 127.0.0.1:11435:127.0.0.1:11434 PI_USER@PI_IP
```

Confirm the Pi's SSH host key fingerprint before accepting it. Enter your Pi password. Leave this window open for a manual session. This encrypted connection exposes Ollama only on the Pi's loopback interface.

On the Pi:

```sh
curl -fsS http://127.0.0.1:11435/api/tags
```

The returned JSON should contain the installed models. Open your dashboard, select **AI settings**, choose a model, and save it. Open **AI analysis** to run a report, or wait for the configured 15-minute Sentinel schedule. Reports can contain domain and client metadata from your own DNS history; keep your model host trusted.

## 3. Optional automatic Windows reconnection

Clone or download this repository on Windows, then run `powershell -ExecutionPolicy Bypass -File .\windows\ollama-bridge.ps1` in PowerShell from the repository directory. It prompts for your Pi address and user, generates a dedicated key, and prints the exact registration command for the Pi. After registering the public key, the script creates a logon task which reconnects the tunnel. Ollama itself must be running on Windows. Keep the key private.

## Troubleshooting

- `Connection refused` on the Pi: verify the SSH bridge is connected and Ollama is running.
- `Permission denied (publickey,password)`: verify the correct public key is registered and `~/.ssh` and `authorized_keys` have permissions 700 and 600 respectively.
- Port already in use: stop another bridge session; do not expose a second public listener.
- Empty model list: run `ollama list` on the model host and install a chat model.
- Check the collector: `sudo journalctl -u pishield-sentinel.service -n 30 --no-pager`.
- Check the complete stack: `sudo bash pishield-v100.sh --check`.

No manual browser tunnel is required. If the AI host is unavailable, DNS protection continues.
