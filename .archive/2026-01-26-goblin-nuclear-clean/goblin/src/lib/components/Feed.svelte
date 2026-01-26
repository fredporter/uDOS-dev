<script lang="ts">
  /**
   * Feed Component - Universal content display
   *
   * Display modes:
   * - ticker: Horizontal scrolling bar (news ticker style)
   * - page: Full-screen teletext-style display
   * - panel: Side/bottom panel overlay
   *
   * Supports typewriter effect, variable scroll speeds, and natural output.
   * Uses monosorts grid fonts controlled by M button (cycled via styleManager)
   */
  import { onMount, onDestroy } from "svelte";
  import {
    type FeedState,
    type FeedItem,
    type FeedDisplayMode,
    getFeed,
    getCurrentItem,
    nextItem,
    prevItem,
    toggleFeedPause,
    startTypewriter,
    skipTypewriter,
    formatTimestamp,
    formatTickerContent,
    subscribeFeed,
  } from "$lib/stores/feed";

  // Props
  interface Props {
    feedId: string;
    mode?: "sentence" | "caps";
    class?: string;
  }

  let { feedId, mode = "sentence", class: className = "" }: Props = $props();

  // Local state
  let feed = $state<FeedState | undefined>(undefined);
  let currentItem = $state<FeedItem | null>(null);
  let tickerOffset = $state(0);
  let tickerContainer = $state<HTMLDivElement | null>(null);
  let unsubscribe: (() => void) | null = null;
  let fontVariantKey = $state(0); // Force re-render when font changes

  // Ticker animation
  let tickerFrame: number | null = null;

  onMount(async () => {
    // Subscribe to feed updates
    unsubscribe = subscribeFeed(() => {
      feed = getFeed(feedId);
      currentItem = getCurrentItem(feedId);
    });

    // Initial load
    feed = getFeed(feedId);
    currentItem = getCurrentItem(feedId);

    // Listen for font style changes from M button (DOM event, not Tauri event)
    const handleStyleChange = () => {
      fontVariantKey++; // Trigger reactivity
    };
    window.addEventListener("udos-style-changed", handleStyleChange);

    // Start ticker animation if in ticker mode
    if (feed?.config.displayMode === "ticker") {
      startTickerAnimation();
    }

    // Start typewriter if configured
    if (feed?.config.scrollBehavior === "typewriter" && currentItem) {
      startTypewriter(feedId);
    }
  });

  onDestroy(() => {
    unsubscribe?.();
    if (tickerFrame) cancelAnimationFrame(tickerFrame);
    window.removeEventListener("udos-style-changed", () => {
      fontVariantKey++;
    });
  });

  function startTickerAnimation() {
    if (!feed || feed.config.displayMode !== "ticker") return;

    let lastTime = performance.now();
    const speed = feed.config.scrollSpeed; // pixels per second

    function animateTicker(timestamp: number) {
      const f = getFeed(feedId);
      if (!f || f.isPaused) {
        tickerFrame = requestAnimationFrame(animateTicker);
        return;
      }

      const delta = timestamp - lastTime;
      lastTime = timestamp;

      // Move ticker
      tickerOffset -= (speed * delta) / 1000;

      // Reset when fully scrolled
      if (tickerContainer) {
        const contentWidth = tickerContainer.scrollWidth / 2;
        if (Math.abs(tickerOffset) >= contentWidth) {
          tickerOffset = 0;
        }
      }

      tickerFrame = requestAnimationFrame(animateTicker);
    }

    tickerFrame = requestAnimationFrame(animateTicker);
  }

  function transformTickerText(text: string): string {
    if (mode === "caps") {
      return text.toUpperCase();
    }
    return text; // sentence case (default)
  }

  function handleKeydown(e: KeyboardEvent) {
    if (!feed) return;

    switch (e.key) {
      case "ArrowRight":
      case "n":
        e.preventDefault();
        nextItem(feedId);
        if (feed.config.scrollBehavior === "typewriter") {
          startTypewriter(feedId);
        }
        break;
      case "ArrowLeft":
      case "p":
        e.preventDefault();
        prevItem(feedId);
        if (feed.config.scrollBehavior === "typewriter") {
          startTypewriter(feedId);
        }
        break;
      case " ":
        e.preventDefault();
        if (feed.isTyping) {
          skipTypewriter(feedId);
        } else {
          toggleFeedPause(feedId);
        }
        break;
      case "Escape":
        toggleFeedPause(feedId);
        break;
    }
  }

  // Get display content based on mode
  function getDisplayContent(): string {
    if (!feed) return "";

    if (feed.config.scrollBehavior === "typewriter") {
      return feed.displayedContent;
    }

    if (currentItem) {
      return `${currentItem.title}\n\n${currentItem.content}`;
    }

    return "";
  }

  // Priority color mapping
  function getPriorityColor(priority: FeedItem["priority"]): string {
    switch (priority) {
      case "urgent":
        return "text-red-400";
      case "high":
        return "text-orange-400";
      case "normal":
        return "text-cyan-400";
      case "low":
        return "text-gray-400";
      default:
        return "text-white";
    }
  }

  // Source icon mapping
  function getSourceIcon(source: string): string {
    switch (source) {
      case "knowledge":
        return "📚";
      case "logs":
        return "📋";
      case "notifications":
        return "🔔";
      case "email":
        return "📧";
      case "mesh":
        return "📡";
      case "commands":
        return "⌨️";
      default:
        return "📌";
    }
  }
</script>

{#if feed}
  <!-- TICKER MODE (horizontal scrolling) -->
  {#if feed.config.displayMode === "ticker"}
    {#key fontVariantKey}
      <div
        class="feed-ticker h-8 bg-gray-100 dark:bg-gray-900 border-y border-gray-300 dark:border-gray-700 overflow-hidden flex items-center {className}"
        role="marquee"
        aria-live="polite"
        style="font-family: var(--font-mono-variant);"
      >
        <div
          class="flex-shrink-0 px-3 bg-gray-200 dark:bg-gray-800 h-full flex items-center border-r border-gray-300 dark:border-gray-700"
        >
          <span
            class="text-xs text-cyan-600 dark:text-cyan-400 uppercase font-bold tracking-wide"
          >
            {getSourceIcon(feed.config.source)}
            {feed.config.source}
          </span>
        </div>

        <div
          class="flex-1 overflow-hidden relative"
          bind:this={tickerContainer}
        >
          <div
            class="whitespace-nowrap text-sm text-gray-900 dark:text-gray-100"
            style="transform: translateX({tickerOffset}px); font-family: var(--font-mono-variant);"
          >
            <!-- Duplicate content for seamless loop -->
            <span class="inline-block px-4">
              {transformTickerText(formatTickerContent(feed.items))}
            </span>
            <span class="inline-block px-4">
              {transformTickerText(formatTickerContent(feed.items))}
            </span>
          </div>
        </div>

        <div class="flex-shrink-0 px-2 flex items-center gap-2">
          <button
            class="text-gray-400 hover:text-white text-xs"
            onclick={() => toggleFeedPause(feedId)}
            title={feed.isPaused ? "Resume" : "Pause"}
          >
            {feed.isPaused ? "▶" : "⏸"}
          </button>
        </div>
      </div>
    {/key}

    <!-- PAGE MODE (Full-screen teletext style) -->
  {:else if feed.config.displayMode === "page"}
    <div
      class="feed-page h-full bg-black text-green-400 p-4 overflow-auto {className}"
      tabindex="-1"
      role="region"
      aria-label="Feed page view"
      style="font-family: var(--font-mono-variant);"
    >
      <!-- Header bar -->
      <div
        class="flex items-center justify-between mb-4 pb-2 border-b border-green-800"
      >
        <div class="flex items-center gap-2">
          <span class="text-yellow-400"
            >{getSourceIcon(feed.config.source)}</span
          >
          <span class="uppercase text-xs">{feed.config.source} FEED</span>
        </div>
        <div class="flex items-center gap-4 text-xs">
          <span class="text-cyan-400">
            {feed.currentIndex + 1}/{feed.items.length}
          </span>
          {#if currentItem}
            <span class="text-gray-500">
              {formatTimestamp(currentItem.timestamp)}
            </span>
          {/if}
          {#if feed.isTyping}
            <span class="animate-pulse text-yellow-400">●</span>
          {/if}
        </div>
      </div>

      <!-- Content area with typewriter effect -->
      <div class="feed-content min-h-[400px]">
        {#if currentItem}
          <div class="mb-4">
            <span class={getPriorityColor(currentItem.priority)}>
              {currentItem.priority.toUpperCase()}
            </span>
          </div>

          <pre
            class="whitespace-pre-wrap text-lg leading-relaxed">{getDisplayContent()}</pre>

          {#if feed.isTyping}
            <span class="inline-block w-2 h-5 bg-green-400 animate-pulse ml-1"
              >_</span
            >
          {/if}
        {:else}
          <div class="text-center text-gray-600 mt-20">
            <div class="text-4xl mb-4">📭</div>
            <p>No items in feed</p>
          </div>
        {/if}
      </div>

      <!-- Navigation footer -->
      <div
        class="mt-4 pt-2 border-t border-green-800 flex justify-between text-xs text-gray-500"
      >
        <div>← PREV</div>
        <div>SPACE: {feed.isTyping ? "SKIP" : "PAUSE"}</div>
        <div>NEXT →</div>
      </div>
    </div>

    <!-- PANEL MODE (Side/bottom overlay) -->
  {:else if feed.config.displayMode === "panel"}
    <div
      class="feed-panel bg-gray-900/95 border-l border-gray-700 p-3 overflow-auto {className}"
    >
      <!-- Panel header -->
      <div
        class="flex items-center justify-between mb-3 pb-2 border-b border-gray-700"
      >
        <div class="flex items-center gap-2 text-sm">
          <span>{getSourceIcon(feed.config.source)}</span>
          <span class="font-medium capitalize">{feed.config.source}</span>
        </div>
        <button
          class="text-gray-400 hover:text-white"
          onclick={() => toggleFeedPause(feedId)}
        >
          {feed.isPaused ? "▶" : "⏸"}
        </button>
      </div>

      <!-- Item list -->
      <div class="space-y-2">
        {#each feed.items.slice(-10).reverse() as item, i}
          <div
            class="p-2 rounded text-sm transition-colors {i === 0
              ? 'bg-gray-800'
              : 'bg-transparent hover:bg-gray-800/50'}"
            class:border-l-2={i === 0}
            class:border-cyan-400={i === 0}
          >
            <div class="flex items-start justify-between gap-2">
              <div class="flex-1 min-w-0">
                <div
                  class="font-medium truncate {getPriorityColor(item.priority)}"
                >
                  {item.title}
                </div>
                <div class="text-xs text-gray-500 truncate mt-1">
                  {item.content.slice(0, 60)}{item.content.length > 60
                    ? "..."
                    : ""}
                </div>
              </div>
              <div class="text-xs text-gray-600 flex-shrink-0">
                {formatTimestamp(item.timestamp)}
              </div>
            </div>
          </div>
        {/each}

        {#if feed.items.length === 0}
          <div class="text-center text-gray-600 py-4">
            <p class="text-sm">No items</p>
          </div>
        {/if}
      </div>

      <!-- Panel footer -->
      <div
        class="mt-3 pt-2 border-t border-gray-700 text-xs text-gray-500 flex justify-between"
      >
        <span>{feed.items.length} items</span>
        <span>{feed.isPaused ? "PAUSED" : "LIVE"}</span>
      </div>
    </div>
  {/if}
{:else}
  <!-- Feed not found -->
  <div class="p-4 text-center text-gray-500">
    <p>Feed "{feedId}" not found</p>
  </div>
{/if}

<style>
  .feed-ticker {
    font-family: inherit;
  }

  .feed-page {
    font-family: inherit;
    text-shadow: 0 0 5px currentColor;
  }

  .feed-page pre {
    font-family: inherit;
  }

  .feed-panel {
    min-width: 280px;
    max-width: 400px;
    font-family: inherit;
  }

  /* Cursor blink animation */
  @keyframes blink {
    0%,
    50% {
      opacity: 1;
    }
    51%,
    100% {
      opacity: 0;
    }
  }
</style>
