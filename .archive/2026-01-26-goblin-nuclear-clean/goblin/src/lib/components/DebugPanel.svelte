<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import {
    debugPanelState,
    hideDebugPanel,
    toggleMinimizeDebugPanel,
  } from "$lib/stores/debugPanel";
  import { copyWithFeedback } from "$lib/util/clipboard";
  import { toastStore } from "$lib/stores/toastStore";

  type LogEntry = {
    timestamp: number;
    level: "log" | "warn" | "error" | "info";
    message: string;
  };

  let logs = $state<LogEntry[]>([]);
  let lastErrors = $state<LogEntry[]>([]);
  let consoleInterceptionActive = $state(false);
  let f12ConsoleOpen = $state(false);
  let performanceData = $state({
    memory: 0,
    timing: 0,
    elements: 0,
  });
  let appState = $state({
    route: "",
    userAgent: "",
    localStorage: 0,
    sessionStorage: 0,
  });

  // Reactive values from store
  let isVisible = $state(false);
  let isMinimized = $state(false);
  let position = $state<
    "top-left" | "top-right" | "bottom-left" | "bottom-right"
  >("top-right");

  // Subscribe to debug panel state
  $effect(() => {
    const unsubscribe = debugPanelState.subscribe((state) => {
      isVisible = state.isVisible;
      isMinimized = state.isMinimized;
      position = state.position;
    });

    return unsubscribe;
  });

  // Note: Console logs feature removed - use browser DevTools instead (Cmd+Option+I)

  onMount(() => {
    updatePerformanceData();
    updateAppState();
    detectF12Console();

    // Update data periodically
    const interval = setInterval(() => {
      updatePerformanceData();
      updateAppState();
    }, 2000);

    return () => clearInterval(interval);
  });

  function updatePerformanceData() {
    try {
      performanceData = {
        memory: (performance as any).memory
          ? Math.round((performance as any).memory.usedJSHeapSize / 1024 / 1024)
          : 0,
        timing: performance.now(),
        elements: document.querySelectorAll("*").length,
      };
    } catch (error) {
      console.warn("Could not update performance data:", error);
    }
  }

  function updateAppState() {
    appState = {
      route: $page.url.pathname,
      userAgent: navigator.userAgent.split(" ")[0] + "...",
      localStorage: Object.keys(localStorage).length,
      sessionStorage: Object.keys(sessionStorage).length,
    };
  }

  function detectF12Console() {
    // Detect if F12 console is open by monitoring console size
    let devtools = { open: false, orientation: null };
    const threshold = 160;

    setInterval(() => {
      if (
        window.outerHeight - window.innerHeight > threshold ||
        window.outerWidth - window.innerWidth > threshold
      ) {
        if (!devtools.open) {
          devtools.open = true;
          f12ConsoleOpen = true;
          console.info("🔍 F12 Developer Console opened");
        }
      } else {
        if (devtools.open) {
          devtools.open = false;
          f12ConsoleOpen = false;
          console.info("🔍 F12 Developer Console closed");
        }
      }
    }, 500);
  }

  function openF12Console() {
    // Show toast with instructions
    toastStore.info(
      "Browser DevTools: Mac: Cmd+Option+I | Windows/Linux: Ctrl+Shift+I | Or right-click → Inspect Element",
      5000
    );
    console.log(
      "%c🔍 Browser DevTools Instructions",
      "font-weight: bold; font-size: 14px; color: #0ea5e9;"
    );
    console.log("  Mac: Cmd+Option+I");
    console.log("  Windows/Linux: Ctrl+Shift+I");
    console.log("  Or right-click → Inspect Element");
  }

  function toggleMinimize() {
    toggleMinimizeDebugPanel();
  }

  function close() {
    hideDebugPanel();
  }

  function clearConsole() {
    console.clear();
    logs = [];
    console.info("🗑️ Console cleared");
  }

  function copyLogs() {
    // Copy current debug panel info
    const debugInfo = `Debug Panel Info:

Performance:
- Memory: ${performanceData.memory}MB
- DOM Elements: ${performanceData.elements}
- Uptime: ${Math.round(performanceData.timing / 1000)}s

App State:
- Route: ${appState.route}
- LocalStorage Keys: ${appState.localStorage}
- SessionStorage Keys: ${appState.sessionStorage}
- User Agent: ${navigator.userAgent}

Timestamp: ${new Date().toISOString()}

Note: For full console logs, use browser DevTools (Cmd+Option+I)`;

    copyWithFeedback(debugInfo, "📋 Debug info copied");
  }

  function runQuickTest() {
    console.log("🧪 Debug Panel Test");
    console.warn("⚠️ Test warning");
    console.error("❌ Test error");
    console.info("ℹ️ Test info");
  }

  function getPositionClasses() {
    const baseClasses = "fixed z-50";
    switch (position) {
      case "top-left":
        return `${baseClasses} top-4 left-4`;
      case "top-right":
        return `${baseClasses} top-4 right-4`;
      case "bottom-left":
        return `${baseClasses} bottom-4 left-4`;
      case "bottom-right":
        return `${baseClasses} bottom-4 right-4`;
      default:
        return `${baseClasses} top-4 right-4`;
    }
  }

  function getLevelColor(level: string) {
    switch (level) {
      case "error":
        return "text-red-400";
      case "warn":
        return "text-yellow-400";
      case "info":
        return "text-blue-400";
      default:
        return "text-gray-400";
    }
  }
</script>

{#if isVisible}
  <div class={getPositionClasses()}>
    <div
      class="bg-gray-900 border border-gray-700 rounded-lg shadow-2xl text-white text-xs max-w-sm min-w-80 backdrop-blur-sm"
    >
      <!-- Header -->
      <div
        class="flex items-center justify-between px-3 py-2 border-b border-gray-700 bg-gray-800 rounded-t-lg"
      >
        <div class="flex items-center gap-2">
          <span class="text-sm font-bold">🛠️ Debug Panel</span>
          <div class="flex gap-1">
            <div
              class="w-2 h-2 rounded-full bg-green-500"
              class:bg-red-500={!consoleInterceptionActive}
              title="Console Interception"
            ></div>
            <div
              class="w-2 h-2 rounded-full bg-blue-500"
              class:bg-gray-500={!f12ConsoleOpen}
              title="F12 Console"
            ></div>
          </div>
        </div>
        <div class="flex items-center gap-1">
          <button
            onclick={toggleMinimize}
            class="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs transition-colors"
            title={isMinimized ? "Expand" : "Minimize"}
          >
            {isMinimized ? "⬆" : "⬇"}
          </button>
          <button
            onclick={close}
            class="px-2 py-1 bg-red-600 hover:bg-red-500 rounded text-xs transition-colors"
            title="Close"
          >
            ✕
          </button>
        </div>
      </div>

      {#if !isMinimized}
        <!-- Content -->
        <div class="p-3 space-y-3">
          <!-- Performance Stats -->
          <div>
            <div class="text-xs font-bold mb-1 text-gray-300">
              ⚡ Performance
            </div>
            <div class="space-y-1 text-xs">
              <div class="flex justify-between">
                <span>Memory:</span>
                <span class="font-mono">{performanceData.memory}MB</span>
              </div>
              <div class="flex justify-between">
                <span>DOM Elements:</span>
                <span class="font-mono">{performanceData.elements}</span>
              </div>
              <div class="flex justify-between">
                <span>Uptime:</span>
                <span class="font-mono"
                  >{Math.round(performanceData.timing / 1000)}s</span
                >
              </div>
            </div>
          </div>

          <!-- App State -->
          <div>
            <div class="text-xs font-bold mb-1 text-gray-300">📍 App State</div>
            <div class="space-y-1 text-xs">
              <div class="flex justify-between">
                <span>Route:</span>
                <span
                  class="font-mono text-blue-400 truncate max-w-32"
                  title={appState.route}>{appState.route}</span
                >
              </div>
              <div class="flex justify-between">
                <span>LocalStorage:</span>
                <span class="font-mono">{appState.localStorage} keys</span>
              </div>
              <div class="flex justify-between">
                <span>Console Logs:</span>
                <span class="font-mono">{logs.length}</span>
              </div>
            </div>
          </div>

          <!-- Recent Errors -->
          {#if lastErrors.length > 0}
            <div>
              <div class="text-xs font-bold mb-1 text-gray-300">
                🚨 Recent Issues
              </div>
              <div class="space-y-1 max-h-20 overflow-y-auto">
                {#each lastErrors as error}
                  <div
                    class="text-xs p-1 bg-gray-800 rounded {getLevelColor(
                      error.level
                    )}"
                  >
                    <span class="font-bold">{error.level.toUpperCase()}:</span>
                    <span class="break-all"
                      >{error.message.substring(0, 50)}{error.message.length >
                      50
                        ? "..."
                        : ""}</span
                    >
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          <!-- Quick Actions -->
          <div>
            <div class="text-xs font-bold mb-1 text-gray-300">
              🔧 Quick Actions
            </div>
            <div class="flex flex-wrap gap-1">
              <button
                onclick={openF12Console}
                class="px-2 py-1 bg-blue-600 hover:bg-blue-500 rounded text-xs transition-colors"
                title="Instructions to open browser DevTools"
              >
                🔍 DevTools
              </button>
              <button
                onclick={clearConsole}
                class="px-2 py-1 bg-yellow-600 hover:bg-yellow-500 rounded text-xs transition-colors"
                title="Clear browser console"
              >
                🗑️ Clear
              </button>
              <button
                onclick={copyLogs}
                class="px-2 py-1 bg-green-600 hover:bg-green-500 rounded text-xs transition-colors"
                title="Copy debug panel info to clipboard"
              >
                📋 Copy Info
              </button>
              <button
                onclick={runQuickTest}
                class="px-2 py-1 bg-purple-600 hover:bg-purple-500 rounded text-xs transition-colors"
                title="Send test logs to console"
              >
                🧪 Test
              </button>
            </div>
          </div>

          <!-- DevTools Integration Status -->
          <div>
            <div class="text-xs font-bold mb-1 text-gray-300">
              🔗 Browser DevTools
            </div>
            <div class="text-xs space-y-1">
              <div class="flex items-center gap-2">
                <div
                  class="w-2 h-2 rounded-full {f12ConsoleOpen
                    ? 'bg-green-500'
                    : 'bg-gray-500'}"
                ></div>
                <span>DevTools: {f12ConsoleOpen ? "Open" : "Closed"}</span>
              </div>
              {#if f12ConsoleOpen}
                <div class="text-blue-400 text-xs">
                  ✅ Check Console tab for all logs
                </div>
              {:else}
                <div class="text-yellow-400 text-xs">
                  💡 Cmd+Option+I (Mac) / Ctrl+Shift+I (Win)
                </div>
              {/if}
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
{/if}
