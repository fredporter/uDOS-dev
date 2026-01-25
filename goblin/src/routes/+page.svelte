<script lang="ts">
  import { onMount } from "svelte";
  import { invoke } from "@tauri-apps/api/core";
  import { listen } from "@tauri-apps/api/event";
  import { goto } from "$app/navigation";

  // Experiments list (Terminal/Teledesk are minimal, not Tailwind-styled)
  const experiments = [
    {
      title: "Dashboard",
      path: "/dashboard",
      tag: "home",
      note: "Alias for Goblin home",
    },
    {
      title: "Desktop",
      path: "/desktop",
      tag: "ui",
      note: "Desktop shell prototype",
    },
    {
      title: "Terminal",
      path: "/terminal",
      tag: "core",
      note: "Hybrid router, WS; minimal styling",
    },
    {
      title: "Teletext",
      path: "/teletext",
      tag: "teletext",
      note: "Alias for Teledesk",
    },
    {
      title: "Teledesk",
      path: "/teledesk",
      tag: "teletext",
      note: "Teletext UI; not Tailwind-styled",
    },
    {
      title: "Web Hub",
      path: "/web",
      tag: "web",
      note: "Publishing and sandbox web tools",
    },
    {
      title: "Grid",
      path: "/grid",
      tag: "grid",
      note: "Teletext/grid demos with router",
    },
    {
      title: "Table Editor",
      path: "/table",
      tag: "tables",
      note: "Table tooling",
    },
    {
      title: "Stories",
      path: "/stories",
      tag: "stories",
      note: "Story playground",
    },
    {
      title: "Blocks",
      path: "/blocks",
      tag: "blocks",
      note: "Blocks manager dev",
    },
  ];

  onMount(() => {
    let unlisten: (() => void) | null = null;

    (async () => {
      // File-open events from Finder → Typo editor
      unlisten = await listen("file-open", (event) => {
        goto(`/editor?file=${encodeURIComponent(event.payload as string)}`);
      });

      // Launch with file arg → Typo editor; otherwise stay on index
      const filePath = await invoke<string | null>("get_file_path_from_args");
      if (filePath) {
        goto(`/editor?file=${encodeURIComponent(filePath)}`);
      }
    })();

    return () => {
      unlisten?.();
    };
  });

  function open(path: string) {
    goto(path);
  }
</script>

<div class="min-h-screen bg-slate-950 text-slate-50">
  <div class="max-w-5xl mx-auto px-6 py-12 space-y-8">
    <header class="space-y-2">
      <p class="text-sm uppercase tracking-[0.2em] text-slate-400">
        Goblin Sandbox
      </p>
      <h1 class="text-4xl font-bold">Experiments Home</h1>
      <p class="text-slate-300">
        Launch any remaining experimental tools. Terminal and Teledesk use their
        own minimal styling; others follow the shared Tailwind skin.
      </p>
    </header>

    <section class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {#each experiments as exp}
        <button
          class="group text-left w-full rounded-2xl border border-slate-800 bg-slate-900/80 hover:bg-slate-800/80 transition shadow-sm hover:shadow-md px-4 py-5"
          on:click={() => open(exp.path)}
        >
          <div class="flex items-center justify-between mb-3">
            <span
              class="text-xs font-semibold uppercase tracking-wide text-slate-400"
              >{exp.tag}</span
            >
            <span
              class="text-sm text-slate-500 group-hover:text-slate-200 transition"
              >↗</span
            >
          </div>
          <div class="text-xl font-semibold mb-1">{exp.title}</div>
          <div class="text-sm text-slate-400 leading-snug">{exp.note}</div>
        </button>
      {/each}
    </section>

    <div
      class="rounded-xl border border-slate-800 bg-slate-900/80 px-4 py-3 text-sm text-slate-300"
    >
      <div class="font-semibold mb-1">Launch notes</div>
      <ul class="list-disc list-inside space-y-1 text-slate-400">
        <li>
          File-open events still route directly to Typo editor if a file is
          passed.
        </li>
        <li>Terminal and Teledesk are minimal (non-Tailwind) by design.</li>
      </ul>
    </div>
  </div>
</div>
