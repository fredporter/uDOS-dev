<script lang="ts">
  let searchQuery = "";
  let files = [
    {
      name: "README.md",
      path: "sandbox/README.md",
      size: "2.4 KB",
      modified: "2 hours ago",
    },
    {
      name: "notes.md",
      path: "drafts/notes.md",
      size: "1.2 KB",
      modified: "1 day ago",
    },
    {
      name: "project.md",
      path: "user/project.md",
      size: "5.7 KB",
      modified: "3 days ago",
    },
  ];

  $: filteredFiles = files.filter(
    (f) =>
      f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.path.toLowerCase().includes(searchQuery.toLowerCase())
  );
</script>

<svelte:head>
  <title>Library - Markdown</title>
</svelte:head>

<div class="h-full flex flex-col">
  <header class="bg-udos-surface px-6 py-4 border-b border-gray-700">
    <h1 class="text-xl font-bold mb-3">Library</h1>
    <input
      type="text"
      bind:value={searchQuery}
      placeholder="Search files..."
      class="w-full px-4 py-2 bg-udos-bg rounded outline-none focus:ring-2 focus:ring-udos-primary"
    />
  </header>

  <div class="flex-1 overflow-y-auto">
    <div class="p-6">
      <div class="space-y-2">
        {#each filteredFiles as file}
          <a
            href="/editor/{encodeURIComponent(file.path)}"
            class="block p-4 bg-udos-surface rounded-lg hover:bg-udos-surface/80 transition-colors"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h3 class="font-bold mb-1">{file.name}</h3>
                <p class="text-sm text-gray-400">{file.path}</p>
              </div>
              <div class="text-right text-sm text-gray-500">
                <div>{file.size}</div>
                <div>{file.modified}</div>
              </div>
            </div>
          </a>
        {/each}
      </div>
    </div>
  </div>
</div>
