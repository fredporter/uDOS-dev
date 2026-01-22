# Empire Scripts

All automation scripts live here and are constrained to the local inbox workspace.

- **Scope:** Scripts must read/write only under `memory/inbox/` (processing area for data in/out).
- **Path safety:** Use `path_guard.resolve_inbox_path()` to build any filesystem paths and to prevent accidental writes outside the inbox tree.
- **Outputs:** Prefer subfolders of `memory/inbox/processed/` for derived artifacts and `memory/inbox/.logs/` for run logs.
- **Dependencies:** Scripts may import from the core Empire modules (e.g., `marketing_db`, `entity_resolver`) but should avoid changing schema or business logic directly.
- **Logging:** If logging is needed, use `core.services.logging_manager.get_logger()` with the `[LOCAL]` tag.

## Usage

```bash
# Example: process inbox CSV files
source .venv/bin/activate
python -m dev.empire.scripts.process_inbox --pattern "*.csv"
```

Add new scripts in this folder to keep the root package clean and to ensure the inbox-only contract is enforced in one place.
