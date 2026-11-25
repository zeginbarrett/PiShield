# Changelog

## 1.0.1
- Fixed HTTP 405 for AI jobs, defense commands and device trust/review controls. Pi-hole Lua templates reject POST; commands now use a dedicated authenticated, CSRF-validated same-origin request header. Plain GET requests remain read-only.
- Defense mode buttons reflect the server-reported configured mode, with a distinct pending indicator and reload/error status.
- Added a web-only maintenance updater with backups; no DNS restart required.

## 1.0.0 (development release)
- Added a unified install entry point for a fresh Pi-hole v6 deployment and the full PiShield extension stack.
- Added mobile navigation, compact homepage, DNS history chart and service diagnostics.
- Included the prior fixes to AI endpoint response formatting, branding and dedicated feature pages.
- Documented generic local Ollama and private Tailscale access.
- Fresh installations start in observation mode; explicitly activate managed defense feeds in the dashboard.
- Retained the v1.0 UI rollback command and incremental installer backups.

The combined installer is syntax-checked, not yet validated on a fresh physical Pi.
