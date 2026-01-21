<script lang="ts">
  /**
   * FileOperations Component
   * Demonstrates toast notifications for file operations
   */

  import { toasts } from "./store";

  // Simulate file operations with toast notifications
  async function handleNewFile() {
    toasts.info("Creating", "New untitled document");
    // Simulate async operation
    await new Promise((resolve) => setTimeout(resolve, 500));
    toasts.success("Created", "New document ready");
  }

  async function handleOpen() {
    toasts.onFileOpen("example.md");
    // Simulate file reading
    await new Promise((resolve) => setTimeout(resolve, 1000));
    toasts.onFileOpenSuccess("example.md");
  }

  async function handleSave() {
    toasts.onFileSave("document.md");
    // Simulate file writing
    await new Promise((resolve) => setTimeout(resolve, 800));
    toasts.onFileSaveSuccess("document.md");
  }

  function handleFormatChange(format: string) {
    toasts.onFormatApply(format);
    setTimeout(() => {
      toasts.onFormatApplySuccess(format);
    }, 500);
  }

  function handleFullscreen(entering: boolean) {
    toasts.onFullscreen(entering);
  }

  function handleError() {
    toasts.onError("Save failed", "Permission denied");
  }

  function handleWarning() {
    toasts.warning("Unsaved changes", "You have unsaved changes");
  }

  function handleMarkdownRender() {
    toasts.info("Rendering", "Converting markdown to HTML");
    setTimeout(() => {
      toasts.success("Rendered", "Markdown successfully rendered");
    }, 700);
  }

  function handleThemeSwitch() {
    toasts.info("Theme", "Switching to dark mode");
    setTimeout(() => {
      toasts.success("Theme", "Dark mode activated");
    }, 400);
  }

  function handleExport() {
    toasts.info("Exporting", "Preparing PDF export");
    setTimeout(() => {
      toasts.success("Exported", "document.pdf created");
    }, 1200);
  }

  function handleSync() {
    toasts.info("Syncing", "Syncing with cloud storage");
    setTimeout(() => {
      toasts.success("Synced", "All changes saved to cloud");
    }, 1500);
  }

  function handleSearch() {
    toasts.info("Searching", "Searching workspace...");
    setTimeout(() => {
      toasts.success("Found", "42 results in 12 files");
    }, 800);
  }

  function handleGitCommit() {
    toasts.info("Git", "Committing changes");
    setTimeout(() => {
      toasts.success("Git", "Changes committed successfully");
    }, 900);
  }
</script>

<div class="demo-panel">
  <h2>🎨 Toast Notifications Demo</h2>
  <p>Click buttons to see different notification types in action</p>

  <div class="section">
    <h3>File Operations</h3>
    <div class="button-grid">
      <button on:click={handleNewFile}>📄 New File</button>
      <button on:click={handleOpen}>📂 Open File</button>
      <button on:click={handleSave}>💾 Save File</button>
      <button on:click={handleExport}>📥 Export PDF</button>
    </div>
  </div>

  <div class="section">
    <h3>Format & Rendering</h3>
    <div class="button-grid">
      <button on:click={() => handleFormatChange("ucode")}
        >🔤 Format uCode</button
      >
      <button on:click={() => handleFormatChange("story")}
        >📖 Format Story</button
      >
      <button on:click={handleMarkdownRender}>✨ Render Markdown</button>
      <button on:click={handleThemeSwitch}>🌙 Switch Theme</button>
    </div>
  </div>

  <div class="section">
    <h3>System Features</h3>
    <div class="button-grid">
      <button on:click={() => handleFullscreen(true)}>🖥️ Fullscreen</button>
      <button on:click={handleSearch}>🔍 Search Files</button>
      <button on:click={handleSync}>☁️ Cloud Sync</button>
      <button on:click={handleGitCommit}>🔀 Git Commit</button>
    </div>
  </div>

  <div class="section">
    <h3>Notifications</h3>
    <div class="button-grid">
      <button on:click={handleWarning} style="background: #f59e0b;"
        >⚠️ Warning</button
      >
      <button on:click={handleError} style="background: #ef4444;"
        >❌ Error</button
      >
      <button on:click={() => toasts.info("Info", "Just a heads up")}
        >ℹ️ Info</button
      >
      <button on:click={() => toasts.success("Success", "All done!")}
        >✅ Success</button
      >
    </div>
  </div>
</div>

<style lang="postcss">
  .demo-panel {
    padding: 2rem;
    background-color: #f8fafc;
    border-radius: 0.75rem;
    margin: 1rem 0;
    border: 1px solid #e2e8f0;
  }

  :global(.dark) .demo-panel {
    background-color: #0f172a;
    border-color: #334155;
  }

  h2 {
    margin: 0 0 0.5rem 0;
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
  }

  :global(.dark) h2 {
    color: #e5e7eb;
  }

  .demo-panel p {
    margin: 0 0 2rem 0;
    color: #475569;
  }

  :global(.dark) .demo-panel p {
    color: #94a3b8;
  }

  .section {
    margin-bottom: 2rem;
  }

  .section:last-child {
    margin-bottom: 0;
  }

  h3 {
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
    font-weight: 700;
    color: #0f172a;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.875rem;
  }

  :global(.dark) h3 {
    color: #e5e7eb;
  }

  .button-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.75rem;
  }

  button {
    padding: 0.75rem 1rem;
    background-color: #3b82f6;
    color: white;
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.875rem;
    transition: all 200ms ease-out;
  }

  button:hover {
    background-color: #2563eb;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
  }

  button:active {
    transform: translateY(0);
  }
</style>
