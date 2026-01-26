<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import GridDisplay from "$lib/components/GridDisplay.svelte";
  import {
    gridMode,
    viewportDims,
    type GridSubmode,
  } from "$lib/stores/gridMode";
  import { goto } from "$app/navigation";
  import {
    fitGridToContainer,
    DEFAULT_GRID_SETTINGS,
  } from "$lib/util/gridSystem";
  import { setMonoVariant } from "$lib/services/styleManager";
  import {
    getPage,
    getNotFoundPage,
    formatContent,
  } from "$lib/stores/teledesk";
  import {
    createHybridRouter,
    createTerminalWSStore,
    type WSMessage,
  } from "$lib/runtime";
  import {
    generateBootDemo,
    generateTeletextDemo,
    generateColumnsDemo,
    generateNewsDemo,
    type DemoLine,
  } from "$lib/util/demoContent";

  // Reactive grid configuration - using proper $state
  let gridState = $state({
    mode: "teledesk" as GridSubmode,
    viewportBorder: false,
    fixedCols: 40,
    fixedRows: 15,
    cellSize: 24,
    mono: "teletext" as any, // Default body: Teletext50 24x24
  });

  // Subscribe to store updates
  let unsubGrid: (() => void) | null = null;
  onMount(() => {
    unsubGrid = gridMode.subscribe((v) => {
      gridState = { ...v };
      // Apply font immediately when it changes
      setMonoVariant(v.mono as any, true);
    });
  });
  onDestroy(() => unsubGrid?.());

  let container: HTMLDivElement;
  let appContainer: HTMLDivElement;
  let dims = $state({ cols: 40, rows: 15 });

  function recalcDynamicGrid() {
    if (!gridState.viewportBorder && container) {
      const rect = container.getBoundingClientRect();
      const fit = fitGridToContainer(
        rect.width,
        rect.height,
        gridState.cellSize
      );
      dims = { cols: Math.max(10, fit.cols), rows: Math.max(10, fit.rows) };
    } else {
      dims = { cols: gridState.fixedCols, rows: gridState.fixedRows };
    }
  }

  let resizeObserver: ResizeObserver | null = null;
  let modeInitialized = false;
  let showModeMenu = $state(false);

  onMount(() => {
    // Ensure default mono variant for grid on mount
    setMonoVariant(gridState.mono as any, true);
    recalcDynamicGrid();
    resizeObserver = new ResizeObserver(() => recalcDynamicGrid());
    if (container) resizeObserver.observe(container);
    // Focus app container for keyboard events
    if (appContainer) appContainer.focus();
  });

  onMount(async () => {
    // Wait for first mount to complete
    await new Promise((resolve) => setTimeout(resolve, 50));

    // Always initialize terminal router for grid commands
    await term_init();

    // Start with demo - always show boot demo first
    showingDemo = true;
    loadDemo("boot");
    modeInitialized = true;
  });

  onDestroy(() => resizeObserver?.disconnect());

  // =====================
  // Script Execution
  // =====================
  async function loadAndExecuteStartup() {
    // Load startup.udos.md script
    try {
      const response = await fetch("/scripts/startup.udos.md");
      if (response.ok) {
        const scriptContent = await response.text();
        // Execute via terminal if available
        if (term_router) {
          // Parse the script and execute commands
          const lines = scriptContent.split("\n");
          for (const line of lines) {
            const trimmed = line.trim();
            // Skip comments and empty lines
            if (!trimmed || trimmed.startsWith("#")) continue;
            // Execute uDOS commands
            if (/^[A-Z]+(\s|$)/.test(trimmed)) {
              try {
                const res = await term_router.executeCommand(trimmed);
                if (res.output) {
                  res.output.forEach((out) => {
                    term_output = [
                      ...term_output,
                      { type: "system", text: out },
                    ];
                  });
                }
              } catch (e) {
                // Continue on error
              }
            }
          }
          term_scroll();
        }
      }
    } catch (e) {
      console.warn("Failed to load startup script", e);
    }
  }

  async function loadAndExecuteReboot() {
    // Load reboot.udos.md script
    try {
      const response = await fetch("/scripts/reboot.udos.md");
      if (response.ok) {
        const scriptContent = await response.text();
        // Clear terminal and show boot sequence
        term_output = [];
        const lines = scriptContent.split("\n");
        for (const line of lines) {
          const trimmed = line.trim();
          // Skip comments and empty lines
          if (!trimmed || trimmed.startsWith("#")) continue;
          // Execute uDOS commands
          if (/^[A-Z]+(\s|$)/.test(trimmed)) {
            try {
              const res = await term_router?.executeCommand(trimmed);
              if (res?.output) {
                res.output.forEach((out) => {
                  term_output = [...term_output, { type: "system", text: out }];
                });
              }
            } catch (e) {
              // Continue on error
            }
          }
        }
        term_scroll();
      }
    } catch (e) {
      console.warn("Failed to load reboot script", e);
    }
  }

  // =====================
  // Demo Mode
  // =====================
  let showingDemo = $state(true); // Start with demo on load
  let currentDemoIndex = $state(0);
  const demoSequence = ["boot", "teletext", "columns", "news"];

  function loadDemo(demoName: string) {
    if (!dims.cols || !dims.rows) return;

    let demo = null;
    switch (demoName) {
      case "teletext":
        demo = generateTeletextDemo(dims.cols, dims.rows);
        break;
      case "columns":
        demo = generateColumnsDemo(dims.cols, dims.rows);
        break;
      case "news":
        demo = generateNewsDemo(dims.cols, dims.rows);
        break;
      case "boot":
      default:
        demo = generateBootDemo(dims.cols, dims.rows);
    }

    if (demo) {
      grid_lines = demo.lines;
      td_lines = demo.lines;
      td_currentPage = 100 + currentDemoIndex;
    }
  }

  function nextDemo() {
    currentDemoIndex = (currentDemoIndex + 1) % demoSequence.length;
    loadDemo(demoSequence[currentDemoIndex]);
  }

  function exitDemo() {
    showingDemo = false;
    setMode("terminal");
  }

  // =====================
  // Grid Viewport (shared display for all modes)
  // =====================
  let grid_lines = $state<(string | DemoLine)[]>([]);

  // =====================
  // Teledesk (Teletext)
  // =====================
  let td_currentPage = $state(100);
  let td_lines = $state<(string | DemoLine)[]>([]);
  let td_loading = $state(false);
  async function td_load(pageNum: number) {
    if (pageNum < 100 || pageNum > 999) return;
    td_loading = true;
    let page = await getPage(pageNum);
    if (!page) page = getNotFoundPage(pageNum);
    td_currentPage = pageNum;
    td_lines = formatContent(
      page.content,
      dims.cols,
      Math.max(1, dims.rows - 0)
    );
    td_loading = false;
  }

  // =====================
  // Terminal (Console)
  // =====================
  let term_output = $state<
    Array<{ type: "input" | "output" | "error" | "system"; text: string }>
  >([]);
  let term_cmd = $state("");
  let term_inputRef = $state<HTMLInputElement | undefined>();
  let term_outputEl = $state<HTMLDivElement | undefined>();
  let term_router: Awaited<ReturnType<typeof createHybridRouter>> | null = null;
  const term_ws = createTerminalWSStore();
  let unsubWS: (() => void) | null = null;
  let unsubState: (() => void) | null = null;

  // =====================
  // Grid Command Prompt (shared across all Grid submodes)
  // =====================
  let grid_cmd = $state("");
  let grid_inputRef = $state<HTMLInputElement | undefined>();
  let grid_cmdHistory = $state<string[]>([]);
  let grid_historyIndex = $state(-1);

  async function grid_execCmd() {
    const cmd = grid_cmd.trim();
    if (!cmd) return;

    // Add to history
    grid_cmdHistory = [...grid_cmdHistory, cmd];
    grid_historyIndex = -1;

    // Add command to grid output
    grid_lines = [
      ...grid_lines,
      { text: `▯ ${cmd}`, font: "body", color: "cyan" },
    ];

    // Clear input
    grid_cmd = "";

    // Route command to appropriate handler
    if (cmd.toUpperCase() === "HELP") {
      // Display help
      grid_lines = [
        ...grid_lines,
        { text: "Available Grid commands:", font: "heading", color: "yellow" },
        { text: "  HELP - Show this help", font: "body", color: "green" },
        {
          text: "  DEMO [boot|teletext|cols|news] - Load demo",
          font: "body",
          color: "green",
        },
        {
          text: "  REBOOT - Execute reboot script",
          font: "body",
          color: "green",
        },
        {
          text: "  STARTUP - Execute startup script",
          font: "body",
          color: "green",
        },
      ];
      return;
    }

    if (cmd.toUpperCase().startsWith("DEMO ")) {
      const demoName = cmd.substring(5).trim().toLowerCase();
      if (["boot", "teletext", "columns", "cols", "news"].includes(demoName)) {
        showingDemo = true;
        const actualName = demoName === "cols" ? "columns" : demoName;
        grid_lines = [];
        loadDemo(actualName);
      } else {
        grid_lines = [
          ...grid_lines,
          {
            text: "Unknown demo. Try: boot, teletext, cols, news",
            font: "body",
            color: "red",
          },
        ];
      }
      return;
    }

    // Try to route to terminal commands
    if (!term_router) {
      grid_lines = [
        ...grid_lines,
        { text: "API router unavailable", font: "body", color: "orange" },
      ];
      return;
    }
    const res = await term_router.executeCommand(cmd);
    if (res.success) {
      res.output?.forEach((line: string) => {
        grid_lines = [
          ...grid_lines,
          { text: line, font: "body", color: "green" },
        ];
      });
    } else {
      grid_lines = [
        ...grid_lines,
        {
          text: `Error: ${res.error || "Command failed"}`,
          font: "body",
          color: "red",
        },
      ];
    }
  }

  function grid_handleKeyDown(e: KeyboardEvent) {
    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (grid_historyIndex < grid_cmdHistory.length - 1) {
        grid_historyIndex++;
        grid_cmd =
          grid_cmdHistory[grid_cmdHistory.length - 1 - grid_historyIndex];
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (grid_historyIndex > 0) {
        grid_historyIndex--;
        grid_cmd =
          grid_cmdHistory[grid_cmdHistory.length - 1 - grid_historyIndex];
      } else if (grid_historyIndex === 0) {
        grid_historyIndex = -1;
        grid_cmd = "";
      }
    }
  }

  async function term_init() {
    try {
      term_router = await createHybridRouter();
    } catch (e) {
      // ignore
    }
    try {
      await term_ws.connect();
      unsubState = term_ws.state.subscribe(() => {});
      unsubWS = term_ws.messages.subscribe((msgs) => {
        const last = msgs[msgs.length - 1];
        if (last) term_handleWS(last);
      });
    } catch {}
  }
  function term_handleWS(msg: WSMessage) {
    if (msg.type === "output")
      term_output = [...term_output, { type: "output", text: msg.data }];
    if (msg.type === "error")
      term_output = [...term_output, { type: "error", text: msg.data }];
    term_scroll();
  }
  function term_scroll() {
    setTimeout(() => {
      if (term_outputEl) term_outputEl.scrollTop = term_outputEl.scrollHeight;
    }, 10);
  }
  async function term_exec() {
    const cmd = term_cmd.trim();
    if (!cmd) return;
    term_output = [...term_output, { type: "input", text: `▶ ${cmd}` }];
    term_cmd = "";

    // Handle special Grid mode commands
    if (cmd.toUpperCase() === "REBOOT") {
      term_output = [
        ...term_output,
        { type: "system", text: "System reboot sequence initiated..." },
      ];
      term_scroll();
      await loadAndExecuteReboot();
      return;
    }

    if (cmd.toUpperCase() === "STARTUP") {
      term_output = [
        ...term_output,
        { type: "system", text: "Loading startup sequence..." },
      ];
      term_scroll();
      await loadAndExecuteStartup();
      return;
    }

    if (/^[A-Z]+(\s|$)/.test(cmd)) {
      try {
        term_ws.sendCommand(cmd);
        return;
      } catch {}
    }
    if (!term_router) return;
    const res = await term_router.executeCommand(cmd);
    if (!res.success)
      term_output = [
        ...term_output,
        { type: "error", text: res.error || "Command failed" },
      ];
    else
      res.output.forEach(
        (line) =>
          (term_output = [...term_output, { type: "output", text: line }])
      );
    term_scroll();
  }
  onDestroy(() => {
    unsubWS?.();
    unsubState?.();
    term_ws.disconnect();
  });

  // React to mode changes (non-async effect)
  $effect(() => {
    if (!modeInitialized || !container) return;
    recalcDynamicGrid();
  });

  // React to cell size changes (zoom)
  $effect(() => {
    if (!modeInitialized || !container) return;
    const _cellSize = gridState.cellSize; // dependency tracking
    recalcDynamicGrid();
  });

  // Reload demo or content when dimensions change
  $effect(() => {
    if (!modeInitialized || dims.cols === 0 || dims.rows === 0) return;
    if (showingDemo) {
      // Reload current demo with new dimensions
      loadDemo(demoSequence[currentDemoIndex]);
    } else if (gridState.mode === "teledesk") {
      td_load(td_currentPage);
    }
  });

  function setMode(m: GridSubmode) {
    gridMode.setMode(m);
    if (m === "terminal") term_init();
  }

  function lineClass(type: string): string {
    switch (type) {
      case "input":
        return "text-udos-cyan";
      case "error":
        return "text-udos-danger";
      case "system":
        return "text-udos-grey";
      default:
        return "text-udos-grass";
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key.toLowerCase() === "m") {
      e.preventDefault();
      showModeMenu = !showModeMenu;
      return;
    }
    // Demo controls
    if (showingDemo) {
      if (e.key === " " || e.key === "ArrowRight") {
        e.preventDefault();
        nextDemo();
      } else if (e.key === "Escape") {
        e.preventDefault();
        exitDemo();
      }
    }
  }
</script>

<svelte:head>
  <title>Grid Display - uDOS</title>
</svelte:head>

<svelte:window on:keydown={handleKeyDown} />

<div
  role="application"
  aria-label="Grid workspace"
  class="grid-app"
  bind:this={appContainer}
>
  <!-- Viewport container that centers content when border is ON -->
  <div
    class="viewport"
    bind:this={container}
    class:border-on={gridState.viewportBorder}
  >
    <div class="viewport-wrapper">
      <GridDisplay
        preset="teledesk"
        cols={dims.cols}
        rows={dims.rows}
        cellSize={gridState.cellSize}
        showGlow={false}
        showScanlines={false}
        showCurvature={false}
        className="grid-surface"
      >
        <!-- Grid Viewport (unified display for all modes) -->
        {#each grid_lines as line}
          <div
            class="udos-grid-line"
            class:font-title={typeof line === 'object' && line.font === "title"}
            class:font-heading={typeof line === 'object' && line.font === "heading"}
            class:color-cyan={typeof line === 'object' && line.color === "cyan"}
            class:color-orange={typeof line === 'object' && line.color === "orange"}
            class:color-yellow={typeof line === 'object' && line.color === "yellow"}
            class:color-red={typeof line === 'object' && line.color === "red"}
            class:color-white={typeof line === 'object' && line.color === "white"}
          >
            {typeof line === "string"
              ? line.padEnd(dims.cols, " ")
              : line.text.padEnd(dims.cols, " ")}
          </div>
        {/each}
      </GridDisplay>

      <!-- Grid Command Prompt (always visible at bottom) -->
      <div class="grid-prompt">
        <span class="prompt-icon">❯</span>
        <input
          class="grid-cmd-input"
          type="text"
          placeholder="Grid command (HELP for options)"
          bind:this={grid_inputRef}
          bind:value={grid_cmd}
          onkeydown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              grid_execCmd();
            } else {
              grid_handleKeyDown(e);
            }
          }}
        />
      </div>
      {#if showModeMenu}
        <div class="mode-menu">
          <div class="udos-grid-line text-udos-cyan">
            ╔ MODE MENU ═══════════════════════════╗
          </div>
          <div class="udos-grid-line text-udos-white">
            <button class="mode-btn" onpointerdown={() => goto("/teledesk")}
              >TELEDESK</button
            >
          </div>
          <div class="udos-grid-line text-udos-white">
            <button class="mode-btn" onpointerdown={() => goto("/terminal")}
              >TERMINAL</button
            >
          </div>
          <div class="udos-grid-line text-udos-cyan">
            ╚ Press M to close ════════════════════╝
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .grid-app {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100vw;
    position: fixed;
    top: 0;
    left: 0;
    background: #0b0b0b;
    overflow: hidden;
  }

  /* ==================== VIEWPORT ==================== */

  .viewport {
    flex: 1;
    position: relative;
    min-height: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: auto;
    width: 100%;
    background-color: #1a1a2e;
    gap: 0;
    padding: 40px;
  }

  .viewport-wrapper {
    display: flex;
    flex-direction: column;
    gap: 12px;
    width: fit-content;
    height: fit-content;
    max-height: 100%;
    align-items: center;
  }

  .mode-menu {
    position: fixed;
    top: 12px;
    left: 12px;
    z-index: 10;
    background: #0a0a0a;
    border: 1px solid #0ff3;
    padding: 8px 12px;
    box-shadow: 0 0 24px #0ff2;
  }

  .mode-btn {
    all: unset;
    cursor: pointer;
    padding: 2px 6px;
    background: #111;
    border: 1px solid #8884;
    color: #fafafa;
    margin: 2px 0;
  }

  /* Grid Command Prompt */
  .grid-prompt {
    display: flex;
    gap: 8px;
    align-items: center;
    padding: 10px 16px;
    background: #000;
    border: 2px solid #06ffa5;
    border-radius: 4px;
    font-family: var(--font-family-mono);
    font-size: 14px;
    color: #06ffa5;
    width: 100%;
    box-shadow: 0 0 10px rgba(6, 255, 165, 0.3);
  }

  .prompt-icon {
    color: #06ffa5;
    font-weight: bold;
    font-size: 16px;
  }

  .grid-cmd-input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: #00d9ff;
    font-family: var(--font-family-mono);
    font-size: 14px;
    caret-color: #00d9ff;
  }

  .grid-cmd-input::placeholder {
    color: #4a4a6e;
    font-size: 12px;
  }

  .grid-cmd-input:focus {
    outline: none;
  }

  /* Font variants for grid lines */
  .udos-grid-line.font-title {
    font-family: var(--font-family-c64);
    font-size: calc(var(--cell-size) * 2);
    height: calc(var(--cell-size) * 2);
    line-height: calc(var(--cell-size) * 2);
  }

  .udos-grid-line.font-heading {
    font-family: var(--font-family-pressstart);
    font-size: var(--cell-size);
  }

  /* Color variants */
  .udos-grid-line.color-cyan {
    color: #00d9ff;
  }

  .udos-grid-line.color-orange {
    color: #fb5607;
  }

  .udos-grid-line.color-yellow {
    color: #ffbe0b;
  }

  .udos-grid-line.color-red {
    color: #ff006e;
  }

  .udos-grid-line.color-white {
    color: #ffffff;
  }
</style>
