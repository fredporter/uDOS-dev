<script lang="ts">
  /**
   * StoryRenderer
   * Renders -story.md files as interactive typeform-style experiences
   */
  import { parseMarkdown } from "$lib/utils/markdown";
  import "$styles/prose.css";

  export let story: any = {};
  export let onSubmit: (answers: Record<string, any>) => void = () => {};

  let currentSectionIndex = 0;
  let totalSections = 4; // Default 4 questions
  let answers: Record<string, any> = {
    name: "",
    email: "",
    feedback: "",
    rating: 5,
  };

  function handleNext() {
    if (currentSectionIndex < totalSections - 1) {
      currentSectionIndex++;
    } else {
      onSubmit(answers);
    }
  }

  function handleBack() {
    if (currentSectionIndex > 0) {
      currentSectionIndex--;
    }
  }

  function handleReset() {
    currentSectionIndex = 0;
    answers = { name: "", email: "", feedback: "", rating: 5 };
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === "Enter" && !event.shiftKey) {
      // Don't submit on enter in textarea
      const target = event.target as HTMLElement;
      if (target.tagName !== "TEXTAREA") {
        event.preventDefault();
        handleNext();
      }
    }
  }
</script>

<form class="story-renderer" on:keydown={handleKeyDown}>
  <!-- Header -->
  <div class="header">
    <h1 class="title">{story.title || "Story"}</h1>
    {#if story.description}
      <p class="description">{story.description}</p>
    {/if}
  </div>

  <!-- Progress bar -->
  <div class="progress-container">
    <div
      class="progress-bar"
      style="width: {((currentSectionIndex + 1) / totalSections) * 100}%"
    ></div>
  </div>

  <!-- Content -->
  <div class="content">
    {#if currentSectionIndex === 0}
      <div class="form-section">
        <label class="form-label">
          <span>What's your name?</span>
          <input
            type="text"
            bind:value={answers.name}
            placeholder="Enter your name"
            class="form-input"
          />
          <span class="field-hint">Press <kbd>Enter</kbd> ↵</span>
        </label>
      </div>
    {:else if currentSectionIndex === 1}
      <div class="form-section">
        <label class="form-label">
          <span>Your email address?</span>
          <input
            type="email"
            bind:value={answers.email}
            placeholder="you@example.com"
            class="form-input"
          />
          <span class="field-hint">Press <kbd>Enter</kbd> ↵</span>
        </label>
      </div>
    {:else if currentSectionIndex === 2}
      <div class="form-section">
        <label class="form-label">
          <span>Rate your experience (1-10)</span>
          <div class="rating-group">
            <input
              type="range"
              min="1"
              max="10"
              bind:value={answers.rating}
              class="form-slider"
            />
            <span class="rating-value">{answers.rating}</span>
          </div>
          <span class="field-hint">Press <kbd>Enter</kbd> ↵</span>
        </label>
      </div>
    {:else}
      <div class="form-section">
        <label class="form-label">
          <span>Any additional feedback?</span>
          <textarea
            bind:value={answers.feedback}
            placeholder="Your feedback here..."
            class="form-textarea"
          />
          <span class="field-hint">Press <kbd>Enter</kbd> to submit</span>
        </label>
      </div>
    {/if}
  </div>

  <!-- Footer buttons -->
  <div class="footer">
    <button
      type="button"
      class="btn btn-secondary"
      disabled={currentSectionIndex === 0}
      on:click={handleBack}>← Back</button
    >
    <button type="button" class="btn btn-primary" on:click={handleNext}>
      {currentSectionIndex === totalSections - 1 ? "Submit" : "Next →"}
    </button>
    <button type="button" class="btn btn-tertiary" on:click={handleReset}
      >Reset</button
    >
  </div>
</form>

<style lang="postcss">
  .story-renderer {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
    background-color: #ffffff;
    color: #0f172a;
    transition: colors 200ms ease-out;
  }

  :global(.dark) .story-renderer {
    background-color: #020617;
    color: #e5e7eb;
  }

  .header {
    padding: 1.5rem 1.5rem 1rem;
    text-align: center;
    border-bottom: 1px solid #e2e8f0;
    flex-shrink: 0;
  }

  :global(.dark) .header {
    border-bottom-color: #334155;
  }

  .title {
    margin: 0 0 0.5rem 0;
    font-size: 1.75rem;
    font-weight: 700;
  }

  .description {
    margin: 0;
    font-size: 0.95rem;
    color: #475569;
  }

  :global(.dark) .description {
    color: #94a3b8;
  }

  .progress-container {
    position: relative;
    height: 3px;
    background-color: #e2e8f0;
    overflow: hidden;
    flex-shrink: 0;
  }

  :global(.dark) .progress-container {
    background-color: #334155;
  }

  .progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #60a5fa, #3b82f6);
    transition: width 300ms ease-out;
  }

  .content {
    flex: 1;
    padding: 1.5rem 1.5rem 8rem 1.5rem;
    max-width: 800px;
    margin: 0 auto;
    width: 100%;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .footer {
    position: fixed;
    bottom: 60px;
    left: 0;
    right: 0;
    padding: 1.25rem 1.5rem;
    border-top: 1px solid #e2e8f0;
    background-color: #f8fafc;
    display: flex;
    justify-content: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    z-index: 40;
  }

  :global(.dark) .footer {
    background-color: #0f172a;
    border-top-color: #334155;
  }

  .btn {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
    font-weight: 600;
    border: 2px solid transparent;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 200ms ease-out;
    outline: none;
    -webkit-appearance: none;
    appearance: none;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    border-color: #2563eb;
  }

  .btn-primary:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
  }

  .btn-secondary {
    background-color: #f1f5f9;
    color: #0f172a;
    border-color: #cbd5e1;
  }

  :global(.dark) .btn-secondary {
    background-color: #1e293b;
    color: #e5e7eb;
    border-color: #475569;
  }

  .btn-secondary:hover:not(:disabled) {
    background-color: #e2e8f0;
  }

  :global(.dark) .btn-secondary:hover:not(:disabled) {
    background-color: #334155;
  }

  .btn-tertiary {
    background-color: transparent;
    color: #475569;
    border-color: #cbd5e1;
    font-weight: 500;
  }

  :global(.dark) .btn-tertiary {
    color: #94a3b8;
    border-color: #475569;
  }

  .btn-tertiary:hover {
    background-color: #f1f5f9;
  }

  :global(.dark) .btn-tertiary:hover {
    background-color: #1e293b;
  }

  .hint {
    width: 100%;
    text-align: center;
    font-size: 0.875rem;
    color: #64748b;
    margin-top: 0.5rem;
  }

  :global(.dark) .hint {
    color: #94a3b8;
  }

  .hint kbd {
    padding: 0.125rem 0.5rem;
    background-color: #e2e8f0;
    border: 1px solid #cbd5e1;
    border-radius: 0.25rem;
    font-family: monospace;
    font-size: 0.875rem;
    color: #0f172a;
  }

  :global(.dark) .hint kbd {
    background-color: #1e293b;
    border-color: #475569;
    color: #e5e7eb;
  }

  .field-hint {
    display: block;
    margin-top: 0.75rem;
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
    text-align: right;
  }

  :global(.dark) .field-hint {
    color: #94a3b8;
  }

  .field-hint kbd {
    padding: 0.125rem 0.5rem;
    background-color: #e2e8f0;
    border: 1px solid #cbd5e1;
    border-radius: 0.25rem;
    font-family: monospace;
    font-size: 0.875rem;
    color: #0f172a;
    margin: 0 0.25rem;
  }

  :global(.dark) .field-hint kbd {
    background-color: #1e293b;
    border-color: #475569;
    color: #e5e7eb;
  }

  .form-section {
    animation: fadeIn 0.3s ease-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .form-label {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
  }

  :global(.dark) .form-label {
    color: #e5e7eb;
  }

  .form-input,
  .form-textarea {
    padding: 0.5rem 0.75rem;
    font-size: 0.95rem;
    border: 2px solid #e2e8f0;
    border-radius: 0.5rem;
    background-color: #ffffff;
    color: #0f172a;
    transition: all 200ms ease-out;
    font-family: inherit;
  }

  :global(.dark) .form-input,
  :global(.dark) .form-textarea {
    background-color: #1e293b;
    border-color: #334155;
    color: #e5e7eb;
  }

  .form-input:focus,
  .form-textarea:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  :global(.dark) .form-input:focus,
  :global(.dark) .form-textarea:focus {
    border-color: #60a5fa;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.1);
  }

  .form-textarea {
    min-height: 80px;
    resize: vertical;
  }

  .rating-group {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .form-slider {
    flex: 1;
    height: 6px;
    border-radius: 3px;
    background: #e2e8f0;
    outline: none;
    -webkit-appearance: none;
    appearance: none;
  }

  :global(.dark) .form-slider {
    background: #334155;
  }

  .form-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    transition: all 200ms ease-out;
  }

  .form-slider::-webkit-slider-thumb:hover {
    background: #2563eb;
    transform: scale(1.2);
  }

  .form-slider::-moz-range-thumb {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: none;
    transition: all 200ms ease-out;
  }

  .form-slider::-moz-range-thumb:hover {
    background: #2563eb;
    transform: scale(1.2);
  }

  .rating-value {
    min-width: 40px;
    text-align: center;
    font-weight: 700;
    color: #3b82f6;
  }

  :global(.dark) .rating-value {
    color: #60a5fa;
  }
</style>
