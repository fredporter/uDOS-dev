<script lang="ts">
  /**
   * FontManager
   * Manage font selection for the app
   */

  import { toasts } from "../UI/Toast/store";

  let selectedFont = "Atkinson Hyperlegible";
  let fontSize = 16;

  const fonts = [
    {
      id: "atkinson",
      name: "Atkinson Hyperlegible",
      family: "'Atkinson Hyperlegible', sans-serif",
    },
    {
      id: "ia-writer",
      name: "iA Writer Mono",
      family: "'iA Writer Mono', monospace",
    },
    {
      id: "monaspace",
      name: "Monaspace Neon",
      family: "'Monaspace Neon', monospace",
    },
    { id: "inter", name: "Inter", family: "'Inter', sans-serif" },
    {
      id: "jetbrains",
      name: "JetBrains Mono",
      family: "'JetBrains Mono', monospace",
    },
    {
      id: "source-code",
      name: "Source Code Pro",
      family: "'Source Code Pro', monospace",
    },
    { id: "fira-code", name: "Fira Code", family: "'Fira Code', monospace" },
    { id: "roboto", name: "Roboto Mono", family: "'Roboto Mono', monospace" },
  ];

  const fontSizes = [12, 13, 14, 15, 16, 17, 18, 20, 22, 24];

  function applyFont(fontFamily: string, fontName: string) {
    selectedFont = fontName;
    document.documentElement.style.setProperty(
      "--typo-font-family",
      fontFamily,
    );
    localStorage.setItem("typo-font-family", fontFamily);
    localStorage.setItem("typo-font-name", fontName);
    toasts.success("Font Applied", `${fontName} is now active`);
  }

  function applyFontSize(size: number) {
    fontSize = size;
    document.documentElement.style.setProperty("--typo-font-size", `${size}px`);
    localStorage.setItem("typo-font-size", size.toString());
    toasts.success("Font Size", `${size}px applied`);
  }

  function resetToDefaults() {
    selectedFont = "Atkinson Hyperlegible";
    fontSize = 16;
    document.documentElement.style.setProperty(
      "--typo-font-family",
      "'Atkinson Hyperlegible', sans-serif",
    );
    document.documentElement.style.setProperty("--typo-font-size", "16px");
    localStorage.removeItem("typo-font-family");
    localStorage.removeItem("typo-font-name");
    localStorage.removeItem("typo-font-size");
    toasts.info("Reset", "Font settings restored to defaults");
  }
</script>

<div class="font-manager">
  <header class="header">
    <h1 class="title">Font Manager</h1>
    <p class="subtitle">Customize typography for the editor and interface</p>
  </header>

  <div class="content">
    <!-- Current Selection -->
    <section class="section current-selection">
      <h2 class="section-title">Current Selection</h2>
      <div class="current-display">
        <div
          class="font-preview"
          style="font-family: var(--typo-font-family, 'Atkinson Hyperlegible'), sans-serif; font-size: var(--typo-font-size, 16px);"
        >
          <p class="preview-text">
            The quick brown fox jumps over the lazy dog
          </p>
          <p class="preview-numbers">0123456789 @#$%&*()</p>
          <code class="preview-code"
            >function hello() {"{"}return "world";{"}"}</code
          >
        </div>
        <div class="current-info">
          <div class="info-row">
            <span class="label">Font:</span>
            <span class="value">{selectedFont}</span>
          </div>
          <div class="info-row">
            <span class="label">Size:</span>
            <span class="value">{fontSize}px</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Font Family Selection -->
    <section class="section">
      <h2 class="section-title">Font Family</h2>
      <div class="font-grid">
        {#each fonts as font}
          <button
            class="font-card {selectedFont === font.name ? 'active' : ''}"
            on:click={() => applyFont(font.family, font.name)}
          >
            <div class="font-card-header">
              <span class="font-name">{font.name}</span>
              {#if selectedFont === font.name}
                <span class="active-badge">Active</span>
              {/if}
            </div>
            <div class="font-sample" style="font-family: {font.family};">
              The quick brown fox
            </div>
          </button>
        {/each}
      </div>
    </section>

    <!-- Font Size Selection -->
    <section class="section">
      <h2 class="section-title">Font Size</h2>
      <div class="size-grid">
        {#each fontSizes as size}
          <button
            class="size-button {fontSize === size ? 'active' : ''}"
            on:click={() => applyFontSize(size)}
          >
            {size}px
          </button>
        {/each}
      </div>
    </section>

    <!-- Actions -->
    <section class="section actions">
      <button class="btn btn-secondary" on:click={resetToDefaults}>
        🔄 Reset to Defaults
      </button>
    </section>
  </div>
</div>

<style lang="postcss">
  .font-manager {
    background-color: #ffffff;
    color: #0f172a;
    min-height: 100vh;
    transition: colors 200ms ease-out;
  }

  :global(.dark) .font-manager {
    background-color: #020617;
    color: #e5e7eb;
  }

  .header {
    padding: 3rem 2rem 2rem;
    text-align: center;
    border-bottom: 1px solid #e2e8f0;
    background-color: #f8fafc;
  }

  :global(.dark) .header {
    background-color: #0f172a;
    border-bottom-color: #334155;
  }

  .title {
    margin: 0 0 0.5rem 0;
    font-size: 2.5rem;
    font-weight: 700;
  }

  .subtitle {
    margin: 0;
    font-size: 1.125rem;
    color: #475569;
  }

  :global(.dark) .subtitle {
    color: #94a3b8;
  }

  .content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }

  .section {
    margin-bottom: 3rem;
  }

  .section-title {
    margin: 0 0 1.5rem 0;
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
  }

  :global(.dark) .section-title {
    color: #e5e7eb;
  }

  /* Current Selection */
  .current-selection {
    background-color: #f8fafc;
    padding: 2rem;
    border-radius: 0.75rem;
    border: 2px solid #e2e8f0;
  }

  :global(.dark) .current-selection {
    background-color: #0f172a;
    border-color: #334155;
  }

  .current-display {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .font-preview {
    background-color: #ffffff;
    padding: 2rem;
    border-radius: 0.5rem;
    border: 1px solid #e2e8f0;
  }

  :global(.dark) .font-preview {
    background-color: #1e293b;
    border-color: #475569;
  }

  .preview-text {
    margin: 0 0 1rem 0;
    font-size: 1.5rem;
    line-height: 1.6;
  }

  .preview-numbers {
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
    color: #475569;
  }

  :global(.dark) .preview-numbers {
    color: #94a3b8;
  }

  .preview-code {
    display: block;
    padding: 0.75rem;
    background-color: #f1f5f9;
    border-radius: 0.375rem;
    font-size: 1rem;
  }

  :global(.dark) .preview-code {
    background-color: #0f172a;
  }

  .current-info {
    display: flex;
    gap: 2rem;
  }

  .info-row {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  :global(.dark) .label {
    color: #94a3b8;
  }

  .value {
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
  }

  :global(.dark) .value {
    color: #e5e7eb;
  }

  /* Font Grid */
  .font-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
  }

  .font-card {
    background-color: #ffffff;
    padding: 1.5rem;
    border: 2px solid #e2e8f0;
    border-radius: 0.75rem;
    cursor: pointer;
    transition: all 200ms ease-out;
    text-align: left;
    width: 100%;
  }

  :global(.dark) .font-card {
    background-color: #1e293b;
    border-color: #475569;
  }

  .font-card:hover {
    border-color: #3b82f6;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
  }

  :global(.dark) .font-card:hover {
    border-color: #60a5fa;
  }

  .font-card.active {
    border-color: #3b82f6;
    background-color: #eff6ff;
  }

  :global(.dark) .font-card.active {
    border-color: #60a5fa;
    background-color: #1e3a5f;
  }

  .font-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .font-name {
    font-weight: 700;
    font-size: 1rem;
    color: #0f172a;
  }

  :global(.dark) .font-name {
    color: #e5e7eb;
  }

  .active-badge {
    padding: 0.25rem 0.5rem;
    background-color: #3b82f6;
    color: white;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .font-sample {
    font-size: 1.125rem;
    color: #475569;
  }

  :global(.dark) .font-sample {
    color: #94a3b8;
  }

  /* Size Grid */
  .size-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 0.75rem;
  }

  .size-button {
    padding: 1rem;
    background-color: #f1f5f9;
    border: 2px solid #e2e8f0;
    border-radius: 0.5rem;
    cursor: pointer;
    font-weight: 600;
    transition: all 200ms ease-out;
    color: #0f172a;
  }

  :global(.dark) .size-button {
    background-color: #1e293b;
    border-color: #475569;
    color: #e5e7eb;
  }

  .size-button:hover {
    border-color: #3b82f6;
    background-color: #e0f2fe;
  }

  :global(.dark) .size-button:hover {
    border-color: #60a5fa;
    background-color: #1e3a5f;
  }

  .size-button.active {
    border-color: #3b82f6;
    background-color: #3b82f6;
    color: white;
  }

  :global(.dark) .size-button.active {
    border-color: #60a5fa;
    background-color: #60a5fa;
  }

  /* Actions */
  .actions {
    display: flex;
    justify-content: center;
  }

  .btn {
    padding: 0.75rem 2rem;
    font-size: 1rem;
    font-weight: 600;
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 200ms ease-out;
  }

  .btn-secondary {
    background-color: #f1f5f9;
    color: #0f172a;
    border: 1px solid #cbd5e1;
  }

  :global(.dark) .btn-secondary {
    background-color: #1e293b;
    color: #e5e7eb;
    border-color: #475569;
  }

  .btn-secondary:hover {
    background-color: #e2e8f0;
    transform: translateY(-2px);
  }

  :global(.dark) .btn-secondary:hover {
    background-color: #334155;
  }

  @media (max-width: 768px) {
    .font-grid {
      grid-template-columns: 1fr;
    }

    .size-grid {
      grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
    }

    .current-info {
      flex-direction: column;
      gap: 1rem;
    }
  }
</style>
