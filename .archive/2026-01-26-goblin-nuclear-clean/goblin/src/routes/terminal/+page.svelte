<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import GridDisplay from "$lib/components/GridDisplay.svelte";
  import { isApiAvailable } from "$lib/stores/api";
  import {
    createHybridRouter,
    createTerminalWSStore,
    type WSMessage,
  } from "$lib/runtime";
  import { loadScript } from "$lib/runtime/scriptLoader";
  import { listen } from "@tauri-apps/api/event";
  import {
    DEFAULT_GRID_SETTINGS,
    getLineColorClass,
  } from "$lib/util/gridSystem";

  // Grid configuration using shared system
  const GRID = DEFAULT_GRID_SETTINGS.terminal;

  let command = $state("");
  let output = $state<
    Array<{
      type: "input" | "output" | "error" | "system";
      text: string;
      font?: "title" | "heading" | "body";
      color?: "green" | "cyan" | "orange" | "yellow" | "red" | "white";
    }>
  >([]);
  let apiOnline = $state(false);
  let wsConnected = $state(false);
  let inputRef: HTMLInputElement;
  let outputContainer: HTMLDivElement;
  let historyIndex = $state(-1);
  let commandHistory = $state<string[]>([]);
  let executionMode = $state<"client" | "api" | "hybrid">("hybrid");

  // Hybrid router for smart execution
  let router: Awaited<ReturnType<typeof createHybridRouter>> | null = null;

  // WebSocket store for streaming
  const wsStore = createTerminalWSStore();
  let unsubscribeWS: (() => void) | null = null;
  let unsubscribeState: (() => void) | null = null;
  let unsubscribeReset: (() => void) | null = null;

  // Track if startup script has been shown
  let hasShownStartup = false;

  onMount(async () => {
    console.log("[Terminal] ━━━━━━━━━━ MOUNT START ━━━━━━━━━━");

    try {
      // Initialize hybrid router
      console.log("[Terminal] Creating hybrid router...");
      router = await createHybridRouter();
      apiOnline = router.isAPIAvailable();
      console.log("[Terminal] Router created. API online:", apiOnline);
    } catch (error) {
      console.error("[Terminal] Failed to create router:", error);
    }

    // Try to connect WebSocket
    try {
      console.log("[Terminal] Connecting WebSocket...");
      await wsStore.connect();
      console.log("[Terminal] WebSocket connected");
    } catch (e) {
      console.log("[Terminal] WebSocket not available, using HTTP fallback");
    }

    // Subscribe to WebSocket state
    try {
      unsubscribeState = wsStore.state.subscribe((state) => {
        wsConnected = state.connected;
      });
      console.log("[Terminal] WebSocket state subscription active");
    } catch (error) {
      console.error("[Terminal] Failed to subscribe to WS state:", error);
    }

    // Subscribe to WebSocket messages
    try {
      unsubscribeWS = wsStore.messages.subscribe((messages) => {
        const lastMsg = messages[messages.length - 1];
        if (lastMsg) {
          handleWSMessage(lastMsg);
        }
      });
      console.log("[Terminal] WebSocket message subscription active");
    } catch (error) {
      console.error("[Terminal] Failed to subscribe to WS messages:", error);
    }

    // Load and run startup script if first time (or forced via URL param)
    const startupShownKey = "udos-terminal-startup-shown";
    const forceStartup = $page.url.searchParams.get("startup") === "true";
    hasShownStartup = localStorage.getItem(startupShownKey) === "true";

    console.log("[Terminal] ━━━━━━━━━━ STARTUP CHECK ━━━━━━━━━━");
    console.log("[Terminal] hasShownStartup:", hasShownStartup);
    console.log("[Terminal] forceStartup:", forceStartup);
    console.log(
      "[Terminal] localStorage value:",
      localStorage.getItem(startupShownKey)
    );

    // Always load startup script when Terminal mode is entered
    console.log("[Terminal] ✓ Loading startup script...");
    try {
      // Load startup script
      const script = await loadScript("startup");
      console.log("[Terminal] Startup script loaded:", script);
      if (script && script.messages && script.messages.length > 0) {
        console.log(
          "[Terminal] Startup script messages count:",
          script.messages.length
        );
        // Display startup messages
        output = script.messages.map((text) => ({
          type: "system" as const,
          text,
        }));
        console.log("[Terminal] ✓ Output set with", output.length, "lines");
        // Mark as shown (unless forced for testing)
        if (!forceStartup) {
          localStorage.setItem(startupShownKey, "true");
          hasShownStartup = true;
        }
      } else {
        throw new Error("Script loaded but has no messages");
      }
    } catch (error) {
      console.error("[Terminal] Error loading startup script:", error);
      console.log("[Terminal] ✗ Failed to load startup script, using fallback");
      // Fallback welcome message
      output = [
        {
          type: "system",
          text: "╔══════════════════════════════════════════════════╗",
        },
        {
          type: "system",
          text: "║           uDOS TERMINAL v1.0.1.0                 ║",
        },
        {
          type: "system",
          text: "║    Type HELP for commands • ⌘K for palette       ║",
        },
        {
          type: "system",
          text: "╚══════════════════════════════════════════════════╝",
        },
        { type: "system", text: "" },
      ];
    }

    // Listen for reset-mode-display to trigger reboot script
    try {
      unsubscribeReset = await listen("reset-mode-display", async () => {
        const script = await loadScript("reboot");
        if (script) {
          // Clear output and show reboot sequence
          output = script.messages.map((text) => ({
            type: "system" as const,
            text,
          }));
          // After 4 seconds, clear and reset startup flag
          setTimeout(() => {
            output = [];
            localStorage.removeItem(startupShownKey);
            hasShownStartup = false;
          }, 4000);
        }
      });
      console.log("[Terminal] Reset listener registered");

      // Listen for restart uDOS to show reboot sequence
      unsubscribeReset = await listen("show-reboot-sequence", async () => {
        console.log(
          "[Terminal] Reboot sequence triggered, loading reboot.udos.md"
        );
        const script = await loadScript("reboot");
        if (script && script.messages && script.messages.length > 0) {
          // Show reboot sequence from reboot.udos.md
          output = script.messages.map((text) => ({
            type: "system" as const,
            text,
          }));
          console.log(
            "[Terminal] Reboot script displayed:",
            output.length,
            "lines"
          );
        } else {
          // Fallback reboot message
          console.warn("[Terminal] reboot.udos.md not found, using fallback");
          output = [
            { type: "system", text: "" },
            {
              type: "system",
              text: "╔══════════════════════════════════════════════════╗",
            },
            {
              type: "system",
              text: "║               RESTARTING uDOS...                 ║",
            },
            {
              type: "system",
              text: "╚══════════════════════════════════════════════════╝",
            },
            { type: "system", text: "" },
          ];
        }
      });
      console.log("[Terminal] Restart listener registered");
    } catch (error) {
      console.error("[Terminal] Failed to register reset listener:", error);
    }

    console.log("[Terminal] Final output length:", output.length);
    console.log("[Terminal] ━━━━━━━━━━ MOUNT COMPLETE ━━━━━━━━━━");

    inputRef?.focus();
  });

  onDestroy(() => {
    unsubscribeWS?.();
    unsubscribeState?.();
    unsubscribeReset?.();
    wsStore.disconnect();
  });

  function handleWSMessage(msg: WSMessage) {
    if (msg.type === "output") {
      output = [...output, { type: "output", text: msg.data }];
    } else if (msg.type === "error") {
      output = [...output, { type: "error", text: msg.data }];
    }
    scrollToBottom();
  }

  async function executeCommand() {
    if (!command.trim()) return;

    const cmd = command.trim();
    output = [...output, { type: "input", text: `▶ ${cmd}` }];

    commandHistory = [...commandHistory, cmd];
    historyIndex = commandHistory.length;
    command = "";

    // Handle special commands
    if (cmd.toLowerCase() === "reboot" || cmd.toLowerCase() === "restart") {
      output = [
        ...output,
        { type: "system", text: "Initiating system reboot..." },
      ];
      scrollToBottom();
      // Trigger the restart event
      import("@tauri-apps/api/event").then(({ emit }) => {
        emit("restart-udos", {});
      });
      return;
    }

    if (!router) {
      output = [
        ...output,
        { type: "error", text: "! Runtime not initialized" },
      ];
      return;
    }

    if (wsConnected && /^[A-Z]+(\s|$)/.test(cmd)) {
      wsStore.sendCommand(cmd);
      return;
    }

    const result = await router.executeCommand(cmd);

    if (result.executedOn !== "api") {
      output = [...output, { type: "system", text: `[${result.executedOn}]` }];
    }

    if (result.success) {
      result.output.forEach((line) => {
        output = [...output, { type: "output", text: line }];
      });
    } else {
      output = [
        ...output,
        { type: "error", text: result.error || "Command failed" },
      ];
    }

    scrollToBottom();
  }

  function scrollToBottom() {
    setTimeout(() => {
      if (outputContainer) {
        outputContainer.scrollTop = outputContainer.scrollHeight;
      }
    }, 10);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      executeCommand();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (historyIndex > 0) {
        historyIndex--;
        command = commandHistory[historyIndex];
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (historyIndex < commandHistory.length - 1) {
        historyIndex++;
        command = commandHistory[historyIndex];
      } else {
        historyIndex = commandHistory.length;
        command = "";
      }
    } else if (e.key === "l" && e.ctrlKey) {
      e.preventDefault();
      output = [];
    } else if (e.key === "Escape") {
      e.preventDefault();
      goto("/teledesk");
    }
  }

  function toggleMode() {
    const modes: Array<"client" | "api" | "hybrid"> = [
      "hybrid",
      "client",
      "api",
    ];
    const idx = modes.indexOf(executionMode);
    executionMode = modes[(idx + 1) % modes.length];
  }

  function getLineClass(type: string): string {
    switch (type) {
      case "input":
        return "input";
      case "error":
        return "error";
      case "system":
        return "system";
      default:
        return "output";
    }
  }
  let showModeMenu = $state(false);
  function handleWindowKeydown(e: KeyboardEvent) {
    if (e.key.toLowerCase() === "m") {
      e.preventDefault();
      showModeMenu = !showModeMenu;
    }
  }
</script>

<svelte:head>
  <title>Terminal - uDOS</title>
</svelte:head>

<svelte:window onkeydown={handleWindowKeydown} />

<!-- Terminal Container: centered with visible border/padding area -->
<div class="terminal-container">
  <!-- Viewport Frame: the actual 40x24 terminal area -->
  <div class="viewport-frame">
    <!-- Viewport Background: dark terminal background -->
    <div class="viewport-bg">
      <!-- Viewport Content Area: where text renders -->
      <div class="viewport-content">
        <div class="output-area" bind:this={outputContainer}>
          {#each output as line}
            <div
              class="line {getLineClass(line.type)} {line.font
                ? 'font-' + line.font
                : 'font-body'} {line.color ? 'color-' + line.color : ''}"
            >
              {line.text}
            </div>
          {/each}
        </div>

        <!-- Input prompt -->
        <div class="prompt-line">
          <span class="prompt-char">▶</span>
          <input
            bind:this={inputRef}
            bind:value={command}
            onkeydown={handleKeydown}
            type="text"
            placeholder=""
            class="input-field"
          />
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Mode Menu (overlay) -->
{#if showModeMenu}
  <div class="mode-menu">
    <div class="menu-item text-udos-cyan">
      ╔ MODE MENU ═══════════════════════════╗
    </div>
    <div class="menu-item">
      <button class="menu-btn" onpointerdown={() => goto("/teledesk")}
        >TELEDESK</button
      >
    </div>
    <div class="menu-item">
      <button class="menu-btn" onpointerdown={() => goto("/terminal")}
        >TERMINAL</button
      >
    </div>
    <div class="menu-item text-udos-cyan">
      ╚ Press M to close ════════════════════╝
    </div>
  </div>
{/if}

<style>
  /* ============================================
     TERMINAL CONTAINER
     ============================================ */

  .terminal-container {
    /* Center the viewport vertically and horizontally
       Account for toolbars (menu bar ~30px, bottom bar ~40px = ~70px total)
       Use flex to center in available space */
    display: flex;
    align-items: center;
    justify-content: center;
    /* Full height minus approximate toolbar heights */
    height: calc(100vh - 70px);
    /* Alternate color background around viewport */
    background: linear-gradient(135deg, #1a1a2e 0%, #2a2a3e 100%);
    padding: 40px;
    font-family: var(--font-family-teletext, monospace);
    flex-grow: 1;
  }

  /* ============================================
     VIEWPORT FRAME
     Direct viewport container (no border/frame)
     ============================================ */

  .viewport-frame {
    /* No border/frame - just direct container */
    flex-shrink: 0;
  }

  /* ============================================
     VIEWPORT BACKGROUND
     The dark terminal screen background
     ============================================ */

  .viewport-bg {
    /* 40 cols × 24 rows at 24px per cell = 960×576px */
    width: 960px;
    height: 576px;
    background-color: rgb(3, 7, 18);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  /* ============================================
     VIEWPORT CONTENT
     The actual text rendering area
     ============================================ */

  .viewport-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    width: 100%;
    height: 100%;
  }

  .output-area {
    flex: 1;
    overflow: hidden;
    padding: 0;
    margin: 0;
    font-size: 24px;
    line-height: 24px;
    letter-spacing: 0;
  }

  .line {
    display: block;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
    margin: 0;
    padding: 0;
    height: auto;
    color: #06ffa5; /* uDOS grass green */
  }

  .prompt-line {
    display: flex;
    align-items: center;
    gap: 0;
    flex-shrink: 0;
    padding: 0;
    margin: 0;
    height: 24px;
    line-height: 24px;
  }

  .prompt-char {
    color: #06ffa5;
    flex-shrink: 0;
    font-weight: bold;
  }

  .input-field {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: #06ffa5;
    padding: 0;
    margin: 0;
    font-size: 24px;
    line-height: 24px;
    font-family: inherit;
    letter-spacing: 0;
  }

  .input-field::placeholder {
    color: rgba(6, 255, 165, 0.3);
  }

  /* ============================================
     LINE TYPE COLORS
     ============================================ */

  .line.input {
    color: #00d9ff; /* cyan for user input */
  }

  .line.error {
    color: #ff006e; /* red/magenta for errors */
  }

  .line.system {
    color: #888; /* gray for system messages */
  }

  .line.output {
    color: #06ffa5; /* green for output */
  }

  /* ============================================
     FONT CLASSES
     Font styles moved to global stylesheet (app.css)
     Shared between Terminal and Teledesk:
     - Title: PetMe64 at 48x48px (2x cell size)
     - Heading: PressStart2P at 24x24px (1x cell size) 
     - Heading-double: Teletext50 at 24px font / 48px line (double-height)
     - Body: Teletext50 at 24x24px (default)
     ============================================ */

  /* ============================================
     COLOR VARIANTS
     ============================================ */

  .line.color-green {
    color: #06ffa5; /* uDOS grass green */
  }

  .line.color-cyan {
    color: #00d9ff; /* uDOS objective cyan */
  }

  .line.color-orange {
    color: #fb5607; /* uDOS heat orange */
  }

  .line.color-yellow {
    color: #ffbe0b; /* uDOS waypoint yellow */
  }

  .line.color-red {
    color: #ff006e; /* uDOS danger red */
  }

  .line.color-white {
    color: #f8f9fa; /* uDOS white */
  }

  /* ============================================
     MODE MENU
     ============================================ */

  .mode-menu {
    position: fixed;
    top: 12px;
    left: 12px;
    z-index: 100;
    background: #0a0a0a;
    border: 2px solid #06ffa5;
    padding: 8px;
    box-shadow: 0 0 24px rgba(6, 255, 165, 0.2);
  }

  .menu-item {
    padding: 4px 8px;
    margin: 0;
    font-size: 12px;
  }

  .menu-btn {
    all: unset;
    cursor: pointer;
    padding: 2px 6px;
    background: #111;
    border: 1px solid #06ffa5;
    color: #06ffa5;
    margin: 2px 0;
    font-size: 12px;
  }

  .menu-btn:hover {
    background: #06ffa5;
    color: #0a0a0a;
  }

  .text-udos-cyan {
    color: #00d9ff;
  }
</style>
