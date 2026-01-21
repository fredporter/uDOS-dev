# v1.0.4.0 Quick Start Guide

**Status:** ✅ Launch Ready  
**Last Updated:** 2026-01-16

## Starting Goblin Dev Server

```bash
cd /Users/fredbook/Code/uDOS
bin/Launch-Goblin-Dev.command
```

**Expected Output:**

```
✓ Uvicorn running on http://127.0.0.1:8767
✓ Swagger UI: http://127.0.0.1:8767/docs
✓ Server ready (no startup blocking)
```

## Interactive API Testing (Recommended)

Open your browser:

```
http://127.0.0.1:8767/docs
```

This gives you:

- ✅ Swagger UI with live endpoint testing
- ✅ Request/response schemas
- ✅ Try-it-out button for each endpoint
- ✅ No curl commands needed

## Command-Line Testing (Alternative)

### Test Server Health

```bash
curl http://127.0.0.1:8767/health
# Should return: {"status": "ok"}
```

### GitHub Integration Endpoints

**Required Setup:**

```bash
gh auth login
# Follow prompts to authenticate with GitHub
```

**Test GitHub Health:**

```bash
curl http://127.0.0.1:8767/api/v0/github/health
# Returns: GitHub CLI status and repo info
```

**Get Development Context:**

```bash
# Get roadmap
curl http://127.0.0.1:8767/api/v0/github/context/roadmap

# Get current devlog
curl http://127.0.0.1:8767/api/v0/github/context/devlog?month=2026-01

# Get AGENTS.md (team rules)
curl http://127.0.0.1:8767/api/v0/github/context/agents

# Get Copilot instructions
curl http://127.0.0.1:8767/api/v0/github/context/copilot
```

**List Issues:**

```bash
curl http://127.0.0.1:8767/api/v0/github/issues?state=open
```

**View Recent Logs:**

```bash
curl http://127.0.0.1:8767/api/v0/github/logs/session-commands
# Returns last 50 lines of memory/logs/session-commands-YYYY-MM-DD.log
```

### AI Integration Endpoints

**Optional Setup (Recommended):**

```bash
# Install Vibe CLI for local AI
pip install vibe-cli
```

**Test AI Health:**

```bash
curl http://127.0.0.1:8767/api/v0/ai/health
# Returns: Vibe CLI status and loaded context files
```

**Get AI Context:**

```bash
curl http://127.0.0.1:8767/api/v0/ai/context
# Returns: All loaded context files (roadmap, devlog, AGENTS.md, etc.)
```

**Query AI with Context:**

```bash
curl -X POST http://127.0.0.1:8767/api/v0/ai/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is our next priority based on the roadmap?",
    "include_context": true,
    "model": "devstral-small"
  }'
```

**Get Next Development Steps:**

```bash
curl http://127.0.0.1:8767/api/v0/ai/suggest-next
# Returns: AI suggestions based on current roadmap
```

**Analyze Logs with AI:**

```bash
curl -X POST http://127.0.0.1:8767/api/v0/ai/analyze-logs \
  -H "Content-Type: application/json" \
  -d '{"log_type": "error"}'
# Returns: AI analysis of recent error logs
```

**Explain Code:**

```bash
curl -X POST http://127.0.0.1:8767/api/v0/ai/explain-code \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "dev/goblin/services/github_integration.py",
    "line_start": 1,
    "line_end": 50
  }'
# Returns: AI explanation of code section
```

### Workflow Manager Endpoints

**No Setup Required** ✅ (Uses local SQLite)

**Test Workflow Health:**

```bash
curl http://127.0.0.1:8767/api/v0/workflow/health
# Returns: Database path and status
```

**Create a Project:**

```bash
curl -X POST http://127.0.0.1:8767/api/v0/workflow/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "v1.0.4.0 Testing",
    "description": "Test all three services"
  }'
# Returns: {"project_id": 1, "name": "v1.0.4.0 Testing"}
```

**Create a Task:**

```bash
curl -X POST http://127.0.0.1:8767/api/v0/workflow/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "title": "Test GitHub integration",
    "description": "Verify all GitHub endpoints work",
    "priority": 1,
    "tags": ["github", "testing"]
  }'
# Returns: {"task_id": 1, "title": "Test GitHub integration"}
```

**Update Task Status:**

```bash
curl -X PATCH http://127.0.0.1:8767/api/v0/workflow/tasks/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "in-progress"}'
# Returns: {"task_id": 1, "status": "in-progress"}
```

**List Project Tasks:**

```bash
curl http://127.0.0.1:8767/api/v0/workflow/projects/1/tasks
# Returns: All tasks for project 1
```

**Get Blocked Tasks:**

```bash
curl http://127.0.0.1:8767/api/v0/workflow/tasks/blocked
# Returns: All tasks with status "blocked"
```

**Export Workflow to Markdown:**

```bash
curl http://127.0.0.1:8767/api/v0/workflow/export/markdown
# Returns: Complete workflow as markdown (copy to file with > workflow.md)
```

## Expected Service Status

| Service  | Endpoint             | Requirement     | Status                  |
| -------- | -------------------- | --------------- | ----------------------- |
| GitHub   | `/api/v0/github/*`   | `gh auth login` | ⏳ Optional (lazy-load) |
| AI       | `/api/v0/ai/*`       | Vibe CLI        | ⏳ Optional (lazy-load) |
| Workflow | `/api/v0/workflow/*` | None            | ✅ Ready                |

**All services use lazy-load:** Server starts immediately, services initialize on first use.

## Troubleshooting

### Server Won't Start

```bash
# Check if port 8767 is already in use
lsof -i :8767
# Kill if needed: kill -9 <PID>
```

### GitHub Endpoints Fail

```bash
# Authenticate GitHub CLI
gh auth login

# Verify auth works
gh repo view
```

### AI Endpoints Fail

```bash
# Check if Vibe CLI installed
which vibe
# or
pip list | grep vibe

# Install if needed
pip install vibe-cli
```

### Check All Routes

```bash
curl http://127.0.0.1:8767/docs
# Open in browser for full Swagger UI
```

## Next Steps

1. ✅ **Test all endpoints** using Swagger UI
2. ⏳ **Set up GitHub CLI** for GitHub integration
3. ⏳ **Install Vibe CLI** for AI features (optional)
4. 📋 **Create workflow tasks** for tracking work
5. 🚀 **Integrate with App** (when switching to App workspace)

---

**Reference:** See [docs/devlog/2026-01-16-v1.0.4.0-launch-ready.md](2026-01-16-v1.0.4.0-launch-ready.md) for detailed status.
