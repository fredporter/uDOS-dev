<script lang="ts">
  import { goto } from "$app/navigation";

  interface FlyinProps {
    open?: boolean;
    onClose?: () => void;
  }

  type CommandKind = "mode" | "command";

  interface CommandItem {
    label: string;
    action: string;
    type: CommandKind;
    keywords: string;
    icon?: string;
  }

  const quickCommands: CommandItem[] = [
    {
      label: "New Document",
      action: "new-doc",
      type: "command",
      keywords: "create doc file",
      icon: "＋",
    },
    {
      label: "Open File",
      action: "open-file",
      type: "command",
      keywords: "open file load",
      icon: "📂",
    },
    {
      label: "Grid Mode",
      action: "/grid",
      type: "mode",
      keywords: "grid layout view",
      icon: "#",
    },
    {
      label: "Library",
      action: "/library",
      type: "mode",
      keywords: "library docs",
      icon: "📚",
    },
  ];

  let { open = false, onClose }: FlyinProps = $props();
  let query = $state("");
  let results = $state<CommandItem[]>(quickCommands);
  let selectedIndex = $state(0);
  let inputRef = $state<HTMLInputElement | null>(null);

  // Filter results when query changes
  $effect(() => {
    const lower = query.trim().toLowerCase();
    results = lower
      ? quickCommands.filter(
          (cmd) =>
            cmd.label.toLowerCase().includes(lower) ||
            cmd.keywords.toLowerCase().includes(lower)
        )
      : quickCommands;
    selectedIndex = 0;
  });

  // Focus input when opened
  $effect(() => {
    if (open && inputRef) {
      setTimeout(() => inputRef?.focus(), 50);
    }
  });

  function handleKeydown(e: KeyboardEvent) {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        selectedIndex = Math.min(selectedIndex + 1, results.length - 1);
        break;
      case "ArrowUp":
        e.preventDefault();
        selectedIndex = Math.max(selectedIndex - 1, 0);
        break;
      case "Enter":
        e.preventDefault();
        if (results[selectedIndex]) {
          executeAction(results[selectedIndex]);
        }
        break;
      case "Escape":
        e.preventDefault();
        close();
        break;
    }
  }

  function executeAction(item: CommandItem) {
    if (item.type === "mode" || item.action.startsWith("/")) {
      goto(item.action);
    } else {
      switch (item.action) {
        case "new-doc":
          goto("/editor?new=true");
          break;
        case "open-file":
          window.dispatchEvent(new CustomEvent("flyin-open-file"));
          break;
      }
    }
    close();
  }

  function close() {
    query = "";
    onClose?.();
  }
</script>

{#if open}
  <div
    class="fixed inset-0 bg-black/50 z-40"
    onclick={close}
    onkeydown={(e) => e.key === "Escape" && close()}
    role="button"
    tabindex="-1"
  ></div>

  <div class="fixed top-20 left-1/2 -translate-x-1/2 w-full max-w-xl z-50">
    <div class="bg-udos-surface rounded-xl shadow-2xl border border-gray-700 overflow-hidden">
      <div class="p-4 border-b border-gray-700">
        <div class="flex items-center gap-3">
          <svg
            class="w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            bind:this={inputRef}
            bind:value={query}
            onkeydown={handleKeydown}
            type="text"
            placeholder="Search commands, modes, actions..."
            class="flex-1 bg-transparent outline-none text-lg placeholder-gray-500"
          />
          <kbd class="px-2 py-1 text-xs bg-gray-700 rounded">esc</kbd>
        </div>
      </div>

      <div class="max-h-80 overflow-y-auto">
        {#if results.length === 0}
          <div class="p-4 text-center text-gray-400">
            No results found for "{query}"
          </div>
        {:else}
          {#each results as item, i}
            <button
              class={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                i === selectedIndex ? "bg-udos-primary/20" : "hover:bg-gray-700/50"
              }`}
              onclick={() => executeAction(item)}
              onmouseenter={() => (selectedIndex = i)}
            >
              <span class="text-xl">{item.icon}</span>
              <div class="flex-1">
                <div class="font-medium">{item.label}</div>
                {#if item.type === "mode"}
                  <span class="text-xs text-gray-500">Mode</span>
                {/if}
              </div>
            </button>
          {/each}
        {/if}
      </div>

      <div class="p-3 border-t border-gray-700 text-xs text-gray-500 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <span><kbd class="px-1 bg-gray-700 rounded">↑↓</kbd> Navigate</span>
          <span><kbd class="px-1 bg-gray-700 rounded">↵</kbd> Select</span>
        </div>
        <span>⌘K to toggle</span>
      </div>
    </div>
  </div>
{/if}
