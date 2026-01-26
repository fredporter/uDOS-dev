<script lang="ts">
  import { Home, Palette, Image, Smile, Package } from "lucide-svelte";
</script>

<svelte:head>
  <title>Visual Library - Markdown</title>
</svelte:head>

<div class="visual-library">
  <header>
    <h1>Visual Library</h1>
    <p>Icons, sprites, and UI components for uDOS</p>
  </header>

  <div class="card-grid">
    <!-- Unified Icon Browser -->
    <a href="/icons" class="feature-card">
      <div class="card-icon">
        <Package size={48} />
      </div>
      <h2>Icon Library</h2>
      <p>
        Browse all icon sources in one place. Search, filter, and preview icons
        from Lucide, System7, NetHack, and emoji collections.
      </p>
      <div class="card-stats">
        <span class="stat">
          <strong>4</strong> sources
        </span>
        <span class="stat">
          <strong>4600+</strong> icons
        </span>
      </div>
      <span class="card-link">Explore Icons →</span>
    </a>

    <!-- System7 UI Demo -->
    <a href="/system7" class="feature-card">
      <div class="card-icon">
        <img src="/sprites/system7/icons/folder.svg" width="48" alt="System7" />
      </div>
      <h2>System 7 UI</h2>
      <p>
        Classic Macintosh System 7 interface components. Draggable windows,
        alerts, buttons, and controls in authentic retro style.
      </p>
      <div class="card-stats">
        <span class="stat">
          <strong>4</strong> components
        </span>
        <span class="stat">
          <strong>12</strong> sprites
        </span>
      </div>
      <span class="card-link">View Demo →</span>
    </a>

    <!-- NetHack Sprites -->
    <a href="/sprites" class="feature-card">
      <div class="card-icon">
        <img src="/sprites/monsters/dog.svg" width="48" alt="NetHack" />
      </div>
      <h2>NetHack Sprites</h2>
      <p>
        Pixel art sprites for roguelike adventures. Monsters, objects, dungeon
        tiles, and effects in 24×24 SVG format.
      </p>
      <div class="card-stats">
        <span class="stat">
          <strong>4</strong> categories
        </span>
        <span class="stat">
          <strong>5</strong> sprites
        </span>
      </div>
      <span class="card-link">Browse Sprites →</span>
    </a>

    <!-- Emoji Reference -->
    <a href="/fonts/emoji.json" class="feature-card" target="_blank">
      <div class="card-icon">
        <Smile size={48} />
      </div>
      <h2>Emoji Library</h2>
      <p>
        Complete emoji shortcode mappings for Noto Emoji fonts. 210+ emoji with
        both TTF and SVG sprite versions available.
      </p>
      <div class="card-stats">
        <span class="stat">
          <strong>210+</strong> mappings
        </span>
        <span class="stat">
          <strong>2</strong> fonts
        </span>
      </div>
      <span class="card-link">View JSON →</span>
    </a>
  </div>

  <section class="documentation">
    <h2>Documentation</h2>

    <div class="doc-grid">
      <a href="/static/icons/README.md" class="doc-card" target="_blank">
        <h3>📚 Icon Library Guide</h3>
        <p>
          Comprehensive guide to all icon sources, usage patterns, size
          guidelines, and best practices.
        </p>
      </a>

      <a
        href="/src/lib/components/system7/README.md"
        class="doc-card"
        target="_blank"
      >
        <h3>🖥️ System7 Quick Reference</h3>
        <p>
          API documentation for System7 components with code examples and usage
          tips.
        </p>
      </a>

      <a href="/static/sprites/README.md" class="doc-card" target="_blank">
        <h3>🎮 Sprite System Guide</h3>
        <p>
          NetHack sprite format, SVG architecture, and Pixel Editor integration
          documentation.
        </p>
      </a>

      <a href="/ICON-SYSTEM-SUMMARY.md" class="doc-card" target="_blank">
        <h3>📝 Implementation Summary</h3>
        <p>
          Complete overview of the icon and sprite system implementation with
          statistics.
        </p>
      </a>
    </div>
  </section>

  <section class="features">
    <h2>Features</h2>

    <div class="feature-list">
      <div class="feature-item">
        <Home size={24} />
        <div>
          <h3>Multiple Icon Sources</h3>
          <p>Lucide (1000+), System7 (12), NetHack (5), Noto Emoji (3600+)</p>
        </div>
      </div>

      <div class="feature-item">
        <Palette size={24} />
        <div>
          <h3>Classic Mac Aesthetic</h3>
          <p>Authentic System 7 UI with period-accurate fonts and colors</p>
        </div>
      </div>

      <div class="feature-item">
        <Image size={24} />
        <div>
          <h3>Scalable SVG Sprites</h3>
          <p>Pixel art that scales perfectly from 16px to 192px</p>
        </div>
      </div>

      <div class="feature-item">
        <Package size={24} />
        <div>
          <h3>Reusable Components</h3>
          <p>Window, Button, Checkbox, Alert components ready to use</p>
        </div>
      </div>
    </div>
  </section>

  <section class="quick-start">
    <h2>Quick Start</h2>

    <div class="code-examples">
      <div class="code-example">
        <h3>Import Lucide Icons</h3>
        <pre><code
            >import &#123; Home, Settings &#125; from 'lucide-svelte';

&lt;Home size=&#123;24&#125; /&gt;
&lt;Settings size=&#123;20&#125; color="#666" /&gt;</code
          ></pre>
      </div>

      <div class="code-example">
        <h3>Use System7 Components</h3>
        <pre><code
            >import &#123; Window, Button &#125; from '$lib/components/system7';

&lt;Window title="My App"&gt;
  &lt;Button label="Save" variant="default" /&gt;
&lt;/Window&gt;</code
          ></pre>
      </div>

      <div class="code-example">
        <h3>Load Sprites</h3>
        <pre><code
            >&lt;img 
  src="/sprites/system7/icons/folder.svg" 
  width="32" 
  alt="Folder" 
/&gt;</code
          ></pre>
      </div>
    </div>
  </section>
</div>

<style>
  .visual-library {
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 20px;
  }

  header {
    text-align: center;
    margin-bottom: 48px;
  }

  h1 {
    font-size: 48px;
    font-weight: bold;
    margin: 0 0 16px 0;
    font-family: "Chicago", "Press Start 2P", monospace;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  header p {
    font-size: 18px;
    color: #666;
  }

  section {
    margin: 64px 0;
  }

  section h2 {
    font-size: 32px;
    font-weight: bold;
    margin: 0 0 24px 0;
    font-family: "Geneva", "Helvetica Neue", sans-serif;
  }

  .card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 24px;
    margin-bottom: 64px;
  }

  .feature-card {
    display: flex;
    flex-direction: column;
    padding: 32px;
    background: #ffffff;
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    text-decoration: none;
    color: inherit;
    transition: all 0.3s;
  }

  .feature-card:hover {
    border-color: #667eea;
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
    transform: translateY(-4px);
  }

  .card-icon {
    width: 48px;
    height: 48px;
    margin-bottom: 16px;
    color: #667eea;
  }

  .card-icon img {
    background: repeating-conic-gradient(#f8f8f8 0% 25%, #ffffff 0% 50%) 50% /
      8px 8px;
    border-radius: 8px;
    padding: 4px;
  }

  .feature-card h2 {
    font-size: 24px;
    font-weight: bold;
    margin: 0 0 12px 0;
  }

  .feature-card p {
    flex: 1;
    font-size: 14px;
    line-height: 1.6;
    color: #666;
    margin: 0 0 16px 0;
  }

  .card-stats {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
    padding-top: 16px;
    border-top: 1px solid #e0e0e0;
  }

  .stat {
    font-size: 12px;
    color: #999;
  }

  .stat strong {
    display: block;
    font-size: 20px;
    color: #333;
    font-weight: bold;
  }

  .card-link {
    font-size: 14px;
    font-weight: 600;
    color: #667eea;
  }

  .doc-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
  }

  .doc-card {
    padding: 24px;
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s;
  }

  .doc-card:hover {
    background: #ffffff;
    border-color: #667eea;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .doc-card h3 {
    font-size: 16px;
    font-weight: bold;
    margin: 0 0 8px 0;
  }

  .doc-card p {
    font-size: 13px;
    color: #666;
    margin: 0;
    line-height: 1.5;
  }

  .feature-list {
    display: grid;
    gap: 16px;
  }

  .feature-item {
    display: flex;
    gap: 16px;
    padding: 20px;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
  }

  .feature-item h3 {
    font-size: 16px;
    font-weight: 600;
    margin: 0 0 4px 0;
  }

  .feature-item p {
    font-size: 14px;
    color: #666;
    margin: 0;
  }

  .code-examples {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 24px;
  }

  .code-example {
    background: #1e1e1e;
    border-radius: 8px;
    overflow: hidden;
  }

  .code-example h3 {
    font-size: 14px;
    font-weight: 600;
    margin: 0;
    padding: 12px 16px;
    background: #2d2d2d;
    color: #ffffff;
  }

  .code-example pre {
    margin: 0;
    padding: 16px;
    overflow-x: auto;
  }

  .code-example code {
    font-family: "Monaco", "Courier New", monospace;
    font-size: 12px;
    line-height: 1.6;
    color: #d4d4d4;
  }
</style>
