# Goblin Services Archival Map

## Archived Services

### Python Runtime Executor (Archived Jan 22, 2026)

- **Location:** `.archive/runtime_executor.py`
- **Documentation:** `.archive/RUNTIME_EXECUTOR_ARCHIVED.md`
- **Reason:** Replaced by Core TypeScript Runtime v1.0.0
- **API Endpoints:** Disabled in `goblin_server.py` (lines ~215-220)

---

## Active Services

| Service            | File                              | Endpoints            | Status   |
| ------------------ | --------------------------------- | -------------------- | -------- |
| Notion Sync        | `services/notion_sync_service.py` | `/api/v0/notion/*`   | ✓ Active |
| Task Scheduler     | `services/task_scheduler.py`      | `/api/v0/tasks/*`    | ✓ Active |
| Binder Compiler    | `services/binder_compiler.py`     | `/api/v0/binder/*`   | ✓ Active |
| GitHub Integration | `services/github_integration.py`  | `/api/v0/github/*`   | ✓ Active |
| Mistral/Vibe       | `services/mistral_vibe.py`        | `/api/v0/ai/*`       | ✓ Active |
| Workflow Manager   | `services/workflow_manager.py`    | `/api/v0/workflow/*` | ✓ Active |
| Setup Manager      | `routes/setup.py`                 | `/api/v0/setup/*`    | ✓ Active |

---

## To Restore

If the Python runtime is needed again:

```bash
# 1. Restore the service
mv .archive/runtime_executor.py services/

# 2. Uncomment imports in goblin_server.py (line ~215)
# and uncomment the mount statement

# 3. Restart Goblin server
```

For more details, see: `.archive/RUNTIME_EXECUTOR_ARCHIVED.md`
