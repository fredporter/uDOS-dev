# Goblin Dev Server - Setup Guide

**Version:** v1.0.4.0  
**Status:** Production-Ready Setup System  
**Last Updated:** 2026-01-16

---

## 📋 Quick Start

### 1. Copy Environment Template

```bash
cd ~/uDOS/dev/goblin
cp .env.example .env
```

### 2. Open Setup Dashboard

Start the server:

```bash
bin/Launch-Goblin-Dev.command
```

Then visit:

```
http://127.0.0.1:8767/api/v0/setup/status
```

This shows your current configuration status.

### 3. Configure Variables (Optional but Recommended)

Visit the setup wizard:

```
http://127.0.0.1:8767/docs
```

Expand the `setup` section and use the endpoints.

---

## 📁 File Structure

### Configuration Files

```
/dev/goblin/
├── .env.example              # Template (copy to .env)
├── .env                      # Your local config (gitignored)
├── config/
│   └── goblin.json          # Server config (gitignored)
├── config_manager.py         # Config management system
└── routes/
    └── setup.py              # Setup API endpoints
```

### Data Directories (Auto-Created)

```
/memory/
├── logs/                     # Server and debug logs
├── goblin/
│   ├── workflow.db           # Task management database
│   ├── tasks.db              # Task scheduler database
│   └── notion_sync.db        # Notion sync queue
├── bank/
│   └── user/
│       └── contacts.db       # HubSpot contacts sync
└── [other user directories]
```

---

## 🔧 Configuration Variables

### Server Configuration

| Variable           | Default       | Purpose                              |
| ------------------ | ------------- | ------------------------------------ |
| `GOBLIN_HOST`      | `127.0.0.1`   | Server hostname (localhost only)     |
| `GOBLIN_PORT`      | `8767`        | Server port                          |
| `GOBLIN_ENV`       | `development` | Environment (development/production) |
| `GOBLIN_LOG_LEVEL` | `INFO`        | Logging level                        |

### GitHub Integration

| Variable            | Purpose               | Required                        |
| ------------------- | --------------------- | ------------------------------- |
| `GITHUB_TOKEN`      | Personal access token | Optional (use `gh cli` instead) |
| `GITHUB_REPO_OWNER` | Repository owner      | No (defaults to `fredporter`)   |
| `GITHUB_REPO_NAME`  | Repository name       | No (defaults to `uDOS`)         |

**Setup Option 1: Use GitHub CLI (Recommended)**

```bash
gh auth login
# Choose: HTTPS, then "Y" for credential helper
```

No environment variable needed.

**Setup Option 2: Personal Access Token**

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `user`
4. Copy token
5. Add to `.env`:
   ```
   GITHUB_TOKEN=ghp_your_token_here
   ```

### Notion Integration

| Variable             | Purpose                   | Required              |
| -------------------- | ------------------------- | --------------------- |
| `NOTION_API_KEY`     | Notion integration secret | Yes (if using Notion) |
| `NOTION_DATABASE_ID` | Your main database ID     | Yes (if using Notion) |

**Setup Steps:**

1. Visit https://www.notion.so/my-integrations
2. Click "Create new integration"
3. Name it "uDOS Goblin"
4. Copy the "Internal Integration Token"
5. Add to `.env`:
   ```
   NOTION_API_KEY=secret_abc123xyz
   ```
6. In Notion, open your database → Share → Add "uDOS Goblin" integration
7. Get database ID from URL: `https://notion.so/abc123xyz?v=...` → `abc123xyz`
8. Add to `.env`:
   ```
   NOTION_DATABASE_ID=abc123xyz
   ```

### AI / Mistral Integration

| Variable          | Purpose                 | Required                       |
| ----------------- | ----------------------- | ------------------------------ |
| `MISTRAL_API_KEY` | Mistral API key (cloud) | No (local Vibe CLI is default) |
| `MISTRAL_API_URL` | API endpoint            | No (defaults to mistral.ai)    |

**Option 1: Local (Recommended)**
Install Vibe CLI:

```bash
pip install vibe-cli
# or follow: https://mistral.ai/news/vibe/
```

No configuration needed.

**Option 2: Cloud (Mistral API)**

1. Visit https://console.mistral.ai
2. Create account and API key
3. Add to `.env`:
   ```
   MISTRAL_API_KEY=your_key_here
   ```

### HubSpot CRM Integration

| Variable               | Purpose                  | Required |
| ---------------------- | ------------------------ | -------- |
| `HUBSPOT_API_KEY`      | Private app access token | No       |
| `HUBSPOT_ACCESS_TOKEN` | OAuth access token       | No       |

**Setup Steps:**

1. Visit https://app.hubspot.com/private-apps
2. Click "Create app"
3. Set name: "uDOS Empire"
4. Go to "Scopes" tab
5. Select: `contacts.lists.read`, `contacts.lists.write`, `crm.objects.contacts.read`, `crm.objects.contacts.write`
6. Click "Create app"
7. Copy "Private app token"
8. Add to `.env`:
   ```
   HUBSPOT_API_KEY=pat_your_token_here
   ```

### Database Paths

| Variable      | Default                        | Purpose                 |
| ------------- | ------------------------------ | ----------------------- |
| `DB_WORKFLOW` | `memory/goblin/workflow.db`    | Workflow/todo database  |
| `DB_CONTACTS` | `memory/bank/user/contacts.db` | Contacts database       |
| `DB_TASKS`    | `memory/goblin/tasks.db`       | Task scheduler database |
| `DB_SYNC_LOG` | `memory/goblin/notion_sync.db` | Notion sync queue       |

All paths are relative to uDOS root. Directories are auto-created on first run.

### Feature Flags

| Variable                    | Default | Purpose                   |
| --------------------------- | ------- | ------------------------- |
| `ENABLE_NOTION_SYNC`        | `true`  | Enable Notion integration |
| `ENABLE_GITHUB_INTEGRATION` | `true`  | Enable GitHub integration |
| `ENABLE_AI_FEATURES`        | `true`  | Enable AI features        |
| `ENABLE_WORKFLOW_MANAGER`   | `true`  | Enable workflow manager   |
| `ENABLE_PUBLIC_URL`         | `true`  | Enable ngrok public URL   |

---

## 🚀 Setup API Endpoints

### Configuration Status

```
GET /api/v0/setup/status
```

Get complete configuration status, all services, databases, feature flags.

```
GET /api/v0/setup/progress
```

Get setup wizard progress percentage and which variables are configured.

```
GET /api/v0/setup/required-variables
```

Get list of all required variables with documentation links.

### Update Configuration

```
POST /api/v0/setup/configure
```

Update a configuration variable (adds to `.env`).

Request:

```json
{
  "name": "GITHUB_TOKEN",
  "value": "ghp_abc123...",
  "description": "GitHub personal access token"
}
```

### Validation Endpoints

```
GET /api/v0/setup/validate/github
GET /api/v0/setup/validate/notion
GET /api/v0/setup/validate/ai
GET /api/v0/setup/validate/hubspot
GET /api/v0/setup/validate/databases
```

Each returns status of that service (configured, missing, etc).

### OAuth Setup

```
POST /api/v0/setup/github/oauth-start
GET /api/v0/setup/github/callback

POST /api/v0/setup/notion/oauth-start

POST /api/v0/setup/hubspot/oauth-start
GET /api/v0/setup/hubspot/callback
```

OAuth endpoints for third-party authentication.

### Path Management

```
GET /api/v0/setup/paths
```

Get organized directory structure (installation, data, documentation).

```
POST /api/v0/setup/paths/initialize
```

Auto-create all required directories.

### Setup Wizard

```
POST /api/v0/setup/wizard/start
```

Start first-time setup wizard (returns 6 steps).

```
POST /api/v0/setup/wizard/complete
```

Mark setup as complete (after all steps done).

### Configuration Export

```
GET /api/v0/setup/export-env
```

Export current configuration as `.env` template.

```
GET /api/v0/setup/export-status
```

Export full status report as JSON.

---

## 🧪 Testing Setup

### 1. Verify All Paths

```bash
curl http://127.0.0.1:8767/api/v0/setup/paths
# Should return: Installation, Data, and Documentation paths
```

### 2. Check Configuration Status

```bash
curl http://127.0.0.1:8767/api/v0/setup/status
```

### 3. Initialize Directories

```bash
curl -X POST http://127.0.0.1:8767/api/v0/setup/paths/initialize
```

### 4. Start Setup Wizard

```bash
curl -X POST http://127.0.0.1:8767/api/v0/setup/wizard/start
```

### 5. Configure a Variable

```bash
curl -X POST http://127.0.0.1:8767/api/v0/setup/configure \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GITHUB_REPO_OWNER",
    "value": "fredporter"
  }'
```

### 6. Validate Configuration

```bash
curl http://127.0.0.1:8767/api/v0/setup/validate/github
curl http://127.0.0.1:8767/api/v0/setup/validate/databases
```

### 7. Complete Setup

```bash
curl -X POST http://127.0.0.1:8767/api/v0/setup/wizard/complete
```

---

## 📊 Setup Flow Diagram

```
Start Server
    ↓
Check Setup State (memory/goblin/setup-state.json)
    ↓
Is setup complete?
    ├─ YES → Load from .env → Ready
    └─ NO → Show wizard progress
        ↓
    User runs /api/v0/setup/wizard/start
        ↓
    Steps:
    1. Database Setup → /paths/initialize
    2. GitHub Setup → /validate/github
    3. Notion Setup → /validate/notion
    4. AI Setup → /validate/ai
    5. HubSpot Setup → /validate/hubspot
    6. Complete → /wizard/complete
        ↓
    Saved to setup-state.json
        ↓
    Ready to use all services!
```

---

## 🔐 Security Best Practices

### .env File (Local-Only)

- **Gitignored** ✅ (never commits secrets)
- **Local-only** ✅ (stored on your machine)
- **Not shared** ✅ (each developer has their own)

### API Keys

- **GitHub Token**: Limited scope (repo, user)
- **Notion Key**: Scoped to your database
- **HubSpot Token**: Limited to contacts
- **Mistral Key**: Rate-limited, rotatable

### OAuth Tokens

- **Redirect URI**: Locked to localhost:8767
- **Scope**: Minimal required permissions only
- **Expiration**: Check provider settings

---

## 🐛 Troubleshooting

### "Setup state not found"

Create the state file:

```bash
mkdir -p memory/goblin
```

The system auto-creates `setup-state.json` on first wizard start.

### "Database paths not writable"

```bash
# Check permissions
ls -la memory/goblin/
chmod 755 memory/goblin/

# Initialize paths
curl -X POST http://127.0.0.1:8767/api/v0/setup/paths/initialize
```

### "GitHub CLI not found"

Install GitHub CLI:

```bash
# macOS
brew install gh

# Then authenticate
gh auth login
```

### ".env file not being read"

Ensure file is in the right location:

```bash
# Should be here:
~/uDOS/dev/goblin/.env

# Not here:
~/uDOS/.env
```

---

## 📈 Next Steps

1. **Copy .env template**: `cp .env.example .env`
2. **Initialize paths**: `POST /setup/paths/initialize`
3. **Complete wizard**: Visit `/setup/wizard/start`
4. **Validate services**: Check `/setup/validate/*` endpoints
5. **Test endpoints**: Use Swagger UI at `/docs`

---

## 📚 References

- [GitHub Docs](https://docs.github.com/)
- [Notion Developers](https://developers.notion.com/)
- [Mistral AI](https://docs.mistral.ai/)
- [HubSpot Developers](https://developers.hubspot.com/)
