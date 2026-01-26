<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import {
    getKeypadLayer,
    setKeypadLayer,
    onKeypadLayerChange,
    type KeypadLayer,
  } from "$lib/services/keyboardManager";
  import { emit } from "@tauri-apps/api/event";

  interface Props {
    isOpen?: boolean;
    onClose?: () => void;
  }

  let { isOpen = true, onClose = () => {} }: Props = $props();

  let keypadMode = $state<"calculator" | "keyboard">("calculator");
  let currentLayer = $state<KeypadLayer>("number");
  let unsubscribe: (() => void) | null = null;

  onMount(() => {
    currentLayer = getKeypadLayer();
    unsubscribe = onKeypadLayerChange((layer) => {
      currentLayer = layer;
    });
  });

  onDestroy(() => {
    if (unsubscribe) unsubscribe();
  });

  const handleKeyPress = (key: string, fKey?: string) => {
    console.log("[Keypad] Key pressed:", key, fKey);
    if (fKey) {
      // Emit F-key event
      emit("execute-function-key", { key: fKey });
    } else {
      // Simulate key press
      const event = new KeyboardEvent("keydown", {
        key,
        code: key,
        bubbles: true,
        cancelable: true,
      });
      document.dispatchEvent(event);
    }
  };

  const toggleMode = () => {
    keypadMode = keypadMode === "calculator" ? "keyboard" : "calculator";
  };

  const toggleLayer = () => {
    const layers: KeypadLayer[] = ["function", "number", "arrows"];
    const currentIndex = layers.indexOf(currentLayer);
    const nextLayer = layers[(currentIndex + 1) % layers.length];
    setKeypadLayer(nextLayer);
  };

  // Standard keypad layouts
  const functionKeys = [
    { label: "F1", value: "F1", fkey: "F1" },
    { label: "F2", value: "F2", fkey: "F2" },
    { label: "F3", value: "F3", fkey: "F3" },
    { label: "F4", value: "F4", fkey: "F4" },
    { label: "F5", value: "F5", fkey: "F5" },
    { label: "F6", value: "F6", fkey: "F6" },
    { label: "F7", value: "F7", fkey: "F7" },
    { label: "F8", value: "F8", fkey: "F8" },
    { label: "F9", value: "F9", fkey: "F9" },
    { label: "F10", value: "F10", fkey: "F10" },
    { label: "F11", value: "F11", fkey: "F11" },
    { label: "F12", value: "F12", fkey: "F12" },
  ];

  const numberKeys = [
    { label: "7", value: "7" },
    { label: "8", value: "8" },
    { label: "9", value: "9" },
    { label: "÷", value: "/" },
    { label: "4", value: "4" },
    { label: "5", value: "5" },
    { label: "6", value: "6" },
    { label: "×", value: "*" },
    { label: "1", value: "1" },
    { label: "2", value: "2" },
    { label: "3", value: "3" },
    { label: "−", value: "-" },
    { label: "0", value: "0" },
    { label: ".", value: "." },
    { label: "=", value: "=" },
    { label: "+", value: "+" },
  ];

  const arrowKeys = [
    { label: "⌫", value: "Backspace" },
    { label: "↑", value: "ArrowUp" },
    { label: "⌦", value: "Delete" },
    { label: "", value: "" },
    { label: "←", value: "ArrowLeft" },
    { label: "↓", value: "ArrowDown" },
    { label: "→", value: "ArrowRight" },
    { label: "", value: "" },
    { label: "Home", value: "Home" },
    { label: "PgUp", value: "PageUp" },
    { label: "PgDn", value: "PageDown" },
    { label: "End", value: "End" },
    { label: "⏎", value: "Enter" },
    { label: "⇥", value: "Tab" },
    { label: "Esc", value: "Escape" },
    { label: "", value: "" },
  ];

  // QWERTY layout - 11 keys x 3 rows
  const qwertyRows = [
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "⌫"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L", "⏎", "⏎"],
    ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "?", "!"],
  ];

  const qwertyModifiers = [
    { label: "SHIFT", value: "Shift" },
    { label: "⌘", value: "Meta" },
    { label: "SPACE", value: " " },
    { label: "OK", value: "Enter" },
  ];
</script>

{#if isOpen}
  <aside
    class="fixed top-0 right-0 bottom-0 w-96 bg-gray-100 dark:bg-gray-900 border-l border-gray-300 dark:border-gray-800 flex flex-col shadow-2xl z-30"
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
            d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
          />
        </svg>
        <h2 class="font-semibold text-gray-900 dark:text-gray-100">
          Keypad & Calculator
        </h2>
      </div>
      <div class="flex items-center gap-2">
        <!-- Toggle Keypad Visibility -->
        <button
          class="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-800 rounded"
          onclick={onClose}
          title="Toggle Keypad"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            class="w-5 h-5 text-gray-700 dark:text-gray-300"
          >
            <path
              d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM7 5h2v2H7V5zm0 4h2v2H7V9zm0 4h2v2H7v-2zm4-8h2v2h-2V5zm0 4h2v2h-2V9zm0 4h2v2h-2v-2zm0 4h2v2h-2v-2zm4-12h2v2h-2V5zm0 4h2v2h-2V9zm0 4h2v2h-2v-2z"
            />
          </svg>
        </button>
        <!-- Mode Toggle -->
        <button
          class="px-3 py-1 text-xs rounded {keypadMode === 'calculator'
            ? 'bg-blue-500 text-white'
            : 'bg-green-500 text-white'}"
          onclick={toggleMode}
          title="Toggle between calculator and keyboard"
        >
          {keypadMode === "calculator" ? "Calculator" : "Keyboard"}
        </button>
        <!-- Close Button -->
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

    <!-- Keypad Area -->
    <div class="flex-1 overflow-y-auto p-4">
      {#if keypadMode === "calculator"}
        <!-- Layer Toggle -->
        <div class="mb-4">
          <button
            class="w-full py-2 px-4 bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 rounded text-sm font-medium transition-colors"
            onclick={toggleLayer}
          >
            Layer: {currentLayer === "function"
              ? "Function Keys"
              : currentLayer === "number"
                ? "Numbers"
                : "Arrows"}
          </button>
        </div>

        <!-- Standard Keypad Grid -->
        {#if currentLayer === "function"}
          <div class="grid grid-cols-3 gap-2">
            {#each functionKeys as key}
              <button
                class="aspect-square bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-700 rounded-lg shadow-sm active:shadow-none active:translate-y-0.5 transition-all font-semibold text-sm"
                onclick={() => handleKeyPress(key.value, key.fkey)}
              >
                {key.label}
              </button>
            {/each}
          </div>
        {:else if currentLayer === "number"}
          <div class="grid grid-cols-4 gap-2">
            {#each numberKeys as key}
              <button
                class="aspect-square bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-700 rounded-lg shadow-sm active:shadow-none active:translate-y-0.5 transition-all font-semibold text-lg"
                onclick={() => handleKeyPress(key.value)}
              >
                {key.label}
              </button>
            {/each}
          </div>
        {:else}
          <div class="grid grid-cols-4 gap-2">
            {#each arrowKeys as key}
              {#if key.value}
                <button
                  class="aspect-square bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-700 rounded-lg shadow-sm active:shadow-none active:translate-y-0.5 transition-all font-semibold text-sm"
                  onclick={() => handleKeyPress(key.value)}
                >
                  {key.label}
                </button>
              {:else}
                <div></div>
              {/if}
            {/each}
          </div>
        {/if}
      {:else}
        <!-- QWERTY Layout -->
        <div class="space-y-2">
          {#each qwertyRows as row, i}
            <div class="grid grid-cols-11 gap-1">
              {#each row as key}
                <button
                  class="aspect-square bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-700 rounded shadow-sm active:shadow-none active:translate-y-0.5 transition-all font-semibold text-sm {key ===
                  '⏎'
                    ? 'col-span-1'
                    : ''}"
                  class:col-span-2={key === "⏎"}
                  onclick={() =>
                    handleKeyPress(
                      key === "⌫"
                        ? "Backspace"
                        : key === "⏎"
                          ? "Enter"
                          : key.toLowerCase()
                    )}
                >
                  {key}
                </button>
              {/each}
            </div>
          {/each}

          <!-- Modifier Row -->
          <div class="grid grid-cols-4 gap-2 mt-4">
            {#each qwertyModifiers as mod}
              <button
                class="py-3 bg-blue-500 hover:bg-blue-600 text-white border border-blue-600 rounded shadow-sm active:shadow-none active:translate-y-0.5 transition-all font-semibold text-sm"
                onclick={() => handleKeyPress(mod.value)}
              >
                {mod.label}
              </button>
            {/each}
          </div>
        </div>
      {/if}
    </div>

    <!-- Footer Info -->
    <footer
      class="border-t border-gray-300 dark:border-gray-800 px-4 py-2 text-xs text-gray-500 dark:text-gray-500"
    >
      {keypadMode === "calculator" ? "Calculator/Keypad" : "Compact Keyboard"} •
      {keypadMode === "calculator" ? currentLayer : "33 keys"}
    </footer>
  </aside>
{/if}
