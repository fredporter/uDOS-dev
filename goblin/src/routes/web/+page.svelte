<script lang="ts">
  import { goto } from "$app/navigation";

  const links = [
    {
      title: "Present",
      path: "/present",
      note: "Slides, decks, and presentation tooling",
    },
    {
      title: "Stories",
      path: "/stories",
      note: "Story playground and flow experiments",
    },
    {
      title: "Knowledge",
      path: "/knowledge",
      note: "Knowledge tooling and sandbox",
    },
  ];
</script>

<div class="min-h-screen bg-slate-950 text-slate-50">
  <div class="max-w-4xl mx-auto px-6 py-12 space-y-8">
    <header class="space-y-2">
      <p class="text-xs uppercase tracking-[0.2em] text-slate-400">
        Goblin Web Tools
      </p>
      <h1 class="text-3xl font-bold">Web Publishing Hub</h1>
      <p class="text-slate-300">
        These tools remain experimental. Use them for internal demos and
        sandboxed workflows.
      </p>
    </header>

    <section class="grid gap-4 md:grid-cols-2">
      {#each links as link}
        <button
          class="text-left w-full rounded-xl border border-slate-800 bg-slate-900/80 hover:bg-slate-800/80 transition px-4 py-4"
          on:click={() => goto(link.path)}
        >
          <div class="text-lg font-semibold mb-1">{link.title}</div>
          <div class="text-sm text-slate-400">{link.note}</div>
        </button>
      {/each}
    </section>
  </div>
</div>
