<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";
  import { emit, listen } from "@tauri-apps/api/event";

  interface MarkdownFile {
    path: string;
    name: string;
    is_dir: boolean;
    modified?: number;
    children?: MarkdownFile[];
  }

  interface Workspace {
    name: string;
    path: string;
  }

  interface Bookmark {
    path: string;
    name: string;
    timestamp: number;
    collection?: string;
  }

  interface BookmarkCollection {
    id: string;
    name: string;
  }

  interface RecentFile {
    path: string;
    name: string;
    timestamp: number;
  }

  interface Props {
    currentFilePath: string | null;
    onFileSelect: (path: string) => void;
    isOpen: boolean;
    onToggle?: () => void;
    mode?: "markdown" | "reader" | "table" | "desktop" | "slides";
  }

  let {
    currentFilePath,
    onFileSelect,
    isOpen,
    onToggle,
    mode = "markdown",
  }: Props = $props();

  // View mode for tabs
  type ViewMode = "files" | "bookmarks" | "recent";
  let viewMode = $state<ViewMode>("files");

  // Dark mode state
  let darkMode = $state(false);

  // Files state
  let allFiles: MarkdownFile[] = $state([]);
  let displayFiles: MarkdownFile[] = $state([]);
  let loading = $state(false);
  let searchQuery = $state("");

  // Workspace state
  let workspaces = $state<Workspace[]>([]);
  let currentWorkspace = $state<string>("");
  let workspaceDropdownOpen = $state(false);

  // Subfolder state
  let subfolders = $state<string[]>([]);
  let selectedSubfolder = $state<string>("");
  let subfolderDropdownOpen = $state(false);

  // Bookmarks state
  let bookmarks = $state<Bookmark[]>([]);
  let collections = $state<BookmarkCollection[]>([]);
  let selectedCollection = $state<string>("all"); // 'all' or collection id
  let collectionDropdownOpen = $state(false);

  // Recent files state
  let recentFiles = $state<RecentFile[]>([]);
  const MAX_RECENT_FILES = 20;

  let unlistenFileOpened: (() => void) | null = null;
  let unlistenDarkMode: (() => void) | null = null;

  // Get allowed file extensions based on mode
  const getAllowedExtensions = (): string[] => {
    switch (mode) {
      case "reader":
      case "slides":
        return [".md", ".markdown", ".txt", ".udos.md"];
      case "table":
        return [".csv", ".tsv", ".db", ".sqlite", ".json"];
      case "desktop":
        return [".md", ".udos.md"];
      case "markdown":
      default:
        return [".md", ".markdown", ".mdx", ".txt", ".udos.md"];
    }
  };

  // Check if file matches allowed extensions for current mode
  const isAllowedFile = (filename: string): boolean => {
    const extensions = getAllowedExtensions();
    const lower = filename.toLowerCase();
    return extensions.some((ext) => lower.endsWith(ext));
  };

  const defaultWorkspaces: Workspace[] = [
    // Paths are relative to project root, resolved by backend
    { name: "uDOS Root", path: "" },
    { name: "Sandbox", path: "memory/sandbox" },
    { name: "Inbox", path: "memory/inbox" },
    { name: "Memory", path: "memory" },
    { name: "Knowledge", path: "knowledge" },
    { name: "Wiki", path: "wiki" },
  ];

  // Folders to hide from Memory workspace (they have their own workspace entries)
  const hiddenMemoryFolders = ["sandbox", "inbox"];

  // === Bookmark Management ===

  const loadBookmarks = () => {
    const stored = localStorage.getItem("file-bookmarks");
    if (stored) {
      bookmarks = JSON.parse(stored);
    }
  };

  const saveBookmarks = () => {
    localStorage.setItem("file-bookmarks", JSON.stringify(bookmarks));
  };

  const isBookmarked = (filePath: string): boolean => {
    return bookmarks.some((b) => b.path === filePath);
  };

  const toggleBookmark = (file: MarkdownFile) => {
    const existingIndex = bookmarks.findIndex((b) => b.path === file.path);

    if (existingIndex >= 0) {
      // Remove bookmark
      bookmarks = bookmarks.filter((_, i) => i !== existingIndex);
    } else {
      // Add bookmark
      bookmarks = [
        ...bookmarks,
        {
          path: file.path,
          name: file.name,
          timestamp: Date.now(),
          collection:
            selectedCollection !== "all" &&
            selectedCollection !== "uncategorized"
              ? selectedCollection
              : undefined,
        },
      ];
    }

    saveBookmarks();
  };

  const removeBookmark = (path: string) => {
    bookmarks = bookmarks.filter((b) => b.path !== path);
    saveBookmarks();
  };

  // === Collection Management ===

  const loadCollections = () => {
    const stored = localStorage.getItem("bookmark-collections");
    if (stored) {
      collections = JSON.parse(stored);
    }
  };

  const saveCollections = () => {
    localStorage.setItem("bookmark-collections", JSON.stringify(collections));
  };

  const createCollection = (name: string) => {
    const id = `col_${Date.now()}`;
    collections = [...collections, { id, name }];
    saveCollections();
    return id;
  };

  const deleteCollection = (id: string) => {
    collections = collections.filter((c) => c.id !== id);
    // Remove collection from bookmarks
    bookmarks = bookmarks.map((b) => ({
      ...b,
      collection: b.collection === id ? undefined : b.collection,
    }));
    saveBookmarks();
    saveCollections();
  };

  const getFilteredBookmarks = (): Bookmark[] => {
    if (selectedCollection === "all") {
      return bookmarks;
    } else if (selectedCollection === "uncategorized") {
      return bookmarks.filter((b) => !b.collection);
    } else {
      return bookmarks.filter((b) => b.collection === selectedCollection);
    }
  };

  // === Recent Files Management ===

  const loadRecentFiles = () => {
    const stored = localStorage.getItem("recent-files");
    if (stored) {
      recentFiles = JSON.parse(stored);
    }
  };

  const saveRecentFiles = () => {
    localStorage.setItem("recent-files", JSON.stringify(recentFiles));
  };

  const trackRecentFile = (path: string, name: string) => {
    // Remove if already exists
    recentFiles = recentFiles.filter((f) => f.path !== path);

    // Add to front
    recentFiles = [{ path, name, timestamp: Date.now() }, ...recentFiles];

    // Limit to MAX_RECENT_FILES
    if (recentFiles.length > MAX_RECENT_FILES) {
      recentFiles = recentFiles.slice(0, MAX_RECENT_FILES);
    }

    saveRecentFiles();
  };

  const clearRecentFiles = () => {
    recentFiles = [];
    saveRecentFiles();
  };

  // Check if a file tree contains any .db or .sqlite files
  const hasDbFiles = (files: MarkdownFile[]): boolean => {
    for (const file of files) {
      if (file.is_dir && file.children) {
        if (hasDbFiles(file.children)) {
          return true;
        }
      } else if (!file.is_dir) {
        const lower = file.name.toLowerCase();
        if (lower.endsWith(".db") || lower.endsWith(".sqlite")) {
          return true;
        }
      }
    }
    return false;
  };

  // Filter workspaces to only show those with .db files in Table mode
  const getFilteredWorkspaces = (): Workspace[] => {
    if (mode !== "table") {
      return workspaces;
    }
    // In table mode, only show workspaces that have .db files
    return workspaces.filter((workspace) => {
      // Find the workspace's file data
      if (workspace.path === currentWorkspace && allFiles.length > 0) {
        return hasDbFiles(allFiles);
      }
      // For non-current workspaces, we can't filter them out without loading
      // So we show all workspaces in the dropdown, but they'll be empty if no .db files
      return true;
    });
  };

  // Derived state for filtered workspaces (prevent re-calculation on every render)
  let filteredWorkspaces = $derived(getFilteredWorkspaces());

  // Flatten all files recursively for display (filtered by mode)
  const flattenFiles = (
    files: MarkdownFile[],
    basePath: string = "",
  ): MarkdownFile[] => {
    let result: MarkdownFile[] = [];
    for (const file of files) {
      if (file.is_dir && file.children) {
        result = [...result, ...flattenFiles(file.children, file.path)];
      } else if (!file.is_dir && isAllowedFile(file.name)) {
        // Only include files matching current mode's extensions
        result.push(file);
      }
    }
    return result;
  };

  // Extract subfolders from file list (only show folders with allowed files for mode)
  // Now supports nested navigation - shows subfolders relative to selectedSubfolder
  const extractSubfolders = (
    files: MarkdownFile[],
    rootPath: string,
  ): string[] => {
    const folders = new Set<string>();
    const basePath = selectedSubfolder
      ? `${rootPath}/${selectedSubfolder}`
      : rootPath;

    const hasAllowedFiles = (items: MarkdownFile[]): boolean => {
      for (const item of items) {
        if (!item.is_dir && isAllowedFile(item.name)) {
          return true;
        }
        if (item.is_dir && item.children && hasAllowedFiles(item.children)) {
          return true;
        }
      }
      return false;
    };

    const processFiles = (items: MarkdownFile[]) => {
      for (const item of items) {
        if (item.is_dir && item.children) {
          // Only include folders that contain allowed files for this mode
          if (hasAllowedFiles(item.children)) {
            // Get relative path from current base (workspace root or selected subfolder)
            const relativePath = item.path
              .replace(basePath, "")
              .replace(/^\//, "");
            // Only show immediate child folders (no nested paths)
            if (relativePath && !relativePath.includes("/")) {
              // Store full path from workspace root for navigation
              const fullRelative = item.path
                .replace(rootPath, "")
                .replace(/^\//, "");
              folders.add(fullRelative);
            }
          }
          processFiles(item.children);
        }
      }
    };

    processFiles(files);

    // Filter out hidden folders if we're in Memory workspace
    let result = Array.from(folders);
    if (rootPath.endsWith("/memory")) {
      result = result.filter(
        (f) => !hiddenMemoryFolders.includes(f.split("/")[0]),
      );
    }
    return result.sort();
  };

  // Get display name for a subfolder (just the last part)
  const getSubfolderDisplayName = (fullPath: string): string => {
    const parts = fullPath.split("/");
    return parts[parts.length - 1];
  };

  // Get first-level subfolder from any path
  const getFirstLevelSubfolder = (path: string): string => {
    if (!path) return "";
    return path.split("/")[0];
  };

  // Get only first-level subfolders for dropdown
  const getFirstLevelSubfolders = (): string[] => {
    return subfolders.filter((f) => !f.includes("/"));
  };

  // Go back one level in subfolder navigation
  const goBackOneLevel = () => {
    if (!selectedSubfolder) return;
    const parts = selectedSubfolder.split("/");
    if (parts.length <= 1) {
      clearSubfolder();
    } else {
      parts.pop();
      selectSubfolder(parts.join("/"));
    }
  };

  // Filter files by subfolder and search query
  const filterBySubfolder = () => {
    let files = flattenFiles(allFiles);

    // In table mode, don't filter by subfolder - show all files with full paths
    if (mode !== "table") {
      // Apply subfolder filter for other modes
      if (selectedSubfolder && currentWorkspace) {
        const subfolderPath = `${currentWorkspace}/${selectedSubfolder}`;
        files = files.filter((f) => f.path.startsWith(subfolderPath));
      }
    }

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      files = files.filter(
        (f) =>
          f.name.toLowerCase().includes(query) ||
          f.path.toLowerCase().includes(query),
      );
    }

    displayFiles = files.sort((a, b) => a.name.localeCompare(b.name));
  };

  // Watch for filter changes - explicit dependencies to prevent loops
  $effect(() => {
    // Only re-run when these specific values change
    const _ = [
      selectedSubfolder,
      searchQuery,
      allFiles.length,
      currentWorkspace,
    ];
    filterBySubfolder();
  });

  const loadWorkspaces = () => {
    const stored = localStorage.getItem("workspaces");
    if (stored) {
      workspaces = JSON.parse(stored);
    } else {
      workspaces = defaultWorkspaces;
      localStorage.setItem("workspaces", JSON.stringify(workspaces));
    }

    const currentStored = localStorage.getItem("currentWorkspace");
    if (currentStored) {
      currentWorkspace = currentStored;
    } else if (workspaces.length > 0) {
      currentWorkspace = workspaces[0].path;
    }
  };

  const selectWorkspace = async (workspace: Workspace) => {
    currentWorkspace = workspace.path;
    localStorage.setItem("currentWorkspace", workspace.path);
    workspaceDropdownOpen = false;
    selectedSubfolder = "";
    searchQuery = "";
    await loadFiles(workspace.path);
  };

  const selectSubfolder = (folder: string) => {
    selectedSubfolder = folder;
    subfolderDropdownOpen = false;
    // Re-extract subfolders for nested navigation
    if (currentWorkspace && allFiles.length > 0) {
      subfolders = extractSubfolders(allFiles, currentWorkspace);
    }
    filterBySubfolder();
  };

  const clearSubfolder = () => {
    selectedSubfolder = "";
    subfolderDropdownOpen = false;
    // Re-extract subfolders for root level
    if (currentWorkspace && allFiles.length > 0) {
      subfolders = extractSubfolders(allFiles, currentWorkspace);
    }
    filterBySubfolder();
  };

  const loadFiles = async (dirPath: string) => {
    if (!dirPath) return;

    loading = true;
    try {
      // Use different Tauri command based on mode
      // For table mode, request specific file extensions
      let result: MarkdownFile[];

      if (mode === "table") {
        // Use the new command that supports custom extensions
        result = await invoke<MarkdownFile[]>("list_files_with_extensions", {
          dirPath,
          extensions: [".csv", ".tsv", ".db", ".sqlite", ".json", ".md"],
        });
      } else {
        // Use standard markdown file listing
        result = await invoke<MarkdownFile[]>("list_markdown_files", {
          dirPath,
        });
      }

      allFiles = result;
      subfolders = extractSubfolders(result, dirPath);
      filterBySubfolder();
    } catch (error) {
      console.error("Failed to load files:", error);
      allFiles = [];
      displayFiles = [];
      subfolders = [];
    } finally {
      loading = false;
    }
  };

  const browseFolder = async () => {
    try {
      const { open: openDialog } = await import("@tauri-apps/plugin-dialog");
      const selected = await openDialog({
        directory: true,
        multiple: false,
      });

      if (selected) {
        const path = selected as string;
        const name = path.split("/").pop() || "Custom";

        // Add to workspaces if not already there
        if (!workspaces.some((w) => w.path === path)) {
          workspaces = [...workspaces, { name, path }];
          localStorage.setItem("workspaces", JSON.stringify(workspaces));
        }

        await selectWorkspace({ name, path });
      }
    } catch (error) {
      console.error("Failed to browse folder:", error);
    }
  };

  const handleFileClick = (file: MarkdownFile) => {
    trackRecentFile(file.path, file.name);
    onFileSelect(file.path);
  };

  const handleBookmarkClick = (bookmark: Bookmark) => {
    trackRecentFile(bookmark.path, bookmark.name);
    onFileSelect(bookmark.path);
  };

  const handleRecentClick = (recent: RecentFile) => {
    onFileSelect(recent.path);
  };

  const getCurrentWorkspaceName = () => {
    const workspace = workspaces.find((w) => w.path === currentWorkspace);
    const name =
      workspace?.name || currentWorkspace.split("/").pop() || "Select...";

    // In table mode, show database count
    if (mode === "table" && displayFiles.length > 0) {
      return `${name} (${displayFiles.length})`;
    }

    return name;
  };

  const getRelativePath = (filePath: string): string => {
    if (!currentWorkspace) return filePath;
    return filePath.replace(currentWorkspace, "").replace(/^\//, "");
  };

  // File Action Functions
  const createNewFile = async () => {
    const fileName = prompt("Enter new file name:", "untitled.md");
    if (!fileName) return;

    const targetDir = selectedSubfolder
      ? `${currentWorkspace}/${selectedSubfolder}`
      : currentWorkspace;
    const newPath = `${targetDir}/${fileName}`;

    try {
      await invoke("write_file", {
        path: newPath,
        content: `# ${fileName.replace(/\.md$/, "")}\n\n`,
      });
      await loadFiles(currentWorkspace);
      onFileSelect(newPath);
    } catch (error) {
      console.error("Failed to create file:", error);
      alert("Failed to create file: " + error);
    }
  };

  const duplicateFile = async () => {
    if (!currentFilePath) return;

    const fileName = currentFilePath.split("/").pop() || "file.md";
    const baseName = fileName.replace(/\.md$/, "");
    const newName = prompt("Enter name for duplicate:", `${baseName}-copy.md`);
    if (!newName) return;

    const dir = currentFilePath.substring(0, currentFilePath.lastIndexOf("/"));
    const newPath = `${dir}/${newName}`;

    try {
      const content = await invoke<string>("read_file", {
        path: currentFilePath,
      });
      await invoke("write_file", { path: newPath, content });
      await loadFiles(currentWorkspace);
      onFileSelect(newPath);
    } catch (error) {
      console.error("Failed to duplicate file:", error);
      alert("Failed to duplicate file: " + error);
    }
  };

  const renameFile = async () => {
    if (!currentFilePath) return;

    const fileName = currentFilePath.split("/").pop() || "";
    const newName = prompt("Enter new name:", fileName);
    if (!newName || newName === fileName) return;

    const dir = currentFilePath.substring(0, currentFilePath.lastIndexOf("/"));
    const newPath = `${dir}/${newName}`;

    try {
      await invoke("rename_file", { oldPath: currentFilePath, newPath });
      await loadFiles(currentWorkspace);
      onFileSelect(newPath);
    } catch (error) {
      console.error("Failed to rename file:", error);
      alert("Failed to rename file: " + error);
    }
  };

  const moveFile = async () => {
    if (!currentFilePath) return;

    const fileName = currentFilePath.split("/").pop() || "";
    const availableFolders = ["archive", ...subfolders].filter((f) => f);
    const folderList = availableFolders.join(", ");
    const targetFolder = prompt(
      `Move to folder (${folderList}):`,
      selectedSubfolder || "",
    );
    if (targetFolder === null) return;

    const newPath = targetFolder
      ? `${currentWorkspace}/${targetFolder}/${fileName}`
      : `${currentWorkspace}/${fileName}`;

    if (newPath === currentFilePath) return;

    try {
      await invoke("rename_file", { oldPath: currentFilePath, newPath });
      await loadFiles(currentWorkspace);
      onFileSelect(newPath);
    } catch (error) {
      console.error("Failed to move file:", error);
      alert("Failed to move file: " + error);
    }
  };

  const archiveFile = async () => {
    if (!currentFilePath) return;

    const fileName = currentFilePath.split("/").pop() || "";
    if (
      !confirm(`Archive "${fileName}"? It will be moved to the archive folder.`)
    )
      return;

    const archivePath = `${currentWorkspace}/archive`;
    const newPath = `${archivePath}/${fileName}`;

    try {
      // Ensure archive folder exists
      await invoke("ensure_directory", { path: archivePath });
      await invoke("rename_file", { oldPath: currentFilePath, newPath });
      await loadFiles(currentWorkspace);
      // Clear selection since file was archived
      onFileSelect("");
    } catch (error) {
      console.error("Failed to archive file:", error);
      alert("Failed to archive file: " + error);
    }
  };

  onMount(async () => {
    // Load dark mode from localStorage
    const savedDarkMode = localStorage.getItem("darkMode");
    if (savedDarkMode === "true") {
      darkMode = true;
    }

    loadWorkspaces();
    loadBookmarks();
    loadCollections();
    loadRecentFiles();

    // Load view mode from localStorage
    const storedView = localStorage.getItem("sidebar-view");
    if (
      storedView &&
      (storedView === "files" ||
        storedView === "bookmarks" ||
        storedView === "recent")
    ) {
      viewMode = storedView as ViewMode;
    }

    if (currentWorkspace) {
      await loadFiles(currentWorkspace);
    }

    // Listen for file-opened events to track recent files
    unlistenFileOpened = await listen("file-opened", (event: any) => {
      const { path, name } = event.payload;
      if (path && name) {
        trackRecentFile(path, name);
      }
    });

    // Listen for dark mode changes
    unlistenDarkMode = await listen<{ darkMode: boolean }>(
      "dark-mode-changed",
      (event) => {
        darkMode = event.payload.darkMode;
      },
    );
  });

  // Watch for view mode changes
  $effect(() => {
    localStorage.setItem("sidebar-view", viewMode);
  });

  // Cleanup
  $effect(() => {
    return () => {
      if (unlistenFileOpened) {
        unlistenFileOpened();
      }
      if (unlistenDarkMode) {
        unlistenDarkMode();
      }
    };
  });
</script>

{#if isOpen}
  {@const bgClass =
    mode === "markdown"
      ? "bg-gray-100 dark:bg-gray-900"
      : mode === "reader"
        ? "bg-gray-900"
        : "bg-white dark:bg-gray-800"}
  <aside
    class="w-full {bgClass} border-r border-gray-200 dark:border-gray-700 flex flex-col h-full max-h-full overflow-hidden relative"
    style="z-index: 60;"
  >
    <!-- File Actions Toolbar (above tabs) - Hidden in Table mode -->
    {#if mode !== "table"}
      <div
        class="flex flex-wrap gap-1 p-2 border-b border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50"
      >
        <button
          class="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          onclick={createNewFile}
          title="Create new file"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 4v16m8-8H4"
            />
          </svg>
          New
        </button>
        <button
          class="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          onclick={duplicateFile}
          disabled={!currentFilePath}
          title="Duplicate current file"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
          Dupe
        </button>
        <button
          class="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          onclick={renameFile}
          disabled={!currentFilePath}
          title="Rename current file"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
            />
          </svg>
          Rename
        </button>
        <button
          class="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          onclick={moveFile}
          disabled={!currentFilePath}
          title="Move current file"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
            />
          </svg>
          Move
        </button>
        <button
          class="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          onclick={archiveFile}
          disabled={!currentFilePath}
          title="Archive current file"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"
            />
          </svg>
          Archive
        </button>
      </div>
    {/if}

    <!-- Tab Navigation -->
    <div class="flex border-b border-gray-200 dark:border-gray-700">
      <button
        class="flex-1 px-3 py-2 text-xs font-medium transition-colors {viewMode ===
        'files'
          ? 'bg-sky-100 dark:bg-sky-900/20 text-sky-600 dark:text-sky-400 border-b-2 border-sky-600 dark:border-sky-400'
          : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'}"
        onclick={() => (viewMode = "files")}
      >
        Files
      </button>
      <button
        class="flex-1 px-3 py-2 text-xs font-medium transition-colors {viewMode ===
        'bookmarks'
          ? 'bg-sky-100 dark:bg-sky-900/20 text-sky-600 dark:text-sky-400 border-b-2 border-sky-600 dark:border-sky-400'
          : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'}"
        onclick={() => (viewMode = "bookmarks")}
      >
        Bookmarks
      </button>
      <button
        class="flex-1 px-3 py-2 text-xs font-medium transition-colors {viewMode ===
        'recent'
          ? 'bg-sky-100 dark:bg-sky-900/20 text-sky-600 dark:text-sky-400 border-b-2 border-sky-600 dark:border-sky-400'
          : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'}"
        onclick={() => (viewMode = "recent")}
      >
        Recent
      </button>
    </div>

    <!-- Content based on view mode -->
    {#if viewMode === "files"}
      <!-- Workspace Selector Row -->
      <div class="p-2 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center gap-1">
          <!-- Workspace Dropdown -->
          <div class="relative flex-1">
            <button
              class="w-full flex items-center justify-between gap-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1.5 text-xs text-gray-900 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
              onclick={() => {
                workspaceDropdownOpen = !workspaceDropdownOpen;
                subfolderDropdownOpen = false;
              }}
            >
              <span class="truncate">{getCurrentWorkspaceName()}</span>
              <svg
                class="w-3 h-3 flex-shrink-0 {workspaceDropdownOpen
                  ? 'rotate-180'
                  : ''}"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>

            {#if workspaceDropdownOpen}
              <div
                class="absolute z-50 mt-1 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 shadow-lg max-h-48 overflow-y-auto"
              >
                {#each filteredWorkspaces as workspace}
                  <button
                    class="w-full text-left px-2 py-1.5 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 {currentWorkspace ===
                    workspace.path
                      ? 'bg-sky-100 dark:bg-sky-900/30 text-sky-600 dark:text-sky-400'
                      : 'text-gray-900 dark:text-gray-200'}"
                    onclick={() => selectWorkspace(workspace)}
                  >
                    {workspace.name}
                  </button>
                {/each}
              </div>
              <!-- Backdrop -->
              <div
                class="fixed inset-0 z-40"
                onclick={() => (workspaceDropdownOpen = false)}
                onkeydown={(e) =>
                  e.key === "Escape" && (workspaceDropdownOpen = false)}
                role="presentation"
              ></div>
            {/if}
          </div>

          <!-- Browse Icon Button -->
          <button
            class="p-1.5 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            onclick={browseFolder}
            title="Browse folder..."
          >
            <svg
              class="w-4 h-4 text-gray-600 dark:text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- Subfolder Filter - always show if we have subfolders OR are in a subfolder (hidden in Table mode) -->
      {#if mode !== "table" && (subfolders.length > 0 || selectedSubfolder)}
        {@const firstLevelFolders = getFirstLevelSubfolders()}
        {@const firstLevel = getFirstLevelSubfolder(selectedSubfolder)}
        {@const extraPath =
          selectedSubfolder && selectedSubfolder.includes("/")
            ? selectedSubfolder.substring(selectedSubfolder.indexOf("/") + 1)
            : ""}
        <div
          class="px-2 py-1.5 border-b border-gray-200 dark:border-gray-700 space-y-1"
        >
          <!-- First-level subfolder dropdown -->
          <div class="relative">
            <button
              class="w-full flex items-center justify-between gap-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800/50 px-2 py-1 text-xs text-gray-900 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              onclick={() => {
                subfolderDropdownOpen = !subfolderDropdownOpen;
                workspaceDropdownOpen = false;
              }}
            >
              <span class="truncate">
                {firstLevel ? `📁 ${firstLevel}` : "📂 All folders"}
              </span>
              <svg
                class="w-3 h-3 flex-shrink-0 {subfolderDropdownOpen
                  ? 'rotate-180'
                  : ''}"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>

            {#if subfolderDropdownOpen}
              <div
                class="absolute z-50 mt-1 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 shadow-lg max-h-48 overflow-y-auto"
              >
                <button
                  class="w-full text-left px-2 py-1.5 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 {!selectedSubfolder
                    ? 'bg-sky-100 dark:bg-sky-900/30 text-sky-600 dark:text-sky-400'
                    : 'text-gray-900 dark:text-gray-200'}"
                  onclick={clearSubfolder}
                >
                  📂 All folders
                </button>
                {#each firstLevelFolders as folder}
                  <button
                    class="w-full text-left px-2 py-1.5 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 {firstLevel ===
                    folder
                      ? 'bg-sky-100 dark:bg-sky-900/30 text-sky-600 dark:text-sky-400'
                      : 'text-gray-900 dark:text-gray-200'}"
                    onclick={() => selectSubfolder(folder)}
                  >
                    📁 {folder}
                  </button>
                {/each}
              </div>
              <!-- Backdrop -->
              <div
                class="fixed inset-0 z-40"
                onclick={() => (subfolderDropdownOpen = false)}
                onkeydown={(e) =>
                  e.key === "Escape" && (subfolderDropdownOpen = false)}
                role="presentation"
              ></div>
            {/if}
          </div>

          <!-- Extra subpath display (when deeper than 1 level) -->
          {#if extraPath}
            <div
              class="flex items-center gap-1 px-1 py-0.5 text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 rounded"
            >
              <span class="text-gray-400">↳</span>
              <span class="truncate">{extraPath}</span>
            </div>
          {/if}
        </div>
      {/if}

      <!-- Search -->
      <div class="px-2 py-1.5 border-b border-gray-200 dark:border-gray-700">
        <input
          type="text"
          placeholder="Filter files..."
          class="w-full px-2 py-1 text-xs bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-gray-900 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:border-sky-500 dark:focus:border-sky-500"
          bind:value={searchQuery}
        />
      </div>

      <!-- File Count -->
      <div
        class="px-2 py-1 text-xs text-gray-600 dark:text-gray-500 border-b border-gray-200 dark:border-gray-700"
      >
        {displayFiles.length} file{displayFiles.length !== 1 ? "s" : ""}
        {selectedSubfolder ? ` in ${selectedSubfolder}` : ""}
      </div>

      <!-- File List -->
      <div class="flex-1 overflow-auto min-h-0">
        {#if loading}
          <div class="p-4 text-center text-gray-600 dark:text-gray-500 text-sm">
            Loading...
          </div>
        {:else if displayFiles.length === 0}
          <div class="p-4 text-center text-gray-600 dark:text-gray-500 text-sm">
            {currentWorkspace
              ? mode === "table"
                ? "No database files found"
                : "No markdown files found"
              : "Select a workspace"}
          </div>
        {:else}
          {@const currentSubfolders =
            mode === "table"
              ? []
              : subfolders.filter((f) => {
                  if (!selectedSubfolder) {
                    // At root: show only top-level folders
                    return !f.includes("/");
                  } else {
                    // In subfolder: show only immediate children
                    return (
                      f.startsWith(selectedSubfolder + "/") &&
                      f.replace(selectedSubfolder + "/", "").indexOf("/") === -1
                    );
                  }
                })}
          {@const totalItems =
            currentSubfolders.length +
            displayFiles.length +
            (selectedSubfolder && mode !== "table" ? 1 : 0)}
          {@const useColumns = mode !== "table" && totalItems >= 8}
          <div class={useColumns ? "flex flex-wrap gap-0.5 p-1" : ""}>
            <!-- Back button when inside a subfolder (not in table mode) -->
            {#if selectedSubfolder && mode !== "table"}
              <button
                class="{useColumns
                  ? 'w-[calc(50%-2px)]'
                  : 'w-full'} flex items-center gap-2 px-2 py-1.5 hover:bg-yellow-100 dark:hover:bg-yellow-900/30 transition-colors rounded text-left bg-yellow-50 dark:bg-yellow-900/20"
                onclick={goBackOneLevel}
                title="Go back to parent folder"
              >
                <span class="text-base">⬅️</span>
                <span
                  class="text-sm truncate font-medium text-gray-700 dark:text-gray-300"
                  >Back</span
                >
              </button>
            {/if}
            <!-- Show subfolders as clickable items (not in table mode) -->
            {#if mode !== "table"}
              {#each currentSubfolders as folder}
                <button
                  class="{useColumns
                    ? 'w-[calc(50%-2px)]'
                    : 'w-full'} flex items-center gap-2 px-2 py-1.5 hover:bg-udos-primary/10 dark:hover:bg-udos-primary/20 transition-colors rounded text-left"
                  onclick={() => selectSubfolder(folder)}
                  title="Open {getSubfolderDisplayName(folder)} folder"
                >
                  <span class="text-base">📁</span>
                  <span
                    class="text-sm truncate font-medium text-gray-900 dark:text-gray-100"
                    >{getSubfolderDisplayName(folder)}</span
                  >
                </button>
              {/each}
            {/if}
            {#each displayFiles as file}
              <div
                class="{useColumns
                  ? 'w-[calc(50%-2px)]'
                  : 'w-full'} flex items-center justify-between px-2 py-1.5 hover:bg-udos-primary/10 dark:hover:bg-udos-primary/20 transition-colors rounded {currentFilePath ===
                file.path
                  ? 'bg-udos-primary/20 dark:bg-udos-primary/30 border-l-2 border-udos-primary'
                  : ''}"
              >
                <button
                  class="flex flex-col gap-0.5 flex-1 min-w-0 text-left"
                  onclick={() => handleFileClick(file)}
                  title={file.path}
                >
                  <div class="flex items-center gap-1.5">
                    <span
                      class="text-sm truncate font-medium text-gray-900 dark:text-gray-100"
                      title={file.name}>{file.name}</span
                    >
                  </div>
                  <div
                    class="text-[10px] text-gray-500 dark:text-gray-400 truncate pl-5"
                    title={getRelativePath(file.path)}
                  >
                    {getRelativePath(file.path)}
                  </div>
                </button>
                <button
                  class="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                  onclick={(e) => {
                    e.stopPropagation();
                    toggleBookmark(file);
                  }}
                  title={isBookmarked(file.path)
                    ? "Remove bookmark"
                    : "Add bookmark"}
                >
                  {#if isBookmarked(file.path)}
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      class="w-5 h-5 text-udos-primary"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M10 2c-1.716 0-3.408.106-5.07.31C3.806 2.45 3 3.414 3 4.517V17.25a.75.75 0 001.075.676L10 15.082l5.925 2.844A.75.75 0 0017 17.25V4.517c0-1.103-.806-2.068-1.93-2.207A41.403 41.403 0 0010 2z"
                        clip-rule="evenodd"
                      />
                    </svg>
                  {:else}
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke-width="1.5"
                      stroke="currentColor"
                      class="w-5 h-5"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z"
                      />
                    </svg>
                  {/if}
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {:else if viewMode === "bookmarks"}
      <!-- Collection Selector -->
      <div class="p-2 border-b border-gray-200 dark:border-gray-700">
        <div class="relative">
          <button
            class="w-full flex items-center justify-between gap-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1.5 text-xs text-gray-900 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
            onclick={() => {
              collectionDropdownOpen = !collectionDropdownOpen;
            }}
          >
            <span class="truncate">
              {#if selectedCollection === "all"}
                📚 All Bookmarks
              {:else if selectedCollection === "uncategorized"}
                📄 Uncategorized
              {:else}
                📁 {collections.find((c) => c.id === selectedCollection)
                  ?.name || "Collection"}
              {/if}
            </span>
            <svg
              class="w-3 h-3 flex-shrink-0 {collectionDropdownOpen
                ? 'rotate-180'
                : ''}"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>

          {#if collectionDropdownOpen}
            <div
              class="absolute z-50 mt-1 w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 shadow-lg max-h-48 overflow-y-auto"
            >
              <button
                class="w-full text-left px-2 py-1.5 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 {selectedCollection ===
                'all'
                  ? 'bg-sky-100 dark:bg-sky-900/30 text-sky-600 dark:text-sky-400'
                  : 'text-gray-900 dark:text-gray-200'}"
                onclick={() => {
                  selectedCollection = "all";
                  collectionDropdownOpen = false;
                }}
              >
                📚 All Bookmarks
              </button>
              <button
                class="w-full text-left px-2 py-1.5 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 {selectedCollection ===
                'uncategorized'
                  ? 'bg-sky-100 dark:bg-sky-900/30 text-sky-600 dark:text-sky-400'
                  : 'text-gray-900 dark:text-gray-200'}"
                onclick={() => {
                  selectedCollection = "uncategorized";
                  collectionDropdownOpen = false;
                }}
              >
                📄 Uncategorized
              </button>
              {#each collections as collection}
                <button
                  class="w-full text-left px-2 py-1.5 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 {selectedCollection ===
                  collection.id
                    ? 'bg-sky-100 dark:bg-sky-900/30 text-sky-600 dark:text-sky-400'
                    : 'text-gray-900 dark:text-gray-200'}"
                  onclick={() => {
                    selectedCollection = collection.id;
                    collectionDropdownOpen = false;
                  }}
                >
                  📁 {collection.name}
                </button>
              {/each}
            </div>
            <!-- Backdrop -->
            <div
              class="fixed inset-0 z-40"
              onclick={() => (collectionDropdownOpen = false)}
              onkeydown={(e) =>
                e.key === "Escape" && (collectionDropdownOpen = false)}
              role="presentation"
            ></div>
          {/if}
        </div>
      </div>

      <!-- Bookmark Count -->
      <div
        class="px-2 py-1 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700"
      >
        {getFilteredBookmarks().length} bookmark{getFilteredBookmarks()
          .length !== 1
          ? "s"
          : ""}
      </div>

      <!-- Bookmark List -->
      <div class="flex-1 overflow-y-auto min-h-0">
        {#if getFilteredBookmarks().length === 0}
          <div class="p-4 text-center text-gray-500 dark:text-gray-400 text-sm">
            No bookmarks yet. Click ☆ on files to bookmark them.
          </div>
        {:else}
          {#each getFilteredBookmarks() as bookmark}
            <div
              class="w-full flex items-center justify-between px-2 py-1.5 hover:bg-udos-primary/10 dark:hover:bg-udos-primary/20 transition-colors {currentFilePath ===
              bookmark.path
                ? 'bg-udos-primary/20 dark:bg-udos-primary/30 border-l-2 border-udos-primary'
                : ''}"
            >
              <button
                class="flex flex-col gap-0.5 flex-1 min-w-0 text-left"
                onclick={() => handleBookmarkClick(bookmark)}
                title={bookmark.path}
              >
                <div class="flex items-center gap-1.5">
                  <span
                    class="text-sm truncate font-medium text-gray-900 dark:text-gray-100"
                    title={bookmark.name}>{bookmark.name}</span
                  >
                </div>
                <div
                  class="text-[10px] text-gray-500 dark:text-gray-400 truncate pl-5"
                >
                  {bookmark.collection
                    ? `📁 ${collections.find((c) => c.id === bookmark.collection)?.name || ""}`
                    : ""}
                </div>
              </button>
              <button
                class="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                onclick={(e) => {
                  e.stopPropagation();
                  removeBookmark(bookmark.path);
                }}
                title="Remove bookmark"
              >
                <span class="text-lg">🗑️</span>
              </button>
            </div>
          {/each}
        {/if}
      </div>
    {:else if viewMode === "recent"}
      <!-- Recent Files Header -->
      <div
        class="px-2 py-1 text-xs text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between"
      >
        <span
          >{recentFiles.length} recent file{recentFiles.length !== 1
            ? "s"
            : ""}</span
        >
        {#if recentFiles.length > 0}
          <button
            class="text-xs text-sky-600 dark:text-sky-400 hover:underline"
          >
            Clear
          </button>
        {/if}
      </div>

      <!-- Recent Files List -->
      <div class="flex-1 overflow-y-auto min-h-0">
        {#if recentFiles.length === 0}
          <div class="p-4 text-center text-gray-500 dark:text-gray-400 text-sm">
            No recent files yet.
          </div>
        {:else}
          {#each recentFiles as recent}
            <button
              class="w-full text-left px-2 py-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex items-center justify-between {currentFilePath ===
              recent.path
                ? 'bg-sky-100 dark:bg-sky-900/40 border-l-2 border-sky-600 dark:border-sky-400'
                : ''}"
              onclick={() => handleRecentClick(recent)}
              title={recent.path}
            >
              <div class="flex flex-col gap-0.5 flex-1 min-w-0">
                <div class="flex items-center gap-1.5">
                  <span
                    class="text-sm truncate font-medium text-gray-900 dark:text-gray-100"
                    title={recent.name}>{recent.name}</span
                  >
                </div>
                <div
                  class="text-[10px] text-gray-500 dark:text-gray-400 truncate pl-5"
                >
                  {new Date(recent.timestamp).toLocaleString()}
                </div>
              </div>
            </button>
          {/each}
        {/if}
      </div>
    {/if}
  </aside>
{/if}
