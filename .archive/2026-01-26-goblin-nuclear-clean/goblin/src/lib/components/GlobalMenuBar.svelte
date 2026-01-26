<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { emit } from "@tauri-apps/api/event";
  import { getCurrentWindow } from "@tauri-apps/api/window";
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import * as svg from "$lib/components/svg";
  import { toastStore } from "$lib/stores/toastStore";

  let {
    currentTime = "",
    tickerMode = "sentence" as "sentence" | "caps" | "hide",
    feedPosition = "top" as "top" | "bottom",
  } = $props();

  let showModeMenu = $state(false);
  let showFileMenu = $state(false);
  let showEditMenu = $state(false);
  let showViewMenu = $state(false);
  let showHelpMenu = $state(false);
  let currentModeName = $derived.by(() => {
    const path = $page.url.pathname.split("/")[1] || "desktop";
    const modeMap: Record<string, string> = {
      desktop: "Desktop",
      editor: "Markdown",
      table: "Table",
      teledesk: "Teledesk",
      terminal: "Terminal",
      groovebox: "Groovebox",
      "pixel-editor": "Pixel Editor",
      "layer-editor": "Layer Editor",
      "svg-processor": "SVG Processor",
    };
    return modeMap[path] || "Desktop";
  });
  let currentModeKey = $derived.by(
    () => $page.url.pathname.split("/")[1] || "desktop"
  );

  const closeAllMenus = () => {
    showModeMenu = false;
    showFileMenu = false;
    showEditMenu = false;
    showViewMenu = false;
    showHelpMenu = false;
  };

  // Menu actions that emit events for pages to handle
  const menuAction = async (action: string, payload?: any) => {
    closeAllMenus();
    await emit(`menu-${action}`, payload);
  };

  const switchMode = (route: string) => {
    closeAllMenus();
    goto(route);
  };

  const openGitHubWiki = () => {
    window.open("https://github.com/fredporter/uDOS-dev/wiki", "_blank");
    closeAllMenus();
  };

  const openGitHubFeedback = () => {
    window.open(
      "https://github.com/fredporter/uDOS-dev/issues/new?labels=feedback&template=feedback.md",
      "_blank"
    );
    closeAllMenus();
  };

  const openAbout = () => {
    alert(
      "uMarkdown v1.1.0.1\n\nA Python-venv OS layer for Tiny Core Linux\n\nOffline-first knowledge system"
    );
    closeAllMenus();
  };

  const openKeyboardShortcuts = async () => {
    closeAllMenus();
    await goto("/editor?file=scripts/hotkey.udos.md");
  };

  const reloadApp = async () => {
    if (
      confirm(
        "Restart uMarkdown? This will show the reboot sequence and refresh the interface."
      )
    ) {
      closeAllMenus();
      // Navigate to terminal
      await goto("/terminal");
      // Wait for navigation
      await new Promise((resolve) => setTimeout(resolve, 200));
      // Emit reboot sequence event
      await emit("show-reboot-sequence", {});
      // Reload after animation (4 seconds)
      setTimeout(() => {
        window.location.reload();
      }, 4000);
    } else {
      closeAllMenus();
    }
  };

  // Global hotkeys (F1–F12 and common shortcuts)
  const handleKeydown = async (e: KeyboardEvent) => {
    const target = e.target as HTMLElement | null;
    const tag = target?.tagName || "";
    const inEditable =
      !!target &&
      (target.isContentEditable ||
        ["INPUT", "TEXTAREA", "SELECT"].includes(tag));
    const isFunctionKey = /^F\d{1,2}$/.test(e.key);

    // Allow function keys everywhere; skip other shortcuts when typing
    if (!isFunctionKey && inEditable) return;

    // Common shortcuts (macOS Command key)
    if (e.metaKey) {
      switch (e.key.toLowerCase()) {
        case "o":
          e.preventDefault();
          await menuAction("open");
          return;
        case "s":
          e.preventDefault();
          await menuAction("save");
          return;
        case "n":
          e.preventDefault();
          await menuAction("new");
          return;
        case "w":
          e.preventDefault();
          await menuAction("close");
          return;
        case "q":
          e.preventDefault();
          await menuAction("quit");
          return;
        case "1":
          e.preventDefault();
          switchMode("/editor");
          return;
        case "2":
          e.preventDefault();
          switchMode("/terminal");
          return;
        case "3":
          e.preventDefault();
          await goto("/editor?file=knowledge/");
          return;
        case "4":
          e.preventDefault();
          await goto("/editor?file=knowledge/");
          return;
        case "b":
          // Toggle sidebar (View → Toggle Sidebar)
          e.preventDefault();
          await menuAction("toggle-sidebar");
          return;
      }
    }

    // Function keys (F1–F12)
    switch (e.key) {
      case "F1":
        e.preventDefault();
        await goto("/editor?file=scripts/hotkey.udos.md");
        return;
      case "F2":
        e.preventDefault();
        switchMode("/editor");
        return;
      case "F3":
        e.preventDefault();
        switchMode("/terminal");
        return;
      case "F4":
        e.preventDefault();
        switchMode("/table");
        return;
      case "F5":
        e.preventDefault();
        switchMode("/table");
        return;
      case "F6":
        e.preventDefault();
        switchMode("/groovebox");
        return;
      case "F7":
        e.preventDefault();
        switchMode("/pixel-editor");
        return;
      case "F8":
        e.preventDefault();
        switchMode("/layer-editor");
        return;
      case "F9":
        e.preventDefault();
        switchMode("/svg-processor");
        return;
      case "F10":
        e.preventDefault();
        await goto("/editor?file=knowledge/");
        return;
      case "F11":
        e.preventDefault();
        try {
          const appWindow = getCurrentWindow();
          const fs = await appWindow.isFullscreen();
          await appWindow.setFullscreen(!fs);
        } catch (err) {
          console.warn("Fullscreen toggle failed", err);
        }
        return;
      case "F12":
        e.preventDefault();
        toastStore.info("Opening Dev Console (Terminal)", 2000);
        switchMode("/terminal");
        return;
    }
  };

  onMount(() => {
    window.addEventListener("keydown", handleKeydown);
    return () => window.removeEventListener("keydown", handleKeydown);
  });
</script>

<!-- System 7-style Menu Bar -->
<header
  class="menu-bar bg-white dark:bg-gray-900 border-b-2 border-gray-800 dark:border-gray-600 shadow-lg flex items-center justify-between px-2 h-7 sticky top-0 z-[9999] text-black dark:text-white"
>
  <!-- Left: Menus -->
  <div class="flex items-center gap-1 font-bold">
    <!-- Mode Menu (shows current mode, dropdown for switching) -->
    <div class="relative">
      <button
        class="px-2 py-1 hover:bg-blue-500 hover:text-white rounded transition"
        onclick={() => {
          closeAllMenus();
          showModeMenu = !showModeMenu;
        }}
      >
        🌀 {currentModeName}
      </button>
      {#if showModeMenu}
        <div
          class="absolute top-full left-0 mt-1 bg-white dark:bg-gray-800 border-2 border-gray-800 dark:border-gray-600 shadow-xl min-w-40"
          style="z-index: 10000;"
        >
          <button
            class="w-full text-left px-3 py-1 hover:bg-blue-500 hover:text-white text-black dark:text-white text-sm"
            onclick={() => switchMode("/desktop")}
          >
            Desktop
          </button>
          <button
            class="w-full text-left px-3 py-1 hover:bg-blue-500 hover:text-white text-black dark:text-white text-sm"
            onclick={() => switchMode("/editor")}
          >
            Markdown
          </button>
          <button
            class="w-full text-left px-3 py-1 hover:bg-blue-500 hover:text-white text-black dark:text-white text-sm"
            onclick={() => switchMode("/table")}
          >
            Table
          </button>
          <button
            class="w-full text-left px-3 py-1 hover:bg-blue-500 hover:text-white text-black dark:text-white text-sm"
            onclick={() => switchMode("/terminal")}
          >
            Terminal
          </button>
          <button
            class="w-full text-left px-3 py-1 hover:bg-blue-500 hover:text-white text-black dark:text-white text-sm"
            onclick={() => switchMode("/teledesk")}
          >
            Teledesk
          </button>
          <button
            class="w-full text-left px-3 py-1 hover:bg-blue-500 hover:text-white text-black dark:text-white text-sm"
            onclick={() => switchMode("/groovebox")}
          >
            Groovebox
          </button>
          <button
            class="w-full text-left px-3 py-1 hover:bg-blue-500 hover:text-white text-black dark:text-white text-sm"
            onclick={() => switchMode("/pixel-editor")}
          >
            Pixel Editor
          </button>
          <button
            class="w-full text-left px-3 py-1 hover:bg-blue-500 hover:text-white text-black dark:text-white text-sm"
            onclick={() => switchMode("/layer-editor")}
          >
            Layer Editor
          </button>
          <button
            class="w-full text-left px-3 py-1 hover:bg-blue-500 hover:text-white text-black dark:text-white text-sm"
            onclick={() => switchMode("/svg-processor")}
          >
            SVG Processor
          </button>
          <div
            class="border-t-2 border-gray-300 dark:border-gray-600 my-0.5"
          ></div>
          <button
            class="w-full text-left px-3 py-1 hover:bg-blue-500 hover:text-white text-black dark:text-white text-sm"
            onclick={reloadApp}
          >
            Restart uDOS
          </button>
          <button
            class="w-full text-left px-3 py-1 hover:bg-blue-500 hover:text-white text-black dark:text-white text-sm"
            onclick={() => menuAction("close")}
          >
            Close <span class="float-right text-gray-500 dark:text-gray-400"
              >⌘W</span
            >
          </button>
          <div
            class="border-t-2 border-gray-300 dark:border-gray-600 my-0.5"
          ></div>
          <button
            class="w-full text-left px-3 py-1 hover:bg-blue-500 hover:text-white text-black dark:text-white text-sm"
            onclick={openAbout}
          >
            About uDOS
          </button>
        </div>
      {/if}
    </div>

    <!-- File Menu -->
    <div class="relative">
      <button
        class="px-2 py-1 hover:bg-blue-500 hover:text-white rounded transition"
        onclick={() => {
          closeAllMenus();
          showFileMenu = !showFileMenu;
        }}
      >
        File
      </button>
      {#if showFileMenu}
        <div
          class="absolute top-full left-0 mt-1 bg-white dark:bg-gray-800 border-2 border-gray-800 dark:border-gray-600 shadow-xl min-w-50"
          style="z-index: 10000;"
        >
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={() => menuAction("new")}
          >
            New... <span class="float-right text-gray-500 dark:text-gray-400"
              >⌘N</span
            >
          </button>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={() => menuAction("open")}
          >
            Open... <span class="float-right text-gray-500 dark:text-gray-400"
              >⌘O</span
            >
          </button>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={() => menuAction("browse")}
          >
            Browse Files... <span
              class="float-right text-gray-500 dark:text-gray-400">⌘B</span
            >
          </button>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={() => menuAction("save")}
          >
            Save <span class="float-right text-gray-500 dark:text-gray-400"
              >⌘S</span
            >
          </button>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={() => menuAction("save-as")}
          >
            Save As... <span
              class="float-right text-gray-500 dark:text-gray-400">⇧⌘S</span
            >
          </button>
          <div
            class="border-t-2 border-gray-300 dark:border-gray-600 my-1"
          ></div>

          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={() => menuAction("print")}
          >
            Print... <span class="float-right text-gray-500 dark:text-gray-400"
              >⌘P</span
            >
          </button>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={() => menuAction("export-pdf")}
          >
            Export PDF...
          </button>
        </div>
      {/if}
    </div>

    <!-- Edit Menu -->
    <div class="relative">
      <button
        class="px-2 py-1 hover:bg-blue-500 hover:text-white rounded transition"
        onclick={() => {
          closeAllMenus();
          showEditMenu = !showEditMenu;
        }}
      >
        Edit
      </button>
      {#if showEditMenu}
        <div
          class="absolute top-full left-0 mt-1 bg-white dark:bg-gray-800 border-2 border-gray-800 dark:border-gray-600 shadow-xl min-w-50"
          style="z-index: 10000;"
        >
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
          >
            Undo <span class="float-right text-gray-500 dark:text-gray-400"
              >⌘Z</span
            >
          </button>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
          >
            Redo <span class="float-right text-gray-500 dark:text-gray-400"
              >⇧⌘Z</span
            >
          </button>
          <div
            class="border-t-2 border-gray-300 dark:border-gray-600 my-1"
          ></div>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
          >
            Cut <span class="float-right text-gray-500 dark:text-gray-400"
              >⌘X</span
            >
          </button>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
          >
            Copy <span class="float-right text-gray-500 dark:text-gray-400"
              >⌘C</span
            >
          </button>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
          >
            Paste <span class="float-right text-gray-500 dark:text-gray-400"
              >⌘V</span
            >
          </button>
          <div
            class="border-t-2 border-gray-300 dark:border-gray-600 my-1"
          ></div>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={() => menuAction("format")}
          >
            Format Document <span
              class="float-right text-gray-500 dark:text-gray-400">⌘F</span
            >
          </button>
        </div>
      {/if}
    </div>

    <!-- View Menu -->
    <div class="relative">
      <button
        class="px-2 py-1 hover:bg-blue-500 hover:text-white rounded transition"
        onclick={() => {
          closeAllMenus();
          showViewMenu = !showViewMenu;
        }}
      >
        View
      </button>
      {#if showViewMenu}
        <div
          class="absolute top-full left-0 mt-1 bg-white dark:bg-gray-800 border-2 border-gray-800 dark:border-gray-600 shadow-xl min-w-55"
          style="z-index: 10000;"
        >
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={() => menuAction("toggle-sidebar")}
          >
            Toggle Sidebar <span
              class="float-right text-gray-500 dark:text-gray-400">⌘B</span
            >
          </button>
          <div
            class="border-t-2 border-gray-300 dark:border-gray-600 my-1"
          ></div>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={async () => {
              console.log("[MenuBar] Reset Display clicked");
              closeAllMenus();
              await import("@tauri-apps/api/event").then(({ emit }) => {
                console.log("[MenuBar] Emitting reset-mode-display event");
                return emit("reset-mode-display", {});
              });
              console.log("[MenuBar] Event emitted");
            }}
          >
            Reset Display
          </button>
          <div
            class="border-t-2 border-gray-300 dark:border-gray-600 my-1"
          ></div>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={() => {
              closeAllMenus();
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
            }}
          >
            Browser DevTools <span
              class="float-right text-gray-500 dark:text-gray-400">⌘⌥I</span
            >
          </button>
        </div>
      {/if}
    </div>

    <!-- Help Menu -->
    <div class="relative">
      <button
        class="px-2 py-1 hover:bg-blue-500 hover:text-white rounded transition"
        onclick={() => {
          closeAllMenus();
          showHelpMenu = !showHelpMenu;
        }}
      >
        Help
      </button>
      {#if showHelpMenu}
        <div
          class="absolute top-full left-0 mt-1 bg-white dark:bg-gray-800 border-2 border-gray-800 dark:border-gray-600 shadow-xl min-w-50"
          style="z-index: 10000;"
        >
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={openGitHubWiki}
          >
            uDOS Wiki
          </button>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={openGitHubFeedback}
          >
            Send Feedback
          </button>
          <div
            class="border-t-2 border-gray-300 dark:border-gray-600 my-1"
          ></div>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={openKeyboardShortcuts}
          >
            Keyboard Shortcuts
          </button>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
          >
            Check for Updates
          </button>
          <div
            class="border-t-2 border-gray-300 dark:border-gray-600 my-1"
          ></div>
          <button
            class="w-full text-left px-4 py-2 hover:bg-blue-500 hover:text-white text-black dark:text-white"
            onclick={openAbout}
          >
            About uDOS
          </button>
        </div>
      {/if}
    </div>
  </div>

  <!-- Right: Clock -->
  <div class="text-sm font-bold px-2">
    {currentTime}
  </div>
</header>

<!-- Click-away listener -->
{#if showModeMenu || showFileMenu || showEditMenu || showViewMenu || showHelpMenu}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="fixed inset-0 z-30" onclick={closeAllMenus}></div>
{/if}

<style>
  /* System 7 menu styling */
  button {
    user-select: none;
  }
</style>
