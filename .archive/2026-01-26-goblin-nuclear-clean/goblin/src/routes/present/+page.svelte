<script lang="ts">
  /**
   * Marp Presentation Mode
   * Full-screen slide presentation with Marp rendering
   * Activated via F8/Cmd+8 or from editor when marp: true is detected
   */
  import { onMount, onDestroy } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { listen, type UnlistenFn } from "@tauri-apps/api/event";
  import { invoke } from "@tauri-apps/api/core";
  import { Marp } from "@marp-team/marp-core";

  let markdown = $state("");
  let slides: string[] = $state([]);
  let currentSlide = $state(0);
  let renderedSlides: { html: string; css: string }[] = $state([]);
  let filePath = $state<string | null>(null);
  let isMarpFile = $state(false);
  let unlisteners: UnlistenFn[] = [];

  // Initialize Marp renderer
  const marp = new Marp({
    html: true,
    emoji: {
      shortcode: true,
      unicode: true,
    },
  });

  onMount(async () => {
    // Get file path from URL params
    const urlParams = new URLSearchParams(window.location.search);
    filePath = urlParams.get("file");

    if (filePath) {
      await loadFile(filePath);
    }

    // Listen for toggle-presentation event
    const unlisten = await listen<{ file?: string }>(
      "toggle-presentation",
      async (event) => {
        if (event.payload.file) {
          await loadFile(event.payload.file);
        } else {
          // Toggle off presentation mode
          await exitPresentation();
        }
      }
    );
    unlisteners.push(unlisten);

    // Keyboard navigation
    document.addEventListener("keydown", handleKeydown);
  });

  onDestroy(() => {
    unlisteners.forEach((fn) => fn());
    document.removeEventListener("keydown", handleKeydown);
  });

  async function loadFile(path: string) {
    try {
      const content = await invoke<string>("read_file", { path });
      markdown = content;
      filePath = path;

      // Check for marp: true in frontmatter
      isMarpFile = /^---\s*\nmarp:\s*true/m.test(markdown);

      if (isMarpFile) {
        renderMarpSlides();
      } else {
        // Fall back to simple HR-split slides
        slides = markdown.split(/\n---\n/);
        currentSlide = 0;
      }
    } catch (err) {
      console.error("[Present] Failed to load file:", err);
    }
  }

  function renderMarpSlides() {
    try {
      const { html, css } = marp.render(markdown);

      // Extract individual slides from rendered HTML
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const slideElements = doc.querySelectorAll("section");

      renderedSlides = Array.from(slideElements).map((section) => ({
        html: section.innerHTML,
        css: css,
      }));

      currentSlide = 0;
    } catch (err) {
      console.error("[Present] Failed to render Marp slides:", err);
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      exitPresentation();
    } else if (e.key === "ArrowRight" || e.key === " ") {
      nextSlide();
    } else if (e.key === "ArrowLeft") {
      previousSlide();
    } else if (e.key === "Home") {
      currentSlide = 0;
    } else if (e.key === "End") {
      currentSlide = isMarpFile ? renderedSlides.length - 1 : slides.length - 1;
    }
  }

  function nextSlide() {
    const maxSlide = isMarpFile ? renderedSlides.length - 1 : slides.length - 1;
    if (currentSlide < maxSlide) {
      currentSlide++;
    }
  }

  function previousSlide() {
    if (currentSlide > 0) {
      currentSlide--;
    }
  }

  async function exitPresentation() {
    // Return to editor with the same file
    if (filePath) {
      await goto(`/editor?file=${encodeURIComponent(filePath)}`);
    } else {
      await goto("/editor");
    }
  }

  const totalSlides = $derived(
    isMarpFile ? renderedSlides.length : slides.length
  );
</script>

<svelte:head>
  <title>Presentation Mode - Markdown</title>
  {#if isMarpFile && renderedSlides[currentSlide]}
    <style>
      {@html renderedSlides[currentSlide].css}
    </style>
  {/if}
</svelte:head>

<div
  class="presentation-container"
  style="
    position: fixed;
    inset: 0;
    background: #000;
    color: #fff;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  "
>
  <!-- Slide Content -->
  <main
    class="slide-viewer"
    style="
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      overflow: hidden;
    "
  >
    {#if isMarpFile && renderedSlides[currentSlide]}
      <!-- Marp-rendered slide -->
      <section
        class="marp-slide"
        style="
          width: 100%;
          height: 100%;
          max-width: 960px;
          max-height: 720px;
          background: #fff;
          color: #000;
          padding: 2rem;
          border-radius: 8px;
          box-shadow: 0 10px 50px rgba(0,0,0,0.5);
          overflow: auto;
        "
      >
        {@html renderedSlides[currentSlide].html}
      </section>
    {:else if slides[currentSlide]}
      <!-- Simple markdown slide -->
      <section
        class="simple-slide prose prose-invert max-w-4xl"
        style="
          background: rgba(255,255,255,0.05);
          padding: 3rem;
          border-radius: 12px;
          max-height: 80vh;
          overflow: auto;
        "
      >
        {slides[currentSlide]}
      </section>
    {:else}
      <div class="text-center">
        <h1 class="text-4xl font-bold mb-4">No Slides Found</h1>
        <p class="text-xl opacity-70">Press Esc to return to editor</p>
      </div>
    {/if}
  </main>

  <!-- Navigation Controls -->
  <footer
    class="presentation-controls"
    style="
      padding: 1rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(0,0,0,0.8);
      backdrop-filter: blur(10px);
      border-top: 1px solid rgba(255,255,255,0.1);
    "
  >
    <div class="flex items-center gap-4">
      <button
        class="control-button"
        onclick={previousSlide}
        disabled={currentSlide === 0}
        style="
          padding: 0.5rem 1rem;
          background: rgba(255,255,255,0.1);
          border: 1px solid rgba(255,255,255,0.2);
          border-radius: 6px;
          color: #fff;
          cursor: pointer;
          transition: all 0.2s;
        "
        style:opacity={currentSlide === 0 ? "0.3" : "1"}
      >
        ← Previous
      </button>
      <span
        class="slide-counter"
        style="font-family: monospace; font-size: 1.1rem;"
      >
        {currentSlide + 1} / {totalSlides}
      </span>
      <button
        class="control-button"
        onclick={nextSlide}
        disabled={currentSlide >= totalSlides - 1}
        style="
          padding: 0.5rem 1rem;
          background: rgba(255,255,255,0.1);
          border: 1px solid rgba(255,255,255,0.2);
          border-radius: 6px;
          color: #fff;
          cursor: pointer;
          transition: all 0.2s;
        "
        style:opacity={currentSlide >= totalSlides - 1 ? "0.3" : "1"}
      >
        Next →
      </button>
    </div>

    <div class="flex items-center gap-4">
      {#if isMarpFile}
        <span
          class="marp-badge"
          style="
            padding: 0.25rem 0.75rem;
            background: linear-gradient(135deg, #00d4ff, #0099ff);
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 600;
            color: #000;
          "
        >
          MARP
        </span>
      {/if}
      <button
        class="exit-button"
        onclick={exitPresentation}
        style="
          padding: 0.5rem 1rem;
          background: rgba(255,71,71,0.2);
          border: 1px solid rgba(255,71,71,0.4);
          border-radius: 6px;
          color: #ff4747;
          cursor: pointer;
          transition: all 0.2s;
          font-weight: 600;
        "
      >
        Exit (Esc)
      </button>
    </div>
  </footer>
</div>

<style>
  .control-button:not([disabled]):hover {
    background: rgba(255, 255, 255, 0.2) !important;
    transform: scale(1.05);
  }

  .exit-button:hover {
    background: rgba(255, 71, 71, 0.3) !important;
    transform: scale(1.05);
  }

  /* Marp slide isolation */
  .marp-slide :global(section) {
    all: initial;
    display: block;
  }

  /* Simple slide typography */
  .simple-slide {
    line-height: 1.8;
  }

  .simple-slide :global(h1) {
    font-size: 3rem;
    margin-bottom: 1.5rem;
  }

  .simple-slide :global(h2) {
    font-size: 2rem;
    margin: 1.5rem 0 1rem;
  }

  .simple-slide :global(p) {
    font-size: 1.25rem;
    margin: 1rem 0;
  }

  .simple-slide :global(ul),
  .simple-slide :global(ol) {
    font-size: 1.25rem;
    margin: 1rem 0;
  }

  .simple-slide :global(code) {
    background: rgba(0, 0, 0, 0.3);
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
  }
</style>
