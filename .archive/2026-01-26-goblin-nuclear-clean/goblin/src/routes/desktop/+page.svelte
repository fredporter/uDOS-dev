<script lang="ts">
  import FileSidebar from "$lib/components/FileSidebar.svelte";
  import { onMount, onDestroy } from "svelte";
  import { navigateToMode } from "$lib/stores/modeState";
  import { invoke } from "@tauri-apps/api/core";
  import { openPath, openUrl } from "@tauri-apps/plugin-opener";
  import { listen, type UnlistenFn } from "@tauri-apps/api/event";
  import "$lib/styles/desktop-patterns.css";
  import {
    getLastFile,
    getStateForMode,
    updateModeState,
  } from "$lib/stores/modeState";
  import {
    getIconSvg,
    loadIconsFromCache,
    saveIconsToCache,
    CORE_DESKTOP_ICONS,
  } from "$lib/services/nounproject";
  import { setFontSize, getStyleState } from "$lib/services/styleManager";
  import { toastStore } from "$lib/stores/toastStore";

  // Types
  interface DesktopIcon {
    id: string;
    emoji: string;
    name: string;
    action: string;
    params?: string;
    nounIcon?: number; // Noun Project icon ID
    x: number;
    y: number;
  }

  interface Pattern {
    id: string;
    name: string;
    class: string;
  }

  // State
  let icons: DesktopIcon[] = $state([]);
  let currentTime = $state("");
  let selectedPattern = $state("pattern-solid-white");
  let sidebarOpen = $state(false);
  let darkMode = $state(false);
  let fontSize = $state(20);
  let unlisteners: UnlistenFn[] = [];
  let iconSvgs: Record<number, string> = $state({}); // Cache for loaded SVGs

  // Available patterns (Mac-style mono)
  const patterns: Pattern[] = [
    { id: "solid-black", name: "Black", class: "pattern-solid-black" },
    { id: "solid-white", name: "White", class: "pattern-solid-white" },
    { id: "solid-gray", name: "Gray", class: "pattern-solid-gray" },
    { id: "dots", name: "Dots", class: "pattern-dots" },
    { id: "dense-dots", name: "Dense", class: "pattern-dense-dots" },
    { id: "lines-h", name: "Horiz", class: "pattern-lines-h" },
    { id: "lines-v", name: "Vert", class: "pattern-lines-v" },
    { id: "diagonal", name: "Diag", class: "pattern-diagonal" },
    { id: "grid", name: "Grid", class: "pattern-grid" },
    { id: "crosshatch", name: "Cross", class: "pattern-crosshatch" },
    { id: "brick", name: "Brick", class: "pattern-brick" },
    { id: "diamond", name: "Diamond", class: "pattern-diamond" },
  ];

  onMount(async () => {
    // Load desktop state from modeState
    const desktopState = getStateForMode("desktop");

    // Load dark mode from state
    darkMode = desktopState.darkMode || false;
    if (darkMode) {
      document.documentElement.classList.add("dark");
    }

    // Load sidebar state from mode state (not global localStorage)
    sidebarOpen = desktopState.sidebarOpen ?? false;

    updateClock();
    setInterval(updateClock, 1000);
    await loadDesktopConfig();
    loadPreferences();

    // Helper to toggle sidebar and emit to layout
    const toggleSidebar = (open?: boolean) => {
      sidebarOpen = open !== undefined ? open : !sidebarOpen;
      // Save to mode state
      updateModeState("desktop", { sidebarOpen });
      import("@tauri-apps/api/event").then(({ emit }) => {
        emit("sidebar-state-changed", { open: sidebarOpen });
      });
    };

    // Listen for menu events
    unlisteners.push(
      await listen("menu-new", () => {
        /* new file */
      }),
    );
    unlisteners.push(
      await listen("menu-browse", () => {
        toggleSidebar(true);
      }),
    );
    unlisteners.push(
      await listen("menu-toggle-sidebar", () => {
        toggleSidebar();
      }),
    );

    // Listen for background pattern changes from GlobalBottomBar
    unlisteners.push(
      await listen<{ pattern: string }>(
        "background-pattern-changed",
        (event) => {
          selectedPattern = event.payload.pattern;
          savePreferences();
        },
      ),
    );

    // Listen for dark mode changes from bottom bar
    unlisteners.push(
      await listen<{ darkMode: boolean }>("dark-mode-changed", (event) => {
        darkMode = event.payload.darkMode;
      }),
    );

    // Listen for global toggle-sidebar event from bottom bar
    unlisteners.push(
      await listen<{ open: boolean }>("toggle-sidebar", (event) => {
        sidebarOpen = event.payload.open;
        // Save to mode state
        updateModeState("desktop", { sidebarOpen });
      }),
    );

    // Listen for font size changes (zoom)
    unlisteners.push(
      await listen<{ fontSize: number }>("font-size-changed", (event) => {
        if (event.payload.fontSize !== undefined) {
          fontSize = event.payload.fontSize;
          // Sync with styleManager so menu bar matches
          setFontSize(fontSize);
        }
      }),
    );

    // Load initial font size from state and sync with styleManager (desktopState already loaded above)
    if (desktopState.fontSize) {
      fontSize = desktopState.fontSize;
      // Ensure global styleManager is in sync with desktop fontSize
      const currentStyleState = getStyleState();
      if (currentStyleState.fontSize !== fontSize) {
        setFontSize(fontSize, true); // skipSave to avoid triggering saves
      }
    }
  });

  // Save fontSize when it changes
  $effect(() => {
    if (fontSize !== 20) {
      // Only save if different from default
      savePreferences();
      // Sync global styleManager so menu bar matches
      setFontSize(fontSize);
    }
  });

  onDestroy(() => {
    unlisteners.forEach((fn) => fn());
  });

  function updateClock() {
    const now = new Date();
    const hours = now.getHours() % 12 || 12;
    const minutes = now.getMinutes().toString().padStart(2, "0");
    const ampm = now.getHours() >= 12 ? "PM" : "AM";
    currentTime = `${hours}:${minutes} ${ampm}`;
  }

  function loadPreferences() {
    // Load from mode state (single source of truth)
    const desktopState = getStateForMode("desktop");
    selectedPattern = desktopState.pattern || "pattern-solid-white";
    sidebarOpen = desktopState.sidebarOpen || false;
    fontSize = desktopState.fontSize || 20;
  }

  function savePreferences() {
    updateModeState("desktop", {
      pattern: selectedPattern,
      sidebarOpen,
      fontSize,
    });
  }

  async function loadDesktopConfig() {
    try {
      // Backend resolves relative paths from project root
      const content = await invoke<string>("read_markdown_file", {
        path: "memory/udos.md",
      });
      parseDesktopConfig(content);
      // Load SVG icons for any Noun Project icons
      await loadNounIcons();
    } catch (err) {
      console.error("Failed to load udos.md:", err);
      icons = getDefaultIcons();
    }
  }

  async function loadNounIcons() {
    // Try to load from cache first
    const cached = loadIconsFromCache();
    if (cached) {
      cached.forEach((svg, term) => {
        // Find icons that match this term
        for (const icon of icons) {
          if (icon.name.toLowerCase() === term) {
            // Use a hash of the name as a pseudo-ID for cache
            const id = term
              .split("")
              .reduce((acc, char) => acc + char.charCodeAt(0), 0);
            iconSvgs[id] = svg;
            if (!icon.nounIcon) {
              icon.nounIcon = id;
            }
          }
        }
      });
      return;
    }

    // Load SVG files for icons with nounIcon IDs - try API directly
    // (local file cache removed as it was causing errors - icons cached in localStorage instead)
    for (const icon of icons) {
      if (icon.nounIcon && !iconSvgs[icon.nounIcon]) {
        try {
          const svg = await getIconSvg(icon.nounIcon);
          if (svg) {
            iconSvgs[icon.nounIcon] = svg;
            // Save to localStorage cache
            const cache = new Map();
            cache.set(icon.name.toLowerCase(), svg);
            saveIconsToCache(cache);
          }
        } catch (apiErr) {
          // Silently fail - will use emoji fallback
          // No need to log as this is expected when API key not configured
        }
      }
    }
  }

  function parseDesktopConfig(content: string) {
    const lines = content.split("\n");
    const parsed: DesktopIcon[] = [];
    let x = 0,
      y = 0;

    for (const line of lines) {
      // Match: - [emoji] Name | action | params | noun:12345
      // Also support old format: - [emoji] Name | action | params
      const match = line.match(
        /^-\s*\[(.+?)\]\s*(.+?)\s*\|\s*(\w+)(?:\s*\|\s*([^|]+?))?(?:\s*\|\s*noun:(\d+))?\s*$/,
      );
      if (match) {
        const [, emoji, name, action, params, nounId] = match;
        const icon: DesktopIcon = {
          id: `icon-${parsed.length}`,
          emoji: emoji.trim(),
          name: name.trim(),
          action: action.trim(),
          params: params?.trim(),
          x: x * 140 + 20,
          y: y * 120 + 20,
        };
        if (nounId) {
          icon.nounIcon = parseInt(nounId);
          console.log(`[Desktop] Icon "${name}" has Noun ID: ${nounId}`);
        }
        parsed.push(icon);
        y++;
        if (y > 3) {
          // 4x4 grid (0-3 = 4 rows)
          y = 0;
          x++;
        }
      }
    }

    icons = parsed.length > 0 ? parsed : getDefaultIcons();
    console.log(
      "[Desktop] Parsed icons:",
      icons.map((i) => ({ name: i.name, nounIcon: i.nounIcon })),
    );
  }

  function getDefaultIcons(): DesktopIcon[] {
    return [
      // Row 1
      {
        id: "typo",
        emoji: "📝",
        name: "Markdown",
        action: "navigate",
        params: "/editor",
        x: 20,
        y: 20,
      },
      {
        id: "table",
        emoji: "📊",
        name: "Table",
        action: "navigate",
        params: "/table",
        x: 220,
        y: 20,
      },
      {
        id: "knowledge",
        emoji: "📚",
        name: "Knowledge",
        action: "navigate",
        params: "/knowledge",
        x: 320,
        y: 20,
      },
      // Row 2
      {
        id: "terminal",
        emoji: "💻",
        name: "Terminal",
        action: "navigate",
        params: "/terminal",
        x: 20,
        y: 120,
      },
      {
        id: "groovebox",
        emoji: "🎹",
        name: "Groovebox",
        action: "navigate",
        params: "/groovebox",
        x: 120,
        y: 120,
      },
      {
        id: "teledesk",
        emoji: "📺",
        name: "Teledesk",
        action: "navigate",
        params: "/teledesk",
        x: 220,
        y: 120,
      },
      {
        id: "files",
        emoji: "📁",
        name: "Files",
        action: "open_sidebar",
        x: 320,
        y: 120,
      },
      // Row 3
      {
        id: "settings",
        emoji: "⚙️",
        name: "Settings",
        action: "open_preferences",
        x: 20,
        y: 220,
      },
      {
        id: "trash",
        emoji: "🗑️",
        name: "Trash",
        action: "open_trash",
        x: 120,
        y: 220,
      },
    ];
  }

  async function handleIconClick(icon: DesktopIcon) {
    switch (icon.action) {
      case "navigate":
        if (icon.params) window.location.href = icon.params;
        break;
      case "open_folder":
        if (icon.params) {
          try {
            await openPath(icon.params);
          } catch {}
        }
        break;
      case "open_sidebar":
        sidebarOpen = true;
        import("@tauri-apps/api/event").then(({ emit }) => {
          emit("sidebar-state-changed", { open: true });
        });
        break;
      case "open_wizard":
        await openUrl("http://localhost:5001/wizard");
        break;
      case "open_transport":
        toastStore.info("Transport panel coming soon");
        break;
      case "open_trash":
        toastStore.info("Trash coming soon");
        break;
    }
  }

  async function handleFileSelect(path: string) {
    // Emit file-opened event for recent files tracking
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("file-opened", {
        path,
        name: path.split("/").pop() || "Untitled",
      });
    });

    // Open file in Typo editor
    navigateToMode("markdown", path);
  }

  function selectPattern(pattern: Pattern) {
    selectedPattern = pattern.class;
    savePreferences();
  }
</script>

<!-- System 7 Desktop -->
<div
  class="desktop-container h-full flex flex-col {selectedPattern}"
  style="--desktop-zoom: {fontSize / 24}"
>
  <!-- Main Desktop Area -->
  <div class="flex-1 flex overflow-hidden transition-all duration-300">
    <div class="flex-1 flex flex-col min-h-0 overflow-hidden">
      <div
        class="grid flex-1 min-h-0 overflow-hidden {sidebarOpen
          ? 'lg:grid-cols-2'
          : ''}"
      >
        <!-- File Sidebar (left half when open) -->
        {#if sidebarOpen}
          <div
            class="flex flex-col min-h-0 overflow-hidden bg-white dark:bg-gray-900 border-r-2 border-black dark:border-gray-700"
          >
            <FileSidebar
              currentFilePath={""}
              onFileSelect={handleFileSelect}
              isOpen={sidebarOpen}
              onToggle={() => {
                sidebarOpen = false;
                import("@tauri-apps/api/event").then(({ emit }) => {
                  emit("sidebar-state-changed", { open: false });
                });
              }}
              mode="desktop"
            />
          </div>
        {/if}

        <!-- Desktop Grid -->
        <div class="flex-1 relative overflow-auto desktop-grid">
          <!-- Icons -->
          {#each icons as icon, i}
            <button
              class="desktop-icon absolute flex flex-col items-center gap-1 p-2 hover:bg-white/50 dark:hover:bg-black/50 rounded transition-all duration-300"
              style="left: {icon.x * (fontSize / 20)}px; top: {icon.y *
                (fontSize / 20)}px; width: {90 * (fontSize / 20)}px;"
              onclick={() => handleIconClick(icon)}
            >
              {#if icon.nounIcon && iconSvgs[icon.nounIcon]}
                <!-- Render Noun Project SVG icon -->
                <div
                  class="icon-image flex items-center justify-center drop-shadow-sm"
                  style="width: {40 * (fontSize / 24)}px; height: {40 *
                    (fontSize / 24)}px;"
                >
                  {@html iconSvgs[icon.nounIcon]}
                </div>
              {:else}
                <!-- Fallback to emoji -->
                <div
                  class="icon-image drop-shadow-sm"
                  style="font-size: {2.25 * (fontSize / 20)}rem;"
                >
                  {icon.emoji}
                </div>
              {/if}
              <div
                class="icon-label text-center px-1 py-0.5 bg-white/90 text-black dark:bg-black/90 dark:text-white rounded shadow-sm"
                style="font-size: {Math.round(fontSize * 0.7)}px;"
              >
                {icon.name}
              </div>
            </button>
          {/each}
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  /* System 7 desktop styling */
  .desktop-container {
    background-repeat: repeat;
  }

  /* Scale background pattern with zoom */
  .desktop-grid {
    background-size: calc(var(--desktop-zoom, 1) * 100%);
    transition: background-size 0.3s ease;
  }

  .desktop-icon {
    user-select: none;
    cursor: default;
    transition: all 0.3s ease;
  }

  .icon-label {
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
  }

  .desktop-icon:active {
    transform: scale(0.95);
  }
</style>
