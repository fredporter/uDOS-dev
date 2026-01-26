<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { moveLogger } from "$lib";
  import { copyBufferLogger } from "$lib/services/copyBufferLogger";
  import {
    getCopyBuffer,
    onCopyBufferChange,
    removeFromCopyBuffer,
    copyToClipboard,
    clearCopyBuffer,
    type CopyBufferItem,
  } from "$lib/services/keyboardManager";

  interface Props {
    isOpen?: boolean;
    onClose?: () => void;
  }

  let { isOpen = true, onClose = () => {} }: Props = $props();

  let buffer = $state<CopyBufferItem[]>([]);
  let selectedItem = $state<string | null>(null);
  let unsubscribe: (() => void) | null = null;
  let activeTab = $state<"buffer" | "session-log">("buffer");
  let sessionLog = $state<any[]>([]);
  let hasUnreadLog = $state(false);

  onMount(() => {
    // Subscribe to copy buffer changes
    unsubscribe = onCopyBufferChange((items) => {
      buffer = items;
      // sync to copy buffer logger (dedupe/update)
      copyBufferLogger.sync(items);
    });

    // Subscribe to session log store
    const storeUnsub = moveLogger.store.subscribe((entries) => {
      sessionLog = entries;
    });

    // Listen for new log entries to show unread indicator
    const onNewLog = () => {
      if (activeTab !== "session-log") hasUnreadLog = true;
    };
    window.addEventListener("session-log:new-entry", onNewLog as any);

    // cleanup
    const prevUnmount = unsubscribe;
    unsubscribe = () => {
      if (prevUnmount) prevUnmount();
      storeUnsub();
      window.removeEventListener("session-log:new-entry", onNewLog as any);
    };
  });

  // Run cleanup policy periodically
  const cleanupTimer = setInterval(() => copyBufferLogger.cleanup(), 60_000);
  onDestroy(() => clearInterval(cleanupTimer));

  onDestroy(() => {
    if (unsubscribe) unsubscribe();
  });

  const handleCopy = async (item: CopyBufferItem) => {
    await copyToClipboard(item.text);
    selectedItem = item.id;
    setTimeout(() => {
      selectedItem = null;
    }, 1000);
  };

  const handleRemove = (id: string) => {
    removeFromCopyBuffer(id);
  };

  const handleClearAll = () => {
    if (confirm("Clear all copy buffer items?")) {
      clearCopyBuffer();
    }
  };

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return "just now";
  };
</script>

{#if isOpen}
  <aside
    class="w-80 bg-gray-100 dark:bg-gray-900 border-l border-gray-300 dark:border-gray-800 flex flex-col relative"
    style="z-index: 20;"
  >
    <!-- Header -->
    <header
      class="flex items-center justify-between border-b border-gray-300 dark:border-gray-800 px-4 py-3"
    >
      <div class="flex items-center gap-2">
        <svg
          class="w-5 h-5 text-gray-700 dark:text-gray-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h2 class="font-semibold text-gray-900 dark:text-gray-100">
          Copy Buffer
        </h2>
      </div>
      <div class="flex items-center gap-1">
        {#if buffer.length > 0}
          <button
            class="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-800 rounded"
            onclick={handleClearAll}
            title="Clear all"
          >
            <svg
              class="w-4 h-4 text-gray-600 dark:text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        {/if}
        <button
          class="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-800 rounded"
          onclick={onClose}
          title="Close"
        >
          <svg
            class="w-4 h-4 text-gray-600 dark:text-gray-400"
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
      </div>
    </header>

    <!-- Tabs -->
    <div class="border-b border-gray-300 dark:border-gray-800 px-2 pt-2">
      <div class="flex gap-2">
        <button
          class="px-2 py-1 text-xs rounded hover:bg-gray-200 dark:hover:bg-gray-800"
          class:bg-gray-300={activeTab === "buffer"}
          class:dark:bg-gray-700={activeTab === "buffer"}
          onclick={() => {
            activeTab = "buffer";
          }}
        >
          Copy Buffer
        </button>
        <button
          class="px-2 py-1 text-xs rounded hover:bg-gray-200 dark:hover:bg-gray-800 relative"
          class:bg-gray-300={activeTab === "session-log"}
          class:dark:bg-gray-700={activeTab === "session-log"}
          onclick={() => {
            activeTab = "session-log";
            hasUnreadLog = false;
          }}
        >
          Session Log
          {#if hasUnreadLog}
            <span
              class="absolute -top-1 -right-1 w-2 h-2 bg-cyan-500 rounded-full"
            ></span>
          {/if}
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto">
      {#if activeTab === "buffer"}
        <!-- Buffer List -->
        {#if buffer.length === 0}
          <div
            class="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-500 p-8 text-center"
          >
            <svg
              class="w-16 h-16 mb-4 opacity-50"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p class="text-sm">No items copied yet</p>
            <p class="text-xs mt-2">
              Select text anywhere<br />to add to buffer
            </p>
          </div>
        {:else}
          <div class="divide-y divide-gray-200 dark:divide-gray-800">
            {#each buffer as item (item.id)}
              <div
                class="p-3 hover:bg-gray-200 dark:hover:bg-gray-800 group transition-colors"
                class:bg-green-100={selectedItem === item.id}
                class:dark:bg-green-900={selectedItem === item.id}
              >
                <div class="flex items-start justify-between gap-2 mb-2">
                  <div class="flex-1 min-w-0">
                    <div class="text-xs text-gray-500 dark:text-gray-500 mb-1">
                      {formatTimestamp(item.timestamp)}
                      {#if item.source}
                        <span class="ml-2 text-gray-400">• {item.source}</span>
                      {/if}
                    </div>
                    <div
                      class="text-sm text-gray-900 dark:text-gray-100 break-words line-clamp-3"
                    >
                      {item.text}
                    </div>
                  </div>
                  <div class="flex flex-col gap-1">
                    <button
                      class="p-1.5 hover:bg-gray-300 dark:hover:bg-gray-700 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                      onclick={() => handleCopy(item)}
                      title="Copy again"
                    >
                      {#if selectedItem === item.id}
                        <svg
                          class="w-4 h-4 text-green-600 dark:text-green-400"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      {:else}
                        <svg
                          class="w-4 h-4 text-gray-600 dark:text-gray-400"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
                          />
                        </svg>
                      {/if}
                    </button>
                    <button
                      class="p-1.5 hover:bg-red-200 dark:hover:bg-red-900 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                      onclick={() => handleRemove(item.id)}
                      title="Remove"
                    >
                      <svg
                        class="w-4 h-4 text-red-600 dark:text-red-400"
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
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      {:else}
        <!-- Session Log List -->
        {#if sessionLog.length === 0}
          <div class="p-4 text-xs text-gray-500 dark:text-gray-500">
            No session log entries yet.
          </div>
        {:else}
          <div class="divide-y divide-gray-200 dark:divide-gray-800">
            {#each sessionLog as entry}
              <div class="p-3">
                <div
                  class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400"
                >
                  <span>{formatTimestamp(Date.parse(entry.timestamp))}</span>
                  <span>• {entry.status.toUpperCase()}</span>
                </div>
                <div class="text-sm text-gray-900 dark:text-gray-100">
                  <span class="font-medium">{entry.action}</span>
                  {#if entry.context}
                    <span class="ml-2 text-gray-600 dark:text-gray-400"
                      >— {entry.context}</span
                    >
                  {/if}
                </div>
                {#if entry.metadata}
                  <div
                    class="mt-1 text-xs text-gray-600 dark:text-gray-400 break-words"
                  >
                    {JSON.stringify(entry.metadata)}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      {/if}
    </div>

    <!-- Footer -->
    <footer
      class="border-t border-gray-300 dark:border-gray-800 px-4 py-2 text-xs text-gray-500 dark:text-gray-500"
    >
      {#if activeTab === "buffer"}
        {buffer.length} {buffer.length === 1 ? "item" : "items"}
      {:else}
        {sessionLog.length} {sessionLog.length === 1 ? "entry" : "entries"}
      {/if}
    </footer>
  </aside>
{/if}

<style>
  .line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
