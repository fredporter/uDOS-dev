<script lang="ts">
  /**
   * AIPanel - Inline AI Assistant Panel
   * 
   * Provides quick AI actions for the Typo editor:
   * - Text expansion/summarization
   * - Image generation (nano-banana sketch)
   * - Smart suggestions
   * - Quick fixes
   */
  import { generateText, executeQuickAction, quickActions, type QuickAction } from '$lib/services/ai';
  import SketchPad from './SketchPad.svelte';
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher<{
    insert: { text: string };
    replace: { text: string };
    close: void;
  }>();

  interface Props {
    selectedText?: string;
    cursorContext?: string;
    visible?: boolean;
  }

  let { selectedText = '', cursorContext = '', visible = false }: Props = $props();

  // State
  let activeTab = $state<'quick' | 'sketch' | 'custom'>('quick');
  let customPrompt = $state('');
  let isProcessing = $state(false);
  let result = $state<string | null>(null);
  let error = $state<string | null>(null);

  // Quick actions with UI metadata
  const actions: Array<{ key: string; action: QuickAction; icon: string; description: string }> = [
    { key: 'expand', action: quickActions.expand, icon: '📝', description: 'Make it longer' },
    { key: 'summarize', action: quickActions.summarize, icon: '📋', description: 'Make it shorter' },
    { key: 'improve', action: quickActions.improve, icon: '✨', description: 'Improve writing' },
    { key: 'continue', action: quickActions.continue, icon: '➡️', description: 'Continue writing' },
    { key: 'toChecklist', action: quickActions.toChecklist, icon: '☑️', description: 'Convert to checklist' },
    { key: 'sketch', action: quickActions.sketch, icon: '🎨', description: 'Describe for sketch' },
  ];

  async function runAction(actionKey: string) {
    if (!selectedText && !cursorContext) {
      error = 'Select some text first';
      return;
    }

    isProcessing = true;
    error = null;
    result = null;

    try {
      const response = await executeQuickAction(actionKey, selectedText || cursorContext);

      if (response.success && response.text) {
        result = response.text;
      } else {
        error = response.error || 'Failed to generate';
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
    } finally {
      isProcessing = false;
    }
  }

  async function executeCustomPrompt() {
    if (!customPrompt.trim()) return;

    isProcessing = true;
    error = null;
    result = null;

    try {
      const context = selectedText || cursorContext;
      const prompt = context 
        ? `${customPrompt}\n\nContext:\n${context}`
        : customPrompt;

      const response = await generateText({
        prompt,
        maxTokens: 2000,
      });

      if (response.success && response.text) {
        result = response.text;
      } else {
        error = response.error || 'Failed to generate';
      }
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error';
    } finally {
      isProcessing = false;
    }
  }

  function insertResult() {
    if (result) {
      dispatch('insert', { text: result });
      result = null;
    }
  }

  function replaceResult() {
    if (result) {
      dispatch('replace', { text: result });
      result = null;
    }
  }

  function handleSketchInsert(event: CustomEvent<{ markdown: string }>) {
    dispatch('insert', { text: event.detail.markdown });
  }

  function close() {
    dispatch('close');
  }
</script>

{#if visible}
  <div class="ai-panel">
    <div class="panel-tabs">
      <button 
        class="tab" 
        class:active={activeTab === 'quick'}
        onclick={() => activeTab = 'quick'}
      >
        ⚡ Quick
      </button>
      <button 
        class="tab" 
        class:active={activeTab === 'sketch'}
        onclick={() => activeTab = 'sketch'}
      >
        🍌 Sketch
      </button>
      <button 
        class="tab" 
        class:active={activeTab === 'custom'}
        onclick={() => activeTab = 'custom'}
      >
        💬 Custom
      </button>
      <button class="close-tab" onclick={close}>×</button>
    </div>

    <div class="panel-content">
      {#if activeTab === 'quick'}
        <div class="quick-actions">
          {#if selectedText}
            <div class="selection-preview">
              <span class="label">Selected:</span>
              <span class="preview">{selectedText.slice(0, 50)}{selectedText.length > 50 ? '...' : ''}</span>
            </div>
          {:else}
            <div class="selection-hint">
              Select text to use AI actions
            </div>
          {/if}

          <div class="action-grid">
            {#each actions as item}
              <button 
                class="action-btn"
                onclick={() => runAction(item.key)}
                disabled={isProcessing || (!selectedText && !cursorContext)}
                title={item.description}
              >
                <span class="action-icon">{item.icon}</span>
                <span class="action-label">{item.action.name}</span>
              </button>
            {/each}
          </div>
        </div>

      {:else if activeTab === 'sketch'}
        <SketchPad 
          on:insert={handleSketchInsert}
          on:close={close}
        />

      {:else if activeTab === 'custom'}
        <div class="custom-prompt">
          <textarea
            bind:value={customPrompt}
            placeholder="Ask AI anything about your document..."
            rows="3"
            disabled={isProcessing}
          ></textarea>
          <button 
            class="send-btn"
            onclick={executeCustomPrompt}
            disabled={isProcessing || !customPrompt.trim()}
          >
            {isProcessing ? '⏳' : '🚀'} Send
          </button>
        </div>
      {/if}

      {#if error}
        <div class="error">{error}</div>
      {/if}

      {#if result}
        <div class="result">
          <div class="result-header">
            <span>AI Response</span>
            <div class="result-actions">
              <button onclick={insertResult} title="Insert at cursor">📥 Insert</button>
              {#if selectedText}
                <button onclick={replaceResult} title="Replace selection">🔄 Replace</button>
              {/if}
            </div>
          </div>
          <div class="result-content">{result}</div>
        </div>
      {/if}

      {#if isProcessing}
        <div class="processing">
          <span class="spinner"></span>
          Generating...
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .ai-panel {
    position: absolute;
    right: 16px;
    top: 60px;
    width: 360px;
    max-height: calc(100vh - 120px);
    background: var(--bg-primary, #0d0d0d);
    border: 1px solid var(--border, #333);
    border-radius: 8px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    overflow: hidden;
    z-index: 100;
  }

  .panel-tabs {
    display: flex;
    background: var(--bg-secondary, #1a1a1a);
    border-bottom: 1px solid var(--border, #333);
  }

  .tab {
    flex: 1;
    padding: 10px;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--text-muted, #888);
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s;
  }

  .tab:hover {
    color: var(--text, #fff);
    background: var(--bg-hover, #222);
  }

  .tab.active {
    color: var(--accent, #4a9eff);
    border-bottom-color: var(--accent, #4a9eff);
  }

  .close-tab {
    padding: 10px 16px;
    background: none;
    border: none;
    color: var(--text-muted, #888);
    cursor: pointer;
    font-size: 1.2rem;
  }

  .close-tab:hover {
    color: var(--text, #fff);
  }

  .panel-content {
    padding: 12px;
    max-height: 500px;
    overflow-y: auto;
  }

  .selection-preview {
    padding: 8px;
    background: var(--bg-secondary, #1a1a1a);
    border-radius: 4px;
    margin-bottom: 12px;
    font-size: 0.8rem;
  }

  .selection-preview .label {
    color: var(--text-muted, #888);
  }

  .selection-preview .preview {
    color: var(--text, #fff);
    margin-left: 4px;
  }

  .selection-hint {
    padding: 8px;
    background: var(--bg-secondary, #1a1a1a);
    border-radius: 4px;
    margin-bottom: 12px;
    font-size: 0.8rem;
    color: var(--text-muted, #888);
    text-align: center;
  }

  .action-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }

  .action-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 12px 8px;
    background: var(--bg-secondary, #1a1a1a);
    border: 1px solid var(--border, #333);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .action-btn:hover:not(:disabled) {
    background: var(--bg-hover, #222);
    border-color: var(--accent, #4a9eff);
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .action-icon {
    font-size: 1.3rem;
  }

  .action-label {
    font-size: 0.7rem;
    color: var(--text-muted, #aaa);
  }

  .custom-prompt {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .custom-prompt textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid var(--border, #333);
    border-radius: 4px;
    background: var(--bg-input, #0a0a0a);
    color: var(--text, #fff);
    resize: vertical;
    font-family: inherit;
    font-size: 0.9rem;
  }

  .custom-prompt textarea:focus {
    outline: none;
    border-color: var(--accent, #4a9eff);
  }

  .send-btn {
    padding: 10px;
    background: var(--accent, #4a9eff);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
  }

  .send-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .error {
    margin-top: 12px;
    padding: 8px;
    background: #3a1a1a;
    border: 1px solid #a33;
    border-radius: 4px;
    color: #f88;
    font-size: 0.85rem;
  }

  .result {
    margin-top: 12px;
    border: 1px solid var(--border, #333);
    border-radius: 6px;
    overflow: hidden;
  }

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: var(--bg-secondary, #1a1a1a);
    font-size: 0.8rem;
    color: var(--text-muted, #888);
  }

  .result-actions {
    display: flex;
    gap: 4px;
  }

  .result-actions button {
    padding: 4px 8px;
    background: var(--bg-tertiary, #2a2a2a);
    border: 1px solid var(--border, #444);
    border-radius: 4px;
    color: var(--text, #fff);
    cursor: pointer;
    font-size: 0.75rem;
  }

  .result-actions button:hover {
    background: var(--bg-hover, #333);
  }

  .result-content {
    padding: 12px;
    font-size: 0.9rem;
    line-height: 1.5;
    white-space: pre-wrap;
    max-height: 200px;
    overflow-y: auto;
  }

  .processing {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 16px;
    color: var(--text-muted, #888);
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid var(--border, #333);
    border-top-color: var(--accent, #4a9eff);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>
