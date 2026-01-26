<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import StoryRenderer from '$lib/components/StoryRenderer.svelte';
  import { loadStory, loadStoryState, saveStoryState } from '$lib/services/storyService';
  import type { StoryState } from '$lib/types/story';

  let story: StoryState | null = null;
  let loading = true;
  let error: string | null = null;
  let storyId: string = '';

  onMount(async () => {
    try {
      storyId = $page.params.slug || '';
      if (!storyId) {
        throw new Error('Invalid story ID');
      }

      // Try to load saved state
      const savedState = loadStoryState(storyId);
      if (savedState) {
        story = savedState;
      } else {
        // Load fresh story
        const storyPath = `/content/stories/${storyId}-story.md`;
        story = await loadStory(storyPath);
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load story';
      console.error('Story load error:', err);
    } finally {
      loading = false;
    }
  });

  function handleSubmit(answers: Record<string, any>) {
    if (!story) return;

    console.log('Story submitted:', answers);

    // Save to localStorage
    if (story) {
      story.answers = answers;
      story.isComplete = true;
      saveStoryState(storyId, story);
    }

    // TODO: Send to server if needed
    // const response = await fetch(`/api/stories/${storyId}/submit`, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(answers),
    // });
  }

  function handleReset() {
    if (!story) return;
    story.answers = {};
    story.isComplete = false;
    localStorage.removeItem(`story:${storyId}`);
  }
</script>

<div class="story-page">
  {#if loading}
    <div class="flex items-center justify-center h-screen">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p class="text-gray-600 dark:text-gray-400">Loading story...</p>
      </div>
    </div>
  {:else if error}
    <div class="flex items-center justify-center h-screen">
      <div class="text-center max-w-md">
        <div class="text-red-500 mb-4">
          <svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold mb-2">Error Loading Story</h1>
        <p class="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
        <a href="/" class="text-blue-500 hover:underline">Return to Home</a>
      </div>
    </div>
  {:else if story}
    <div class="story-container max-w-2xl mx-auto px-4 py-8">
      <StoryRenderer
        {story}
        onSubmit={handleSubmit}
        onReset={handleReset}
        showProgress={true}
        theme="auto"
      />
    </div>
  {/if}
</div>

<style>
  :global(body) {
    transition: color 0.2s, background-color 0.2s;
  }

  .story-page {
    min-height: 100vh;
    background-color: white;
    color: rgb(17, 24, 39);
  }

  :global(.dark) .story-page {
    background-color: rgb(17, 24, 39);
    color: rgb(243, 244, 246);
  }

  .story-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
  }
</style>
