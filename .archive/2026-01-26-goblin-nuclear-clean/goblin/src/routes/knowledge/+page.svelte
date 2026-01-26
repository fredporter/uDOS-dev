<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { apiRequest, isApiAvailable } from "$lib";

  interface KnowledgeCategory {
    id: string;
    name: string;
    icon: string;
    description: string;
    articleCount: number;
    teletextPage: number;
  }

  interface KnowledgeArticle {
    id: string;
    title: string;
    category: string;
    excerpt: string;
    tags: string[];
    path: string;
  }

  let searchQuery = $state("");
  let selectedCategory = $state<string | null>(null);
  let articles = $state<KnowledgeArticle[]>([]);
  let isLoading = $state(false);
  let apiConnected = $state(false);

  const categories: KnowledgeCategory[] = [
    {
      id: "survival",
      name: "Survival",
      icon: "🏕️",
      description: "Essential wilderness skills",
      articleCount: 0,
      teletextPage: 200,
    },
    {
      id: "medical",
      name: "Medical",
      icon: "🏥",
      description: "First aid & health",
      articleCount: 0,
      teletextPage: 400,
    },
    {
      id: "tech",
      name: "Technical",
      icon: "⚙️",
      description: "Hardware & software",
      articleCount: 0,
      teletextPage: 300,
    },
    {
      id: "food",
      name: "Food & Water",
      icon: "🍳",
      description: "Foraging, cooking, purification",
      articleCount: 0,
      teletextPage: 800,
    },
    {
      id: "navigation",
      name: "Navigation",
      icon: "🧭",
      description: "Maps, terrain, orientation",
      articleCount: 0,
      teletextPage: 500,
    },
    {
      id: "communication",
      name: "Communication",
      icon: "📡",
      description: "Signals, radio, mesh",
      articleCount: 0,
      teletextPage: 600,
    },
    {
      id: "tools",
      name: "Tools & Making",
      icon: "🔧",
      description: "Crafting, repair, building",
      articleCount: 0,
      teletextPage: 700,
    },
    {
      id: "reference",
      name: "Reference",
      icon: "📚",
      description: "System commands & uPY",
      articleCount: 0,
      teletextPage: 900,
    },
  ];

  onMount(async () => {
    apiConnected = await isApiAvailable();
    if (apiConnected) {
      await loadKnowledgeStats();
    }
  });

  async function loadKnowledgeStats() {
    try {
      const response = await apiRequest<{ stats: Record<string, number> }>(
        "/api/knowledge/stats"
      );
      if (response.ok && response.data?.stats) {
        for (const cat of categories) {
          cat.articleCount = response.data.stats[cat.id] || 0;
        }
      }
    } catch (e) {
      console.error("Failed to load stats:", e);
    }
  }

  async function searchKnowledge() {
    if (!searchQuery.trim()) {
      articles = [];
      return;
    }

    isLoading = true;
    try {
      const response = await apiRequest<{ results: KnowledgeArticle[] }>(
        `/api/knowledge/search?query=${encodeURIComponent(searchQuery)}`
      );
      if (response.ok && response.data?.results) {
        articles = response.data.results;
      }
    } catch (e) {
      console.error("Search failed:", e);
    } finally {
      isLoading = false;
    }
  }

  function selectCategory(cat: KnowledgeCategory) {
    selectedCategory = cat.id;
    // Navigate to Teledesk with category's base page
    goto(`/teledesk?p=${cat.teletextPage}`);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && searchQuery) {
      e.preventDefault();
      searchKnowledge();
    }
    if (e.key === "Escape") {
      if (selectedCategory) {
        selectedCategory = null;
      } else {
        goto("/dashboard");
      }
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<svelte:head>
  <title>Knowledge Bank - Markdown</title>
</svelte:head>

<div class="h-full flex flex-col bg-gray-900 text-white">
  <!-- Header -->
  <div class="px-6 py-4 bg-gray-800 border-b border-gray-700">
    <div class="flex items-center justify-between mb-3">
      <div>
        <h1 class="text-xl font-bold">📚 Knowledge Bank</h1>
        <p class="text-sm text-gray-400">
          Offline-first survival & technical reference
        </p>
      </div>
      <div class="flex items-center gap-2">
        {#if apiConnected}
          <span class="text-green-400 text-xs">● Online</span>
        {:else}
          <span class="text-yellow-400 text-xs">○ Offline Mode</span>
        {/if}
      </div>
    </div>

    <!-- Search bar -->
    <div class="relative">
      <input
        type="text"
        bind:value={searchQuery}
        placeholder="Search knowledge bank..."
        class="w-full px-4 py-2 bg-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        onkeydown={(e) => e.key === "Enter" && searchKnowledge()}
      />
      <button
        onclick={searchKnowledge}
        class="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1 bg-blue-600 rounded hover:bg-blue-500 text-sm"
      >
        Search
      </button>
    </div>
  </div>

  <div class="flex-1 overflow-auto p-6">
    {#if isLoading}
      <div class="flex items-center justify-center h-32">
        <div class="text-gray-400">Searching...</div>
      </div>
    {:else if articles.length > 0}
      <!-- Search results -->
      <div class="mb-4 text-sm text-gray-400">
        Found {articles.length} results for "{searchQuery}"
      </div>
      <div class="space-y-3">
        {#each articles as article}
          <button
            onclick={() =>
              goto(`/desktop?file=${encodeURIComponent(article.path)}`)}
            class="w-full text-left p-4 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
          >
            <h3 class="font-semibold mb-1">{article.title}</h3>
            <p class="text-sm text-gray-400 mb-2">{article.excerpt}</p>
            <div class="flex gap-2">
              {#each article.tags.slice(0, 3) as tag}
                <span class="text-xs px-2 py-0.5 bg-gray-700 rounded"
                  >{tag}</span
                >
              {/each}
            </div>
          </button>
        {/each}
      </div>
    {:else}
      <!-- Category grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {#each categories as cat}
          <button
            onclick={() => selectCategory(cat)}
            class="p-6 bg-gray-800 rounded-lg hover:bg-gray-700 transition-all hover:scale-102 text-left group"
          >
            <div class="text-4xl mb-3">{cat.icon}</div>
            <h3 class="text-lg font-bold mb-1 group-hover:text-blue-400">
              {cat.name}
            </h3>
            <p class="text-sm text-gray-400 mb-2">{cat.description}</p>
            <div
              class="flex items-center justify-between text-xs text-gray-500"
            >
              <span>Page {cat.teletextPage}</span>
              {#if cat.articleCount > 0}
                <span>{cat.articleCount} articles</span>
              {/if}
            </div>
          </button>
        {/each}
      </div>

      <!-- Quick access -->
      <div class="mt-8">
        <h2
          class="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wider"
        >
          Quick Access
        </h2>
        <div class="flex flex-wrap gap-2">
          <button
            onclick={() => goto("/teledesk?p=100")}
            class="px-3 py-1.5 bg-gray-800 rounded hover:bg-gray-700 text-sm"
          >
            📺 Teledesk Index
          </button>
          <button
            onclick={() => goto("/teledesk?p=900")}
            class="px-3 py-1.5 bg-gray-800 rounded hover:bg-gray-700 text-sm"
          >
            📖 Command Reference
          </button>
          <button
            onclick={() => goto("/teledesk?p=903")}
            class="px-3 py-1.5 bg-gray-800 rounded hover:bg-gray-700 text-sm"
          >
            🐍 uPY Guide
          </button>
          <button
            onclick={() => goto("/teledesk?p=200")}
            class="px-3 py-1.5 bg-gray-800 rounded hover:bg-gray-700 text-sm"
          >
            🏕️ Survival Basics
          </button>
        </div>
      </div>
    {/if}
  </div>

  <!-- Footer -->
  <div
    class="px-4 py-2 bg-gray-800 border-t border-gray-700 text-xs text-gray-500 flex justify-between"
  >
    <span>ESC Dashboard • Enter Search</span>
    <span>Click category → Teledesk view</span>
  </div>
</div>

<style>
  .hover\:scale-102:hover {
    transform: scale(1.02);
  }
</style>
