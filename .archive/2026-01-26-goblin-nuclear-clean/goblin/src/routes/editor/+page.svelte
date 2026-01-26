<script lang="ts">
  import { dev } from "$app/environment";
  import Metrics from "$lib/components/Metrics.svelte";
  import Slides from "$lib/components/Slides.svelte";
  import FileSidebar from "$lib/components/FileSidebar.svelte";
  import * as svg from "$lib/components/svg";
  import printCss from "$lib/styles/print.css?raw";
  import gettingStarted from "$lib/content/getting-started.md?raw";
  import { codeEval } from "$lib/util/codeEval";
  import { onMount, onDestroy, tick } from "svelte";
  import { invoke } from "@tauri-apps/api/core";
  import { listen, type UnlistenFn } from "@tauri-apps/api/event";
  import { open as openDialog } from "@tauri-apps/plugin-dialog";
  import { page } from "$app/stores";
  import {
    getLastFile,
    getStateForMode,
    updateModeState,
  } from "$lib/stores/modeState";
  import "$lib/styles/desktop-patterns.css";
  import { getStyleState } from "$lib/services/styleManager";

  let content = $state("");
  let html = $state("");
  let viewMode = $state(false);
  let textArea: HTMLTextAreaElement;
  let currentSlide = $state(0);
  let editorReady = $state(false);
  let file: File | null = $state(null);
  let fileHandle: FileSystemFileHandle | null;
  let currentFilePath = $state<string | null>(null);
  let sidebarOpen = $state(true);
  let backgroundPattern = $state("pattern-solid-white");
  let editorBgColor = $state<string | null>(null);
  let unlisteners: UnlistenFn[] = [];
  // When sidebar open, show 'code' or 'preview' (not both)
  let activePaneWhenSidebarOpen = $state<"code" | "preview">("preview");

  const fontSizes = [
    "prose-sm",
    "prose-base",
    "prose-lg",
    "prose-xl",
    "prose-2xl",
  ];
  // Tailwind Typography standard fonts only - bundled in /library/fonts/tailwind/
  const fontFamilies = ["font-sans", "font-serif", "font-mono"];
  // Original Typo code background colors (no grey patterns)
  const colors = {
    medium: ["bg-gray-500", "bg-teal-500", "bg-sky-500", "bg-indigo-500"],
    dark: ["bg-gray-900", "bg-teal-950", "bg-sky-950", "bg-indigo-950"],
  };
  const viewTypes = ["document", "slideshow"] as const;

  let preferences: {
    proseSizeIndex: number;
    fontFamily: number;
    color: number;
    viewType: (typeof viewTypes)[number];
  } = $state({
    proseSizeIndex: 1,
    fontFamily: 0,
    color: 0,
    viewType: "document",
  });

  const savePreferences = () => {
    const isDarkMode = getStyleState().darkMode;
    localStorage.setItem("preferences", JSON.stringify(preferences));
    updateModeState("markdown", {
      proseSizeIndex: preferences.proseSizeIndex,
      color: preferences.color,
      viewType: preferences.viewType,
      viewMode,
      darkMode: isDarkMode,
    });
  };
  const toggleSidebar = () => {
    sidebarOpen = !sidebarOpen;
    // Save to mode state (layout will sync via event)
    updateModeState("markdown", { sidebarOpen });
    // Emit to layout to sync indicator
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("sidebar-state-changed", { open: sidebarOpen });
    });
  };

  const changeViewType = async () => {
    if (preferences.viewType === "document") {
      preferences.viewType = "slideshow";
    } else {
      preferences.viewType = "document";
    }
    savePreferences();

    // Emit event to update bottom bar icon
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("read-view-type-changed", { viewType: preferences.viewType });
    });

    await tick();
    codeEval();
  };

  const changeColor = () => {
    if (preferences.color < colors.medium.length - 1) {
      preferences.color++;
    } else {
      preferences.color = 0;
    }
    savePreferences();
  };

  const newFile = async () => {
    content = "";
    currentFilePath = null;
    await onInput();
  };

  const open = async () => {
    try {
      const selected = await openDialog({
        multiple: false,
        filters: [{ name: "Markdown", extensions: ["md", "mdx", "markdown"] }],
      });
      if (selected) {
        currentFilePath = selected as string;
        content = await invoke<string>("read_markdown_file", {
          path: currentFilePath,
        });
        await onInput();

        // Emit file-opened event for recent files tracking
        import("@tauri-apps/api/event").then(({ emit }) => {
          emit("file-opened", {
            path: currentFilePath,
            name: currentFilePath!.split("/").pop() || "Untitled",
          });
        });
      }
    } catch (error) {
      console.error("Failed to open file:", error);
    }
  };

  const saveAs = async () => {
    try {
      const { save: saveDialog } = await import("@tauri-apps/plugin-dialog");
      const selected = await saveDialog({
        filters: [{ name: "Markdown", extensions: ["md", "mdx", "markdown"] }],
      });
      if (selected) {
        await invoke("write_markdown_file", { path: selected, content });
        currentFilePath = selected;
      }
    } catch (error) {
      console.error("Failed to save file:", error);
    }
  };

  const save = async () => {
    if (currentFilePath && !viewMode) {
      try {
        await invoke("write_markdown_file", { path: currentFilePath, content });
      } catch (error) {
        console.error("Failed to save:", error);
      }
    } else if (!currentFilePath) {
      // No file path yet, trigger Save As
      await saveAs();
    }
  };

  const toggleView = () => {
    // Simply toggle between edit and preview (view) mode
    viewMode = !viewMode;
    // Emit editing mode change
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("editing-mode-changed", { editing: !viewMode });
    });
  };

  const changeProseSize = (action: "increase" | "decrease") => {
    if (
      action === "increase" &&
      preferences.proseSizeIndex < fontSizes.length - 1
    ) {
      preferences.proseSizeIndex++;
    } else if (action === "decrease" && preferences.proseSizeIndex > 0) {
      preferences.proseSizeIndex--;
    }
    savePreferences();
  };

  const changeFontFamily = () => {
    preferences.fontFamily = (preferences.fontFamily + 1) % fontFamilies.length;
    savePreferences();
  };

  const onKeyUp = (e: KeyboardEvent) => {
    save();
    if (e.key === "i" && textArea) textArea.focus();
    if (e.key === "Escape") toggleView();
    else findCurrentSlide();
  };

  const fmt = async () => {
    if (!textArea) return;
    const { formatMd } = await import("$lib/util/formatMd");
    let sel = textArea.selectionStart - content.trim().length;
    content = await formatMd(content);
    sel += content.trim().length;
    await onInput();
    textArea.setSelectionRange(sel, sel);
  };

  const onKeyDown = (e: KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      fmt();
    }
  };

  let copyMarkdownSuccess = $state(false);
  let copyHtmlSuccess = $state(false);

  const copyMarkdown = async () => {
    try {
      await navigator.clipboard.writeText(content);
      copyMarkdownSuccess = true;
      setTimeout(() => (copyMarkdownSuccess = false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const copyHtml = async () => {
    try {
      await navigator.clipboard.writeText(html);
      copyHtmlSuccess = true;
      setTimeout(() => (copyHtmlSuccess = false), 2000);
    } catch (err) {
      console.error("Failed to copy HTML:", err);
    }
  };

  const printContent = () => {
    const printWindow = window.open("", "_blank");
    if (printWindow) {
      printWindow.document.write(
        `<html><head><title>Print</title><${""}style>${printCss}</style></head><body>`
      );
      printWindow.document.write(html);
      printWindow.document.write("</body></html>");
      printWindow.document.close();
      printWindow.onload = () => {
        printWindow.print();
        printWindow.onafterprint = () => {};
        printWindow.close();
      };
    }
  };

  const onInput = async () => {
    const { processor } = await import("$lib/util/md");
    html = processor.render(content ? content : gettingStarted.trim());
    await tick();
    codeEval();

    // Emit stats to layout for bottom bar
    const chars = content.length;
    const words = content
      .trim()
      .split(/\s+/)
      .filter((w) => w.length > 0).length;
    const readTime = Math.ceil(words / 200); // 200 words per minute

    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("document-stats", { chars, words, readTime });
      if (currentFilePath) {
        emit("current-file-changed", { path: currentFilePath });
      }
      emit("editing-mode-changed", { editing: !viewMode });
    });
  };

  const findCurrentSlide = () => {
    if (preferences.viewType === "slideshow" && !viewMode) {
      if (!textArea) return;
      const s = content.slice(0, textArea.selectionStart);
      let curr = s.split("\n\n---\n").length - 1;
      if (s.startsWith("---\n")) curr++;
      currentSlide = curr;
    }
  };

  const openFileFromSidebar = async (filePath: string) => {
    try {
      content = await invoke<string>("read_markdown_file", { path: filePath });
      currentFilePath = filePath;
      await onInput();

      // Emit file-opened event for recent files tracking
      import("@tauri-apps/api/event").then(({ emit }) => {
        emit("file-opened", {
          path: filePath,
          name: filePath.split("/").pop() || "Untitled",
        });
      });
    } catch (error) {
      console.error("Failed to open file:", error);
    }
  };

  onMount(async () => {
    // Safely get textarea reference - it might not exist yet if sidebar is open or in view mode
    const textAreaElement = document.querySelector("textarea");
    if (textAreaElement) {
      textArea = textAreaElement;
    }

    // Load from mode state first
    const editorState = getStateForMode("markdown");

    // Load preferences from localStorage first (legacy)
    const saved = localStorage.getItem("preferences");
    if (saved) {
      preferences = JSON.parse(saved);
    } else {
      // Load from mode state
      preferences = {
        proseSizeIndex: editorState.proseSizeIndex || 1,
        fontFamily: 0, // Default to first font
        color: editorState.color,
        viewType: editorState.viewType,
      };
      viewMode = editorState.viewMode;
      savePreferences();
    }

    // Dark mode applied globally by layout/styleManager; reflect local state
    const isDarkMode = editorState.darkMode ?? getStyleState().darkMode;

    // Load sidebar state from mode state (not global localStorage)
    sidebarOpen = editorState.sidebarOpen ?? true;

    // Listen for menu events from Tauri
    unlisteners.push(await listen("menu-new", () => newFile()));
    unlisteners.push(await listen("menu-open", () => open()));
    unlisteners.push(await listen("menu-browse", () => toggleSidebar()));
    unlisteners.push(await listen("menu-save", () => save()));
    unlisteners.push(await listen("menu-save-as", () => saveAs()));
    unlisteners.push(await listen("menu-print", () => printContent()));
    unlisteners.push(await listen("menu-format", () => fmt()));
    unlisteners.push(await listen("menu-format", () => fmt()));
    unlisteners.push(
      await listen("file-open", (event) => {
        const filePath = event.payload as string;
        openFileFromSidebar(filePath);
      })
    );

    // Listen for background pattern changes from GlobalBottomBar
    unlisteners.push(
      await listen<{ pattern: string }>(
        "background-pattern-changed",
        (event) => {
          backgroundPattern = event.payload.pattern;
        }
      )
    );

    // Listen for edit/view mode changes from bottom bar
    unlisteners.push(
      await listen<{ isEditing: boolean }>("edit-mode-changed", (event) => {
        viewMode = !event.payload.isEditing; // viewMode true = view only
      })
    );

    // Listen for editor background color changes from GlobalBottomBar
    unlisteners.push(
      await listen<{ hex: string }>("change-color", (event) => {
        editorBgColor = event.payload.hex;
      })
    );

    // Check for file parameter in URL or load last file
    const fileParam = $page.url.searchParams.get("file");
    const viewParam = $page.url.searchParams.get("view");
    const lastFile = getLastFile();

    if (fileParam) {
      try {
        content = await invoke<string>("read_markdown_file", {
          path: fileParam,
        });
        currentFilePath = fileParam;

        // Set view type if specified in URL
        if (viewParam === "slideshow") {
          preferences.viewType = "slideshow";
          savePreferences();
        }
      } catch (error) {
        console.error("Failed to open file from URL:", error);
      }
    } else if (lastFile) {
      // Restore last file if no param specified
      try {
        content = await invoke<string>("read_markdown_file", {
          path: lastFile,
        });
        currentFilePath = lastFile;
      } catch (error) {
        console.error("Failed to restore last file:", error);
        // Fall back to getting started
        if (!content) content = gettingStarted;
      }
    } else if (!content) {
      // No file - show getting started
      content = gettingStarted;
    }

    // Listen for global toggle-sidebar event from bottom bar
    unlisteners.push(
      await listen<{ open: boolean }>("toggle-sidebar", (event) => {
        sidebarOpen = event.payload.open;
        // Save to mode state
        updateModeState("markdown", { sidebarOpen });
      })
    );

    // Listen for toggle-edit event from GlobalBottomBar
    unlisteners.push(
      await listen("toggle-edit", () => {
        toggleView();
      })
    );

    // Listen for editing-mode-changed event from layout
    unlisteners.push(
      await listen<{ editing: boolean }>("editing-mode-changed", (event) => {
        viewMode = !event.payload.editing;
      })
    );

    // Listen for view type toggle from GlobalBottomBar
    unlisteners.push(
      await listen("toggle-view-type", () => {
        changeViewType();
      })
    );

    // Listen for color change from GlobalBottomBar
    unlisteners.push(
      await listen("change-color", () => {
        changeColor();
      })
    );

    // Listen for dark mode toggle
    unlisteners.push(
      await listen<{ darkMode: boolean }>("dark-mode-changed", (event) => {
        // Layout updates styleManager; persist mode state only
        savePreferences();
      })
    );

    // Listen for reset display to restore defaults
    unlisteners.push(
      await listen("reset-mode-display", async () => {
        console.log("[Editor] Reset display triggered");

        // Clear localStorage to remove all persisted overrides
        localStorage.removeItem("preferences");

        // Reload from fresh mode state (layout has already reset it)
        const freshState = getStateForMode("markdown");

        // Mutate properties directly for Svelte 5 reactivity
        preferences.proseSizeIndex = freshState.proseSizeIndex || 1;
        preferences.fontFamily = 0;
        preferences.color = freshState.color || 0;
        preferences.viewType = freshState.viewType || "document";
        viewMode = freshState.viewMode || false;
        editorBgColor = null;

        console.log("[Editor] Preferences reset to:", preferences);
        console.log("[Editor] editorBgColor cleared:", editorBgColor);

        // Save the fresh defaults
        savePreferences();

        // Force DOM update
        await tick();
        await onInput();
      })
    );

    await onInput();

    await import("drab/editor/define");
    await import("drab/fullscreen/define");
    await import("drab/share/define");

    // Allow DOM to settle before mounting drab-editor
    await tick();
    editorReady = true;
  });

  onDestroy(() => {
    // Clean up event listeners
    unlisteners.forEach((unlisten) => unlisten());
  });
</script>

<svelte:document onkeyup={onKeyUp} onkeydown={onKeyDown} />

<div
  class="flex flex-col h-full overflow-hidden bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-50 selection:bg-gray-400/40 {fontFamilies[
    preferences.fontFamily
  ]}"
>
  <!-- Main Content Area -->
  <main class="flex flex-1 min-h-0 overflow-hidden {backgroundPattern}">
    <div class="flex flex-1 min-h-0 overflow-hidden">
      <!-- Grid layout: Filepicker (optional) | Editor/Preview -->
      <div class="flex-1 flex min-h-0 overflow-hidden">
        <!-- Filepicker (independent of viewMode) -->
        {#if sidebarOpen}
          <div class="w-1/2 flex flex-col min-h-0 overflow-hidden">
            <FileSidebar
              isOpen={sidebarOpen}
              {currentFilePath}
              onFileSelect={openFileFromSidebar}
              onToggle={toggleSidebar}
              mode="markdown"
            />
          </div>
        {/if}

        <!-- Editor/Preview Area (takes remaining space) -->
        <div
          class="flex-1 flex min-h-0 overflow-hidden"
          class:w-full={!sidebarOpen}
        >
          <div
            class="grid flex-1 min-h-0 overflow-hidden {!viewMode &&
              'lg:grid-cols-2'}"
          >
            {#if !viewMode}
              <!-- Code Editor -->
              <div class="flex flex-col min-h-0 overflow-hidden">
                <!-- Toolbar buttons at top of code editor -->
                <div
                  class="flex flex-wrap gap-1 border-b border-gray-300 dark:border-gray-800 p-2 bg-gray-100 dark:bg-gray-900"
                >
                  <!-- File Toggle (first button on LHS) -->
                  <button
                    title="Toggle File Picker (⌘B)"
                    class="button {sidebarOpen
                      ? 'bg-gray-200 dark:bg-gray-700'
                      : ''}"
                    onclick={toggleSidebar}
                  >
                    <!-- svelte-ignore component_name_lowercase -->
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      class="h-5 w-5"
                    >
                      <path
                        d="M4.75 3A1.75 1.75 0 003 4.75v2.752l.104-.002h13.792c.035 0 .07 0 .104.002V6.75A1.75 1.75 0 0015.25 5h-3.836a.25.25 0 01-.177-.073L9.823 3.513A1.75 1.75 0 008.586 3H4.75zM3.104 9a1.75 1.75 0 00-1.673 2.265l1.385 4.5A1.75 1.75 0 004.488 17h11.023a1.75 1.75 0 001.673-1.235l1.384-4.5A1.75 1.75 0 0016.896 9H3.104z"
                      ></path>
                    </svg>
                    <span class="hidden lg:inline">Files</span>
                  </button>

                  <!-- Edit/View Toggle (second button on LHS) -->
                  <button
                    title="Toggle Edit/View Mode"
                    class="button {viewMode
                      ? 'bg-teal-600 dark:bg-teal-700'
                      : ''}"
                    onclick={toggleView}
                  >
                    <!-- svelte-ignore component_name_lowercase -->
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      class="h-5 w-5"
                    >
                      {#if viewMode}
                        <path d="M10 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z"
                        ></path>
                        <path
                          fill-rule="evenodd"
                          d="M.664 10.59a1.651 1.651 0 010-1.186A10.004 10.004 0 0110 3c4.257 0 7.893 2.66 9.336 6.41.147.381.146.804 0 1.186A10.004 10.004 0 0110 17c-4.257 0-7.893-2.66-9.336-6.41zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                          clip-rule="evenodd"
                        ></path>
                      {:else}
                        <path
                          d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"
                        ></path>
                      {/if}
                    </svg>
                    <span class="hidden lg:inline"
                      >{viewMode ? "View" : "Edit"}</span
                    >
                  </button>

                  <!-- Separator -->
                  <div class="w-px h-6 bg-gray-300 dark:bg-gray-700"></div>

                  <!-- Background Color Toggle -->
                  <button
                    title="Change Background Color"
                    class="button"
                    onclick={changeColor}
                  >
                    <div
                      class="h-5 w-5 rounded border-2 border-gray-400 dark:border-gray-600 {colors
                        .medium[preferences.color]}"
                    ></div>
                    <span class="hidden lg:inline">Color</span>
                  </button>

                  <button
                    title="Open File... (⌘O)"
                    class="button"
                    onclick={open}
                  >
                    <!-- svelte-ignore component_name_lowercase -->
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      class="h-5 w-5"
                    >
                      <path
                        d="M4.75 3A1.75 1.75 0 003 4.75v2.752l.104-.002h13.792c.035 0 .07 0 .104.002V6.75A1.75 1.75 0 0015.25 5h-3.836a.25.25 0 01-.177-.073L9.823 3.513A1.75 1.75 0 008.586 3H4.75zM3.104 9a1.75 1.75 0 00-1.673 2.265l1.385 4.5A1.75 1.75 0 004.488 17h11.023a1.75 1.75 0 001.673-1.235l1.384-4.5A1.75 1.75 0 0016.896 9H3.104z"
                      ></path>
                    </svg>
                    <span class="hidden lg:inline">Open</span>
                  </button>
                  <button
                    title="Save As... (⌘⇧S)"
                    class="button"
                    onclick={saveAs}
                  >                    <!-- svelte-ignore component_name_lowercase -->                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      class="h-5 w-5"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M2 4.75C2 3.784 2.784 3 3.75 3h4.836c.464 0 .909.184 1.237.513l1.414 1.414a.25.25 0 00.177.073h4.836c.966 0 1.75.784 1.75 1.75v8.5A1.75 1.75 0 0116.25 17H3.75A1.75 1.75 0 012 15.25V4.75zm8.75 4a.75.75 0 00-1.5 0v2.546l-.943-1.048a.75.75 0 10-1.114 1.004l2.25 2.5a.75.75 0 001.114 0l2.25-2.5a.75.75 0 10-1.114-1.004l-.943 1.048V8.75z"
                        clip-rule="evenodd"
                      ></path>
                    </svg>
                    <span class="hidden lg:inline">Save As</span>
                  </button>
                  <button
                    title="Copy Markdown"
                    class="button"
                    onclick={copyMarkdown}
                  >
                    <!-- svelte-ignore component_name_lowercase -->
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      class="h-5 w-5"
                    >
                      <path
                        d="M7 3.5A1.5 1.5 0 018.5 2h3.879a1.5 1.5 0 011.06.44l3.122 3.12A1.5 1.5 0 0117 6.622V12.5a1.5 1.5 0 01-1.5 1.5h-1v-3.379a3 3 0 00-.879-2.121L10.5 5.379A3 3 0 008.379 4.5H7v-1z"
                      ></path>
                      <path
                        d="M4.5 6A1.5 1.5 0 003 7.5v9A1.5 1.5 0 004.5 18h7a1.5 1.5 0 001.5-1.5v-5.879a1.5 1.5 0 00-.44-1.06L9.44 6.439A1.5 1.5 0 008.378 6H4.5z"
                      ></path>
                    </svg>
                    <span class="hidden lg:inline"
                      >{copyMarkdownSuccess ? "✓ Copied!" : "Copy MD"}</span
                    >
                  </button>
                  <button title="Copy HTML" class="button" onclick={copyHtml}>
                    <!-- svelte-ignore component_name_lowercase -->
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      class="h-5 w-5"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M4.5 2A2.5 2.5 0 002 4.5v11A2.5 2.5 0 004.5 18h11a2.5 2.5 0 002.5-2.5v-11A2.5 2.5 0 0015.5 2h-11zm3.544 1.5a.5.5 0 01.353.146l1.5 1.5a.5.5 0 010 .708l-1.5 1.5a.5.5 0 01-.708-.708l.647-.646H5a.5.5 0 010-1h3.336l-.647-.646a.5.5 0 01.355-.854zm4.912 0a.5.5 0 01.353.854l-.647.646H16a.5.5 0 010 1h-3.336l.647.646a.5.5 0 01-.708.708l-1.5-1.5a.5.5 0 010-.708l1.5-1.5a.5.5 0 01.353-.146zM5.5 9A.5.5 0 015 9.5v6a.5.5 0 00.5.5h9a.5.5 0 00.5-.5v-6A.5.5 0 0014.5 9h-9z"
                        clip-rule="evenodd"
                      ></path>
                    </svg>
                    <span class="hidden lg:inline"
                      >{copyHtmlSuccess ? "✓ Copied!" : "Copy HTML"}</span
                    >
                  </button>
                  <button title="Print" class="button" onclick={printContent}>
                    <!-- svelte-ignore component_name_lowercase -->
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      class="h-5 w-5"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M5 2.75C5 1.784 5.784 1 6.75 1h6.5c.966 0 1.75.784 1.75 1.75v3.552c.377.046.752.097 1.126.153A2.212 2.212 0 0118 8.653v4.097A2.25 2.25 0 0115.75 15h-.241l.305 1.984A1.75 1.75 0 0114.084 19H5.915a1.75 1.75 0 01-1.73-2.016L4.492 15H4.25A2.25 2.25 0 012 12.75V8.653c0-1.082.775-2.034 1.874-2.198.374-.056.75-.107 1.127-.153L5 2.75zm8.5 3.397a41.533 41.533 0 00-7 0V2.75a.25.25 0 01.25-.25h6.5a.25.25 0 01.25.25v3.397zM6.608 12.5a.25.25 0 00-.247.212l-.693 4.5a.25.25 0 00.247.288h8.17a.25.25 0 00.246-.288l-.692-4.5a.25.25 0 00-.247-.212H6.608z"
                        clip-rule="evenodd"
                      ></path>
                    </svg>
                    <span class="hidden lg:inline">Print</span>
                  </button>
                  <button
                    title="Format Document (⌘S)"
                    class="button"
                    onclick={fmt}
                  >                    <!-- svelte-ignore component_name_lowercase -->                    <svg
                      class="h-5 w-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M4 6h16M4 12h16m-7 6h7"
                      />
                    </svg>
                    <span class="hidden lg:inline">Format</span>
                  </button>
                </div>
                {#if editorReady}
                  <drab-editor
                    class="flex-1 overflow-hidden {colors.medium[
                      preferences.color
                    ]}"
                  >
                    <textarea
                      class="h-full w-full resize-none bg-transparent p-4 font-mono text-base leading-normal text-gray-900 outline-none dark:text-gray-50"
                      style={editorBgColor
                        ? `background-color: ${editorBgColor} !important;`
                        : ""}
                      bind:value={content}
                      oninput={onInput}
                      spellcheck="false"
                    ></textarea>
                    <div class="flex flex-wrap gap-0.5 border-t p-0.5">
                      <button
                        data-trigger
                        class="button"
                        title="Heading"
                        data-value="#"
                        data-type="line">H</button
                      >
                      <button
                        data-trigger
                        class="button"
                        title="Unordered List"
                        data-value="-"
                        data-type="line">•</button
                      >
                      <button
                        data-trigger
                        class="button"
                        title="Ordered List"
                        data-value="1."
                        data-type="line">1.</button
                      >
                      <button
                        data-trigger
                        class="button"
                        title="Task"
                        data-value="- [ ]"
                        data-type="line">☐</button
                      >
                      <button
                        data-trigger
                        class="button"
                        title="Blockquote"
                        data-value=">"
                        data-type="line">❝</button
                      >
                      <button
                        data-trigger
                        class="button"
                        title="Code Block"
                        data-value="```"
                        data-type="block">{"{ }"}</button
                      >
                      <button
                        data-trigger
                        class="button"
                        title="Divider"
                        data-value="---"
                        data-type="block">―</button
                      >
                      <button
                        data-trigger
                        class="button"
                        title="Bold"
                        data-value="**"
                        data-type="inline"><strong>B</strong></button
                      >
                      <button
                        data-trigger
                        class="button"
                        title="Italic"
                        data-value="_"
                        data-type="inline"><em>I</em></button
                      >
                      <button
                        data-trigger
                        class="button"
                        title="Strikethrough"
                        data-value="~~"
                        data-type="inline"><s>S</s></button
                      >
                      <button
                        data-trigger
                        class="button"
                        title="Link"
                        data-value="[]()"
                        data-type="inline">🔗</button
                      >
                    </div>
                  </drab-editor>
                {:else}
                  <div
                    class="flex-1 overflow-hidden {colors.medium[
                      preferences.color
                    ]} flex items-center justify-center"
                  >
                    <div class="text-gray-500">Loading editor...</div>
                  </div>
                {/if}
              </div>
            {/if}

            <!-- Preview Area (always visible, right half in split mode) -->
            <div
              class="flex flex-col min-h-0 overflow-y-auto bg-white dark:bg-gray-950"
              class:dark:border-none={preferences.viewType === "slideshow" &&
                viewMode}
            >
              <div
                class="prose dark:prose-invert prose-img:rounded-lg mx-auto max-w-[72ch] break-words {fontSizes[
                  preferences.proseSizeIndex
                ]}"
              >
                {#if preferences.viewType === "document"}
                  <div class="p-8">{@html html}</div>
                {:else}
                  <Slides bind:viewMode bind:currentSlide {html} />
                {/if}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</div>
