<!--
  PageLayout - Shared layout template for MODE pages
  Provides consistent header, sidebar, and content areas
  Uses Tailwind with dark mode via 'class' strategy
-->
<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    title?: string;
    sidebarOpen?: boolean;
    onToggleSidebar?: () => void;
    actions?: Snippet;
    sidebar?: Snippet;
    class?: string;
    children?: Snippet;
  }

  let {
    title = "",
    sidebarOpen = false,
    onToggleSidebar = () => {},
    actions,
    sidebar,
    class: customClass = "",
    children,
  }: Props = $props();

</script>

<div
  class={[
    "min-h-[calc(100vh-3.5rem)]",
    "bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100",
    customClass,
  ].join(" ")}
>
  <!-- Header -->
  <div
    class="flex items-center justify-between px-3 py-2 border-b dark:border-gray-700"
  >
    <div class="flex items-center gap-2">
      <button
        class="px-2 py-1 text-xs rounded bg-gray-200 hover:bg-gray-300 dark:bg-gray-800 dark:hover:bg-gray-700"
        onclick={onToggleSidebar}
      >
        {sidebarOpen ? "Hide Sidebar" : "Show Sidebar"}
      </button>
      {#if title}
        <h2 class="text-sm font-semibold">{title}</h2>
      {/if}
    </div>
    <div class="flex items-center gap-2">
      {#if actions}{@render (actions as any)()}{/if}
    </div>
  </div>

  <!-- Body -->
  <div class="grid grid-cols-12 gap-0">
    <!-- Sidebar -->
    {#if sidebarOpen && sidebar}
      <aside class="col-span-3 border-r dark:border-gray-700 p-2">
        {@render (sidebar as any)()}
      </aside>
    {/if}

    <!-- Content -->
    <main class={sidebarOpen && sidebar ? "col-span-9" : "col-span-12"}>
      <div class="p-2">
        {#if children}{@render (children as any)()}{/if}
      </div>
    </main>
  </div>
</div>
