<script lang="ts">
  import { onMount } from "svelte";
  import { toasts } from "./components/UI/Toast/store";
  import { themeStore } from "./lib/stores/themeStore";
  import { fileManager } from "./lib/utils/fileManager";
  import {
    keyboardShortcuts,
    initKeyboardShortcuts,
    SHORTCUTS_HELP,
  } from "./lib/utils/keyboardShortcuts";
  import TypoBottomBar from "./components/UI/TypoBottomBar.svelte";
  // Remove fontFamily/fontSize store imports
  import ToastContainer from "./components/UI/Toast/ToastContainer.svelte";
  import FileOperations from "./components/UI/Toast/FileOperations.svelte";
  import {
    UCodeRenderer,
    StoryRenderer,
    GuideRenderer,
    ConfigRenderer,
    MarpRenderer,
    FontManager,
    Landing,
    TypoEditor,
  } from "./components/Renderers";
  import {
    Menu,
    Close,
    CodeBracket,
    Bullet,
    Info,
    Warning,
    Slideshow,
    Eye,
    Settings,
    Type,
    Document,
  } from "./components/icons";

  let isDark = true;
  let currentFormat = "editor";
  let isCommandPaletteOpen = false;
  let isSettingsOpen = false;
  let menuOpen = false;
  let showLanding = true;
  let showLandingOnStartup = true;
  // Editor state for binding
  let viewMode = false;
  let charCount = 0;
  let wordCount = 0;
  // File management state
  let currentFilePath: string = "";
  let currentFileContent: string = "";
  let editorRef: any = null;

  // Subscribe to theme changes
  $: if ($themeStore) {
    isDark = $themeStore.isDark;
  }

  // Initialize theme on mount
  onMount(() => {
    themeStore.initialize();
  });

  // Marp example slides
  const marpSlides = [
    {
      content: `<div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; text-align: center; background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; padding: 3rem;">
        <h1 style="margin: 0; font-size: 3rem; margin-bottom: 1rem; animation: fadeInUp 0.8s ease-out;">uMarkdown</h1>
        <p style="margin: 0; font-size: 1.5rem; opacity: 0.9; animation: fadeInUp 0.8s ease-out 0.2s backwards;">Interactive Markdown Presentation</p>
        <p style="margin: 1.5rem 0 0 0; font-size: 1rem; opacity: 0.8; animation: fadeInUp 0.8s ease-out 0.4s backwards;">Powered by Marp</p>
        <style>@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }</style>
      </div>`,
    },
    {
      content: `<div style="padding: 3rem; height: 100%; display: flex; flex-direction: column; justify-content: center; background: white; color: #0f172a;">
        <h2 style="margin-top: 0; color: #3b82f6; font-size: 2.5rem;">What is Marp?</h2>
        <ul style="font-size: 1.3rem; line-height: 2; margin: 2rem 0;">
          <li>📝 Markdown-powered presentations</li>
          <li>🎨 Beautiful default themes</li>
          <li>⚡ Fast and lightweight</li>
          <li>✨ Auto-scaling for code and math</li>
          <li>🔄 Smooth slide transitions</li>
        </ul>
      </div>`,
    },
    {
      content: `<div style="padding: 3rem; height: 100%; display: flex; flex-direction: column; justify-content: center; background: linear-gradient(to right, #6366f1, #8b5cf6); color: white;">
        <h2 style="margin-top: 0; font-size: 2.5rem; text-shadow: 0 2px 10px rgba(0,0,0,0.2);">Color Themes</h2>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem; margin-top: 2rem;">
          <div style="background: rgba(255,255,255,0.15); padding: 1.5rem; border-radius: 0.5rem; backdrop-filter: blur(10px); text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🎨</div>
            <h3 style="margin: 0.5rem 0; font-size: 1.3rem;">Default</h3>
            <p style="margin: 0; font-size: 0.95rem; opacity: 0.9;">GitHub-style</p>
          </div>
          <div style="background: rgba(255,255,255,0.15); padding: 1.5rem; border-radius: 0.5rem; backdrop-filter: blur(10px); text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">✨</div>
            <h3 style="margin: 0.5rem 0; font-size: 1.3rem;">Gaia</h3>
            <p style="margin: 0; font-size: 0.95rem; opacity: 0.9;">Elegant design</p>
          </div>
          <div style="background: rgba(255,255,255,0.15); padding: 1.5rem; border-radius: 0.5rem; backdrop-filter: blur(10px); text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🎭</div>
            <h3 style="margin: 0.5rem 0; font-size: 1.3rem;">Custom</h3>
            <p style="margin: 0; font-size: 0.95rem; opacity: 0.9;">Your style</p>
          </div>
        </div>
      </div>`,
    },
    {
      content: `<div style="padding: 3rem; height: 100%; display: flex; flex-direction: column; justify-content: center; background: #0f172a; color: white;">
        <h2 style="margin-top: 0; color: #60a5fa; font-size: 2.5rem;">Features</h2>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 2rem; font-size: 1.1rem;">
          <div style="border-left: 4px solid #60a5fa; padding-left: 1.5rem;">
            <h3 style="color: #60a5fa; margin-top: 0;">Markdown Support</h3>
            <p>Full CommonMark compatibility with extended syntax for presentations</p>
          </div>
          <div style="border-left: 4px solid #34d399; padding-left: 1.5rem;">
            <h3 style="color: #34d399; margin-top: 0;">Multiple Themes</h3>
            <p>Default, Gaia, and custom themes for professional presentations</p>
          </div>
          <div style="border-left: 4px solid #fbbf24; padding-left: 1.5rem;">
            <h3 style="color: #fbbf24; margin-top: 0;">Math Rendering</h3>
            <p>MathJax support for complex equations and formulas</p>
          </div>
          <div style="border-left: 4px solid #f87171; padding-left: 1.5rem;">
            <h3 style="color: #f87171; margin-top: 0;">Code Highlighting</h3>
            <p>Syntax highlighting for 50+ programming languages</p>
          </div>
        </div>
      </div>`,
    },
    {
      content: `<div style="padding: 3rem; height: 100%; display: flex; flex-direction: column; justify-content: center; background: radial-gradient(circle at top right, #ec4899, #8b5cf6); color: white;">
        <h2 style="margin-top: 0; font-size: 2.5rem; text-shadow: 0 2px 10px rgba(0,0,0,0.3);">Transitions</h2>
        <div style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 0.75rem; backdrop-filter: blur(10px); margin-top: 1.5rem;">
          <p style="font-size: 1.3rem; margin: 0 0 1.5rem 0; line-height: 1.6;">
            Marp supports 33 built-in transition effects:
          </p>
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; font-size: 1rem;">
            <div>• Fade</div>
            <div>• Slide</div>
            <div>• Cover</div>
            <div>• Wipe</div>
            <div>• Zoom</div>
            <div>• Clockwise</div>
            <div>• Drop</div>
            <div>• Swap</div>
            <div>• & more...</div>
          </div>
        </div>
      </div>`,
    },
    {
      content: `<div style="padding: 3rem; height: 100%; display: flex; flex-direction: column; justify-content: center; background: #f0f9ff; color: #0c4a6e;">
        <h2 style="margin-top: 0; color: #0c4a6e; font-size: 2.5rem;">Code Example</h2>
        <pre style="background: #1e293b; color: #e5e7eb; padding: 1.5rem; border-radius: 0.5rem; overflow: auto; margin: 1.5rem 0; font-size: 0.95rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15);"><code>---
theme: default
transition: fade
---

# This is a Marp slide

- Supports **bold** and *italic*
- Code blocks with syntax highlighting
- Math: $ax^2 + bx + c = 0$
- Images, tables, and more!</code></pre>
        <p style="margin: 1rem 0 0 0; font-size: 1rem; text-align: center;">Easy to write, powerful to present 🚀</p>
      </div>`,
    },
    {
      content: `<div style="padding: 3rem; height: 100%; display: flex; flex-direction: column; justify-content: center; background: linear-gradient(135deg, #f59e0b 0%, #ef4444 50%, #ec4899 100%); color: white;">
        <h2 style="margin-top: 0; font-size: 2.5rem; text-align: center; text-shadow: 0 2px 15px rgba(0,0,0,0.3);">Morphing Animations</h2>
        <div style="background: rgba(255,255,255,0.15); padding: 2.5rem; border-radius: 1rem; backdrop-filter: blur(10px); margin-top: 2rem; text-align: center;">
          <div style="font-size: 4rem; margin-bottom: 1.5rem;">🎬</div>
          <p style="font-size: 1.3rem; margin: 0; line-height: 1.8;">
            Create smooth element transitions between slides with CSS properties
          </p>
          <p style="margin-top: 1.5rem; font-size: 1rem; opacity: 0.9;">
            Similar to PowerPoint Morph & Keynote Magic Move
          </p>
        </div>
      </div>`,
    },
    {
      content: `<div style="padding: 3rem; height: 100%; display: flex; flex-direction: column; justify-content: center; text-align: center; background: linear-gradient(135deg, #0ea5e9, #06b6d4); color: white;">
        <h2 style="margin: 0; font-size: 2.5rem; margin-bottom: 1.5rem; text-shadow: 0 2px 10px rgba(0,0,0,0.2);">Get Started!</h2>
        <p style="font-size: 1.3rem; margin: 0 0 2rem 0;">
          Create beautiful presentations with just Markdown
        </p>
        <div style="background: rgba(255,255,255,0.2); padding: 1.5rem; border-radius: 0.75rem; backdrop-filter: blur(10px); display: inline-block; margin: 0 auto;">
          <p style="margin: 0; font-size: 1.1rem;">Switch to <strong>Present</strong> mode to explore more ✨</p>
        </div>
      </div>`,
    },
  ];

  // Global font and size reactivity
  // Global dark mode reactivity only
  $: {
    if (typeof window !== "undefined") {
      if (isDark) {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    }
  }

  function registerKeyboardShortcuts() {
    // Register shortcuts with the keyboard shortcuts manager
    keyboardShortcuts.register("cmd-n", {
      name: "New",
      keys: "Cmd+N",
      description: "Create a new document",
      handler: handleNewFile,
    });

    keyboardShortcuts.register("cmd-o", {
      name: "Open",
      keys: "Cmd+O",
      description: "Open a file",
      handler: handleOpenFile,
    });

    keyboardShortcuts.register("cmd-s", {
      name: "Save",
      keys: "Cmd+S",
      description: "Save the current file",
      handler: handleSaveFile,
    });

    keyboardShortcuts.register("cmd-shift-s", {
      name: "Save As",
      keys: "Cmd+Shift+S",
      description: "Save the file with a new name",
      handler: () => toasts.info("💾 Save As - Open dialog"),
    });

    keyboardShortcuts.register("cmd-k", {
      name: "Command Palette",
      keys: "Cmd+K",
      description: "Open command palette",
      handler: handleCommandPalette,
    });

    keyboardShortcuts.register("cmd-comma", {
      name: "Settings",
      keys: "Cmd+,",
      description: "Open settings",
      handler: handleSettings,
    });

    keyboardShortcuts.register("cmd-h", {
      name: "Hide Window",
      keys: "Cmd+H",
      description: "Hide the application window",
      handler: () => {
        if (typeof window !== "undefined") {
          (window as any).__TAURI__.window.getCurrent().hide();
        }
      },
    });

    keyboardShortcuts.register("cmd-q", {
      name: "Quit",
      keys: "Cmd+Q",
      description: "Quit the application",
      handler: () => {
        if (typeof window !== "undefined") {
          (window as any).__TAURI__.app.exit(0);
        }
      },
    });
  }

  onMount(async () => {
    // Initialize theme from localStorage
    const saved = localStorage.getItem("theme");
    if (saved) {
      isDark = saved === "dark";
    } else {
      // Check system preference
      isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    applyTheme();

    // Check if landing page should be shown
    const landingPref = localStorage.getItem("showLandingOnStartup");
    if (landingPref === "false") {
      showLanding = false;
      showLandingOnStartup = false;
    }

    // Register keyboard shortcuts
    initKeyboardShortcuts();
    registerKeyboardShortcuts();
  });

  async function handleNewFile() {
    try {
      // Get default folder or Documents folder
      let defaultFolder: string;
      try {
        defaultFolder = await fileManager.getDefaultMdFolder();
      } catch {
        // Fallback to Documents folder
        defaultFolder = await fileManager.getDocumentsFolder();
      }

      const filePath = await fileManager.createNewFile(defaultFolder);
      if (filePath) {
        currentFilePath = filePath;
        currentFileContent = "# New Document\n\nStart typing here...";

        // Update editor if it exists
        if (editorRef && editorRef.setContent) {
          editorRef.setContent(currentFileContent);
        }

        // Write initial content
        await fileManager.writeFile(filePath, currentFileContent);

        const fileName = filePath.split("/").pop() || "document.md";
        toasts.success(`📄 Created: ${fileName}`);

        // Switch to editor view
        currentFormat = "editor";
      }
    } catch (error) {
      console.error("Create file error:", error);
      toasts.error("Failed to create new file");
    }
  }

  async function handleOpenFile() {
    try {
      const filePath = await fileManager.openFileDialog();
      if (filePath) {
        const content = await fileManager.readFile(filePath);
        currentFilePath = filePath;
        currentFileContent = content;

        // Update editor if it exists
        if (editorRef && editorRef.setContent) {
          editorRef.setContent(content);
        }

        const fileName = filePath.split("/").pop() || "file.md";
        toasts.success(`📂 Opened: ${fileName}`);

        // Switch to editor view
        currentFormat = "editor";
      }
    } catch (error) {
      console.error("Open file error:", error);
      toasts.error("Failed to open file");
    }
  }

  async function handleSaveFile() {
    try {
      // Get current content from editor
      let content = currentFileContent;
      if (editorRef && editorRef.getContent) {
        content = editorRef.getContent();
      }

      // If no current file, do Save As (prompt for location)
      if (!currentFilePath) {
        // Get default folder
        let defaultFolder: string;
        try {
          defaultFolder = await fileManager.getDefaultMdFolder();
        } catch {
          defaultFolder = await fileManager.getDocumentsFolder();
        }

        // Create new file
        const filePath = await fileManager.createNewFile(defaultFolder);
        if (!filePath) return;

        currentFilePath = filePath;
      }

      // Save to current file path
      await fileManager.writeFile(currentFilePath, content);
      currentFileContent = content;

      const fileName = currentFilePath.split("/").pop() || "document.md";
      toasts.success(`💾 Saved: ${fileName}`);
    } catch (error) {
      console.error("Save file error:", error);
      toasts.error("Failed to save file");
    }
  }

  function handleCommandPalette() {
    toasts.info("🎯 Command palette");
    isCommandPaletteOpen = true;
  }

  function handleSettings() {
    toasts.info("⚙️ Settings");
    isSettingsOpen = true;
  }

  function toggleDarkMode() {
    themeStore.toggle();
    toasts.info(`Switched to ${isDark ? "dark" : "light"} mode`);
  }

  function applyTheme() {
    const html = document.documentElement;
    if (isDark) {
      html.classList.add("dark");
    } else {
      html.classList.remove("dark");
    }
  }

  function handleLandingDismiss() {
    showLanding = false;
    if (!showLandingOnStartup) {
      localStorage.setItem("showLandingOnStartup", "false");
    }
  }

  function toggleShowLandingOnStartup() {
    showLandingOnStartup = !showLandingOnStartup;
    localStorage.setItem(
      "showLandingOnStartup",
      showLandingOnStartup.toString(),
    );
  }
</script>

<div class="app-wrapper" id="app-wrapper">
  <!-- Global Hamburger Menu -->
  <button
    class="fixed top-4 right-4 z-[200] p-2 rounded-lg bg-gray-900 hover:bg-gray-800 transition text-white shadow-lg"
    on:click={() => (menuOpen = !menuOpen)}
    aria-label="Menu"
  >
    <Menu class="w-5 h-5" />
  </button>

  <!-- Compact Dropdown Menu -->
  {#if menuOpen}
    <button
      class="fixed inset-0 z-[250]"
      on:click={() => (menuOpen = false)}
      aria-label="Close menu"
      type="button"
    />
    <div
      class="fixed top-16 right-4 w-72 z-[260] rounded-xl flex flex-col p-2 gap-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-2xl"
    >
      <nav class="flex flex-col gap-1">
        <button
          class="w-full text-left px-4 py-2 rounded-lg font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          on:click={() => {
            currentFormat = "editor";
            menuOpen = false;
          }}
        >
          Markdown Editor
        </button>
        <button
          class="w-full text-left px-4 py-2 rounded-lg font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          on:click={() => {
            currentFormat = "guide";
            menuOpen = false;
          }}
        >
          Guide Reader
        </button>
        <button
          class="w-full text-left px-4 py-2 rounded-lg font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          on:click={() => {
            currentFormat = "story";
            menuOpen = false;
          }}
        >
          Interactive Story
        </button>
        <button
          class="w-full text-left px-4 py-2 rounded-lg font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          on:click={() => {
            currentFormat = "marp";
            menuOpen = false;
          }}
        >
          Slide Presentation
        </button>
        <button
          class="w-full text-left px-4 py-2 rounded-lg font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          on:click={() => {
            currentFormat = "ucode";
            menuOpen = false;
          }}
        >
          uCode Runtime
        </button>
        <button
          class="w-full text-left px-4 py-2 rounded-lg font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          on:click={() => {
            currentFormat = "fonts";
            menuOpen = false;
          }}
        >
          Font Manager
        </button>
        <button
          class="w-full text-left px-4 py-2 rounded-lg font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          on:click={() => {
            currentFormat = "config";
            menuOpen = false;
          }}
        >
          Config Settings
        </button>
      </nav>
      <button
        class="absolute top-2 right-2 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400"
        on:click={() => (menuOpen = false)}
        aria-label="Close menu"
        style="z-index:214;"
      >
        <Close class="w-4 h-4" />
      </button>
    </div>
  {/if}

  <!-- Landing Page -->
  {#if showLanding}
    <Landing
      {isDark}
      {showLandingOnStartup}
      onRendererSelect={(format) => {
        currentFormat = format;
        handleLandingDismiss();
      }}
      onDarkModeToggle={toggleDarkMode}
      onDismiss={handleLandingDismiss}
      onToggleShowOnStartup={toggleShowLandingOnStartup}
    />
  {:else if currentFormat === "editor"}
    <TypoEditor
      bind:isDark
      bind:viewMode
      bind:charCount
      bind:wordCount
      onDarkModeToggle={toggleDarkMode}
      onSave={(content) => toasts.success("Document saved")}
    />
  {:else}
    <!-- Header for other renderers -->
    <header class="app-header">
      <div class="header-content">
        <button
          on:click={() => (currentFormat = "editor")}
          class="logo-button"
          title="Back to editor"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            class="w-5 h-5 inline"
            style="display: inline; margin-right: 0.5rem; vertical-align: middle;"
          >
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 5 12 12 19"></polyline>
          </svg> Markdown
        </button>
        <nav class="nav">
          <button
            on:click={() => (currentFormat = "guide")}
            class="nav-button flex items-center gap-1"
          >
            <Info class="w-4 h-4" /><span class="nav-label">Guide</span>
          </button>
          <button
            on:click={() => (currentFormat = "story")}
            class="nav-button flex items-center gap-1"
          >
            <Bullet class="w-4 h-4" /><span class="nav-label">Story</span>
          </button>
          <button
            on:click={() => (currentFormat = "marp")}
            class="nav-button flex items-center gap-1"
          >
            <Slideshow class="w-4 h-4" /><span class="nav-label">Present</span>
          </button>
          <button
            on:click={() => (currentFormat = "ucode")}
            class="nav-button flex items-center gap-1"
          >
            <CodeBracket class="w-4 h-4" /><span class="nav-label">uCode</span>
          </button>
        </nav>
      </div>
    </header>

    <!-- Main content -->
    <main class="app-main">
      {#if currentFormat === "editor"}
        <TypoEditor
          bind:this={editorRef}
          {isDark}
          onDarkModeToggle={toggleDarkMode}
          onSave={handleSaveFile}
          onNew={handleNewFile}
          onOpen={handleOpenFile}
          currentFile={currentFilePath}
          bind:viewMode
          bind:wordCount
          bind:charCount
        />
      {:else if currentFormat === "ucode"}
        <UCodeRenderer
          content="<h2>uCode Document</h2><p>Executable markdown with runtime blocks.</p>"
          frontmatter={{
            title: "Sample uCode",
            description: "Example document",
          }}
        />
      {:else if currentFormat === "story"}
        <StoryRenderer
          story={{ title: "Interactive Story", description: "Tell your story" }}
        />
      {:else if currentFormat === "guide"}
        <GuideRenderer
          content="<h2>Getting Started</h2><p>Welcome to the guide.</p>"
          frontmatter={{
            title: "Knowledge Guide",
            author: "uDOS",
            date: new Date(),
          }}
        />
      {:else if currentFormat === "fonts"}
        <FontManager />
      {:else if currentFormat === "config"}
        <ConfigRenderer config={{ theme: "auto", reducedMotion: false }} />
      {:else if currentFormat === "marp"}
        <MarpRenderer slides={marpSlides} />
      {:else if currentFormat === "home"}
        <!-- Toast Demo Section -->
        <section class="demo-section">
          <h2>🎨 Toast Notifications Demo</h2>
          <p>Click buttons below to see toast notifications in action:</p>
          <FileOperations />
        </section>
      {/if}
    </main>
  {/if}

  <!-- Toast notifications -->
  <ToastContainer />
  <TypoBottomBar
    {isDark}
    onDarkModeToggle={toggleDarkMode}
    bind:viewMode
    onToggleView={() => (viewMode = !viewMode)}
    {charCount}
    {wordCount}
  />
</div>

<style>
  :global(html) {
    color-scheme: light;
    transition:
      color-scheme 200ms ease-out,
      background-color 200ms ease-out;
  }

  :global(html.dark) {
    color-scheme: dark;
  }

  .app-wrapper {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    background-color: transparent;
    color: inherit;
    font-family: inherit;
    font-size: inherit;
    transition:
      background-color 200ms ease-out,
      color 200ms ease-out;
  }

  .app-header {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 0.5rem 1.5rem;
    position: sticky;
    top: 0;
    z-index: 100;
    transition: all 200ms ease-out;
    display: flex;
    align-items: center;
  }

  :global(html.dark) .app-header {
    background-color: #0f172a;
    border-bottom-color: #334155;
  }

  .header-content {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 2rem;
    width: 100%;
    height: 100%;
  }

  .logo-button {
    background: none;
    border: none;
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
    cursor: pointer;
    padding: 0.375rem 0.75rem;
    margin: 0;
    border-radius: 0.375rem;
    transition: color 200ms ease-out;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    white-space: nowrap;
  }

  :global(html.dark) .logo-button {
    color: #e5e7eb;
  }

  .logo-button:hover {
    color: #2563eb;
  }

  :global(html.dark) .logo-button:hover {
    color: #60a5fa;
  }

  .nav {
    display: flex;
    gap: 0.5rem;
    flex: 1;
  }

  .nav-button {
    background: none;
    border: none;
    color: #334155;
    text-decoration: none;
    font-weight: 500;
    padding: 0.375rem 0.75rem;
    border-radius: 0.375rem;
    transition: all 200ms ease-out;
    cursor: pointer;
    font-size: 0.875rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    opacity: 0.8;
  }

  :global(html.dark) .nav-button {
    color: #cbd5e1;
  }

  .nav-button:hover {
    background-color: #f1f5f9;
    color: #2563eb;
    opacity: 1;
  }

  :global(html.dark) .nav-button:hover {
    background-color: #1e293b;
    color: #60a5fa;
  }

  .nav-label {
    display: inline;
  }

  @media (max-width: 768px) {
    .nav-label {
      display: none;
    }

    .nav {
      gap: 0.25rem;
    }

    .nav-button {
      padding: 0.5rem;
    }
  }

  .app-main {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .demo-section {
    padding: 2rem;
    margin: 1rem;
    background-color: #f8fafc;
    border-radius: 0.5rem;
    border: 1px solid #e2e8f0;
  }

  :global(html.dark) .demo-section {
    background-color: #1e293b;
    border-color: #334155;
  }

  .demo-section h2 {
    margin-top: 0;
    color: #2563eb;
  }

  :global(html.dark) .demo-section h2 {
    color: #60a5fa;
  }

  .demo-section p {
    margin-bottom: 1rem;
    color: #475569;
  }

  :global(html.dark) .demo-section p {
    color: #94a3b8;
  }
</style>
