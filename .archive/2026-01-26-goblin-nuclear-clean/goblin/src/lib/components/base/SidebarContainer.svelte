<script lang="ts">
  /**
   * SidebarContainer - Base component for all sidebars
   *
   * Provides consistent structure, styling, and behavior:
   * - Responsive width control
   * - Dark mode support
   * - Optional header with title and close button
   * - Overflow handling
   * - Z-index management
   * - Position control (left/right)
   */

  import type { Snippet } from "svelte";

  interface Props {
    /** Sidebar title (optional) */
    title?: string;
    /** Whether sidebar is currently open */
    isOpen: boolean;
    /** Callback when sidebar should toggle */
    onToggle?: () => void;
    /** Position on screen */
    position?: "left" | "right";
    /** Width in tailwind units or custom CSS */
    width?: string;
    /** Z-index for layering */
    zIndex?: number;
    /** Show header with title and close button */
    showHeader?: boolean;
    /** Additional CSS classes */
    class?: string;
    /** Custom background color/gradient */
    background?: string;
    /** Content to render */
    children?: Snippet;
  }

  let {
    title,
    isOpen,
    onToggle,
    position = "left",
    width = "w-80",
    zIndex = 20,
    showHeader = true,
    class: customClass = "",
    background,
    children,
  }: Props = $props();


  const borderClass = $derived(position === "left" ? "border-r" : "border-l");
  const bgClass = $derived(background ? "" : "bg-white dark:bg-gray-800");
</script>

{#if isOpen}
  <aside
    class="{width} {bgClass} {borderClass} border-gray-200 dark:border-gray-700 flex flex-col h-full relative {customClass}"
    style="z-index: {zIndex}; {background ? `background: ${background};` : ''}"
  >
    {#if showHeader && (title || onToggle)}
      <header
        class="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-4 py-3 shrink-0"
      >
        {#if title}
          <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {title}
          </h2>
        {:else}
          <div></div>
        {/if}

        {#if onToggle}
          <button
            onclick={onToggle}
            class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title="Close sidebar"
          >
            <svg
              class="w-5 h-5 text-gray-600 dark:text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
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
      </header>
    {/if}

    <div class="flex-1 overflow-y-auto">
      {#if children}{@render (children as any)()}{/if}
    </div>
  </aside>
{/if}

<style>
  /* Custom scrollbar styling */
  aside :global(.overflow-y-auto)::-webkit-scrollbar {
    width: 8px;
  }

  aside :global(.overflow-y-auto)::-webkit-scrollbar-track {
    background: transparent;
  }

  aside :global(.overflow-y-auto)::-webkit-scrollbar-thumb {
    background: rgba(156, 163, 175, 0.3);
    border-radius: 4px;
  }

  aside :global(.overflow-y-auto)::-webkit-scrollbar-thumb:hover {
    background: rgba(156, 163, 175, 0.5);
  }

  :global(.dark) aside :global(.overflow-y-auto)::-webkit-scrollbar-thumb {
    background: rgba(75, 85, 99, 0.5);
  }

  :global(.dark)
    aside
    :global(.overflow-y-auto)::-webkit-scrollbar-thumb:hover {
    background: rgba(75, 85, 99, 0.7);
  }
</style>
