<script lang="ts">
  /**
   * GuideRenderer
   * Renders -guide.md files as knowledge bank articles
   */
  import { onMount } from "svelte";
  import { parseMarkdown, extractFrontmatter } from "$lib/utils/markdown";
  import "$styles/prose.css";

  export let content: string = "";
  export let frontmatter: Record<string, any> = {};

  let showIndex = true;
  let index: any = null;
  let currentArticle: string = "";
  let articleContent: string = "";
  let articleFrontmatter: any = {};
  let renderedContent: string = "";

  $: {
    if (articleContent) {
      renderedContent = parseMarkdown(articleContent);
    }
  }

  onMount(async () => {
    // Load the knowledge base index
    try {
      const response = await fetch("/knowledge/index.json");
      if (response.ok) {
        index = await response.json();
      }
    } catch (error) {
      console.error("Failed to load knowledge index:", error);
    }

    // Apply syntax highlighting after mount
    const hljs = await import('highlight.js');
    document.querySelectorAll('.guide-renderer pre code').forEach((block) => {
      hljs.default.highlightElement(block as HTMLElement);
    });
  });

  async function loadArticle(file: string) {
    try {
      const response = await fetch(`/knowledge/${file}`);
      if (response.ok) {
        const text = await response.text();
        const { frontmatter: fm, body } = extractFrontmatter(text);
        articleFrontmatter = fm;
        articleContent = body;
        currentArticle = file;
        showIndex = false;
      }
    } catch (error) {
      console.error("Failed to load article:", error);
    }
  }

  function backToIndex() {
    showIndex = true;
    currentArticle = "";
  }
</script>

<div class="guide-renderer">
  {#if showIndex}
    <!-- Knowledge Base Index -->
    <div class="index-view">
      <header class="index-header">
        <h1 class="title">📚 Knowledge Base</h1>
        <p class="subtitle">
          Learn everything about uMarkdown formats and features
        </p>
      </header>

      {#if index}
        <div class="categories">
          {#each index.categories as category}
            <section class="category">
              <h2 class="category-title">{category.title}</h2>
              <p class="category-description">{category.description}</p>
              <div class="articles">
                {#each category.articles as article}
                  <button
                    class="article-card"
                    on:click={() => loadArticle(article.file)}
                  >
                    <h3 class="article-title">{article.title}</h3>
                    <p class="article-description">{article.description}</p>
                    <span class="read-more">Read more →</span>
                  </button>
                {/each}
              </div>
            </section>
          {/each}
        </div>
      {:else}
        <div class="loading">Loading knowledge base...</div>
      {/if}
    </div>
  {:else}
    <!-- Article View -->
    <div class="article-view">
      <button class="back-button" on:click={backToIndex}>← Back to Index</button
      >

      <article>
        <header>
          <h1 class="title">{articleFrontmatter.title || "Guide"}</h1>
          {#if articleFrontmatter.author}
            <p class="byline">By {articleFrontmatter.author}</p>
          {/if}
          {#if articleFrontmatter.date}
            <p class="date">
              {new Date(articleFrontmatter.date).toLocaleDateString()}
            </p>
          {/if}
        </header>

        <div class="prose dark:prose-invert body">
          {@html renderedContent}
        </div>
      </article>
    </div>
  {/if}
</div>

<style lang="postcss">
  .guide-renderer {
    background-color: #ffffff;
    color: #0f172a;
    min-height: 100vh;
    transition: colors 200ms ease-out;
  }

  :global(.dark) .guide-renderer {
    background-color: #020617;
    color: #e5e7eb;
  }

  /* Index View */
  .index-view {
    max-width: 1200px;
    margin: 0 auto;
    padding: 3rem 2rem;
  }

  .index-header {
    text-align: center;
    margin-bottom: 4rem;
    padding-bottom: 2rem;
    border-bottom: 2px solid #e2e8f0;
  }

  :global(.dark) .index-header {
    border-bottom-color: #334155;
  }

  .index-header .title {
    margin: 0 0 1rem 0;
    font-size: 3rem;
    font-weight: 700;
  }

  .subtitle {
    font-size: 1.25rem;
    color: #475569;
    margin: 0;
  }

  :global(.dark) .subtitle {
    color: #94a3b8;
  }

  .categories {
    display: flex;
    flex-direction: column;
    gap: 3rem;
  }

  .category {
    background-color: #f8fafc;
    padding: 2rem;
    border-radius: 1rem;
    border: 1px solid #e2e8f0;
  }

  :global(.dark) .category {
    background-color: #0f172a;
    border-color: #334155;
  }

  .category-title {
    margin: 0 0 0.5rem 0;
    font-size: 1.75rem;
    font-weight: 700;
    color: #0f172a;
  }

  :global(.dark) .category-title {
    color: #e5e7eb;
  }

  .category-description {
    margin: 0 0 1.5rem 0;
    color: #475569;
  }

  :global(.dark) .category-description {
    color: #94a3b8;
  }

  .articles {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
  }

  .article-card {
    background-color: #ffffff;
    padding: 1.5rem;
    border-radius: 0.75rem;
    border: 2px solid #e2e8f0;
    cursor: pointer;
    transition: all 200ms ease-out;
    text-align: left;
    width: 100%;
  }

  :global(.dark) .article-card {
    background-color: #1e293b;
    border-color: #475569;
  }

  .article-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    border-color: #3b82f6;
  }

  :global(.dark) .article-card:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    border-color: #60a5fa;
  }

  .article-title {
    margin: 0 0 0.5rem 0;
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
  }

  :global(.dark) .article-title {
    color: #e5e7eb;
  }

  .article-description {
    margin: 0 0 0.75rem 0;
    color: #475569;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  :global(.dark) .article-description {
    color: #94a3b8;
  }

  .read-more {
    color: #3b82f6;
    font-weight: 600;
    font-size: 0.875rem;
  }

  :global(.dark) .read-more {
    color: #60a5fa;
  }

  .loading {
    text-align: center;
    padding: 4rem 2rem;
    color: #475569;
    font-size: 1.125rem;
  }

  :global(.dark) .loading {
    color: #94a3b8;
  }

  /* Article View */
  .article-view {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem;
  }

  .back-button {
    background-color: #f1f5f9;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    cursor: pointer;
    font-weight: 600;
    margin-bottom: 2rem;
    transition: all 200ms ease-out;
  }

  :global(.dark) .back-button {
    background-color: #1e293b;
    color: #e5e7eb;
    border-color: #475569;
  }

  .back-button:hover {
    background-color: #e2e8f0;
  }

  :global(.dark) .back-button:hover {
    background-color: #334155;
  }

  article header {
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #e2e8f0;
  }

  :global(.dark) article header {
    border-bottom-color: #334155;
  }

  article .title {
    margin: 0 0 0.5rem 0;
    font-size: 2.5rem;
    font-weight: 700;
  }

  .byline {
    margin: 0;
    color: #475569;
    font-size: 1rem;
  }

  :global(.dark) .byline {
    color: #94a3b8;
  }

  .date {
    margin: 0.25rem 0 0 0;
    color: #64748b;
    font-size: 0.875rem;
  }

  :global(.dark) .date {
    color: #94a3b8;
  }

  .body {
    line-height: 1.8;
  }

  .markdown-content {
    white-space: pre-wrap;
    font-family: inherit;
  }

  @media (max-width: 768px) {
    .articles {
      grid-template-columns: 1fr;
    }
  }
</style>
