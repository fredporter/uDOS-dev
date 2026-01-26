<script lang="ts">
  /**
   * GlobalBottomBar - Persistent bottom toolbar
   * Uses centralized styleManager for consistent styling
   */

  import { page } from "$app/stores";
  import { emit, listen, type UnlistenFn } from "@tauri-apps/api/event";
  import { onMount, onDestroy } from "svelte";
  import { setLastFile } from "$lib/stores/modeState";
  import {
    initStyleManager,
    getStyleState,
    cycleHeadingFont,
    cycleBodyFont,
    zoomIn as styleZoomIn,
    zoomOut as styleZoomOut,
    getFontName,
  } from "$lib/services/styleManager";
  import { getColorById } from "$lib/util/udosPalette";
   import { get } from "svelte/store";
   import { gridMode, type GridModeState } from "$lib/stores/gridMode";
  import "$lib/styles/desktop-patterns.css";

  interface Props {
    currentFile?: string | null;
    isEditing?: boolean;
    darkMode?: boolean;
    sidebarOpen?: boolean;
    menuBarVisible?: boolean;
    utilitySidebarOpen?: boolean;
    charCount?: number;
    wordCount?: number;
    readTime?: number;
    viewType?: string; // "document" or "slideshow" in read mode
    tickerMode?: "sentence" | "caps" | "hide";
    feedPosition?: "top" | "bottom";
    onToggleSidebar?: () => void;
    onToggleEdit?: () => void;
    onToggleDarkMode?: () => void;
    onToggleMenuBar?: () => void;
    onToggleUtilitySidebar?: () => void;
    onCycleTicker?: () => void;
  }

  let {
    currentFile = null,
    isEditing = false,
    darkMode = false,
    sidebarOpen = false,
    menuBarVisible = true,
    utilitySidebarOpen = false,
    charCount = 0,
    wordCount = 0,
    readTime = 0,
    viewType = "document",
    tickerMode = "hide",
    feedPosition = "top",
    onToggleSidebar = () => {},
    onToggleEdit = () => {},
    onToggleDarkMode = () => {},
    onToggleMenuBar = () => {},
    onToggleUtilitySidebar = () => {},
    onCycleTicker = () => {},
  }: Props = $props();

  // Style state from centralized manager
  let styleState = $state(getStyleState());
   let gridState = $state<GridModeState>(get(gridMode));
  let backgroundPattern = $state("pattern-solid-white");
  let unlisteners: UnlistenFn[] = [];

  // Code editor background color cycling
  const editorBgColorsDark = [16, 17, 18, 31]; // Black, Dark Grey, Charcoal, Deep Sea
  const editorBgColorsLight = [23, 22, 21, 29]; // White, Off White, Light Grey, Ice Blue
  let editorBgColorIndex = $state(0);
  let editorBgHex = $state("#000000");

  // Desktop patterns - Classic Mac patterns + Tailwind color backgrounds
  const patterns = [
    // Classic patterns
    { id: "solid-white", name: "White" },
    { id: "solid-gray", name: "Gray" },
    { id: "checkerboard", name: "Check" },
    { id: "dots", name: "Dots" },
    { id: "dense-dots", name: "Dense" },
    { id: "lines-h", name: "Horiz" },
    { id: "lines-v", name: "Vert" },
    { id: "diagonal", name: "Diag" },
    { id: "grid", name: "Grid" },
    { id: "crosshatch", name: "Cross" },
    { id: "brick", name: "Brick" },
    { id: "weave", name: "Weave" },
    { id: "diamond", name: "Diamond" },
    { id: "scales", name: "Scales" },
    { id: "tiles", name: "Tiles" },
    // Tailwind Gray Scale (for code editor backgrounds)
    { id: "bg-gray-50", name: "Gray-50" },
    { id: "bg-gray-100", name: "Gray-100" },
    { id: "bg-gray-200", name: "Gray-200" },
    { id: "bg-gray-700", name: "Gray-700" },
    { id: "bg-gray-800", name: "Gray-800" },
    { id: "bg-gray-900", name: "Gray-900" },
    { id: "bg-slate-50", name: "Slate-50" },
    { id: "bg-slate-100", name: "Slate-100" },
    { id: "bg-slate-800", name: "Slate-800" },
    { id: "bg-slate-900", name: "Slate-900" },
  ];

  // Current mode from URL
  let currentMode = $derived($page.url.pathname.split("/")[1] || "desktop");

  onMount(async () => {
    initStyleManager();
    styleState = getStyleState();

     unlisteners.push(gridMode.subscribe((state) => (gridState = state)));

    const saved = localStorage.getItem("bottombar-background-pattern");
    if (saved) backgroundPattern = saved;

    // Restore editor background color
    const savedColorIndex = localStorage.getItem("editor-bg-color-index");
    if (savedColorIndex) editorBgColorIndex = parseInt(savedColorIndex, 10);
    updateEditorBgColor();

    unlisteners.push(await listen("bottombar-zoom-in", handleZoomIn));
    unlisteners.push(await listen("bottombar-zoom-out", handleZoomOut));

    const handleStyleChange = () => {
      styleState = getStyleState();
      updateEditorBgColor(); // Update hex when dark mode changes
    };
    window.addEventListener("udos-style-changed", handleStyleChange);
    unlisteners.push(() =>
      window.removeEventListener("udos-style-changed", handleStyleChange)
    );
  });

  onDestroy(() => {
    unlisteners.forEach((fn) => fn());
  });

  $effect(() => {
    if (currentFile) {
      setLastFile(currentFile);
    }
  });

  function handleZoomIn() {
    styleZoomIn();
    styleState = getStyleState();
  }

  function handleZoomOut() {
    styleZoomOut();
    styleState = getStyleState();
  }

  function handleToggleHeadingFont() {
    cycleHeadingFont();
    styleState = getStyleState();
  }

  function handleToggleBodyFont() {
    cycleBodyFont();
    styleState = getStyleState();
  }

  function handleToggleMonoFont() {
    // Mono font toggling removed; JetBrains Mono is the fixed code font
  }

  function cycleDesktopPattern() {
    if (currentMode !== "desktop") return;
    const currentIndex = patterns.findIndex(
      (p) => `pattern-${p.id}` === backgroundPattern
    );
    const nextIndex = (currentIndex + 1) % patterns.length;
    backgroundPattern = `pattern-${patterns[nextIndex].id}`;
    localStorage.setItem("bottombar-background-pattern", backgroundPattern);
    emit("background-pattern-changed", { pattern: backgroundPattern });
  }

  async function toggleViewType() {
    await emit("toggle-view-type", {});
  }

  function updateEditorBgColor() {
    const colorIds = darkMode ? editorBgColorsDark : editorBgColorsLight;
    const colorId = colorIds[editorBgColorIndex % colorIds.length];
     const color = getColorById(colorId);
     if (!color) return;
     editorBgHex = color.hex;
  }

  async function changeCodeColor() {
    // Cycle to next color
    editorBgColorIndex = (editorBgColorIndex + 1) % 4;
    localStorage.setItem(
      "editor-bg-color-index",
      editorBgColorIndex.toString()
    );
    updateEditorBgColor();

    // Emit color change event with hex value
    await emit("change-color", { hex: editorBgHex });
  }

  async function toggleFullscreen() {
    try {
      const { getCurrentWindow } = await import("@tauri-apps/api/window");
      const appWindow = getCurrentWindow();
      const isFullscreen = await appWindow.isFullscreen();
      await appWindow.setFullscreen(!isFullscreen);
    } catch (error) {
      console.error("Failed to toggle fullscreen:", error);
    }
  }

  let fileName = $derived(currentFile?.split("/").pop() || "No file");
  let headingFontName = $derived(getFontName(styleState.headingFont));
  let bodyFontName = $derived(getFontName(styleState.bodyFont));
  // Mono variant name no longer needed; JetBrains Mono is the default
</script>

<div class="bottom-bar">
  <div class="flex items-center gap-2">
    <!-- Toggle File Picker -->
    <button
      class="btn {sidebarOpen ? 'active' : ''}"
      title="Toggle file picker (⌘B)"
      onclick={onToggleSidebar}
    >
      {#if sidebarOpen}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="w-5 h-5"
        >
          <path
            d="M3.75 3A1.75 1.75 0 002 4.75v2.752l.104-.002h13.792c.035 0 .07 0 .104.002V6.75A1.75 1.75 0 0014.25 5h-3.836a.25.25 0 01-.177-.073L8.823 3.513A1.75 1.75 0 007.586 3H3.75zM2.104 9a1.75 1.75 0 00-1.673 2.265l1.385 4.5A1.75 1.75 0 003.488 17h11.023a1.75 1.75 0 001.673-1.235l1.384-4.5A1.75 1.75 0 0015.896 9H2.104z"
          />
        </svg>
      {:else}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="w-5 h-5"
        >
          <path
            d="M3.75 3A1.75 1.75 0 002 4.75v2.752l.104-.002h13.792c.035 0 .07 0 .104.002V6.75A1.75 1.75 0 0014.25 5h-3.836a.25.25 0 01-.177-.073L8.823 3.513A1.75 1.75 0 007.586 3H3.75zM2.104 9a1.75 1.75 0 00-1.673 2.265l1.385 4.5A1.75 1.75 0 003.488 17h11.023a1.75 1.75 0 001.673-1.235l1.384-4.5A1.75 1.75 0 0015.896 9H2.104z"
          />
        </svg>
      {/if}
    </button>

    <!-- Toggle Edit/View Mode (position 2) -->
    <button
      class="btn"
      title={isEditing ? "View" : "Edit"}
      onclick={onToggleEdit}
    >
      {#if isEditing}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="w-5 h-5"
        >
          <path
            d="M2.695 14.763l-1.262 3.154a.5.5 0 00.65.65l3.155-1.262a4 4 0 001.343-.885L17.5 5.5a2.121 2.121 0 00-3-3L3.58 13.42a4 4 0 00-.885 1.343z"
          />
        </svg>
      {:else}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="w-5 h-5"
        >
          <path d="M10 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z" />
          <path
            fill-rule="evenodd"
            d="M.664 10.59a1.651 1.651 0 010-1.186A10.004 10.004 0 0110 3c4.257 0 7.893 2.66 9.336 6.41.147.381.146.804 0 1.186A10.004 10.004 0 0110 17c-4.257 0-7.893-2.66-9.336-6.41zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
            clip-rule="evenodd"
          />
        </svg>
      {/if}
    </button>

    <!-- Ticker Toggle: 3-state cycle (on-top → on-bottom → off) -->
    <button
      class="btn {tickerMode !== 'hide' ? 'active' : ''}"
      title={tickerMode === "hide"
        ? "Ticker: Off"
        : `Ticker: ${feedPosition === "top" ? "Top" : "Bottom"}`}
      onclick={onCycleTicker}
    >
      <!-- RSS icon -->
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        class="w-5 h-5"
        style="opacity: {tickerMode === 'hide' ? '0.4' : '1'}"
      >
        <path
          d="M3.75 3a.75.75 0 00-.75.75v.5c0 .414.336.75.75.75H4c6.075 0 11 4.925 11 11v.25c0 .414.336.75.75.75h.5a.75.75 0 00.75-.75V16C17 8.82 11.18 3 4 3h-.25z"
        />
        <path
          d="M3 8.75A.75.75 0 013.75 8H4a8 8 0 018 8v.25a.75.75 0 01-.75.75h-.5a.75.75 0 01-.75-.75V16a6 6 0 00-6-6h-.25A.75.75 0 013 9.25v-.5z"
        />
        <circle cx="4.5" cy="15.5" r="1.5" />
      </svg>
    </button>

    <!-- Toggle Copy Buffer -->
    <button
      class="btn"
      title="Copy buffer"
      onclick={() => emit("toggle-copy-buffer", {})}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        class="w-5 h-5"
      >
        <path
          d="M7 3.5A1.5 1.5 0 018.5 2h3.879a1.5 1.5 0 011.06.44l3.122 3.12A1.5 1.5 0 0117 6.622V12.5a1.5 1.5 0 01-1.5 1.5h-1v-3.379a3 3 0 00-.879-2.121L10.5 5.379A3 3 0 008.379 4.5H7v-1z"
        />
        <path
          d="M4.5 6A1.5 1.5 0 003 7.5v9A1.5 1.5 0 004.5 18h7a1.5 1.5 0 001.5-1.5v-5.879a1.5 1.5 0 00-.44-1.06L9.44 6.439A1.5 1.5 0 008.378 6H4.5z"
        />
      </svg>
    </button>

    <!-- Toggle Menu Bar -->
    <button
      class="btn {menuBarVisible ? 'active' : ''}"
      title="Toggle menu bar"
      onclick={onToggleMenuBar}
    >
      {#if menuBarVisible}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="w-5 h-5"
        >
          <path
            fill-rule="evenodd"
            d="M2 4.75A.75.75 0 012.75 4h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 4.75zm0 10.5a.75.75 0 01.75-.75h7.5a.75.75 0 010 1.5h-7.5a.75.75 0 01-.75-.75zM2 10a.75.75 0 01.75-.75h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 10z"
            clip-rule="evenodd"
          />
        </svg>
      {:else}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="w-5 h-5"
        >
          <path
            fill-rule="evenodd"
            d="M2 4.75A.75.75 0 012.75 4h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 4.75zM2 10a.75.75 0 01.75-.75h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 10zm0 5.25a.75.75 0 01.75-.75h14.5a.75.75 0 010 1.5H2.75a.75.75 0 01-.75-.75z"
            clip-rule="evenodd"
          />
        </svg>
      {/if}
    </button>

    <!-- Toggle Utility Sidebar -->
    <button
      class="btn {utilitySidebarOpen ? 'active' : ''}"
      title="Toggle utility sidebar (Keypad, Keyboard, F-Keys)"
      onclick={onToggleUtilitySidebar}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        class="w-5 h-5"
      >
        <path
          d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM13 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2h-2z"
        />
      </svg>
    </button>

    <button class="btn" title="Toggle slideshow" onclick={toggleViewType}>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        class="w-5 h-5"
      >
        <path
          d="M5.127 3.502L5.25 3.5h9.5c.041 0 .082 0 .123.002A2.251 2.251 0 0012.75 2h-5.5a2.25 2.25 0 00-2.123 1.502zM1 10.25A2.25 2.25 0 013.25 8h13.5A2.25 2.25 0 0119 10.25v5.5A2.25 2.25 0 0116.75 18H3.25A2.25 2.25 0 011 15.75v-5.5zM3.25 6.5c-.04 0-.082 0-.123.002A2.25 2.25 0 015.25 5h9.5c.98 0 1.814.627 2.123 1.502a3.819 3.819 0 00-.123-.002H3.25z"
        />
      </svg>
    </button>

    <div class="stats">
      <span>{charCount.toLocaleString()} char</span>
      <span>{wordCount.toLocaleString()} word</span>
      <span>{readTime} min</span>
    </div>

    {#if currentFile}
      <div class="filename" title={currentFile}>{fileName}</div>
    {/if}
  </div>

  <div class="flex items-center gap-1">
    {#if currentMode === "desktop"}
      <button class="btn" title="Desktop pattern" onclick={cycleDesktopPattern}>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="w-5 h-5"
        >
          <path
            fill-rule="evenodd"
            d="M4.25 2A2.25 2.25 0 002 4.25v2.5A2.25 2.25 0 004.25 9h2.5A2.25 2.25 0 009 6.75v-2.5A2.25 2.25 0 006.75 2h-2.5zM4.25 11A2.25 2.25 0 002 13.25v2.5A2.25 2.25 0 004.25 18h2.5A2.25 2.25 0 009 15.75v-2.5A2.25 2.25 0 006.75 11h-2.5zm7-9A2.25 2.25 0 009 4.25v2.5A2.25 2.25 0 0011.25 9h4.5A2.25 2.25 0 0018 6.75v-2.5A2.25 2.25 0 0015.75 2h-4.5zm0 9A2.25 2.25 0 009 13.25v2.5A2.25 2.25 0 0011.25 18h4.5A2.25 2.25 0 0018 15.75v-2.5A2.25 2.25 0 0015.75 11h-4.5z"
            clip-rule="evenodd"
          />
        </svg>
      </button>
    {/if}

    <!-- Slides / Presentation Mode -->
    {#if currentMode === "markdown"}
      <button
        class="btn {viewType === 'slideshow'
          ? 'bg-blue-500/20 border-blue-500'
          : ''}"
        title="Toggle slideshow pagination"
        onclick={async () => {
          // Toggle view type in editor
          await emit("toggle-view-type", {});
        }}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="w-5 h-5"
        >
          <path
            d="M3 3.5A1.5 1.5 0 014.5 2h11A1.5 1.5 0 0117 3.5V12a1.5 1.5 0 01-1.5 1.5h-11A1.5 1.5 0 013 12V3.5zM4.5 3a.5.5 0 00-.5.5V12a.5.5 0 00.5.5h11a.5.5 0 00.5-.5V3.5a.5.5 0 00-.5-.5h-11zM9 15.5v2a.5.5 0 001 0v-2h-.5a.5.5 0 01-.5 0zm-4 0a.5.5 0 011 0V18h8v-2.5a.5.5 0 011 0V18.5a.5.5 0 01-.5.5h-9a.5.5 0 01-.5-.5v-3z"
          />
        </svg>
      </button>
    {/if}

    <button
      class="btn code-color-btn"
      title="Code editor background color (cycle)"
      onclick={changeCodeColor}
      style="border: 2px solid {editorBgHex}; box-sizing: border-box;"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        class="w-5 h-5"
      >
        <path
          fill-rule="evenodd"
          d="M4.25 2A2.25 2.25 0 002 4.25v11.5A2.25 2.25 0 004.25 18h11.5A2.25 2.25 0 0018 15.75V4.25A2.25 2.25 0 0015.75 2H4.25zm4.03 6.28a.75.75 0 00-1.06-1.06L4.97 9.47a.75.75 0 000 1.06l2.25 2.25a.75.75 0 001.06-1.06L6.56 10l1.72-1.72zm4.5-1.06a.75.75 0 10-1.06 1.06L13.44 10l-1.72 1.72a.75.75 0 101.06 1.06l2.25-2.25a.75.75 0 000-1.06l-2.25-2.25z"
          clip-rule="evenodd"
        />
      </svg>
    </button>

    <button
      class="btn font-bold"
      title="Heading & Menu: {headingFontName}"
      onclick={handleToggleHeadingFont}>H</button
    >
    <button
      class="btn"
      title="Body: {bodyFontName}"
      onclick={handleToggleBodyFont}>B</button
    >
    <button
      class="btn"
      title={currentMode === "grid"
        ? `Zoom out (${gridState.cellSize}px)`
        : `Zoom out (${styleState.fontSize}px)`}
      onclick={handleZoomOut}>−</button
    >
    <button
      class="btn"
      title={currentMode === "grid"
        ? `Zoom in (${gridState.cellSize}px)`
        : `Zoom in (${styleState.fontSize}px)`}
      onclick={handleZoomIn}>+</button
    >

    <button class="btn" title="Fullscreen" onclick={toggleFullscreen}>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        class="w-5 h-5"
      >
        <path
          d="M3.28 2.22a.75.75 0 00-1.06 1.06L5.44 6.5H3.75a.75.75 0 000 1.5h3.5a.75.75 0 00.75-.75v-3.5a.75.75 0 00-1.5 0v1.69L3.28 2.22zM13.5 2.75a.75.75 0 01.75-.75h3.5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0V4.56l-3.22 3.22a.75.75 0 11-1.06-1.06l3.22-3.22h-1.69a.75.75 0 01-.75-.75zm3.75 11.5a.75.75 0 011.5 0v3.5a.75.75 0 01-.75.75h-3.5a.75.75 0 010-1.5h1.69l-3.22-3.22a.75.75 0 111.06-1.06l3.22 3.22v-1.69zM3.75 14.25a.75.75 0 000 1.5h1.69l-3.22 3.22a.75.75 0 101.06 1.06l3.22-3.22v1.69a.75.75 0 001.5 0v-3.5a.75.75 0 00-.75-.75h-3.5z"
        />
      </svg>
    </button>

    <button
      class="btn"
      title={darkMode ? "Light mode" : "Dark mode"}
      onclick={onToggleDarkMode}
    >
      {#if darkMode}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="w-5 h-5"
        >
          <path
            d="M10 2a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 2zM10 15a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 15zM10 7a3 3 0 100 6 3 3 0 000-6zM15.657 5.404a.75.75 0 10-1.06-1.06l-1.061 1.06a.75.75 0 001.06 1.06l1.06-1.06zM6.464 14.596a.75.75 0 10-1.06-1.06l-1.06 1.06a.75.75 0 001.06 1.06l1.06-1.06zM18 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 0118 10zM5 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 015 10zM14.596 15.657a.75.75 0 001.06-1.06l-1.06-1.061a.75.75 0 10-1.06 1.06l1.06 1.06zM5.404 6.464a.75.75 0 001.06-1.06l-1.06-1.06a.75.75 0 10-1.061 1.06l1.06 1.06z"
          />
        </svg>
      {:else}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          class="w-5 h-5"
        >
          <path
            fill-rule="evenodd"
            d="M7.455 2.004a.75.75 0 01.26.77 7 7 0 009.958 7.967.75.75 0 011.067.853A8.5 8.5 0 116.647 1.921a.75.75 0 01.808.083z"
            clip-rule="evenodd"
          />
        </svg>
      {/if}
    </button>
  </div>
</div>

<style>
  .bottom-bar {
    position: relative;
    z-index: 50;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem;
    border-top: 1px solid rgb(209, 213, 219);
    background-color: rgb(243, 244, 246);
    color: rgb(17, 24, 39);
    font-size: 0.875rem;
  }

  :global(.dark) .bottom-bar {
    border-color: rgb(55, 65, 81);
    background-color: rgba(17, 24, 39, 0.95);
    color: rgb(229, 231, 235);
  }

  .btn {
    padding: 0.375rem;
    border-radius: 0.375rem;
    transition: all 150ms;
    min-width: 2rem;
    min-height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    cursor: pointer;
    color: inherit;
  }

  .btn:hover {
    background-color: rgb(229, 231, 235);
    color: rgb(31, 41, 55);
  }

  :global(.dark) .btn:hover {
    background-color: rgb(55, 65, 81);
    color: rgb(229, 231, 235);
  }

  .btn.active {
    background-color: rgb(209, 213, 219);
  }

  :global(.dark) .btn.active {
    background-color: rgb(55, 65, 81);
  }

  .stats {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-left: 0.5rem;
    font-size: 0.75rem;
    color: rgb(75, 85, 99);
    font-variant-numeric: tabular-nums;
  }

  :global(.dark) .stats {
    color: rgb(156, 163, 175);
  }

  .filename {
    margin-left: 1rem;
    font-size: 0.75rem;
    color: rgb(75, 85, 99);
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  :global(.dark) .filename {
    color: rgb(156, 163, 175);
  }
</style>
