<script lang="ts">
  import { onMount } from 'svelte';
  import { parseMarkdown } from '$lib/utils/markdown';
  import '$styles/prose.css';

  export let content: string = '';
  export let className: string = '';
  export let enableSyntaxHighlighting: boolean = true;

  let htmlContent: string = '';

  $: {
    if (content) {
      htmlContent = parseMarkdown(content);
    }
  }

  onMount(() => {
    // Apply syntax highlighting if needed
    if (enableSyntaxHighlighting && typeof window !== 'undefined') {
      import('highlight.js').then((hljs) => {
        document.querySelectorAll('pre code').forEach((block) => {
          hljs.default.highlightElement(block as HTMLElement);
        });
      });
    }
  });
</script>

<div class="prose dark:prose-invert {className}">
  {@html htmlContent}
</div>
