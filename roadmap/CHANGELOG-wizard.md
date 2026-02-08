# Wizard Changelog

## v1.1.2 — 2026-02-07
- Refactored `wizard/server.py` to delegate auth, log reading, system stats, web proxy, plugin repo, scheduler runner, and webhook helpers into services.
- Added fallback dashboard helper and environment loader for server bootstrap.
