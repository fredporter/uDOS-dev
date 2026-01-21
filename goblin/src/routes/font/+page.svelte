<script lang="ts">
  import { onMount } from "svelte";

  interface FontInfo {
    name: string;
    file: string;
    type: string;
    author: string;
    license: string;
    description: string;
    category: string;
  }

  let fonts: FontInfo[] = $state([]);
  let selectedFont = $state<FontInfo | null>(null);
  let markdownContent = $state("");
  let renderedHtml = $state("");
  let fontSize = $state(16);
  let isLoading = $state(true);

  // Load manifest and markdown
  onMount(async () => {
    try {
      // Load manifest (try both locations)
      let manifestRes;
      try {
        manifestRes = await fetch("/fonts/manifest.json");
      } catch {
        // Fallback to fonts directory
        manifestRes = await fetch("/fonts/manifest.json");
      }
      const manifest = await manifestRes.json();
      
      // Parse fonts from manifest
      const fontList: FontInfo[] = [];
      for (const [categoryName, category] of Object.entries(manifest.collections)) {
        for (const [subcategoryName, subcategory] of Object.entries(category as any)) {
          for (const [fontKey, fontData] of Object.entries(subcategory as any)) {
            fontList.push({
              name: (fontData as any).name,
              file: (fontData as any).file,
              type: (fontData as any).type,
              author: (fontData as any).author,
              license: (fontData as any).license,
              description: (fontData as any).description,
              category: `${categoryName}/${subcategoryName}`
            });
          }
        }
      }
      fonts = fontList;
      
      // Load markdown test file
      const mdRes = await fetch("/font-test.md");
      markdownContent = await mdRes.text();
      
      // Select first font by default
      if (fonts.length > 0) {
        selectFont(fonts[0]);
      }
      
      isLoading = false;
    } catch (err) {
      console.error("Failed to load fonts:", err);
      isLoading = false;
    }
  });

  function selectFont(font: FontInfo) {
    selectedFont = font;
    loadFontFace(font);
  }

  function loadFontFace(font: FontInfo) {
    console.log(`[FontDemo] Loading font: ${font.name} from /fonts/${font.file}`);
    const fontFace = new FontFace(
      font.name,
      `url(/fonts/${font.file})`
    );
    
    fontFace.load().then((loaded) => {
      console.log(`[FontDemo] Font loaded successfully: ${font.name}`);
      document.fonts.add(loaded);
      renderMarkdown();
    }).catch((err) => {
      console.error(`[FontDemo] Failed to load font ${font.name}:`, err);
      console.error(`[FontDemo] Font path attempted: /fonts/${font.file}`);
    });
  }

  function renderMarkdown() {
    if (!markdownContent) {
      renderedHtml = "";
      return;
    }

    // Simple markdown to HTML conversion
    let html = markdownContent
      // Headers
      .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      // Bold and italic
      .replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Code
      .replace(/`(.*?)`/g, '<code>$1</code>')
      // Code blocks
      .replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>')
      // Blockquotes
      .replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>')
      // Lists (simplified)
      .replace(/^\- (.*$)/gim, '<li>$1</li>')
      .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
      // Horizontal rule
      .replace(/^---$/gim, '<hr>')
      // Small text
      .replace(/<small>(.*?)<\/small>/g, '<small>$1</small>')
      // Divs (pass through)
      .replace(/<div style="([^"]+)">(.*?)<\/div>/gs, '<div style="$1">$2</div>')
      // Tables
      .replace(/^\|(.+)\|$/gim, (match) => {
        const cells = match.slice(1, -1).split('|').map(c => c.trim());
        return '<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>';
      })
      // Paragraphs
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');

    // Wrap in paragraph tags
    html = '<p>' + html + '</p>';
    
    // Clean up empty paragraphs
    html = html.replace(/<p><\/p>/g, '');
    html = html.replace(/<p><h/g, '<h').replace(/<\/h(\d)><\/p>/g, '</h$1>');
    html = html.replace(/<p><hr><\/p>/g, '<hr>');
    html = html.replace(/<p><pre>/g, '<pre>').replace(/<\/pre><\/p>/g, '</pre>');
    html = html.replace(/<p><blockquote>/g, '<blockquote>').replace(/<\/blockquote><\/p>/g, '</blockquote>');

    renderedHtml = html;
  }

  function adjustFontSize(delta: number) {
    fontSize = Math.max(8, Math.min(72, fontSize + delta));
  }
</script>

<div class="h-screen bg-slate-900 text-slate-100 flex flex-col">
  <!-- Header -->
  <div class="bg-slate-800 border-b border-slate-700 p-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">🎨 uFont Manager</h1>
        <p class="text-sm text-slate-400">Beta v1.0.0 • Font Repository & Testing</p>
      </div>
      <div class="text-right text-xs text-slate-500">
        <div>{fonts.length} fonts loaded</div>
        <div>Repository: /dev/goblin/fonts/</div>
      </div>
    </div>
  </div>

  {#if isLoading}
    <div class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="animate-spin text-4xl mb-4">⚙️</div>
        <div class="text-slate-400">Loading fonts...</div>
      </div>
    </div>
  {:else}
    <div class="flex-1 flex overflow-hidden">
      <!-- Sidebar -->
      <div class="w-80 bg-slate-800 border-r border-slate-700 flex flex-col overflow-hidden">
        <div class="p-4 border-b border-slate-700">
          <h2 class="font-bold mb-2">Font Collections</h2>
          <div class="text-xs text-slate-400">Select a font to test</div>
        </div>

        <div class="flex-1 overflow-y-auto">
          {#each fonts as font}
            <button
              onclick={() => selectFont(font)}
              class="w-full text-left p-3 border-b border-slate-700 hover:bg-slate-700 transition-colors {selectedFont?.name === font.name ? 'bg-slate-700' : ''}"
            >
              <div class="font-bold text-sm">{font.name}</div>
              <div class="text-xs text-slate-400">{font.category}</div>
              <div class="text-xs text-slate-500 mt-1">{font.author}</div>
              <div class="text-xs text-slate-600">{font.license}</div>
            </button>
          {/each}
        </div>

        <!-- Font Controls -->
        <div class="p-4 border-t border-slate-700 bg-slate-800">
          <div class="mb-2 text-sm font-bold">Font Size: {fontSize}px</div>
          <div class="flex gap-2">
            <button
              onclick={() => adjustFontSize(-2)}
              class="flex-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded"
            >
              A-
            </button>
            <button
              onclick={() => fontSize = 16}
              class="flex-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded text-xs"
            >
              Reset
            </button>
            <button
              onclick={() => adjustFontSize(2)}
              class="flex-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded"
            >
              A+
            </button>
          </div>
        </div>
      </div>

      <!-- Preview Area -->
      <div class="flex-1 flex flex-col overflow-hidden">
        {#if selectedFont}
          <!-- Font Info Bar -->
          <div class="bg-slate-800 border-b border-slate-700 p-3">
            <div class="flex items-center justify-between">
              <div>
                <span class="font-bold">{selectedFont.name}</span>
                <span class="text-slate-400 text-sm ml-3">{selectedFont.description}</span>
              </div>
              <div class="flex gap-4 text-xs text-slate-500">
                <span>Type: {selectedFont.type}</span>
                <span>File: {selectedFont.file}</span>
              </div>
            </div>
          </div>

          <!-- Rendered Content -->
          <div class="flex-1 overflow-y-auto bg-white p-8">
            <div 
              class="prose prose-slate max-w-none"
              style="font-family: '{selectedFont.name}', monospace; font-size: {fontSize}px; color: #1e293b;"
            >
              {@html renderedHtml}
            </div>
          </div>
        {:else}
          <div class="flex-1 flex items-center justify-center text-slate-500">
            Select a font from the sidebar to preview
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  :global(.prose h1) { 
    font-size: 2em; 
    font-weight: bold; 
    margin: 1em 0 0.5em; 
    border-bottom: 2px solid #cbd5e1;
    padding-bottom: 0.3em;
  }
  :global(.prose h2) { 
    font-size: 1.5em; 
    font-weight: bold; 
    margin: 1em 0 0.5em; 
  }
  :global(.prose h3) { 
    font-size: 1.25em; 
    font-weight: bold; 
    margin: 0.8em 0 0.4em; 
  }
  :global(.prose h4) { 
    font-size: 1.1em; 
    font-weight: bold; 
    margin: 0.6em 0 0.3em; 
  }
  :global(.prose p) { 
    margin: 0.5em 0; 
    line-height: 1.6; 
  }
  :global(.prose code) { 
    background: #f1f5f9; 
    padding: 0.2em 0.4em; 
    border-radius: 3px;
    font-size: 0.9em;
  }
  :global(.prose pre) { 
    background: #1e293b; 
    color: #e2e8f0;
    padding: 1em; 
    border-radius: 6px;
    overflow-x: auto;
    margin: 1em 0;
  }
  :global(.prose pre code) {
    background: none;
    padding: 0;
  }
  :global(.prose blockquote) { 
    border-left: 4px solid #94a3b8; 
    padding-left: 1em; 
    margin: 1em 0;
    color: #475569;
    font-style: italic;
  }
  :global(.prose ul, .prose ol) { 
    padding-left: 2em; 
    margin: 0.5em 0;
  }
  :global(.prose li) { 
    margin: 0.25em 0;
  }
  :global(.prose hr) { 
    border: none; 
    border-top: 2px solid #cbd5e1; 
    margin: 2em 0; 
  }
  :global(.prose table) {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
  }
  :global(.prose td) {
    border: 1px solid #cbd5e1;
    padding: 0.5em;
  }
  :global(.prose tr:first-child td) {
    background: #f1f5f9;
    font-weight: bold;
  }
  :global(.prose small) {
    font-size: 0.8em;
    color: #64748b;
  }
  :global(.prose strong) {
    font-weight: bold;
  }
  :global(.prose em) {
    font-style: italic;
  }
</style>
