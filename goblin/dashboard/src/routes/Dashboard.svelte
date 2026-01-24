<script>
  import { onMount } from "svelte";

  let serverInfo = null;
  let loading = true;

  async function loadInfo() {
    try {
      const res = await fetch("/api/v0/info");
      if (res.ok) {
        serverInfo = await res.json();
      }
    } catch (err) {
      console.error("Failed to load server info", err);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loadInfo();
  });
</script>

<div class="max-w-7xl mx-auto px-4 py-8 space-y-6">
  <div>
    <h1 class="text-3xl font-bold text-white mb-2">Goblin Dev Server</h1>
    <p class="text-gray-300">
      Experimental development server for uDOS feature testing
    </p>
  </div>

  {#if loading}
    <div class="bg-slate-800/50 rounded-lg p-6 text-center text-gray-400">
      Loading server info...
    </div>
  {:else if serverInfo}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div class="bg-slate-800/50 rounded-lg p-6 border border-purple-500/30">
        <div class="text-sm text-gray-400 mb-1">Server</div>
        <div class="text-xl font-semibold text-white">{serverInfo.server}</div>
      </div>

      <div class="bg-slate-800/50 rounded-lg p-6 border border-purple-500/30">
        <div class="text-sm text-gray-400 mb-1">Version</div>
        <div class="text-xl font-semibold text-white">{serverInfo.version}</div>
      </div>

      <div class="bg-slate-800/50 rounded-lg p-6 border border-purple-500/30">
        <div class="text-sm text-gray-400 mb-1">Status</div>
        <div class="text-xl font-semibold text-amber-400">
          {serverInfo.status}
        </div>
      </div>

      <div class="bg-slate-800/50 rounded-lg p-6 border border-purple-500/30">
        <div class="text-sm text-gray-400 mb-1">Port</div>
        <div class="text-xl font-semibold text-white">{serverInfo.port}</div>
      </div>

      <div class="bg-slate-800/50 rounded-lg p-6 border border-purple-500/30">
        <div class="text-sm text-gray-400 mb-1">Scope</div>
        <div class="text-xl font-semibold text-white">{serverInfo.scope}</div>
      </div>

      <div class="bg-slate-800/50 rounded-lg p-6 border border-purple-500/30">
        <div class="text-sm text-gray-400 mb-1">API Prefix</div>
        <div class="text-xl font-semibold text-white">
          {serverInfo.api_prefix}
        </div>
      </div>
    </div>

    <div class="bg-amber-900/30 border border-amber-500/50 rounded-lg p-6">
      <div class="flex items-start gap-3">
        <div class="text-amber-400 text-2xl">⚠️</div>
        <div>
          <h3 class="text-lg font-semibold text-amber-300 mb-2">
            Experimental Server
          </h3>
          <p class="text-amber-100 mb-2">{serverInfo.warning}</p>
          <p class="text-sm text-amber-200">
            Features developed here are promoted to Core, Extensions, or Wizard
            when stable.
          </p>
        </div>
      </div>
    </div>

    <div class="bg-slate-800/50 rounded-lg p-6 border border-purple-500/30">
      <h2 class="text-xl font-semibold text-white mb-4">
        🧪 Active Features in Development
      </h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div class="bg-slate-700/50 rounded-lg p-4">
          <h3 class="font-semibold text-purple-300 mb-2">� Binder Compiler</h3>
          <p class="text-sm text-gray-300">
            Multi-chapter generation with format exports
          </p>
        </div>

        <div class="bg-slate-700/50 rounded-lg p-4">
          <h3 class="font-semibold text-purple-300 mb-2">🔧 Screwdriver</h3>
          <p class="text-sm text-gray-300">
            Device provisioning & flash pack distribution
          </p>
        </div>

        <div class="bg-slate-700/50 rounded-lg p-4">
          <h3 class="font-semibold text-purple-300 mb-2">
            🌐 MeshCore Manager
          </h3>
          <p class="text-sm text-gray-300">
            P2P mesh network device management
          </p>
        </div>
      </div>

      <div class="mt-4 p-4 bg-slate-700/30 rounded-lg border border-slate-600">
        <p class="text-sm text-gray-400">
          <strong class="text-gray-300">Moved to Wizard:</strong> Notion Sync,
          Task Scheduler<br />
          <strong class="text-gray-300">In Core:</strong> TS Markdown Runtime
        </p>
      </div>
    </div>

    <div class="bg-slate-800/50 rounded-lg p-6 border border-purple-500/30">
      <h2 class="text-xl font-semibold text-white mb-2">Quick Links</h2>
      <div class="flex flex-wrap gap-3">
        <a
          href={serverInfo.docs}
          target="_blank"
          class="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-semibold transition"
        >
          API Docs (Swagger)
        </a>
        <a
          href="/redoc"
          target="_blank"
          class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-semibold transition"
        >
          ReDoc
        </a>
      </div>
    </div>
  {/if}
</div>
