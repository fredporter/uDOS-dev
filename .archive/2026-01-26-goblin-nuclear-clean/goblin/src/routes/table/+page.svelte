<script lang="ts">
  import DatabaseTable from "$lib/components/DatabaseTable.svelte";
  import FileSidebar from "$lib/components/FileSidebar.svelte";
  import { invoke } from "@tauri-apps/api/core";
  import { open as openDialog } from "@tauri-apps/plugin-dialog";
  import * as svg from "$lib/components/svg";
  import { listen, type UnlistenFn } from "@tauri-apps/api/event";
  import { onMount, onDestroy } from "svelte";
  import { getStateForMode, updateModeState } from "$lib/stores/modeState";
  import { getStyleState } from "$lib/services/styleManager";
  import { UButton, PageLayout } from "$lib";

  interface TableData {
    headers: string[];
    rows: { value: string; editable: boolean }[][];
  }

  let tableData = $state<TableData>({ headers: [], rows: [] });
  let currentFilePath = $state<string | null>(null);
  let filename = $state("");
  let sidebarOpen = $state(false);
  let loading = $state(false);
  let error = $state("");
  let unlisteners: UnlistenFn[] = [];
  let backgroundColor = $state(0);
  let isDarkMode = $state(false);
  let fontSize = $state(16);
  let fontFamily = $state(0);
  let editorBgColor = $state<string | null>(null);

  const bgColors = [
    "bg-white dark:bg-gray-950",
    "bg-teal-50 dark:bg-teal-950",
    "bg-sky-50 dark:bg-sky-950",
    "bg-indigo-50 dark:bg-indigo-950",
  ];

  const parseMarkdownTable = (content: string): TableData => {
    const lines = content.split("\n").filter((line) => line.trim());

    if (lines.length < 2) {
      throw new Error("Invalid table format");
    }

    // Parse headers
    const headers = lines[0]
      .split("|")
      .map((h) => h.trim())
      .filter((h) => h);

    // Skip separator line (line 1)
    // Parse data rows
    const rows = lines.slice(2).map((line) => {
      const cells = line
        .split("|")
        .map((c) => c.trim())
        .filter((_, i, arr) => i > 0 && i < arr.length - 1); // Skip leading/trailing pipes

      return cells.map((value) => ({
        value,
        editable: true,
      }));
    });

    return { headers, rows };
  };

  const toggleSidebar = () => {
    sidebarOpen = !sidebarOpen;
    // Save to mode state
    updateModeState("table", { sidebarOpen });
    // Emit to layout to sync indicator
    import("@tauri-apps/api/event").then(({ emit }) => {
      emit("sidebar-state-changed", { open: sidebarOpen });
    });
  };

  const openFileFromSidebar = async (filePath: string) => {
    try {
      loading = true;
      error = "";
      currentFilePath = filePath;
      filename = filePath.split("/").pop() || "";

      if (filePath.endsWith(".csv") || filePath.endsWith(".tsv")) {
        const content: string = await invoke("read_file", { path: filePath });
        tableData = parseMarkdownTable(content);
      } else if (filePath.endsWith(".db") || filePath.endsWith(".sqlite")) {
        error = "SQLite database viewing not yet implemented";
      } else if (filePath.endsWith(".json")) {
        const content: string = await invoke("read_file", { path: filePath });
        const data = JSON.parse(content);
        // Convert JSON array to table format
        if (Array.isArray(data) && data.length > 0) {
          const headers = Object.keys(data[0]);
          const rows = data.map((obj) =>
            headers.map((h) => ({ value: String(obj[h]), editable: false }))
          );
          tableData = { headers, rows };
        } else {
          error = "JSON must be an array of objects";
        }
      }
    } catch (err) {
      console.error("Failed to open file:", err);
      error = String(err);
    } finally {
      loading = false;
    }
  };

  const openFile = async () => {
    try {
      loading = true;
      error = "";

      const selected = await openDialog({
        multiple: false,
        directory: false,
        filters: [
          { name: "Markdown", extensions: ["md", "markdown"] },
          { name: "CSV", extensions: ["csv"] },
        ],
      });

      if (selected) {
        const filePath =
          typeof selected === "string" ? selected : (selected as any).path;
        const content = await invoke<string>("read_markdown_file", {
          path: filePath,
        });

        tableData = parseMarkdownTable(content);
        currentFilePath = filePath;
        filename = filePath.split("/").pop() || "Untitled";
      }
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to open file";
      console.error("Error opening file:", err);
    } finally {
      loading = false;
    }
  };

  const handleCellChange = async (
    rowIndex: number,
    colIndex: number,
    newValue: string
  ) => {
    // TODO: Implement save to file functionality
    console.log(`Cell changed: [${rowIndex},${colIndex}] = "${newValue}"`);

    // Could send to API for saving
    try {
      // await invoke('save_table_cell', {
      // 	path: currentFilePath,
      // 	row: rowIndex,
      // 	col: colIndex,
      // 	value: newValue
      // });
    } catch (err) {
      console.error("Failed to save cell:", err);
    }
  };

  const saveTable = async () => {
    if (!currentFilePath) return;

    try {
      // Convert table data back to markdown
      const header = "| " + tableData.headers.join(" | ") + " |";
      const separator =
        "| " + tableData.headers.map(() => "---").join(" | ") + " |";
      const rows = tableData.rows.map(
        (row) => "| " + row.map((cell) => cell.value).join(" | ") + " |"
      );

      const markdown = [header, separator, ...rows].join("\n");

      await invoke("write_markdown_file", {
        path: currentFilePath,
        content: markdown,
      });

      console.log("Table saved successfully");
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to save table";
      console.error("Error saving table:", err);
    }
  };

  onMount(async () => {
    // Load state from mode state
    const tableState = getStateForMode("table");
    isDarkMode = tableState.darkMode || false;
    fontSize = tableState.fontSize || 16;
    // Load sidebar state from mode state (not global localStorage)
    sidebarOpen = tableState.sidebarOpen ?? false;

    // Dark mode applied globally via styleManager; no direct toggle

    // Listen for background color change from GlobalBottomBar
    unlisteners.push(
      await listen<{ hex: string }>("change-color", (event) => {
        if (event.payload.hex) {
          editorBgColor = event.payload.hex;
        }
      })
    );

    // Listen for dark mode toggle
    unlisteners.push(
      await listen<{ darkMode: boolean }>("dark-mode-changed", (event) => {
        isDarkMode = event.payload.darkMode;
        // Layout updates styleManager; persist mode state only
        updateModeState("table", { darkMode: isDarkMode });
      })
    );

    // Listen for global toggle-sidebar event from bottom bar
    unlisteners.push(
      await listen<{ open: boolean }>("toggle-sidebar", (event) => {
        sidebarOpen = event.payload.open;
        // Save to mode state
        updateModeState("table", { sidebarOpen });
      })
    );

    // Listen for reset display to restore defaults
    unlisteners.push(
      await listen("reset-mode-display", async () => {
        // Reload from fresh mode state (layout has already reset it)
        const freshState = getStateForMode("table");
        backgroundColor = 0;
        editorBgColor = null;
        isDarkMode = freshState.darkMode;
        fontSize = freshState.fontSize;

        // No need to update mode state - layout already did resetModeDisplay()
      })
    );
  });

  onDestroy(() => {
    unlisteners.forEach((unlisten) => unlisten());
  });
</script>

<div
  class="flex h-full flex-col {bgColors[
    backgroundColor
  ]} text-gray-900 dark:text-gray-50 font-sans"
>
  <!-- Header (hidden when sidebar is open) -->
  {#if !sidebarOpen}
    <header
      class="flex items-center justify-between border-b border-gray-300 dark:border-gray-800 p-4"
    >
      <div class="flex items-center gap-1">
        <!-- Sidebar Toggle -->
        <button
          class="button"
          onclick={toggleSidebar}
          title="{sidebarOpen ? 'Close' : 'Open'} File Browser"
        >
          <svg.Table />
        </button>

        <button
          class="button"
          onclick={openFile}
          disabled={loading}
          title="Open Table"
        >
          <svg.Open />
          <span class="hidden lg:inline">Open</span>
        </button>

        {#if currentFilePath}
          <button class="button" onclick={saveTable} title="Save Table">
            <svg.Save />
            <span class="hidden lg:inline">Save</span>
          </button>
        {/if}

        {#if filename}
          <span class="text-sm text-gray-600 dark:text-gray-400 ml-2"
            >{filename}</span
          >
        {/if}

        {#if loading}
          <span class="text-sm text-sky-400 animate-pulse">Loading...</span>
        {/if}
      </div>

      <nav class="flex items-center gap-1">
        <a href="/editor" class="button" title="Editor">
          <svg.Edit />
          <span class="hidden lg:inline">Editor</span>
        </a>

        <a href="/desktop" class="button" title="Desktop">
          <svg
            class="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
            />
          </svg>
          <span class="hidden lg:inline">Read</span>
        </a>

        <a href="/" class="button" title="Home">
          <svg
            class="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
            />
          </svg>
          <span class="hidden lg:inline">Home</span>
        </a>
      </nav>
    </header>
  {/if}

  <!-- Flex container for sidebar + content -->
  <div class="flex flex-1 min-h-0 overflow-hidden relative">
    <!-- Sidebar: inline single column, takes 1/4 width when open -->
    {#if sidebarOpen}
      <div
        class="w-1/4 flex flex-col min-h-0 overflow-hidden bg-gray-900 border-r border-gray-700 shadow-xl"
      >
        <FileSidebar
          isOpen={sidebarOpen}
          {currentFilePath}
          onFileSelect={openFileFromSidebar}
          onToggle={toggleSidebar}
          mode="table"
        />
      </div>
    {/if}

    <!-- Main content - 3/4 width when sidebar is open -->
    <div class="flex-1 overflow-auto flex flex-col">
      <!-- Error Display -->
      {#if error}
        <div
          class="bg-red-900/20 border border-red-800 text-red-400 px-4 py-2 mx-4 mt-4 rounded-lg"
        >
          {error}
        </div>
      {/if}

      <!-- Main Content -->
      <main
        class="flex-1 overflow-auto p-6"
        style={editorBgColor
          ? `background-color: ${editorBgColor} !important;`
          : ""}
      >
        {#if tableData.rows.length > 0}
          <DatabaseTable
            bind:data={tableData}
            onCellChange={handleCellChange}
          />
        {:else}
          <div class="flex h-full items-center justify-center">
            <div class="text-center">
              <svg
                class="mx-auto h-16 w-16 text-gray-400 dark:text-gray-700 mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
              <h2 class="text-2xl font-bold mb-2">uDOS Table Viewer</h2>
              <p class="text-gray-600 dark:text-gray-400 mb-4">
                Open a markdown table file to view and edit data
              </p>
              <button class="button px-6 py-3" onclick={openFile}>
                <svg.Open />
                Open Table
              </button>
            </div>
          </div>
        {/if}
      </main>
    </div>
  </div>
</div>
