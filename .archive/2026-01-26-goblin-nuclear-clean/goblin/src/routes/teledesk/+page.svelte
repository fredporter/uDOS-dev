<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { listen } from "@tauri-apps/api/event";
  import GridDisplay from "$lib/components/GridDisplay.svelte";
  import {
    getPage,
    getNotFoundPage,
    formatContent,
    PAGE_RANGES,
    type TeletextPage,
  } from "$lib/stores/teledesk";
  import { isApiAvailable } from "$lib/stores/api";
  import { fitGridToContainer } from "$lib/util/gridSystem";
  import { setMonoVariant } from "$lib/services/styleManager";

  // Responsive grid - fills actual viewport
  let container: HTMLDivElement;
  let dims = $state({ cols: 80, rows: 30 });
  let currentPage = $state(100);
  let pageInput = $state("");
  let displayLines = $state<
    Array<
      | string
      | {
          text: string;
          font?: "title" | "heading" | "heading-double" | "alt-heading" | "body";
          color?: string;
        }
    >
  >([]);
  let pageTitle = $state("INDEX");
  let pageCategory = $state("index");
  let isLoading = $state(false);
  let flashPage = $state(false);
  let apiConnected = $state(false);
  let pageLinks = $state<Array<{ page: number; label: string }>>([]);
  let unsubscribeReset: (() => void) | null = null;
  let promptValue = $state("");
  let showModeMenu = $state(false);

  // Font state - controlled via commands, not UI
  let monoVariant = $state<"teletext" | "c64" | "pressstart">("teletext");
  let cellSize = $state(24);

  // Teletext color palette - using UDOS palette
  const categoryColors: Record<string, string> = {
    index: "text-udos-cyan",
    guide: "text-udos-grass",
    survival: "text-udos-waypoint",
    reference: "text-udos-magenta",
    error: "text-udos-danger",
    knowledge: "text-udos-safe",
    technical: "text-udos-water",
    medical: "text-udos-alert",
  };

  function recalcDynamicGrid() {
    if (container) {
      const rect = container.getBoundingClientRect();
      // Account for prompt bar height (3 lines × 24px + padding)
      const availableHeight = rect.height - 100;
      const fit = fitGridToContainer(rect.width, availableHeight, cellSize);
      dims = { cols: Math.max(40, fit.cols), rows: Math.max(15, fit.rows - 3) };
      // Reload page with new dimensions
      loadPage(currentPage);
    }
  }

  let resizeObserver: ResizeObserver | null = null;
  onMount(async () => {
    // Set default font
    setMonoVariant("teletext", true);

    // Check API status
    apiConnected = await isApiAvailable();

    // Listen for reset-mode-display
    try {
      unsubscribeReset = await listen("reset-mode-display", async () => {
        await loadPage(100);
        pageInput = "";
      });
    } catch (error) {
      console.error("[Teledesk] Failed to register reset listener:", error);
    }

    // Setup resize observer for responsive grid
    recalcDynamicGrid();
    resizeObserver = new ResizeObserver(() => recalcDynamicGrid());
    if (container) resizeObserver.observe(container);

    // Load initial page
    const urlPage = $page.url.searchParams.get("p");
    if (urlPage) {
      const num = parseInt(urlPage);
      if (num >= 100 && num <= 999) {
        await loadPage(num);
      } else {
        await loadPage(100);
      }
    } else {
      await loadPage(100);
    }
  });

  onDestroy(() => {
    if (unsubscribeReset) {
      unsubscribeReset();
    }
    resizeObserver?.disconnect();
  });

  async function loadPage(pageNum: number) {
    if (pageNum < 100 || pageNum > 999) return;

    isLoading = true;
    flashPage = true;

    await new Promise((resolve) => setTimeout(resolve, 50));

    let pageData = await getPage(pageNum);
    if (!pageData) {
      pageData = getNotFoundPage(pageNum);
    }

    currentPage = pageNum;
    pageTitle = pageData.title;
    pageCategory = pageData.category;
    pageLinks = pageData.links;
    displayLines = formatContent(
      pageData.content,
      dims.cols,
      Math.max(1, dims.rows - 3)
    );

    isLoading = false;
    setTimeout(() => (flashPage = false), 100);

    goto(`/teledesk?p=${pageNum}`, { replaceState: true, noScroll: true });
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key.toLowerCase() === "m") {
      e.preventDefault();
      showModeMenu = !showModeMenu;
      return;
    }
    if (/^[0-9]$/.test(e.key)) {
      pageInput += e.key;
      if (pageInput.length === 3) {
        const num = parseInt(pageInput);
        pageInput = "";
        loadPage(num);
      }
      return;
    }

    switch (e.key) {
      case "ArrowLeft":
        e.preventDefault();
        loadPage(currentPage - 1);
        break;
      case "ArrowRight":
        e.preventDefault();
        loadPage(currentPage + 1);
        break;
      case "Home":
        e.preventDefault();
        loadPage(100);
        break;
      case "Escape":
        e.preventDefault();
        goto("/terminal");
        break;
      case "Backspace":
        e.preventDefault();
        pageInput = pageInput.slice(0, -1);
        break;
    }
  }

  function handlePromptKeydown(e: KeyboardEvent) {
    if (e.key !== "Enter") return;
    const value = promptValue.trim().toUpperCase();
    if (/^\d{3}$/.test(value)) {
      loadPage(parseInt(value));
      promptValue = "";
      return;
    }
    switch (value) {
      case "HELP":
      case "INDEX":
        loadPage(100);
        promptValue = "";
        return;
      case "TERMINAL":
        goto("/terminal");
        promptValue = "";
        return;
      case "TELEDESK":
        goto("/teledesk");
        promptValue = "";
        return;
      default:
        // Unknown command: briefly flash page to indicate invalid input
        flashPage = true;
        setTimeout(() => (flashPage = false), 150);
    }
  }

  function getLineColor(
    line:
      | string
      | {
          text: string;
          font?: "title" | "heading" | "heading-double" | "alt-heading" | "body";
          color?: string;
        }
  ): string {
    // Extract text content
    const text = typeof line === "string" ? line : line.text;

    // If line is an object with explicit color, use that
    if (typeof line === "object" && line.color) {
      return line.color;
    }

    // Block graphics and borders - Cyan
    if (
      text.includes("═") ||
      text.includes("╔") ||
      text.includes("╚") ||
      text.includes("║") ||
      text.includes("╠") ||
      text.includes("╣")
    )
      return "text-udos-cyan";

    // Shaded blocks and boxes - Magenta/Purple
    if (
      text.includes("▄") ||
      text.includes("▀") ||
      text.includes("█") ||
      text.includes("▓") ||
      text.includes("▒")
    )
      return "text-udos-magenta";

    // Page references - Yellow
    if (/\d{3}\s*\.\.\./.test(text) || /█ \d{3} █/.test(text))
      return "text-udos-waypoint";

    // Navigation arrows - White
    if (text.includes("←") || text.includes("→")) return "text-udos-white";

    // Dividers - Grey
    if (text.includes("─────") || text.includes("───────"))
      return "text-udos-grey";

    // STATUS indicator - Green for online
    if (text.includes("ONLINE")) return "text-udos-safe";

    // TYPE/INPUT prompt - Yellow
    if (text.includes("Type PAGE NUMBER") || text.includes("Type page number"))
      return "text-udos-waypoint";

    // Default body text based on category
    return categoryColors[pageCategory] || "text-udos-grass";
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<svelte:head>
  <title>Teledesk P{currentPage} - Markdown</title>
</svelte:head>

<div class="teledesk-app">
  <!-- Viewport container - fills entire screen, no borders/padding -->
  <div class="viewport" bind:this={container}>
    <GridDisplay
      preset="teledesk"
      cols={dims.cols}
      rows={dims.rows}
      {cellSize}
      glowColor="cyan"
      showScanlines={true}
      showCurvature={true}
      className="grid-surface"
    >
      <!-- Content lines (includes header from page data) -->
      {#each displayLines as line}
        <div
          class="udos-grid-line {getLineColor(line)} {typeof line === 'object'
            ? 'font-' + (line.font || 'body')
            : 'font-body'} transition-opacity duration-100 {flashPage
            ? 'opacity-50'
            : 'opacity-100'}"
        >
          {typeof line === "object"
            ? line.text.padEnd(dims.cols, " ")
            : line.padEnd(dims.cols, " ")}
        </div>
      {/each}
    </GridDisplay>
  </div>
  <!-- Full-width Terminal-style prompt bar at bottom -->
  <div class="prompt-bar">
    <div class="udos-grid-line font-heading text-udos-waypoint">
      ▶ PAGE (000–999): {pageInput.padEnd(3, "_")} · ← → browse · HOME index · ESC
      exit · STATUS: {apiConnected ? "ONLINE" : "OFFLINE"}
    </div>
    <div class="udos-grid-line font-body text-udos-white prompt-input-row">
      ▒ INPUT: <input
        class="prompt-input"
        bind:value={promptValue}
        onkeydown={handlePromptKeydown}
        placeholder="100 · HELP · GRID · TERMINAL"
      />
    </div>
  </div>
  {#if showModeMenu}
    <div class="mode-menu">
      <div class="udos-grid-line font-body text-udos-cyan">
        ╔ MODE MENU ═══════════════════════════╗
      </div>
      <div class="udos-grid-line font-body text-udos-white">
        <button class="mode-btn" onpointerdown={() => goto("/teledesk")}
          >TELEDESK</button
        >
      </div>
      <div class="udos-grid-line font-body text-udos-white">
        <button class="mode-btn" onpointerdown={() => goto("/terminal")}
          >TERMINAL</button
        >
      </div>
      <div class="udos-grid-line font-body text-udos-cyan">
        ╚ Press M to close ════════════════════╝
      </div>
    </div>
  {/if}
</div>

<style>
  .teledesk-app {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    width: 100%;
    position: relative;
    background: #0b0b0b;
  }

  .viewport {
    flex: 1;
    position: relative;
    min-height: 0;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    overflow-y: auto;
    overflow-x: visible;
    width: 100%;
    padding: 16px 0;
  }

  .grid-surface {
    box-shadow:
      0 0 0 2px #003c40,
      0 0 40px #00d9ff22 inset;
  }

  .header {
    display: contents;
  }

  .status {
    display: contents;
  }

  .prompt-bar {
    position: sticky;
    bottom: 0;
    left: 0;
    right: 0;
    background: #0a0a0a;
    border-top: 1px solid #0ff3;
    padding: 6px 12px;
  }

  .prompt-input-row {
    display: flex;
    gap: 8px;
  }

  .prompt-input {
    all: unset;
    display: inline-block;
    min-width: 320px;
    padding: 2px 6px;
    background: #111;
    border: 1px solid #0ff3;
    color: #f0f0f0;
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

  /* Font styles moved to global stylesheet (app.css) for proper specificity */

  /* Color classes using uDOS 2.0 palette */
  .udos-grid-line.text-udos-grass {
    color: var(--color-udos-grass);
  }

  .udos-grid-line.text-udos-cyan {
    color: var(--color-udos-cyan);
  }

  .udos-grid-line.text-udos-alert {
    color: var(--color-udos-alert);
  }

  .udos-grid-line.text-udos-waypoint {
    color: var(--color-udos-waypoint);
  }

  .udos-grid-line.text-udos-danger {
    color: var(--color-udos-danger);
  }

  .udos-grid-line.text-udos-white {
    color: var(--color-udos-white);
  }

  .udos-grid-line.text-udos-magenta {
    color: var(--color-udos-magenta);
  }

  .udos-grid-line.text-udos-forest {
    color: var(--color-udos-forest);
  }

  .udos-grid-line.text-udos-deep-water {
    color: var(--color-udos-deep-water);
  }

  .udos-grid-line.text-udos-water {
    color: var(--color-udos-water);
  }

  .udos-grid-line.text-udos-safe {
    color: var(--color-udos-safe);
  }

  .udos-grid-line.text-udos-earth {
    color: var(--color-udos-earth);
  }

  .udos-grid-line.text-udos-sand {
    color: var(--color-udos-sand);
  }

  .udos-grid-line.text-udos-mountain {
    color: var(--color-udos-mountain);
  }

  .udos-grid-line.text-udos-snow {
    color: var(--color-udos-snow);
  }

  .udos-grid-line.text-udos-purple {
    color: var(--color-udos-purple);
  }

  .udos-grid-line.text-udos-pink {
    color: var(--color-udos-pink);
  }

  .udos-grid-line.text-udos-grey {
    color: var(--color-udos-grey);
  }

  .udos-grid-line.text-udos-dark-grey {
    color: var(--color-udos-dark-grey);
  }

  .udos-grid-line.text-udos-light-grey {
    color: var(--color-udos-light-grey);
  }

  .udos-grid-line.text-udos-off-white {
    color: var(--color-udos-off-white);
  }
</style>
