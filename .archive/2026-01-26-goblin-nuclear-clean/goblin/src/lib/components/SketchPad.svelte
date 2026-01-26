<script lang="ts">
  /**
   * SketchPad - nano-banana Prompt Sketch Pad
   * 
   * A minimal interface for quick AI sketch generation using Gemini's
   * image generation capabilities. Produces simple, technical diagrams.
   */
  import { generateImage, type GenerationResponse } from '$lib/services/ai';
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher<{
    insert: { markdown: string; imageUrl: string };
    close: void;
  }>();

  // State
  let prompt = $state('');
  let isGenerating = $state(false);
  let error = $state<string | null>(null);
  let generatedImage = $state<string | null>(null);
  let history = $state<Array<{ prompt: string; imageUrl: string }>>([]);

  // Style presets for quick sketches
  const presets = [
    { label: '📊 Diagram', prefix: 'technical diagram of' },
    { label: '🔧 Parts', prefix: 'exploded parts view of' },
    { label: '📐 Blueprint', prefix: 'blueprint schematic of' },
    { label: '🗺️ Map', prefix: 'simple map showing' },
    { label: '📋 Flowchart', prefix: 'flowchart showing' },
    { label: '🎨 Sketch', prefix: 'hand-drawn sketch of' },
  ];

  let selectedPreset = $state(0);

  async function generateSketch() {
    if (!prompt.trim()) return;

    isGenerating = true;
    error = null;

    try {
      const fullPrompt = `${presets[selectedPreset].prefix} ${prompt}. 
        Style: Clean black and white technical illustration, minimal shading, 
        clear labels, suitable for documentation.`;

      const result = await generateImage({
        prompt: fullPrompt,
        type: 'sketch',
      });

      if (result.success && (result.imageUrl || result.imageBase64)) {
        const imageUrl = result.imageUrl || `data:image/png;base64,${result.imageBase64}`;
        generatedImage = imageUrl;
        history = [{ prompt, imageUrl }, ...history.slice(0, 9)];
      } else {
        error = result.error || 'Failed to generate image';
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
    } finally {
      isGenerating = false;
    }
  }

  function insertImage() {
    if (generatedImage) {
      const markdown = `![${prompt}](${generatedImage})`;
      dispatch('insert', { markdown, imageUrl: generatedImage });
      generatedImage = null;
      prompt = '';
    }
  }

  function close() {
    dispatch('close');
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
      generateSketch();
    } else if (event.key === 'Escape') {
      close();
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div
  class="sketchpad"
  role="application"
  aria-label="Sketch pad"
>
  <header class="sketchpad-header">
    <h3>🍌 Sketch Pad</h3>
    <button class="close-btn" onclick={close}>×</button>
  </header>

  <div class="preset-bar">
    {#each presets as preset, i}
      <button 
        class="preset-btn" 
        class:active={selectedPreset === i}
        onclick={() => selectedPreset = i}
      >
        {preset.label}
      </button>
    {/each}
  </div>

  <div class="input-area">
    <textarea
      bind:value={prompt}
      placeholder="Describe what you want to sketch..."
      rows="3"
      disabled={isGenerating}
    ></textarea>
    <button 
      class="generate-btn" 
      onclick={generateSketch}
      disabled={isGenerating || !prompt.trim()}
    >
      {isGenerating ? '⏳ Generating...' : '✏️ Generate Sketch'}
    </button>
  </div>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  {#if generatedImage}
    <div class="preview">
      <img src={generatedImage} alt={prompt} />
      <div class="preview-actions">
        <button class="insert-btn" onclick={insertImage}>
          📥 Insert into Document
        </button>
        <button class="retry-btn" onclick={generateSketch}>
          🔄 Regenerate
        </button>
      </div>
    </div>
  {/if}

  {#if history.length > 0}
    <div class="history">
      <h4>Recent Sketches</h4>
      <div class="history-grid">
        {#each history as item}
          <button 
            class="history-item"
            onclick={() => {
              generatedImage = item.imageUrl;
              prompt = item.prompt;
            }}
          >
            <img src={item.imageUrl} alt={item.prompt} />
          </button>
        {/each}
      </div>
    </div>
  {/if}

  <footer class="sketchpad-footer">
    <span class="hint">⌘+Enter to generate • Esc to close</span>
  </footer>
</div>

<style>
  .sketchpad {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
    background: var(--bg-secondary, #1a1a1a);
    border-radius: 8px;
    max-width: 400px;
    max-height: 600px;
    overflow-y: auto;
  }

  .sketchpad-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .sketchpad-header h3 {
    margin: 0;
    font-size: 1.1rem;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: var(--text-muted, #888);
  }

  .preset-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .preset-btn {
    padding: 4px 8px;
    font-size: 0.75rem;
    background: var(--bg-tertiary, #2a2a2a);
    border: 1px solid transparent;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .preset-btn:hover {
    background: var(--bg-hover, #333);
  }

  .preset-btn.active {
    border-color: var(--accent, #4a9eff);
    background: var(--accent-bg, #1a3a5a);
  }

  .input-area {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid var(--border, #333);
    border-radius: 4px;
    background: var(--bg-input, #0a0a0a);
    color: var(--text, #fff);
    resize: vertical;
    font-family: inherit;
  }

  textarea:focus {
    outline: none;
    border-color: var(--accent, #4a9eff);
  }

  .generate-btn {
    padding: 10px 16px;
    background: var(--accent, #4a9eff);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: opacity 0.2s;
  }

  .generate-btn:hover:not(:disabled) {
    opacity: 0.9;
  }

  .generate-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .error {
    padding: 8px;
    background: #3a1a1a;
    border: 1px solid #a33;
    border-radius: 4px;
    color: #f88;
    font-size: 0.85rem;
  }

  .preview {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .preview img {
    width: 100%;
    border-radius: 4px;
    border: 1px solid var(--border, #333);
  }

  .preview-actions {
    display: flex;
    gap: 8px;
  }

  .insert-btn, .retry-btn {
    flex: 1;
    padding: 8px;
    border: 1px solid var(--border, #333);
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
  }

  .insert-btn {
    background: var(--success-bg, #1a3a1a);
    color: var(--success, #4a4);
  }

  .retry-btn {
    background: var(--bg-tertiary, #2a2a2a);
  }

  .history h4 {
    margin: 0 0 8px;
    font-size: 0.85rem;
    color: var(--text-muted, #888);
  }

  .history-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 4px;
  }

  .history-item {
    aspect-ratio: 1;
    padding: 0;
    border: 1px solid var(--border, #333);
    border-radius: 4px;
    overflow: hidden;
    cursor: pointer;
    background: none;
  }

  .history-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .sketchpad-footer {
    border-top: 1px solid var(--border, #333);
    padding-top: 8px;
  }

  .hint {
    font-size: 0.75rem;
    color: var(--text-muted, #666);
  }
</style>
