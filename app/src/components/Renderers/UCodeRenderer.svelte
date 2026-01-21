<script lang="ts">
  /**
   * UCodeRenderer
   * Renders -ucode.md files with executable code blocks
   * Frontmatter + markdown content + runtime blocks
   */
  import { onMount } from 'svelte';
  import { parseMarkdown } from '$lib/utils/markdown';
  import '$styles/prose.css';

  export let content: string = "";
  export let frontmatter: Record<string, any> = {};

  let htmlContent: string = '';

  $: {
    if (content) {
      htmlContent = parseMarkdown(content);
    }
  }

  onMount(async () => {
    // Apply syntax highlighting
    const hljs = await import('highlight.js');
    document.querySelectorAll('.ucode-renderer pre code').forEach((block) => {
      hljs.default.highlightElement(block as HTMLElement);
    });
  });
</script>

<div class="ucode-renderer">
  <div class="metadata">
    <h1 class="title">{frontmatter.title || "Untitled"}</h1>
    {#if frontmatter.description}
      <p class="description">{frontmatter.description}</p>
    {/if}
  </div>

  <div class="prose dark:prose-invert content">
    {@html htmlContent}
  </div>
</div>

<style lang="postcss">
  .ucode-renderer {
    background-color: #ffffff;
    color: #0f172a;
    padding: 2rem;
    min-height: 100vh;
    transition: colors 200ms ease-out;
  }

  :global(.dark) .ucode-renderer {
    background-color: #020617;
    color: #e5e7eb;
  }

  .metadata {
    margin-bottom: 2rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid #e2e8f0;
  }

  :global(.dark) .metadata {
    border-bottom-color: #334155;
  }

  .title {
    margin: 0 0 1rem 0;
    font-size: 2.5rem;
    font-weight: 700;
  }

  .description {
    margin: 0;
    font-size: 1.125rem;
    color: #475569;
  }

  :global(.dark) .description {
    color: #94a3b8;
  }

  .content {
    max-width: 65ch;
  }
</style>
