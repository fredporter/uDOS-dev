<script lang="ts">
  import {
    Home,
    File,
    Folder,
    Settings,
    Search,
    Star,
    Heart,
    Mail,
    Bell,
    User,
    Calendar,
    Clock,
    Download,
    Upload,
    Trash2,
    Edit,
    Save,
    Copy,
    Clipboard,
    Share2,
    Link,
    Image,
    Video,
    Music,
    Database,
    Server,
    Cloud,
    Code,
    Terminal,
    Package,
    Box,
    Archive,
    FileText,
    ChevronLeft,
    ChevronRight,
    ChevronUp,
    ChevronDown,
    Plus,
    Minus,
    X,
    Check,
    AlertCircle,
    AlertTriangle,
    Info,
    HelpCircle,
    Eye,
    EyeOff,
    Lock,
    Unlock,
    Play,
    Pause,
    SkipForward,
    SkipBack,
    Volume2,
    VolumeX,
  } from "lucide-svelte";

  let selectedSource: "all" | "lucide" | "system7" | "emoji" | "nethack" =
    "all";
  let iconSize = 24;
  let searchQuery = "";

  // Lucide icons showcase
  const lucideIcons = [
    { name: "Home", component: Home },
    { name: "File", component: File },
    { name: "Folder", component: Folder },
    { name: "Settings", component: Settings },
    { name: "Search", component: Search },
    { name: "Star", component: Star },
    { name: "Heart", component: Heart },
    { name: "Mail", component: Mail },
    { name: "Bell", component: Bell },
    { name: "User", component: User },
    { name: "Calendar", component: Calendar },
    { name: "Clock", component: Clock },
    { name: "Download", component: Download },
    { name: "Upload", component: Upload },
    { name: "Trash", component: Trash2 },
    { name: "Edit", component: Edit },
    { name: "Save", component: Save },
    { name: "Copy", component: Copy },
    { name: "Clipboard", component: Clipboard },
    { name: "Share", component: Share2 },
    { name: "Link", component: Link },
    { name: "Image", component: Image },
    { name: "Video", component: Video },
    { name: "Music", component: Music },
    { name: "Database", component: Database },
    { name: "Server", component: Server },
    { name: "Cloud", component: Cloud },
    { name: "Code", component: Code },
    { name: "Terminal", component: Terminal },
    { name: "Package", component: Package },
    { name: "Box", component: Box },
    { name: "Archive", component: Archive },
    { name: "FileText", component: FileText },
    { name: "ChevronLeft", component: ChevronLeft },
    { name: "ChevronRight", component: ChevronRight },
    { name: "ChevronUp", component: ChevronUp },
    { name: "ChevronDown", component: ChevronDown },
    { name: "Plus", component: Plus },
    { name: "Minus", component: Minus },
    { name: "X", component: X },
    { name: "Check", component: Check },
    { name: "AlertCircle", component: AlertCircle },
    { name: "AlertTriangle", component: AlertTriangle },
    { name: "Info", component: Info },
    { name: "Help", component: HelpCircle },
    { name: "Eye", component: Eye },
    { name: "EyeOff", component: EyeOff },
    { name: "Lock", component: Lock },
    { name: "Unlock", component: Unlock },
    { name: "Play", component: Play },
    { name: "Pause", component: Pause },
    { name: "SkipForward", component: SkipForward },
    { name: "SkipBack", component: SkipBack },
    { name: "Volume", component: Volume2 },
    { name: "Mute", component: VolumeX },
  ];

  // System7 sprites
  const system7Sprites = [
    {
      name: "Folder",
      path: "/sprites/system7/icons/folder.svg",
      category: "icons",
    },
    {
      name: "Document",
      path: "/sprites/system7/icons/document.svg",
      category: "icons",
    },
    {
      name: "Trash",
      path: "/sprites/system7/icons/trash-empty.svg",
      category: "icons",
    },
    {
      name: "Default Button",
      path: "/sprites/system7/buttons/button-default.svg",
      category: "buttons",
    },
    {
      name: "Checkbox",
      path: "/sprites/system7/controls/checkbox-checked.svg",
      category: "controls",
    },
    {
      name: "Radio",
      path: "/sprites/system7/controls/radio-selected.svg",
      category: "controls",
    },
    {
      name: "Scrollbar Up",
      path: "/sprites/system7/controls/scrollbar-up.svg",
      category: "controls",
    },
    {
      name: "Stop Alert",
      path: "/sprites/system7/alerts/stop.svg",
      category: "alerts",
    },
    {
      name: "Caution Alert",
      path: "/sprites/system7/alerts/caution.svg",
      category: "alerts",
    },
    {
      name: "Title Bar",
      path: "/sprites/system7/windows/titlebar-active.svg",
      category: "windows",
    },
    {
      name: "Resize Box",
      path: "/sprites/system7/windows/resize-box.svg",
      category: "windows",
    },
  ];

  // Emoji sprites
  const emojiSprites = [
    { name: "Rocket", path: "/sprites/emoji/rocket.svg" },
    { name: "Fire", path: "/sprites/emoji/fire.svg" },
  ];

  // NetHack sprites
  const nethackSprites = [
    { name: "Dog", path: "/sprites/monsters/dog.svg", category: "monsters" },
    { name: "Sword", path: "/sprites/objects/sword.svg", category: "objects" },
    {
      name: "Door (Closed)",
      path: "/sprites/dungeon/door_closed.svg",
      category: "dungeon",
    },
  ];

  $: filteredLucide = lucideIcons.filter(
    (icon) =>
      (selectedSource === "all" || selectedSource === "lucide") &&
      icon.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  $: filteredSystem7 = system7Sprites.filter(
    (sprite) =>
      (selectedSource === "all" || selectedSource === "system7") &&
      sprite.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  $: filteredEmoji = emojiSprites.filter(
    (sprite) =>
      (selectedSource === "all" || selectedSource === "emoji") &&
      sprite.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  $: filteredNethack = nethackSprites.filter(
    (sprite) =>
      (selectedSource === "all" || selectedSource === "nethack") &&
      sprite.name.toLowerCase().includes(searchQuery.toLowerCase())
  );
</script>

<svelte:head>
  <title>Icon Library - Markdown</title>
</svelte:head>

<div class="icon-browser">
  <header>
    <h1>Icon Library</h1>
    <p>Comprehensive icon collection from multiple sources</p>
  </header>

  <div class="controls">
    <div class="source-filters">
      <button
        class:active={selectedSource === "all"}
        on:click={() => (selectedSource = "all")}
      >
        All Sources
      </button>
      <button
        class:active={selectedSource === "lucide"}
        on:click={() => (selectedSource = "lucide")}
      >
        Lucide ({lucideIcons.length})
      </button>
      <button
        class:active={selectedSource === "system7"}
        on:click={() => (selectedSource = "system7")}
      >
        System7 ({system7Sprites.length})
      </button>
      <button
        class:active={selectedSource === "emoji"}
        on:click={() => (selectedSource = "emoji")}
      >
        Emoji ({emojiSprites.length})
      </button>
      <button
        class:active={selectedSource === "nethack"}
        on:click={() => (selectedSource = "nethack")}
      >
        NetHack ({nethackSprites.length})
      </button>
    </div>

    <div class="search-box">
      <Search size={16} />
      <input
        type="text"
        bind:value={searchQuery}
        placeholder="Search icons..."
      />
    </div>

    <div class="size-control">
      <label>
        Size: {iconSize}px
        <input type="range" min="16" max="128" bind:value={iconSize} />
      </label>
    </div>
  </div>

  {#if filteredLucide.length > 0}
    <section class="icon-section">
      <h2>Lucide Icons</h2>
      <p class="section-desc">
        Modern, clean icon set from <a href="https://lucide.dev" target="_blank"
          >lucide.dev</a
        >
      </p>

      <div class="icon-grid">
        {#each filteredLucide as icon}
          <div class="icon-card">
            <div
              class="icon-preview"
              style="width: {iconSize}px; height: {iconSize}px;"
            >
              <svelte:component this={icon.component} size={iconSize} />
            </div>
            <span class="icon-name">{icon.name}</span>
          </div>
        {/each}
      </div>
    </section>
  {/if}

  {#if filteredSystem7.length > 0}
    <section class="icon-section">
      <h2>System 7 Icons</h2>
      <p class="section-desc">Classic Mac System 7 style UI elements</p>

      <div class="icon-grid">
        {#each filteredSystem7 as sprite}
          <div class="icon-card">
            <div
              class="icon-preview sprite-preview"
              style="width: {iconSize}px; height: {iconSize}px;"
            >
              <img
                src={sprite.path}
                alt={sprite.name}
                style="width: 100%; height: 100%;"
              />
            </div>
            <span class="icon-name">{sprite.name}</span>
            <span class="icon-category">{sprite.category}</span>
          </div>
        {/each}
      </div>
    </section>
  {/if}

  {#if filteredEmoji.length > 0}
    <section class="icon-section">
      <h2>Emoji Sprites</h2>
      <p class="section-desc">Custom SVG emoji in uDOS style</p>

      <div class="icon-grid">
        {#each filteredEmoji as sprite}
          <div class="icon-card">
            <div
              class="icon-preview sprite-preview"
              style="width: {iconSize}px; height: {iconSize}px;"
            >
              <img
                src={sprite.path}
                alt={sprite.name}
                style="width: 100%; height: 100%;"
              />
            </div>
            <span class="icon-name">{sprite.name}</span>
          </div>
        {/each}
      </div>
    </section>
  {/if}

  {#if filteredNethack.length > 0}
    <section class="icon-section">
      <h2>NetHack Sprites</h2>
      <p class="section-desc">Pixel art sprites for roguelike adventures</p>

      <div class="icon-grid">
        {#each filteredNethack as sprite}
          <div class="icon-card">
            <div
              class="icon-preview sprite-preview"
              style="width: {iconSize}px; height: {iconSize}px;"
            >
              <img
                src={sprite.path}
                alt={sprite.name}
                style="width: 100%; height: 100%;"
              />
            </div>
            <span class="icon-name">{sprite.name}</span>
            <span class="icon-category">{sprite.category}</span>
          </div>
        {/each}
      </div>
    </section>
  {/if}

  {#if filteredLucide.length === 0 && filteredSystem7.length === 0 && filteredEmoji.length === 0 && filteredNethack.length === 0}
    <div class="no-results">
      <AlertCircle size={48} />
      <p>No icons found matching "{searchQuery}"</p>
    </div>
  {/if}
</div>

<style>
  .icon-browser {
    min-height: 100vh;
    padding: 24px;
    max-width: 1400px;
    margin: 0 auto;
  }

  header {
    margin-bottom: 32px;
  }

  h1 {
    font-size: 32px;
    font-weight: bold;
    margin: 0 0 8px 0;
    font-family: "Chicago", "Press Start 2P", monospace;
  }

  header p {
    color: #666;
    font-size: 14px;
  }

  .controls {
    background: #f5f5f5;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 32px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .source-filters {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .source-filters button {
    padding: 8px 16px;
    border: 2px solid #ddd;
    background: #fff;
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.2s;
  }

  .source-filters button:hover {
    border-color: #999;
  }

  .source-filters button.active {
    background: #000;
    color: #fff;
    border-color: #000;
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #fff;
    padding: 8px 12px;
    border: 2px solid #ddd;
    border-radius: 4px;
  }

  .search-box input {
    flex: 1;
    border: none;
    outline: none;
    font-size: 14px;
  }

  .size-control label {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 13px;
    color: #666;
  }

  .size-control input[type="range"] {
    width: 200px;
  }

  .icon-section {
    margin-bottom: 48px;
  }

  .icon-section h2 {
    font-size: 20px;
    font-weight: bold;
    margin: 0 0 8px 0;
    font-family: "Geneva", "Helvetica Neue", sans-serif;
  }

  .section-desc {
    color: #666;
    font-size: 13px;
    margin: 0 0 16px 0;
  }

  .section-desc a {
    color: #0066cc;
    text-decoration: none;
  }

  .section-desc a:hover {
    text-decoration: underline;
  }

  .icon-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 16px;
  }

  .icon-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 16px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    background: #fff;
    transition: all 0.2s;
    cursor: pointer;
  }

  .icon-card:hover {
    border-color: #999;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }

  .icon-preview {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .sprite-preview {
    background: repeating-conic-gradient(#f0f0f0 0% 25%, #ffffff 0% 50%) 50% /
      12px 12px;
    border-radius: 4px;
  }

  .icon-name {
    font-size: 12px;
    font-weight: 500;
    text-align: center;
    word-break: break-word;
  }

  .icon-category {
    font-size: 10px;
    color: #999;
    background: #f0f0f0;
    padding: 2px 6px;
    border-radius: 3px;
  }

  .no-results {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    padding: 64px;
    color: #999;
  }

  .no-results p {
    font-size: 16px;
  }
</style>
