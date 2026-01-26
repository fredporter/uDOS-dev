<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";

  interface Workspace {
    name: string;
    path: string;
  }

  let { onWorkspaceChange = (path: string) => {} } = $props();

  let workspaces = $state<Workspace[]>([]);
  let currentWorkspace = $state<string | null>(null);
  let isOpen = $state(false);
  let loading = $state(false);

  const defaultWorkspaces: Workspace[] = [
    // These will be populated from the API on mount
    // Paths are relative to project root, resolved by backend
    { name: "uDOS Root", path: "" },
    { name: "Sandbox", path: "memory/sandbox" },
    { name: "Inbox", path: "memory/inbox" },
    { name: "Memory", path: "memory" },
    { name: "Knowledge", path: "knowledge" },
    { name: "Wiki", path: "wiki" },
  ];

  const loadWorkspaces = async () => {
    try {
      // Load from localStorage
      const saved = localStorage.getItem("workspaces");
      if (saved) {
        workspaces = JSON.parse(saved);
      } else {
        workspaces = defaultWorkspaces;
      }

      // Load current workspace
      const current = localStorage.getItem("currentWorkspace");
      if (current) {
        currentWorkspace = current;
      } else if (workspaces.length > 0) {
        currentWorkspace = workspaces[0].path;
      }
    } catch (error) {
      console.error("Failed to load workspaces:", error);
      workspaces = defaultWorkspaces;
    }
  };

  const saveWorkspaces = () => {
    localStorage.setItem("workspaces", JSON.stringify(workspaces));
    if (currentWorkspace) {
      localStorage.setItem("currentWorkspace", currentWorkspace);
    }
  };

  const selectWorkspace = (workspace: Workspace) => {
    currentWorkspace = workspace.path;
    saveWorkspaces();
    onWorkspaceChange(workspace.path);
    isOpen = false;
  };

  const addCustomWorkspace = async () => {
    try {
      // Use Tauri dialog to select folder
      const selected = await invoke<string>("select_folder");
      if (selected) {
        const name = selected.split("/").pop() || "Custom Workspace";
        const newWorkspace = { name, path: selected };

        // Add if not already in list
        if (!workspaces.some((w) => w.path === selected)) {
          workspaces = [...workspaces, newWorkspace];
          saveWorkspaces();
        }

        selectWorkspace(newWorkspace);
      }
    } catch (error) {
      console.error("Failed to add workspace:", error);
    }
  };

  const removeWorkspace = (workspace: Workspace, event: Event) => {
    event.stopPropagation();
    workspaces = workspaces.filter((w) => w.path !== workspace.path);
    if (currentWorkspace === workspace.path && workspaces.length > 0) {
      selectWorkspace(workspaces[0]);
    }
    saveWorkspaces();
  };

  const getCurrentWorkspaceName = () => {
    const workspace = workspaces.find((w) => w.path === currentWorkspace);
    return workspace?.name || "Select Workspace";
  };

  onMount(() => {
    loadWorkspaces();
  });
</script>

<div class="relative">
  <!-- Dropdown Button -->
  <button
    class="flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-900 px-4 py-2 text-sm font-medium text-gray-200 transition hover:bg-gray-800 hover:border-gray-600"
    onclick={() => (isOpen = !isOpen)}
  >
    <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
      />
    </svg>
    <span class="max-w-[200px] truncate">{getCurrentWorkspaceName()}</span>
    <svg
      class="h-4 w-4 transition-transform {isOpen ? 'rotate-180' : ''}"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M19 9l-7 7-7-7"
      />
    </svg>
  </button>

  <!-- Dropdown Menu -->
  {#if isOpen}
    <!-- Backdrop -->
    <div
      class="fixed inset-0 z-30"
      onclick={() => (isOpen = false)}
      onkeydown={(e) => e.key === "Escape" && (isOpen = false)}
      role="presentation"
    ></div>
    <div
      class="absolute z-40 mt-2 w-72 rounded-lg border border-gray-700 bg-gray-900 shadow-xl"
    >
      <div class="p-2">
        <div
          class="mb-2 px-3 py-2 text-xs font-semibold uppercase tracking-wider text-gray-500"
        >
          Workspaces
        </div>

        <!-- Workspace List -->
        <div class="max-h-60 overflow-y-auto">
          {#each workspaces as workspace}
            <div
              class="flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm transition cursor-pointer
								{currentWorkspace === workspace.path
                ? 'bg-sky-900/30 text-sky-400'
                : 'text-gray-200 hover:bg-gray-800'}"
              onclick={() => selectWorkspace(workspace)}
              onkeydown={(e) => e.key === "Enter" && selectWorkspace(workspace)}
              role="button"
              tabindex="0"
            >
              <div class="flex items-center gap-2 flex-1 min-w-0">
                <svg
                  class="h-4 w-4 flex-shrink-0"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                  />
                </svg>
                <div class="text-left min-w-0 flex-1">
                  <div class="font-medium truncate">{workspace.name}</div>
                  <div class="text-xs text-gray-500 truncate">
                    {workspace.path}
                  </div>
                </div>
              </div>

              {#if workspaces.length > 1}
                <button
                  class="ml-2 flex-shrink-0 rounded p-1 text-gray-500 hover:bg-red-900/20 hover:text-red-400"
                  onclick={(e) => removeWorkspace(workspace, e)}
                  title="Remove workspace"
                >
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
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              {/if}
            </div>
          {/each}
        </div>

        <!-- Add Custom Workspace -->
        <div class="mt-2 border-t border-gray-800 pt-2">
          <button
            class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-400 transition hover:bg-gray-800 hover:text-gray-200"
            onclick={addCustomWorkspace}
          >
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
                d="M12 4v16m8-8H4"
              />
            </svg>
            <span>Add Custom Workspace</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Backdrop to close dropdown -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="fixed inset-0 z-30" onclick={() => (isOpen = false)}></div>
  {/if}
</div>
