<script lang="ts">
  import type { CharacterData } from "$lib/util/fontLoader";
  import { getAllColors } from "$lib/util/udosPalette";
  import { onMount } from "svelte";

  type Props = {
    characters: CharacterData[];
    currentCharacter: CharacterData | null;
    onSelect: (char: CharacterData) => void;
    fontFamily?: string;
    gridSize?: number;
    fontType?: "mono" | "color";
  };

  let {
    characters,
    currentCharacter,
    onSelect,
    fontFamily = "monospace",
    gridSize = 24,
    fontType = "mono",
  }: Props = $props();

  // Track dark mode reactively for thumbnail re-rendering
  let isDark = $state(false);
  onMount(() => {
    const update = () => {
      const next = document.documentElement.classList.contains("dark");
      if (next !== isDark) isDark = next;
    };
    update();
    const obs = new MutationObserver(update);
    obs.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
    return () => obs.disconnect();
  });

  // Detect if character is emoji based on code point
  const isEmoji = (code: number): boolean => {
    return (
      code >= 0x1f300 || // Misc symbols and pictographs, emoticons, etc.
      (code >= 0x2600 && code <= 0x26ff) || // Misc symbols
      (code >= 0x2700 && code <= 0x27bf) || // Dingbats
      (code >= 0x231a && code <= 0x23f3) || // Watch, hourglass, etc.
      (code >= 0x2300 && code <= 0x23ff) || // Misc Technical
      (code >= 0x2b50 && code <= 0x2b55) // Stars and circles
    );
  };

  // Render character pixels to a canvas data URL for display
  const renderPixelsToDataURL = (
    char: CharacterData,
    displaySize: number = 32
  ): string => {
    const canvas = document.createElement("canvas");
    canvas.width = displaySize;
    canvas.height = displaySize;
    const ctx = canvas.getContext("2d");
    if (!ctx) return "";

    // Background (theme-aware)
    ctx.fillStyle = isDark ? "#1f2937" : "#f3f4f6"; // dark:gray-800 light:gray-100
    ctx.fillRect(0, 0, displaySize, displaySize);

    const pixels = char.pixels;
    const sourceSize = pixels.length;
    const scale = displaySize / sourceSize;

    // Get uDOS color palette
    const palette = getAllColors();

    for (let row = 0; row < sourceSize; row++) {
      for (let col = 0; col < sourceSize; col++) {
        const pixel = pixels[row]?.[col];

        // Handle color palette index (number)
        if (typeof pixel === "number" && pixel !== null) {
          const color = palette[pixel];
          ctx.fillStyle = color?.hex || "#ffffff";
          ctx.fillRect(
            Math.floor(col * scale),
            Math.floor(row * scale),
            Math.ceil(scale),
            Math.ceil(scale)
          );
        }
        // Handle boolean (mono)
        else if (pixel === true) {
          // Mono pixel color (theme-aware)
          ctx.fillStyle = isDark ? "#f3f4f6" : "#1f2937"; // dark:gray-100 light:gray-800
          ctx.fillRect(
            Math.floor(col * scale),
            Math.floor(row * scale),
            Math.ceil(scale),
            Math.ceil(scale)
          );
        }
      }
    }

    return canvas.toDataURL();
  };
</script>

<div class="space-y-1">
  {#if characters.length === 0}
    <div class="text-center py-8 text-gray-500 text-sm">
      No characters loaded
    </div>
  {:else}
    <div class="grid grid-cols-8 gap-px">
      {#each characters as char}
        {@const hasPixelData = char.pixels?.some((row) => row?.some((p) => p))}
        {@const charIsEmoji = isEmoji(char.code)}
        {#if charIsEmoji}
          <!-- Debug: log emoji rendering -->
          {console.log(
            `[CharacterLibrary] Rendering emoji ${char.char} (U+${char.code.toString(16)}) with fontFamily=${fontFamily}, hasPixelData=${hasPixelData}`
          )}
        {/if}
        <button
          onclick={() => onSelect(char)}
          class="
            aspect-square rounded transition-all
            {currentCharacter?.code === char.code
            ? 'border-2 border-blue-500 bg-blue-100 ring-1 ring-blue-300 dark:bg-blue-900/30 dark:ring-blue-400'
            : 'border border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-900 dark:hover:border-gray-600 dark:hover:bg-gray-800'}
          "
          title={`${char.char} (U+${char.code.toString(16).toUpperCase().padStart(4, "0")})${char.asciiMapping ? ` → ASCII: ${char.asciiMapping}` : ""}`}
        >
          <div
            class="w-full h-full flex items-center justify-center bg-gray-100 dark:bg-gray-800 rounded-sm"
          >
            {#if hasPixelData}
              <!-- Render from pixel data (works for both mono and color) -->
              <img
                src={renderPixelsToDataURL(char, 32)}
                alt={char.char}
                class="w-full h-full object-contain"
                style="image-rendering: pixelated;"
              />
            {:else if charIsEmoji}
              <!-- Emoji without pixel data - render as large emoji with system font -->
              <div
                class="text-2xl leading-none text-gray-800 dark:text-gray-100"
                style="font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;"
              >
                {char.char}
              </div>
            {:else}
              <!-- Regular character fallback: render with provided font -->
              <div
                class="text-base leading-none text-gray-800 dark:text-gray-100"
                style="font-family: {fontFamily}; font-size: {isEmoji(char.code)
                  ? '1.25rem'
                  : '1rem'};"
              >
                {char.char}
              </div>
            {/if}
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>
