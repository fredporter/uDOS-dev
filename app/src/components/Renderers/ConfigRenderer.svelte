<script lang="ts">
  /**
   * ConfigRenderer
   * Renders -config.md files as system configuration panels
   * Layout: Code editor (LHS) + Controls/Settings (RHS)
   */
  import { parseMarkdown } from "$lib/utils/markdown";
  import { fileManager } from "$lib/utils/fileManager";
  import "$styles/prose.css";
  import { toasts } from "../UI/Toast/store";

  export let config: Record<string, any> = {};
  export let onSave: (config: Record<string, any>) => void = () => {};

  let selectedFile = "locations.json";
  let editorContent = "";
  let hasChanges = false;
  let defaultMdFolder: string = "";

  const configFiles = [
    {
      id: "locations.json",
      label: "Locations",
      path: "../core/locations.json",
    },
    { id: "settings.json", label: "Settings", path: "./settings.json" },
    { id: "themes.json", label: "Themes", path: "./themes.json" },
    { id: "version.json", label: "Version", path: "../core/version.json" },
  ];

  // Sample default content for demonstration
  const defaultContent: Record<string, string> = {
    "locations.json": '{\n  "version": "1.0.0",\n  "locations": []\n}',
    "settings.json":
      '{\n  "theme": "auto",\n  "fontSize": 16,\n  "fontFamily": "Atkinson Hyperlegible"\n}',
    "themes.json":
      '{\n  "light": { "bg": "#ffffff", "fg": "#000000" },\n  "dark": { "bg": "#020617", "fg": "#e5e7eb" }\n}',
    "version.json": '{\n  "version": "1.0.0.0",\n  "build": "2026-01-20"\n}',
  };

  async function loadDefaultMdFolder() {
    try {
      defaultMdFolder = await fileManager.getDefaultMdFolder();
    } catch (error) {
      console.error("Error loading default folder:", error);
    }
  }

  async function chooseDefaultMdFolder() {
    try {
      const folder = await fileManager.openFolderDialog();
      if (folder) {
        await fileManager.setDefaultMdFolder(folder);
        defaultMdFolder = folder;
      }
    } catch (error) {
      toasts.error("Failed to set default folder");
    }
  }

  function loadFile(fileId: string) {
    selectedFile = fileId;
    editorContent = defaultContent[fileId] || "";
    hasChanges = false;
  }

  function handleEditorChange() {
    hasChanges = true;
  }

  function handleSave() {
    try {
      // Validate JSON
      JSON.parse(editorContent);
      toasts.success(`Saved ${selectedFile}`);
      hasChanges = false;
    } catch (error) {
      toasts.error("Invalid JSON format");
    }
  }

  function handleRestore() {
    editorContent = defaultContent[selectedFile] || "";
    hasChanges = false;
    toasts.info("Restored to defaults");
  }

  function handleFormat() {
    try {
      const parsed = JSON.parse(editorContent);
      editorContent = JSON.stringify(parsed, null, 2);
      toasts.success("Formatted JSON");
    } catch (error) {
      toasts.error("Cannot format invalid JSON");
    }
  }

  function handleExport() {
    const blob = new Blob([editorContent], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = selectedFile;
    a.click();
    URL.revokeObjectURL(url);
    toasts.success(`Exported ${selectedFile}`);
  }

  // Initialize with first file and default folder
  loadFile(selectedFile);
  loadDefaultMdFolder();

</script>

<div class="config-renderer">
  <!-- Left Side: Code Editor -->
  <div class="editor-panel">
    <div class="editor-header">
      <h2 class="editor-title">Configuration Editor</h2>
      {#if hasChanges}
        <span class="unsaved-indicator">• Unsaved changes</span>
      {/if}
    </div>
    <textarea
      bind:value={editorContent}
      on:input={handleEditorChange}
      class="code-editor"
      spellcheck="false"
      placeholder="Select a config file to edit..."
    ></textarea>
  </div>

  <!-- Right Side: Controls -->
  <div class="controls-panel">
    <div class="section">
      <h3 class="section-title">Config Files</h3>
      <div class="file-list">
        {#each configFiles as file}
          <button
            class="file-button {selectedFile === file.id ? 'active' : ''}"
            on:click={() => loadFile(file.id)}
          >
            <span class="file-label">{file.label}</span>
            <span class="file-name">{file.id}</span>
          </button>
        {/each}
      </div>
    </div>

    <div class="section">
      <h3 class="section-title">Actions</h3>
      <div class="action-buttons">
        <button
          class="btn btn-primary"
          on:click={handleSave}
          disabled={!hasChanges}
        >
          💾 Save
        </button>
        <button class="btn btn-secondary" on:click={handleFormat}>
          ✨ Format
        </button>
        <button class="btn btn-secondary" on:click={handleExport}>
          📥 Export
        </button>
        <button class="btn btn-tertiary" on:click={handleRestore}>
          🔄 Restore
        </button>
      </div>
    </div>

    <div class="section">
      <h3 class="section-title">⚙️ File Settings</h3>
      <div class="file-settings">
        <label class="setting">
          <span class="label-text">Default Markdown Folder</span>
          <div class="folder-input">
            <input
              type="text"
              value={defaultMdFolder}
              readonly
              class="folder-path"
              placeholder="Documents folder"
            />
            <button
              class="btn btn-secondary btn-sm"
              on:click={chooseDefaultMdFolder}
            >
              📁 Browse
            </button>
          </div>
        </label>
      </div>
    </div>

    <div class="section">
      <h3 class="section-title">Quick Settings</h3>
      <div class="quick-settings">
        <label class="setting">
          <span>Font Size</span>
          <select>
            <option>12px</option>
            <option selected>14px</option>
            <option>16px</option>
            <option>18px</option>
          </select>
        </label>
        <label class="setting">
          <span>Tab Size</span>
          <select>
            <option selected>2 spaces</option>
            <option>4 spaces</option>
            <option>Tab character</option>
          </select>
        </label>
        <label class="setting-checkbox">
          <input type="checkbox" checked />
          <span>Auto-format on save</span>
        </label>
        <label class="setting-checkbox">
          <input type="checkbox" />
          <span>Line numbers</span>
        </label>
      </div>
    </div>

    <div class="info-panel">
      <h4>💡 Tips</h4>
      <ul>
        <li>Edit JSON config files directly</li>
        <li>Use Format to beautify JSON</li>
        <li>Changes are validated before saving</li>
        <li>Restore to reset to defaults</li>
      </ul>
    </div>
  </div>
</div>

<style lang="postcss">
  .config-renderer {
    display: grid;
    grid-template-columns: 2fr 1fr;
    height: 100vh;
    background-color: #ffffff;
    color: #0f172a;
    transition: colors 200ms ease-out;
  }

  :global(.dark) .config-renderer {
    background-color: #020617;
    color: #e5e7eb;
  }

  /* Left Panel: Code Editor */
  .editor-panel {
    display: flex;
    flex-direction: column;
    border-right: 1px solid #e2e8f0;
  }

  :global(.dark) .editor-panel {
    border-right-color: #334155;
  }

  .editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #e2e8f0;
    background-color: #f8fafc;
  }

  :global(.dark) .editor-header {
    border-bottom-color: #334155;
    background-color: #0f172a;
  }

  .editor-title {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
  }

  .unsaved-indicator {
    color: #f59e0b;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .code-editor {
    flex: 1;
    padding: 1.5rem;
    font-family: "Monaco", "Menlo", "Courier New", monospace;
    font-size: 14px;
    line-height: 1.6;
    background-color: #f8fafc;
    color: #0f172a;
    border: none;
    resize: none;
    outline: none;
  }

  :global(.dark) .code-editor {
    background-color: #0f172a;
    color: #e5e7eb;
  }

  .code-editor::placeholder {
    color: #94a3b8;
  }

  /* Right Panel: Controls */
  .controls-panel {
    display: flex;
    flex-direction: column;
    padding: 1.5rem;
    gap: 2rem;
    overflow-y: auto;
    background-color: #ffffff;
  }

  :global(.dark) .controls-panel {
    background-color: #020617;
  }

  .section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .section-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    color: #0f172a;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.875rem;
  }

  :global(.dark) .section-title {
    color: #e5e7eb;
  }

  /* File List */
  .file-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .file-button {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    padding: 0.75rem 1rem;
    background-color: #f1f5f9;
    border: 2px solid #e2e8f0;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 200ms ease-out;
    text-align: left;
    width: 100%;
  }

  :global(.dark) .file-button {
    background-color: #1e293b;
    border-color: #475569;
  }

  .file-button:hover {
    background-color: #e2e8f0;
    border-color: #cbd5e1;
  }

  :global(.dark) .file-button:hover {
    background-color: #334155;
    border-color: #64748b;
  }

  .file-button.active {
    background-color: #dbeafe;
    border-color: #3b82f6;
  }

  :global(.dark) .file-button.active {
    background-color: #1e3a5f;
    border-color: #60a5fa;
  }

  .file-label {
    font-weight: 700;
    font-size: 0.95rem;
    color: #0f172a;
  }

  :global(.dark) .file-label {
    color: #e5e7eb;
  }

  .file-name {
    font-size: 0.75rem;
    color: #64748b;
    font-family: monospace;
    margin-top: 0.25rem;
  }

  :global(.dark) .file-name {
    color: #94a3b8;
  }

  /* Action Buttons */
  .action-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }

  .btn {
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    font-weight: 600;
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 200ms ease-out;
    text-align: center;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    grid-column: span 2;
  }

  .btn-primary:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
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
  }

  :global(.dark) .btn-secondary:hover {
    background-color: #334155;
  }

  .btn-tertiary {
    background-color: transparent;
    color: #475569;
    border: 1px solid #cbd5e1;
    grid-column: span 2;
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

  /* Quick Settings */
  .quick-settings {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .setting {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .setting span {
    font-size: 0.875rem;
    font-weight: 500;
    color: #334155;
  }

  :global(.dark) .setting span {
    color: #cbd5e1;
  }

  .setting select {
    padding: 0.5rem;
    border: 1px solid #cbd5e1;
    border-radius: 0.375rem;
    background-color: #ffffff;
    color: #0f172a;
    font-size: 0.875rem;
  }

  :global(.dark) .setting select {
    background-color: #1e293b;
    color: #e5e7eb;
    border-color: #475569;
  }

  .setting-checkbox {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    cursor: pointer;
  }

  .setting-checkbox input[type="checkbox"] {
    width: 1rem;
    height: 1rem;
    cursor: pointer;
  }

  /* File Settings */
  .file-settings {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .label-text {
    font-size: 0.875rem;
    font-weight: 500;
    color: #334155;
  }

  :global(.dark) .label-text {
    color: #cbd5e1;
  }

  .folder-input {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .folder-path {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #cbd5e1;
    border-radius: 0.375rem;
    background-color: #f8fafc;
    color: #0f172a;
    font-size: 0.875rem;
  }

  :global(.dark) .folder-path {
    background-color: #1e293b;
    color: #e5e7eb;
    border-color: #475569;
  }

  .btn-sm {
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
  }

  /* Info Panel */
  .info-panel {
    background-color: #f0f9ff;
    border: 1px solid #bae6fd;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-top: auto;
  }

  :global(.dark) .info-panel {
    background-color: #082f49;
    border-color: #0c4a6e;
  }

  .info-panel h4 {
    margin: 0 0 0.75rem 0;
    font-size: 0.875rem;
    font-weight: 700;
    color: #0c4a6e;
  }

  :global(.dark) .info-panel h4 {
    color: #bae6fd;
  }

  .info-panel ul {
    margin: 0;
    padding-left: 1.25rem;
    font-size: 0.875rem;
    color: #0c4a6e;
    line-height: 1.6;
  }

  :global(.dark) .info-panel ul {
    color: #7dd3fc;
  }

  .info-panel li {
    margin-bottom: 0.25rem;
  }

  @media (max-width: 1024px) {
    .config-renderer {
      grid-template-columns: 1fr;
      grid-template-rows: 1fr auto;
    }

    .editor-panel {
      border-right: none;
      border-bottom: 1px solid #e2e8f0;
    }

    :global(.dark) .editor-panel {
      border-bottom-color: #334155;
    }

    .controls-panel {
      max-height: 400px;
    }
  }
</style>
