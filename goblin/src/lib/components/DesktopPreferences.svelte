<script lang="ts">
  /**
   * DesktopPreferences - Desktop-specific settings panel
   *
   * Configures:
   * - UI Font (Apple retro fonts for menus, titles, buttons)
   * - Desktop Pattern (15 System 7 patterns)
   * - Icon Set (API-driven)
   */

  interface Props {
    open: boolean;
    selectedPattern: string;
    onClose: () => void;
    onSave: (pattern: string) => void;
  }

  let { open, selectedPattern, onClose, onSave }: Props = $props();

  // Available Apple retro fonts
  const appleFonts = [
    { id: "chicagoflf", name: "ChicagoFLF", family: "'ChicagoFLF', monospace" },
    { id: "athens", name: "Athens", family: "'Athene', sans-serif" },
    {
      id: "lexington",
      name: "Lexington",
      family: "'Lexington-Gothic', sans-serif",
    },
    { id: "liverpool", name: "Liverpool", family: "'Liverpool', serif" },
    { id: "losaltos", name: "Los Altos", family: "'Los Altos', sans-serif" },
    { id: "monaco", name: "Monaco", family: "'monaco', monospace" },
    { id: "parcplace", name: "Parc Place", family: "'Parc Place', serif" },
    {
      id: "sanfrisco",
      name: "San Francisco",
      family: "'Sanfrisco', sans-serif",
    },
    { id: "torrance", name: "Torrance", family: "'Torrance', sans-serif" },
    { id: "valencia", name: "Valencia", family: "'Valencia', serif" },
  ];

  // Desktop patterns
  const patterns = [
    { id: "solid-white", name: "White" },
    { id: "solid-gray", name: "Gray" },
    { id: "checkerboard", name: "Check" },
    { id: "dots", name: "Dots" },
    { id: "dense-dots", name: "Dense" },
    { id: "lines-h", name: "Horizontal" },
    { id: "lines-v", name: "Vertical" },
    { id: "diagonal", name: "Diagonal" },
    { id: "grid", name: "Grid" },
    { id: "crosshatch", name: "Crosshatch" },
    { id: "brick", name: "Brick" },
    { id: "weave", name: "Weave" },
    { id: "diamond", name: "Diamond" },
    { id: "scales", name: "Scales" },
    { id: "tiles", name: "Tiles" },
  ];

  // Local state - initialize and sync with props
  let localPattern = $state("");

  $effect(() => {
    localPattern = selectedPattern;
  });

  function handleSave() {
    onSave(localPattern);
    onClose();
  }

  function handleCancel() {
    onClose();
  }
</script>

{#if open}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <!-- Backdrop -->
  <div
    class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center"
    onclick={handleCancel}
  >
    <!-- Preferences Window -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="bg-white border-2 border-black shadow-2xl w-[500px] max-h-[600px] flex flex-col text-black"
      onclick={(e: MouseEvent) => e.stopPropagation()}
    >
      <!-- Title Bar -->
      <div
        class="flex items-center justify-between px-3 py-2 border-b-2 border-black bg-gray-100 text-black"
      >
        <span class="font-bold">Desktop Preferences</span>
        <button
          class="px-2 py-1 text-xs bg-white border border-black hover:bg-gray-200 text-black"
          onclick={handleCancel}
        >
          ✕
        </button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-auto p-4 space-y-6 text-black">
        <!-- Desktop Pattern Section -->
        <div>
          <h3 class="font-bold mb-2 text-sm text-black">Desktop Pattern</h3>
          <p class="text-xs text-gray-700 mb-3">System 7 classic patterns</p>
          <div class="grid grid-cols-5 gap-2">
            {#each patterns as pattern}
              <button
                class="h-12 border-2 transition-all pattern-{pattern.id} {localPattern ===
                `pattern-${pattern.id}`
                  ? 'border-black scale-110'
                  : 'border-gray-300 hover:border-gray-400'}"
                title={pattern.name}
                onclick={() => (localPattern = `pattern-${pattern.id}`)}
              >
                <span class="sr-only">{pattern.name}</span>
              </button>
            {/each}
          </div>
          <div class="mt-2 text-center text-xs text-gray-700">
            {patterns.find((p) => `pattern-${p.id}` === localPattern)?.name ||
              "Select pattern"}
          </div>
        </div>

        <!-- Note about body font -->
        <div class="p-3 border border-gray-300 bg-blue-50 text-xs text-black">
          <strong>Note:</strong> Content body font is controlled globally via
          the <strong>F</strong> button in the bottom toolbar (applies to Typo editor
          and all markdown views). Desktop UI uses the font selected above.
        </div>
      </div>

      <!-- Footer -->
      <div
        class="flex items-center justify-end gap-2 px-4 py-3 border-t-2 border-black bg-gray-100"
      >
        <button
          class="px-4 py-2 text-sm bg-white border-2 border-black hover:bg-gray-200 text-black"
          onclick={handleCancel}
        >
          Cancel
        </button>
        <button
          class="px-4 py-2 text-sm bg-black text-white border-2 border-black hover:bg-gray-800"
          onclick={handleSave}
        >
          Save
        </button>
      </div>
    </div>
  </div>
{/if}
