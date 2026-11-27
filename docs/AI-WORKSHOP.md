# AI Chat, Tool Workshop and Interface Design

Open **Intelligence → AI Chat** for a dedicated plain-English conversation. Choose a local model and optional read-only sources. Chat and Workshop share the bounded recent conversation; clear it to remove prior context. The Ollama bridge must be connected for AI requests. The existing report page remains available.

Open **Intelligence → Tool Workshop** to create reusable analysis recipes, draft Python diagnostic code, propose an interface design, or request a fixed maintenance operation. Recipes are saved in the browser after approval. Python drafts are syntax-checked and downloadable as text only; they are not sandbox-executed, installed or granted access to system files. Syntax checking is not a security review.

## Design by asking

Enter a request such as `Make the dashboard blue, use compact spacing, and make cards square`. Click **Propose design**, then **Preview on this page**. Approve and save to apply the validated theme across authenticated dashboard browsers when pages next load. Restore original theme resets the settings without requiring an AI response. Supported choices: green, blue, yellow, purple, red, cyan or gray; compact, normal or comfortable spacing; square, rounded or soft corners; normal or large text; normal or wide dashboard columns. Some native widgets and security status colors intentionally retain their original appearance. The design engine accepts enumerated settings only, not model-generated CSS, JavaScript, HTML or arbitrary repository changes. It cannot automatically rewrite or deploy application code.

## Supervised maintenance

Choose Administrator or Supervised root and describe a task. The assistant may propose one operation from the fixed allowlist, not an arbitrary command. Administrator choices include refreshing Gravity, refreshing counters or intelligence, and restarting the live monitor. Root choices include refreshing package metadata and installing jq or tcpdump from configured repositories. Nothing executes from the dashboard. An owner must connect via SSH, run the displayed `sudo pishield-approve REQUEST_ID`, review the exact command and type APPROVE within ten minutes. Requests are consumed before execution and cannot replay. Do not approve a request you did not initiate. No changes to sudoers, authentication, firewall or network configuration are made by the installer. No unrestricted AI root access or autonomous code deployment is provided.

The chat service uses the existing fixed local Ollama bridge and bounded snapshots. It has a restricted filesystem and network policy. Its persistent design directory is separate from the privileged approval receipt directory. Theme changes do not grant new privileges. Chat and tool proposals are visible to authenticated administrators. Use a trusted private connection; don't expose the dashboard publicly.

## Update

On an existing v2.0.1 installation, `git pull --ff-only` and `sudo bash pishield-v210.sh`. Backups are made before modifying the interface. The chat service restarts. Mock model, approval validation, theme persistence, syntax and repeat-patch tests are not substitutes for verification on the physical Pi.
