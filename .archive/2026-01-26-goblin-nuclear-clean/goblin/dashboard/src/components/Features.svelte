<script lang="ts">
  interface Feature {
    name: string;
    description: string;
    endpoint: string;
    status: "active" | "experimental" | "planned";
  }

  const features: Feature[] = [
    {
      name: "Notion Sync",
      description: "Bidirectional Notion ↔ Markdown synchronization",
      endpoint: "/api/v0/notion/webhook",
      status: "active",
    },
    {
      name: "TS Runtime",
      description: "Execute TypeScript Markdown runtime blocks",
      endpoint: "/api/v0/runtime/execute",
      status: "active",
    },
    {
      name: "Task Scheduler",
      description: "Organic cron task scheduling (Plant → Sprout → Harvest)",
      endpoint: "/api/v0/tasks/schedule",
      status: "active",
    },
    {
      name: "Binder Compiler",
      description: "Multi-format document compilation (MD, PDF, JSON, Brief)",
      endpoint: "/api/v0/binder/compile",
      status: "active",
    },
    {
      name: "AI Assistant",
      description: "Mistral/Vibe CLI integration for code assistance",
      endpoint: "/api/v0/ai/query",
      status: "experimental",
    },
    {
      name: "GitHub Tools",
      description: "GitHub CLI integration (issues, PRs, devlog)",
      endpoint: "/api/v0/github/repos",
      status: "experimental",
    },
    {
      name: "Workflow Manager",
      description: "Native project and task management",
      endpoint: "/api/v0/workflow/projects",
      status: "experimental",
    },
  ];

  function getStatusColor(status: string): string {
    switch (status) {
      case "active":
        return "#10b981";
      case "experimental":
        return "#f59e0b";
      case "planned":
        return "#6b7280";
      default:
        return "#6b7280";
    }
  }

  function getStatusLabel(status: string): string {
    switch (status) {
      case "active":
        return "✓ Active";
      case "experimental":
        return "⚗️ Experimental";
      case "planned":
        return "📋 Planned";
      default:
        return status;
    }
  }
</script>

<div class="features-section">
  <h3>Available Dev Features</h3>
  <p class="subtitle">Experimental services for development and testing</p>

  <div class="features-grid">
    {#each features as feature}
      <div class="feature-card">
        <div class="feature-header">
          <h4>{feature.name}</h4>
          <span
            class="status-badge"
            style="background-color: {getStatusColor(feature.status)}20; 
                   color: {getStatusColor(feature.status)}; 
                   border: 1px solid {getStatusColor(feature.status)}"
          >
            {getStatusLabel(feature.status)}
          </span>
        </div>
        <p class="description">{feature.description}</p>
        <code class="endpoint">{feature.endpoint}</code>
      </div>
    {/each}
  </div>
</div>

<style>
  .features-section {
    margin: 30px 0;
  }

  h3 {
    font-size: 1.5em;
    color: #333;
    margin-bottom: 5px;
  }

  .subtitle {
    color: #666;
    font-size: 0.9em;
    margin-bottom: 20px;
  }

  .features-grid {
    display: grid;
    gap: 15px;
  }

  .feature-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    border-left: 4px solid #667eea;
  }

  .feature-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  h4 {
    margin: 0;
    color: #333;
    font-size: 1.1em;
    font-weight: 600;
  }

  .status-badge {
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75em;
    font-weight: 600;
  }

  .description {
    color: #666;
    font-size: 0.9em;
    line-height: 1.5;
    margin: 8px 0;
  }

  .endpoint {
    display: block;
    font-family: "Monaco", "Courier New", monospace;
    font-size: 0.8em;
    color: #667eea;
    background: rgba(102, 126, 234, 0.1);
    padding: 4px 8px;
    border-radius: 4px;
    margin-top: 8px;
  }
</style>
