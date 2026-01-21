<script lang="ts">
  import {
    Sun,
    Moon,
    Close,
    CodeBracket,
    Bullet,
    Info,
    Settings,
    Slideshow,
    Eye,
    Type,
    Document,
  } from "../icons";

  export let isDark: boolean = false;
  export let showLandingOnStartup: boolean = true;
  export let onRendererSelect: (format: string) => void = () => {};
  export let onDarkModeToggle: () => void = () => {};
  export let onDismiss: () => void = () => {};
  export let onToggleShowOnStartup: () => void = () => {};

  const formats = [
    {
      id: "editor",
      title: "Markdown Editor",
      description: "Distraction-free markdown writing",
      icon: Document,
    },
    {
      id: "guide",
      title: "Guide Reader",
      description: "Knowledge base and documentation",
      icon: Info,
    },
    {
      id: "story",
      title: "Interactive Story",
      description: "Typeform-style questionnaires",
      icon: Bullet,
    },
    {
      id: "marp",
      title: "Slide Presentation",
      description: "Beautiful presentation slides",
      icon: Slideshow,
    },
    {
      id: "ucode",
      title: "uCode Runtime",
      description: "Executable markdown documents",
      icon: CodeBracket,
    },
    {
      id: "fonts",
      title: "Font Manager",
      description: "Customize typography",
      icon: Type,
    },
    {
      id: "config",
      title: "Config Settings",
      description: "App configuration & preferences",
      icon: Settings,
    },
    {
      id: "home",
      title: "Demo",
      description: "Feature demonstrations",
      icon: Eye,
    },
  ];
</script>

<!-- Modal Overlay -->
<div class="fixed inset-0 z-300 flex items-center justify-center bg-black/40">
  <!-- Modal Card -->
  <div
    class="relative w-full max-w-2xl mx-auto bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-8 sm:p-12 flex flex-col gap-8 border border-gray-200 dark:border-gray-700"
  >
    <!-- Close Button -->
    <button
      class="absolute top-4 right-4 p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400"
      on:click={onDismiss}
      aria-label="Close landing page"
    >
      <Close className="w-5 h-5" />
    </button>
    <!-- Title and Theme Toggle -->
    <div class="flex items-center justify-between gap-4">
      <h2 class="text-3xl font-bold tracking-tight">Welcome to Markdown</h2>
      <button
        on:click={onDarkModeToggle}
        class="flex items-center justify-center w-10 h-10 rounded-lg transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
        aria-label="Toggle dark mode"
      >
        {#if isDark}
          <Sun />
        {:else}
          <Moon />
        {/if}
      </button>
    </div>
    <p class="text-lg text-gray-600 dark:text-gray-400 text-center">
      Pick a format below to get started. Each renderer provides a unique way to
      experience your markdown documents.
    </p>
    <!-- Format Grid -->
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {#each formats as format (format.id)}
        <button
          on:click={() => onRendererSelect(format.id)}
          class="group relative flex flex-col items-start rounded-xl border border-gray-200 bg-white p-5 text-left transition-all hover:border-gray-300 hover:shadow-md dark:border-gray-800 dark:bg-gray-900 dark:hover:border-gray-700 dark:hover:shadow-lg"
        >
          <div class="mb-3">
            <svelte:component
              this={format.icon}
              class="w-6 h-6 text-gray-700 dark:text-gray-300"
            />
          </div>
          <h3 class="text-base font-semibold">{format.title}</h3>
          <p class="mt-1 text-xs text-gray-600 dark:text-gray-400">
            {format.description}
          </p>
          <div
            class="absolute inset-0 rounded-xl border-2 border-transparent transition-colors group-hover:border-blue-400 dark:group-hover:border-blue-500"
          />
        </button>
      {/each}
    </div>
    <!-- Show on Startup Checkbox and Continue -->
    <div
      class="flex flex-col sm:flex-row items-center justify-between gap-4 mt-2"
    >
      <label class="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={showLandingOnStartup}
          on:change={onToggleShowOnStartup}
          class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800"
        />
        <span class="text-sm text-gray-600 dark:text-gray-400"
          >Show this page on startup</span
        >
      </label>
      <button
        on:click={onDismiss}
        class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
      >
        Continue to Editor
      </button>
    </div>
  </div>
</div>

<style lang="postcss">
  :global(html) {
    color-scheme: light;
    transition: color-scheme 200ms ease-out;
  }

  :global(html.dark) {
    color-scheme: dark;
  }
</style>
