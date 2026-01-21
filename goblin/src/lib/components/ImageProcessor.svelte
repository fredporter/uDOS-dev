<script lang="ts">
  /**
   * ImageProcessor - Markdown Image Processor
   * 
   * Processes images in markdown content:
   * - Detects image placeholders like [[generate: description]]
   * - Batch generates images for placeholders
   * - Manages image URLs and base64 data
   */
  import { generateImage, processMarkdownImages } from '$lib/services/ai';
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher<{
    processed: { content: string; imageCount: number };
    progress: { current: number; total: number; description: string };
  }>();

  interface Props {
    content: string;
  }

  let { content }: Props = $props();

  // State
  let isProcessing = $state(false);
  let progress = $state({ current: 0, total: 0, description: '' });
  let error = $state<string | null>(null);
  let placeholders = $state<Array<{ match: string; description: string }>>([]);

  // Detect image placeholders in content
  $effect(() => {
    const pattern = /\[\[(?:generate|sketch|diagram|image):\s*([^\]]+)\]\]/gi;
    const matches: Array<{ match: string; description: string }> = [];
    let match;
    
    while ((match = pattern.exec(content)) !== null) {
      matches.push({
        match: match[0],
        description: match[1].trim(),
      });
    }
    
    placeholders = matches;
  });

  async function processAllPlaceholders() {
    if (placeholders.length === 0) return;

    isProcessing = true;
    error = null;
    progress = { current: 0, total: placeholders.length, description: '' };

    let processedContent = content;

    for (let i = 0; i < placeholders.length; i++) {
      const placeholder = placeholders[i];
      progress = { 
        current: i + 1, 
        total: placeholders.length, 
        description: placeholder.description 
      };

      dispatch('progress', progress);

      try {
        const result = await generateImage({
          prompt: placeholder.description,
          type: 'image',
        });

        if (result.success && (result.imageUrl || result.imageBase64)) {
          const imageUrl = result.imageUrl || `data:image/png;base64,${result.imageBase64}`;
          const markdown = `![${placeholder.description}](${imageUrl})`;
          processedContent = processedContent.replace(placeholder.match, markdown);
        } else {
          // Keep placeholder but mark as failed
          const failedMark = `<!-- AI generation failed: ${placeholder.description} -->\n${placeholder.match}`;
          processedContent = processedContent.replace(placeholder.match, failedMark);
        }
      } catch (e) {
        console.error('Failed to generate image:', e);
        // Keep placeholder on error
      }
    }

    isProcessing = false;
    dispatch('processed', { 
      content: processedContent, 
      imageCount: placeholders.length 
    });
  }

  async function processSinglePlaceholder(index: number) {
    const placeholder = placeholders[index];
    if (!placeholder) return;

    isProcessing = true;
    error = null;
    progress = { current: 1, total: 1, description: placeholder.description };

    try {
      const result = await generateImage({
        prompt: placeholder.description,
        type: 'image',
      });

      if (result.success && (result.imageUrl || result.imageBase64)) {
        const imageUrl = result.imageUrl || `data:image/png;base64,${result.imageBase64}`;
        const markdown = `![${placeholder.description}](${imageUrl})`;
        const processedContent = content.replace(placeholder.match, markdown);
        
        dispatch('processed', { content: processedContent, imageCount: 1 });
      } else {
        error = result.error || 'Failed to generate image';
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
    } finally {
      isProcessing = false;
    }
  }
</script>

{#if placeholders.length > 0}
  <div class="image-processor">
    <header class="processor-header">
      <span class="badge">{placeholders.length}</span>
      <span>Image placeholder{placeholders.length !== 1 ? 's' : ''} detected</span>
    </header>

    {#if isProcessing}
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          style="width: {(progress.current / progress.total) * 100}%"
        ></div>
      </div>
      <div class="progress-text">
        Generating {progress.current}/{progress.total}: {progress.description}
      </div>
    {:else}
      <div class="placeholder-list">
        {#each placeholders as placeholder, i}
          <div class="placeholder-item">
            <code class="placeholder-code">{placeholder.match}</code>
            <button 
              class="generate-single"
              onclick={() => processSinglePlaceholder(i)}
            >
              ✏️
            </button>
          </div>
        {/each}
      </div>

      <button 
        class="process-all-btn"
        onclick={processAllPlaceholders}
        disabled={isProcessing}
      >
        🖼️ Generate All Images
      </button>
    {/if}

    {#if error}
      <div class="error">{error}</div>
    {/if}
  </div>
{/if}

<style>
  .image-processor {
    padding: 12px;
    background: var(--bg-secondary, #1a1a1a);
    border: 1px solid var(--border, #333);
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .processor-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 20px;
    height: 20px;
    padding: 0 6px;
    background: var(--accent, #4a9eff);
    color: white;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .progress-bar {
    height: 4px;
    background: var(--bg-tertiary, #2a2a2a);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 8px;
  }

  .progress-fill {
    height: 100%;
    background: var(--accent, #4a9eff);
    transition: width 0.3s ease;
  }

  .progress-text {
    color: var(--text-muted, #888);
    font-size: 0.8rem;
  }

  .placeholder-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 12px;
  }

  .placeholder-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    background: var(--bg-tertiary, #2a2a2a);
    border-radius: 4px;
  }

  .placeholder-code {
    flex: 1;
    font-size: 0.75rem;
    color: var(--text-muted, #aaa);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .generate-single {
    padding: 4px 8px;
    background: none;
    border: 1px solid var(--border, #444);
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
  }

  .generate-single:hover {
    background: var(--bg-hover, #333);
  }

  .process-all-btn {
    width: 100%;
    padding: 10px;
    background: var(--accent, #4a9eff);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: opacity 0.2s;
  }

  .process-all-btn:hover:not(:disabled) {
    opacity: 0.9;
  }

  .process-all-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .error {
    margin-top: 8px;
    padding: 8px;
    background: #3a1a1a;
    border: 1px solid #a33;
    border-radius: 4px;
    color: #f88;
  }
</style>
