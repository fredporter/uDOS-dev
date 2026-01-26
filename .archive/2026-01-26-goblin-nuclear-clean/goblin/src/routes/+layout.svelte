<script lang="ts">
  import type { Snippet } from "svelte";
  import favicon from "$lib/assets/favicon.svg";
  import "../app.css";
  import GlobalMenuBar from "$lib/components/GlobalMenuBar.svelte";
  import Flyin from "$lib/components/Flyin.svelte";
  import Feed from "$lib/components/Feed.svelte";
  import GlobalBottomBar from "$lib/components/GlobalBottomBar.svelte";
  import InputSidebar from "$lib/components/InputSidebar.svelte";
  import UDOSSidebar from "$lib/components/UDOSSidebar.svelte";
  import CopyBufferSidebar from "$lib/components/CopyBufferSidebar.svelte";
  import KeypadSidebar from "$lib/components/KeypadSidebar.svelte";
  import DebugPanel from "$lib/components/DebugPanel.svelte";
  import { Toaster } from "svelte-sonner";
  import {
    initKeyboardManager,
    addToCopyBuffer,
  } from "$lib/services/keyboardManager";
  import { page } from "$app/stores";
  import { onMount, untrack } from "svelte";
  import { listen, type UnlistenFn } from "@tauri-apps/api/event";
  import { invoke } from "@tauri-apps/api/core";
  import {
    createFeed,
    loadNotificationFeed,
    loadKnowledgeFeed,
    getFeed,
  } from "$lib/stores/feed";
  import {
    initStyleManager,
    toggleDarkMode as styleToggleDarkMode,
    getStyleState,
    setHeadingFont,
    setBodyFont,
    setMonoVariant,
    setFontSize,
    setDarkMode,
    applyStyles,
  } from "$lib/services/styleManager";
  import {
    getModeState,
    updateModeState,
    getStateForMode,
    resetModeDisplay,
    loadModeStateFromAPI,
  } from "$lib/stores/modeState";

  let { children }: { children?: Snippet } = $props();
  let flyinOpen = $state(false);
  let tickerMode = $state<"sentence" | "caps" | "hide">("sentence");
  let feedPosition = $state<"top" | "bottom">("top");
  let tickerReady = $state(false);
  let sidebarOpen = $state(false);
  let isEditing = $state(false);
  let darkMode = $state(true);
  let menuBarVisible = $state(true);
  let utilitySidebarOpen = $state(false);
  let copyBufferOpen = $state(false);
  let keypadOpen = $state(false);
  let currentFile = $state<string | null>(null);
  let charCount = $state(0);
  let wordCount = $state(0);
  let readTime = $state(0);
  let viewType = $state("document"); // For read mode: "document" or "slideshow"
  let unlisteners: UnlistenFn[] = [];
  let currentMode = $derived($page.url.pathname.split("/")[1] || "desktop");
  let previousMode = $state<string | null>(null);
  let enableAutoSave = $state(false); // Start disabled until after first mode load
  let isRestoringMode = $state(false); // Track if we're currently restoring a mode
  let restorationTimeoutId: number | null = null; // Track timeout to prevent stacking

  // svelte-sonner ships Svelte 4 typings; cast loosely for Svelte 5 compatibility
  const ToastHost: any = Toaster;

  // Map route paths to mode state keys (some routes have different names)
  const routeToModeKey = (route: string): string => {
    const routeMap: Record<string, string> = {
      editor: "markdown",
      present: "markdown", // Presentation mode is part of markdown
      // Most routes match their mode key directly
    };
    return routeMap[route] || route;
  };

  // Get the proper mode key for state management
  let modeKey = $derived.by(() => {
    const key = routeToModeKey(currentMode);
    return key === "default" ? "desktop" : key;
  });

  // Track previous style state to prevent unnecessary saves
  let previousStyleState = $state<{
    fontSize: number;
    headingFont: string;
    bodyFont: string;
    darkMode: boolean;
  } | null>(null);

  // Valid mode keys that support state persistence
  const VALID_MODES = [
    "desktop",
    "read",
    "markdown",
    "table",
    "dashboard",
    "terminal",
    "teledesk",
    "blocks",
  ] as const;
  type ValidMode = (typeof VALID_MODES)[number];

  // Save mode state for a specific mode
  function saveModeState(mode: string) {
    if (!VALID_MODES.includes(mode as ValidMode)) return;

    const styleState = getStyleState();
    console.log(
      "[ModeState] Saving state for mode:",
      mode,
      styleState,
      "sidebarOpen:",
      sidebarOpen
    );

    // Save monoVariant and sidebarOpen for all modes (each mode maintains its own preferences)
    updateModeState(mode as ValidMode, {
      headingFont: styleState.headingFont,
      bodyFont: styleState.bodyFont,
      fontSize: styleState.fontSize,
      darkMode: styleState.darkMode,
      monoVariant: styleState.monoVariant as any,
      sidebarOpen: sidebarOpen,
    });
  }

  // Restore mode state when mode changes
  $effect(() => {
    if (currentMode && currentMode !== previousMode) {
      console.log(
        "[ModeState] Mode changed from",
        previousMode,
        "to",
        currentMode
      );

      // Clear any pending restoration timeout to prevent stacking
      if (restorationTimeoutId !== null) {
        clearTimeout(restorationTimeoutId);
        restorationTimeoutId = null;
      }

      // Disable auto-save during the entire restoration process
      enableAutoSave = false;
      isRestoringMode = true;
      console.log("[ModeState] Auto-save DISABLED - starting restoration");

      // Save previous mode state before switching (only if not first load)
      if (previousMode && VALID_MODES.includes(previousMode as ValidMode)) {
        saveModeState(previousMode);
      }

      // Restore new mode state
      if (VALID_MODES.includes(currentMode as ValidMode)) {
        const modeState = getStateForMode(currentMode as ValidMode);
        console.log(
          "[ModeState] Restoring state for",
          currentMode,
          ":",
          modeState
        );

        if (modeState) {
          // Use untrack to prevent these setter calls from triggering reactive effects
          untrack(() => {
            // Restore fonts and settings WITHOUT saving to global preferences
            setHeadingFont(modeState.headingFont, true); // skipSave = true
            setBodyFont(modeState.bodyFont, true); // skipSave = true
            setFontSize(modeState.fontSize, true); // skipSave = true
            setDarkMode(modeState.darkMode, true); // skipSave = true

            // Restore monoVariant for all modes (each mode maintains its own font preference)
            if ("monoVariant" in modeState) {
              setMonoVariant((modeState as any).monoVariant, true); // skipSave = true
            }

            darkMode = modeState.darkMode;

            // Restore mode-specific sidebar state for layout's bottom bar indicator
            // Pages load their own sidebar state from modeState, no emit needed
            if ("sidebarOpen" in modeState) {
              sidebarOpen = (modeState as any).sidebarOpen;
            }

            // Update previousStyleState IMMEDIATELY to prevent false change detection
            previousStyleState = {
              fontSize: modeState.fontSize,
              headingFont: modeState.headingFont,
              bodyFont: modeState.bodyFont,
              darkMode: modeState.darkMode,
            };
          });

          // Apply styles once and re-enable auto-save after DOM updates
          applyStyles();

          // Use a single timeout to re-enable auto-save after DOM settles
          restorationTimeoutId = setTimeout(() => {
            enableAutoSave = true;
            isRestoringMode = false;
            restorationTimeoutId = null;
            console.log("[ModeState] Auto-save ENABLED (restoration complete)");
          }, 150) as unknown as number;
        }
      }

      previousMode = currentMode;
    }
  });

  // Watch for style changes and save current mode state
  $effect(() => {
    // Track style state changes
    const styleState = getStyleState();
    const _ = styleState.fontSize; // Access to trigger reactivity
    const __ = styleState.headingFont;
    const ___ = styleState.bodyFont;
    const ____ = styleState.darkMode;

    // Check if style state actually changed
    const hasChanged =
      !previousStyleState ||
      previousStyleState.fontSize !== styleState.fontSize ||
      previousStyleState.headingFont !== styleState.headingFont ||
      previousStyleState.bodyFont !== styleState.bodyFont ||
      previousStyleState.darkMode !== styleState.darkMode;

    // Only save if auto-save is enabled, we have a current mode, it's not during initial load, AND something changed
    if (
      hasChanged &&
      enableAutoSave &&
      !isRestoringMode &&
      currentMode &&
      previousMode !== null &&
      VALID_MODES.includes(currentMode as ValidMode)
    ) {
      console.log(
        "[ModeState] ⚠️ Style changed in mode:",
        currentMode,
        "- AUTO-SAVING",
        {
          fontSize: styleState.fontSize,
          headingFont: styleState.headingFont,
          bodyFont: styleState.bodyFont,
          darkMode: styleState.darkMode,
        }
      );
      saveModeState(currentMode);

      // Update previous style state
      previousStyleState = {
        fontSize: styleState.fontSize,
        headingFont: styleState.headingFont,
        bodyFont: styleState.bodyFont,
        darkMode: styleState.darkMode,
      };
    } else if (!enableAutoSave) {
      console.log(
        "[ModeState] ✋ Style change detected but auto-save is DISABLED"
      );
    }
  });

  // Save feed preferences
  function saveFeedPreferences() {
    localStorage.setItem("tickerMode", tickerMode);
    localStorage.setItem("feedPosition", feedPosition);
  }

  // Cycle ticker: on-top → on-bottom → off
  function cycleTickerMode() {
    if (tickerMode !== "hide" && feedPosition === "top") {
      // State 1: On Top → State 2: On Bottom
      feedPosition = "bottom";
    } else if (tickerMode !== "hide" && feedPosition === "bottom") {
      // State 2: On Bottom → State 3: Off
      tickerMode = "hide";
    } else {
      // State 3: Off → State 1: On Top
      tickerMode = "sentence";
      feedPosition = "top";
    }
    saveFeedPreferences();
  }

  // Initialize global feeds on mount
  onMount(() => {
    // Initialize style manager (MUST be first!)
    const styleState = initStyleManager();
    darkMode = styleState.darkMode;

    // Load mode state from API file system (sync across instances)
    loadModeStateFromAPI().catch((err) => {
      console.warn("[Layout] Could not load mode state from API:", err);
    });

    // Load feed preferences
    const savedTickerMode = localStorage.getItem("tickerMode") as
      | "sentence"
      | "caps"
      | "hide"
      | null;
    if (
      savedTickerMode &&
      ["sentence", "caps", "hide"].includes(savedTickerMode)
    ) {
      tickerMode = savedTickerMode;
    }
    const savedFeedPosition = localStorage.getItem("feedPosition") as
      | "top"
      | "bottom"
      | null;
    if (savedFeedPosition) {
      feedPosition = savedFeedPosition;
    }

    // Load sidebar preference
    const savedSidebar = localStorage.getItem("sidebarOpen");
    if (savedSidebar === "true") {
      sidebarOpen = true;
    }

    // Load menu bar preference
    const savedMenuBar = localStorage.getItem("menuBarVisible");
    if (savedMenuBar !== null) {
      menuBarVisible = savedMenuBar === "true";
    }

    // Load utility sidebar preference
    const savedUtilitySidebar = localStorage.getItem("utilitySidebarOpen");
    if (savedUtilitySidebar === "true") {
      utilitySidebarOpen = true;
    }

    // Create notification ticker
    if (!getFeed("notification-ticker")) {
      createFeed("notification-ticker", "notifications", "ticker", {
        scrollSpeed: 50,
        autoAdvance: true,
        advanceDelay: 5000,
      });
      loadNotificationFeed("notification-ticker");
    }

    // Create knowledge ticker as fallback
    if (!getFeed("knowledge-ticker")) {
      createFeed("knowledge-ticker", "knowledge", "ticker", {
        scrollSpeed: 40,
        autoAdvance: true,
        advanceDelay: 8000,
      });
      loadKnowledgeFeed("knowledge-ticker");
    }

    tickerReady = true;

    // Set up event listeners
    const setupListeners = async () => {
      // Listen for reset mode display
      unlisteners.push(
        await listen("reset-mode-display", () => {
          console.log("[Layout] Reset mode display event received");
          console.log("[Layout] Current route:", currentMode);
          console.log("[Layout] Mode key:", modeKey);
          console.log("[Layout] Valid modes:", VALID_MODES);

          if (VALID_MODES.includes(modeKey as ValidMode)) {
            console.log("[Layout] Resetting mode:", modeKey);

            // Reset mode state to defaults (this saves to storage)
            resetModeDisplay(modeKey as ValidMode);
            // Get the fresh default state after reset
            const modeState = getStateForMode(modeKey as ValidMode);
            console.log("[Layout] Fresh mode state:", modeState);

            // Apply all default styles without saving to global preferences
            setHeadingFont(modeState.headingFont, true);
            setBodyFont(modeState.bodyFont, true);
            setFontSize(modeState.fontSize, true);
            setDarkMode(modeState.darkMode, true);

            // Restore default monoVariant
            if ("monoVariant" in modeState) {
              setMonoVariant((modeState as any).monoVariant, true);
            }

            // Update local dark mode state
            darkMode = modeState.darkMode;
            console.log("[Layout] Applying styles...");
            // Force apply styles after reset
            setTimeout(() => applyStyles(), 50);
          } else {
            console.warn("[Layout] Mode key not in VALID_MODES:", modeKey);
          }
        })
      );

      // Listen for document stats updates from editors
      unlisteners.push(
        await listen<{ chars: number; words: number; readTime: number }>(
          "document-stats",
          (event) => {
            charCount = event.payload.chars;
            wordCount = event.payload.words;
            readTime = event.payload.readTime;
          }
        )
      );

      // Listen for current file changes from editors/viewers
      unlisteners.push(
        await listen<{ path: string }>("current-file-changed", (event) => {
          currentFile = event.payload.path;
        })
      );

      // Listen for editing mode changes
      unlisteners.push(
        await listen<{ editing: boolean }>("editing-mode-changed", (event) => {
          isEditing = event.payload.editing;
        })
      );

      // Listen for read mode view type changes
      unlisteners.push(
        await listen<{ viewType: string }>(
          "read-view-type-changed",
          (event) => {
            viewType = event.payload.viewType;
          }
        )
      );

      // Listen for feed control events from menu
      unlisteners.push(
        await listen("menu-toggle-feed", () => {
          cycleTickerMode();
        })
      );

      unlisteners.push(
        await listen<{ position: "top" | "bottom" }>(
          "menu-feed-position",
          (event) => {
            feedPosition = event.payload.position;
            saveFeedPreferences();
          }
        )
      );

      // Listen for restart uDOS event
      unlisteners.push(
        await listen("restart-udos", async () => {
          // Trigger reboot script and reload
          console.log("[Layout] Restarting uDOS...");

          // Navigate to terminal if not already there
          const currentPath = window.location.pathname;
          if (currentPath !== "/terminal") {
            console.log(
              "[Layout] Navigating to terminal for reboot sequence..."
            );
            window.location.href = "/terminal";
            // Wait for navigation
            await new Promise((resolve) => setTimeout(resolve, 100));
          }

          // Emit event to terminal page to show reboot sequence
          import("@tauri-apps/api/event").then(({ emit }) => {
            emit("show-reboot-sequence", {});
          });

          // Wait for reboot animation (4 seconds as defined in terminal page)
          setTimeout(() => {
            console.log("[Layout] Reloading application...");
            window.location.reload();
          }, 4000);
        })
      );

      // Listen for toggle-edit event from bottom bar
      unlisteners.push(
        await listen("toggle-edit", () => {
          isEditing = !isEditing;
          // Re-emit for mode-specific handling
          import("@tauri-apps/api/event").then(({ emit }) => {
            emit("editing-mode-changed", { editing: isEditing });
          });
        })
      );

      // Listen for sidebar state changes from pages
      unlisteners.push(
        await listen<{ open: boolean }>("sidebar-state-changed", (event) => {
          sidebarOpen = event.payload.open;
        })
      );

      // Listen for toggle copy buffer
      unlisteners.push(
        await listen("toggle-copy-buffer", () => {
          copyBufferOpen = !copyBufferOpen;
        })
      );

      // Listen for toggle keypad
      unlisteners.push(
        await listen("toggle-keypad", () => {
          keypadOpen = !keypadOpen;
        })
      );

      // Listen for toggle flyin (Cmd+K)
      unlisteners.push(
        await listen("toggle-flyin", () => {
          flyinOpen = !flyinOpen;
        })
      );

      // Listen for cycle ticker mode (Cmd+T)
      unlisteners.push(
        await listen("cycle-ticker-mode", () => {
          cycleTickerMode();
        })
      );

      // Listen for toggle sidebar (Cmd+B) - from keyboard manager
      unlisteners.push(
        await listen("toggle-sidebar-request", () => {
          sidebarOpen = !sidebarOpen;
          // Emit to pages with the new state
          import("@tauri-apps/api/event").then(({ emit }) => {
            emit("toggle-sidebar", { open: sidebarOpen });
          });
        })
      );

      // Listen for toggle dev console (F12)
      unlisteners.push(
        await listen("toggle-dev-console", () => {
          window.location.href = "/dev-console";
        })
      );

      // Listen for toggle presentation (F8)
      unlisteners.push(
        await listen("toggle-presentation", () => {
          // Check if we're in editor mode with a file
          if (currentMode === "editor" && currentFile) {
            window.location.href = `/present?file=${encodeURIComponent(currentFile)}`;
          } else if (currentMode === "present") {
            // Exit presentation mode
            window.history.back();
          } else {
            // Default: go to presentation with demo slideshow (relative path)
            window.location.href =
              "/present?file=memory/sandbox/demo/slideshow.udos.md";
          }
        })
      );

      // Auto-copy selected text to clipboard and buffer on mouseup
      // Disabled on dev-console page to prevent crashes
      const handleTextSelection = async () => {
        // Don't auto-copy on dev-console page
        if (window.location.pathname === "/dev-console") {
          return;
        }

        const selection = window.getSelection();
        const selectedText = selection?.toString().trim();

        if (selectedText && selectedText.length > 0) {
          try {
            await navigator.clipboard.writeText(selectedText);
            // Add to copy buffer
            addToCopyBuffer(selectedText, currentMode);
          } catch (err) {
            console.error("[Clipboard] Failed to auto-copy selection:", err);
          }
        }
      };

      document.addEventListener("mouseup", handleTextSelection);

      // Initialize global keyboard manager
      const cleanupKeyboard = initKeyboardManager();

      // Cleanup on unmount
      return () => {
        document.removeEventListener("mouseup", handleTextSelection);
        cleanupKeyboard();
      };
    };

    setupListeners();

    // Listen for style changes from styleManager and immediately save to current mode
    const handleStyleChanged = () => {
      if (
        enableAutoSave &&
        !isRestoringMode &&
        currentMode &&
        VALID_MODES.includes(currentMode as ValidMode)
      ) {
        console.log(
          "[ModeState] 🎨 Style changed via setter - saving to mode:",
          currentMode
        );
        saveModeState(currentMode);
      }
    };
    window.addEventListener("udos-style-changed", handleStyleChanged);

    return () => {
      unlisteners.forEach((unlisten) => unlisten());
      window.removeEventListener("udos-style-changed", handleStyleChanged);

      // Clear any pending restoration timeout
      if (restorationTimeoutId !== null) {
        clearTimeout(restorationTimeoutId);
        restorationTimeoutId = null;
      }
    };
  });

  // Don't show app shell on the loading/redirect page
  let showAppShell = $derived(!$page.url.pathname.match(/^\/$/));
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

{#if showAppShell}
  <!-- App Shell with top bar -->
  <div class="h-screen bg-udos-bg flex flex-col overflow-hidden">
    <!-- Global Menu Bar (System 7 style - universal across modes) -->
    {#if menuBarVisible}
      <GlobalMenuBar {tickerMode} {feedPosition} />
    {/if}

    <!-- Feed Ticker (global - top position) -->
    {#if tickerMode !== "hide" && tickerReady && feedPosition === "top"}
      <Feed feedId="knowledge-ticker" mode={tickerMode} />
    {/if}

    <!-- Main Content Area -->
    <main class="flex-1 min-h-0 overflow-hidden flex">
      <div class="flex-1 min-w-0 mode-{currentMode}">
        {#if children}{@render (children as any)()}{/if}
      </div>

      <!-- Copy Buffer Sidebar (Right) -->
      {#if copyBufferOpen}
        <CopyBufferSidebar
          isOpen={copyBufferOpen}
          onClose={() => {
            copyBufferOpen = false;
          }}
        />
      {/if}

      <!-- Utility Sidebar (Right) - uDOS Styled -->
      {#if utilitySidebarOpen}
        <UDOSSidebar />
      {/if}
    </main>

    <!-- Keypad Overlay (positioned absolutely on top of content) -->
    {#if keypadOpen}
      <KeypadSidebar
        isOpen={keypadOpen}
        onClose={() => {
          keypadOpen = false;
        }}
      />
    {/if}

    <!-- Feed Ticker (global - bottom position, above bottom bar) -->
    {#if tickerMode !== "hide" && tickerReady && feedPosition === "bottom"}
      <Feed feedId="knowledge-ticker" mode={tickerMode} />
    {/if}

    <!-- Global Bottom Bar -->
    <GlobalBottomBar
      {currentFile}
      {isEditing}
      {darkMode}
      {sidebarOpen}
      {menuBarVisible}
      {utilitySidebarOpen}
      {charCount}
      {wordCount}
      {readTime}
      {viewType}
      {tickerMode}
      {feedPosition}
      onToggleSidebar={() => {
        sidebarOpen = !sidebarOpen;
        // Emit for page-level sidebars
        import("@tauri-apps/api/event").then(({ emit }) => {
          emit("toggle-sidebar", { open: sidebarOpen });
        });
      }}
      onToggleEdit={() => {
        isEditing = !isEditing;
        // Emit for pages that care about edit/view mode
        import("@tauri-apps/api/event").then(({ emit }) => {
          emit("edit-mode-changed", { isEditing });
        });
      }}
      onToggleDarkMode={() => {
        darkMode = styleToggleDarkMode();
        // Emit for pages that need to know
        import("@tauri-apps/api/event").then(({ emit }) => {
          emit("dark-mode-changed", { darkMode });
        });
      }}
      onToggleMenuBar={() => {
        menuBarVisible = !menuBarVisible;
        localStorage.setItem("menuBarVisible", menuBarVisible.toString());
      }}
      onToggleUtilitySidebar={() => {
        utilitySidebarOpen = !utilitySidebarOpen;
        localStorage.setItem(
          "utilitySidebarOpen",
          utilitySidebarOpen.toString()
        );
      }}
      onCycleTicker={cycleTickerMode}
    />
  </div>
{:else}
  {#if children}{@render (children as any)()}{/if}
{/if}

<!-- Flyin Command Palette -->
<Flyin open={flyinOpen} onClose={() => (flyinOpen = false)} />

<!-- Debug Panel -->
<DebugPanel />

<!-- Toast Notifications -->
<ToastHost position="bottom-center" richColors offset="20vh" />
