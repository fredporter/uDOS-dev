<script lang="ts">
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";

  interface AppMode {
    id: string;
    name: string;
    icon: string;
    route: string;
    description: string;
    shortcut: string;
  }

  const modes: AppMode[] = [
    {
      id: "typo",
      name: "Typo",
      icon: "✏️",
      route: "/editor",
      description: "Markdown editor",
      shortcut: "⌘1",
    },
    {
      id: "desktop",
      name: "Desktop",
      icon: "🖥️",
      route: "/desktop",
      description: "System 7 style desktop",
      shortcut: "⌘2",
    },
    {
      id: "terminal",
      name: "Terminal",
      icon: "⌘",
      route: "/terminal",
      description: "TUI/CLI - Execute commands",
      shortcut: "⌘3",
    },
    {
      id: "teledesk",
      name: "Teledesk",
      icon: "📺",
      route: "/teledesk",
      description: "Teletext-style pages",
      shortcut: "⌘4",
    },
    {
      id: "grid",
      name: "Grid",
      icon: "▦",
      route: "/grid",
      description: "Unified grid display - Teletext/Terminal",
      shortcut: "⌘5",
    },
    {
      id: "dashboard",
      name: "Dashboard",
      icon: "📊",
      route: "/dashboard",
      description: "Status & quick actions",
      shortcut: "⌘6",
    },
    {
      id: "knowledge",
      name: "Knowledge",
      icon: "📚",
      route: "/knowledge",
      description: "Search knowledge bank",
      shortcut: "⌘7",
    },
    {
      id: "groovebox",
      name: "Groovebox",
      icon: "🎹",
      route: "/groovebox",
      description: "808 drum machine",
      shortcut: "⌘8",
    },
  ];

  let currentMode = $derived(
    modes.find((m) => $page.url.pathname.startsWith(m.route)) || modes[1]
  );

  let showModeList = $state(false);

  function switchMode(mode: AppMode) {
    goto(mode.route);
    showModeList = false;
  }

  function handleKeydown(e: KeyboardEvent) {
    // Cmd/Ctrl + 1-8 for mode switching
    if (e.metaKey || e.ctrlKey) {
      const num = parseInt(e.key);
      if (num >= 1 && num <= 8) {
        e.preventDefault();
        switchMode(modes[num - 1]);
      }
    }
    // Escape to close mode list
    if (e.key === "Escape" && showModeList) {
      showModeList = false;
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="relative">
  <button
    class="flex items-center gap-2 px-3 py-2 rounded-lg bg-udos-surface hover:bg-udos-surface/80 transition-colors"
    onclick={() => (showModeList = !showModeList)}
    aria-label="Switch mode"
    aria-expanded={showModeList}
  >
    <span class="text-lg">{currentMode.icon}</span>
    <span class="font-medium">{currentMode.name}</span>
    <svg
      class="w-4 h-4 text-gray-400 transition-transform {showModeList
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

  {#if showModeList}
    <!-- Backdrop to close on outside click -->
    <div
      class="fixed inset-0 z-40"
      onclick={() => (showModeList = false)}
      onkeydown={(e) => e.key === "Escape" && (showModeList = false)}
      role="presentation"
    ></div>
    <div
      class="absolute top-full left-0 mt-2 w-64 bg-udos-surface rounded-lg shadow-lg border border-gray-700 overflow-hidden z-50"
    >
      {#each modes as mode}
        <button
          class="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-700/50 transition-colors text-left {mode.id ===
          currentMode.id
            ? 'bg-gray-700/30'
            : ''}"
          onclick={() => switchMode(mode)}
        >
          <span class="text-xl">{mode.icon}</span>
          <div class="flex-1">
            <div class="font-medium">{mode.name}</div>
            <div class="text-xs text-gray-400">{mode.description}</div>
          </div>
          <span class="text-xs text-gray-500 font-mono">{mode.shortcut}</span>
        </button>
      {/each}
    </div>
  {/if}
</div>
