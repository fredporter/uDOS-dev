<script lang="ts">
  import { onMount } from "svelte";
  import { Settings, Server, Database, Bell, Calendar, FileText, Code, Zap } from "lucide-svelte";

  type Config = {
    server?: { host?: string; port?: number; debug?: boolean; log_level?: string };
    notion?: {
      webhook_secret_keychain_id?: string;
      integration_token_keychain_id?: string;
      database_id?: string;
      sync_mode?: string;
      auto_sync?: boolean;
      queue_max_size?: number;
    };
    database?: { path?: string };
    runtime?: Record<string, unknown>;
    scheduler?: Record<string, unknown>;
    binder?: Record<string, unknown>;
    providers?: Record<string, unknown>;
  };

  let config: Config | null = null;
  let loadError = "";
  let loading = true;
  let serverStatus: "checking" | "online" | "offline" = "checking";
  let notionStatus: "checking" | "ready" | "unconfigured" = "checking";

  onMount(async () => {
    try {
      const mod = await import("../../../config/goblin.json");
      config = mod.default as Config;
      await checkServerStatus();
      checkNotionConfig();
    } catch (err: any) {
      loadError = err?.message || "Failed to load goblin.json";
    } finally {
      loading = false;
    }
  });

  async function checkServerStatus() {
    try {
      const response = await fetch("/api/v0/health", { method: "GET" });
      serverStatus = response.ok ? "online" : "offline";
    } catch {
      serverStatus = "offline";
    }
  }

  function checkNotionConfig() {
    if (config?.notion?.integration_token_keychain_id && config?.notion?.webhook_secret_keychain_id) {
      notionStatus = "ready";
    } else {
      notionStatus = "unconfigured";
    }
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
  }
</script>

<svelte:head>
  <title>Goblin Config</title>
</svelte:head>

<div class="page">
  <header class="header">
    <div class="header-content">
      <div class="title-area">
        <Settings class="header-icon" size={28} />
        <div>
          <p class="eyebrow">Goblin Dev Server v0.2.0</p>
          <h1>Configuration Dashboard</h1>
          <p class="muted">Live view of dev/goblin/config/goblin.json (read-only)</p>
        </div>
      </div>
      
      <div class="status-badges">
        <div class="badge {serverStatus === 'online' ? 'online' : serverStatus === 'offline' ? 'offline' : 'checking'}">
          <Server size={14} />
          {serverStatus === 'checking' ? 'Checking...' : serverStatus === 'online' ? 'Server Online' : 'Server Offline'}
        </div>
        <div class="badge {notionStatus === 'ready' ? 'online' : notionStatus === 'unconfigured' ? 'offline' : 'checking'}">
          <Bell size={14} />
          {notionStatus === 'checking' ? 'Checking...' : notionStatus === 'ready' ? 'Notion Ready' : 'Not Configured'}
        </div>
      </div>
    </div>
    
    <nav class="nav-links">
      <a class="nav-btn" href="/">🏠 Home</a>
      <a class="nav-btn" href="/desktop">🖥️ Desktop</a>
      <a class="nav-btn" href="/api/v0/notion/status" target="_blank">📊 API Status</a>
      <a class="nav-btn" href="https://developers.notion.com/docs" target="_blank">📚 Notion Docs</a>
    </nav>
  </header>

  {#if loading}
    <div class="card">Loading config...</div>
  {:else if loadError}
    <div class="card error">
      <p class="label">Error</p>
      <p>{loadError}</p>
      <p class="hint">Ensure dev/goblin/config/goblin.json exists.</p>
    </div>
  {:else if config}
    <div class="grid">
      <!-- Server Config -->
      <div class="card server-card">
        <div class="card-header">
          <Server size={20} class="card-icon" />
          <p class="label">Server Configuration</p>
        </div>
        <div class="info-row">
          <span class="info-label">Endpoint:</span>
          <button class="value-btn" onclick={() => copyToClipboard(`${config.server?.host}:${config.server?.port}`)}>
            {config.server?.host ?? "localhost"}:{config.server?.port ?? 8767}
          </button>
        </div>
        <div class="info-row">
          <span class="info-label">Debug Mode:</span>
          <span class="badge-small {config.server?.debug ? 'debug-on' : 'debug-off'}">
            {config.server?.debug ? 'ON' : 'OFF'}
          </span>
        </div>
        <div class="info-row">
          <span class="info-label">Log Level:</span>
          <span class="value">{config.server?.log_level ?? "info"}</span>
        </div>
      </div>

      <!-- Notion Config -->
      <div class="card notion-card">
        <div class="card-header">
          <Bell size={20} class="card-icon" />
          <p class="label">Notion Integration</p>
        </div>
        <div class="info-row">
          <span class="info-label">Token Keychain:</span>
          <span class="value monospace">{config.notion?.integration_token_keychain_id ?? "goblin-notion-token"}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Webhook Keychain:</span>
          <span class="value monospace">{config.notion?.webhook_secret_keychain_id ?? "goblin-notion-webhook"}</span>
        </div>
        {#if config.notion?.database_id}
          <div class="info-row">
            <span class="info-label">Database ID:</span>
            <button class="value-btn monospace" onclick={() => copyToClipboard(config.notion?.database_id ?? '')}>
              {config.notion?.database_id}
            </button>
          </div>
        {/if}
        <div class="info-row">
          <span class="info-label">Sync Mode:</span>
          <span class="badge-small">{config.notion?.sync_mode ?? "publish"}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Auto Sync:</span>
          <span class="badge-small {config.notion?.auto_sync ? 'debug-on' : 'debug-off'}">
            {config.notion?.auto_sync ? 'ON' : 'OFF'}
          </span>
        </div>
      </div>

      <!-- Database Config -->
      <div class="card database-card">
        <div class="card-header">
          <Database size={20} class="card-icon" />
          <p class="label">Database</p>
        </div>
        <div class="info-row">
          <span class="info-label">SQLite Path:</span>
          <button class="value-btn monospace" onclick={() => copyToClipboard(config.database?.path ?? '')}>
            {config.database?.path ?? "memory/synced/notion_sync.db"}
          </button>
        </div>
        <p class="muted mt">⚠️ Ensure this path is writable by Goblin server</p>
      </div>

      <!-- Runtime Config -->
      <div class="card">
        <div class="card-header">
          <Code size={20} class="card-icon" />
          <p class="label">Runtime Executor</p>
        </div>
        <pre>{JSON.stringify(config.runtime ?? { status: "experimental", blocks: ["state", "set", "form", "if", "nav", "panel", "map"] }, null, 2)}</pre>
      </div>

      <!-- Scheduler Config -->
      <div class="card">
        <div class="card-header">
          <Calendar size={20} class="card-icon" />
          <p class="label">Task Scheduler</p>
        </div>
        <pre>{JSON.stringify(config.scheduler ?? { model: "organic_cron", phases: ["Plant", "Sprout", "Prune", "Trellis", "Harvest", "Compost"] }, null, 2)}</pre>
      </div>

      <!-- Binder Config -->
      <div class="card">
        <div class="card-header">
          <FileText size={20} class="card-icon" />
          <p class="label">Binder Compiler</p>
        </div>
        <pre>{JSON.stringify(config.binder ?? { formats: ["markdown", "pdf", "json"], pandoc_required: true }, null, 2)}</pre>
      </div>

      <!-- Providers Config -->
      <div class="card">
        <div class="card-header">
          <Zap size={20} class="card-icon" />
          <p class="label">AI Providers</p>
        </div>
        <pre>{JSON.stringify(config.providers ?? { ollama: { priority: 1 }, openrouter: { priority: 2, fallback: true } }, null, 2)}</pre>
      </div>
    </div>
  {/if}
</div>

<style>
  :global(body) { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
  
  .page { 
    padding: 20px; 
    color: #e2e8f0; 
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    min-height: 100vh; 
  }
  
  .header { 
    margin-bottom: 24px; 
    background: #111827; 
    border: 1px solid #1f2937; 
    border-radius: 12px; 
    padding: 20px;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  }
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 16px;
    flex-wrap: wrap;
  }
  
  .title-area {
    display: flex;
    gap: 12px;
    align-items: flex-start;
  }
  
  .header-icon {
    color: #22d3ee;
    flex-shrink: 0;
  }
  
  .eyebrow { 
    text-transform: uppercase; 
    letter-spacing: 0.08em; 
    font-size: 11px; 
    color: #22d3ee; 
    margin: 0 0 4px;
    font-weight: 600;
  }
  
  h1 { 
    margin: 0 0 6px; 
    font-size: 24px; 
    font-weight: 700;
    background: linear-gradient(135deg, #22d3ee 0%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .muted { 
    color: #94a3b8; 
    margin: 0; 
    font-size: 13px; 
  }
  
  .status-badges {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  
  .badge {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    border: 1px solid;
  }
  
  .badge.online {
    background: #064e3b;
    color: #6ee7b7;
    border-color: #065f46;
  }
  
  .badge.offline {
    background: #7f1d1d;
    color: #fca5a5;
    border-color: #991b1b;
  }
  
  .badge.checking {
    background: #422006;
    color: #fbbf24;
    border-color: #78350f;
  }
  
  .nav-links {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  
  .nav-btn {
    background: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 13px;
    text-decoration: none;
    transition: all 0.2s;
    font-weight: 500;
  }
  
  .nav-btn:hover {
    border-color: #22d3ee;
    background: #334155;
    color: #22d3ee;
    transform: translateY(-1px);
  }
  
  .grid { 
    display: grid; 
    gap: 16px; 
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
  }
  
  .card { 
    background: #111827; 
    border: 1px solid #1f2937; 
    border-radius: 10px; 
    padding: 16px;
    transition: all 0.2s;
  }
  
  .card:hover {
    border-color: #334155;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.2);
  }
  
  .card.error { 
    border-color: #f87171; 
    background: #7f1d1d; 
    color: #fecdd3; 
  }
  
  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1f2937;
  }
  
  .card-icon {
    color: #22d3ee;
  }
  
  .label { 
    text-transform: uppercase; 
    letter-spacing: 0.08em; 
    font-size: 10px; 
    color: #94a3b8; 
    margin: 0;
    font-weight: 600;
  }
  
  .info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    gap: 12px;
  }
  
  .info-label {
    font-size: 12px;
    color: #94a3b8;
    font-weight: 500;
  }
  
  .value { 
    font-size: 13px; 
    margin: 0; 
    word-break: break-all;
    color: #e2e8f0;
  }
  
  .value-btn {
    background: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
    font-family: ui-monospace, monospace;
  }
  
  .value-btn:hover {
    border-color: #22d3ee;
    color: #22d3ee;
  }
  
  .badge-small {
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 600;
    background: #1e293b;
    color: #94a3b8;
    border: 1px solid #334155;
  }
  
  .badge-small.debug-on {
    background: #064e3b;
    color: #6ee7b7;
    border-color: #065f46;
  }
  
  .badge-small.debug-off {
    background: #422006;
    color: #fbbf24;
    border-color: #78350f;
  }
  
  .monospace { 
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; 
  }
  
  .mt { margin-top: 8px; }
  
  pre { 
    margin: 0; 
    background: #0b1221; 
    border: 1px solid #1f2937; 
    border-radius: 6px; 
    padding: 12px; 
    font-size: 11px; 
    overflow: auto; 
    color: #cbd5e1;
    line-height: 1.6;
  }
  
  .hint {
    color: #fbbf24;
    font-size: 12px;
    margin-top: 8px;
  }
</style>
