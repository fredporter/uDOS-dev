<script>
  import { onMount } from "svelte";

  export let currentRoute = "dashboard";
  export let onNavigate = (route) => {};

  let menuOpen = false;
  let isFullscreen = false;

  const topNavRoutes = [
    { id: "dashboard", label: "Dashboard" },
    { id: "binder", label: "Binder" },
    { id: "screwdriver", label: "Screwdriver" },
  ];

  const allMenuRoutes = [
    { id: "dashboard", label: "🏠 Dashboard" },
    { separator: true, label: "Core Features" },
    { id: "binder", label: "📚 Binder Compiler" },
    { separator: true, label: "Device Provisioning" },
    { id: "screwdriver", label: "🔧 Screwdriver" },
    { id: "meshcore", label: "🌐 MeshCore" },
    { separator: true, label: "System" },
    { id: "config", label: "⚙️ Config" },
    { id: "logs", label: "📋 Logs" },
  ];

  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
        isFullscreen = false;
      } else {
        await document.documentElement.requestFullscreen();
        isFullscreen = true;
      }
    } catch (err) {
      console.error("Fullscreen error:", err);
    }
  }

  function handleNavigate(route) {
    onNavigate(route);
    menuOpen = false;
  }

  onMount(() => {
    const handleFullscreenChange = () => {
      isFullscreen = !!document.fullscreenElement;
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  });
</script>

<div class="goblin-top-bar">
  <div class="goblin-bar-content">
    <!-- Logo/Title -->
    <div class="goblin-bar-left">
      <h1 class="goblin-title">Goblin Dev Server</h1>
    </div>

    <!-- Center: Desktop Nav -->
    <nav class="goblin-nav-desktop">
      {#each topNavRoutes as route}
        <button
          class="nav-button {currentRoute === route.id ? 'active' : ''}"
          on:click={() => handleNavigate(route.id)}
          title={route.label}
        >
          {route.label}
        </button>
      {/each}
    </nav>

    <!-- Right: Controls -->
    <div class="goblin-bar-right">
      <!-- Hamburger Menu -->
      <button
        class="hamburger-button"
        on:click={() => (menuOpen = !menuOpen)}
        aria-label="Menu"
        title="Open menu"
      >
        <svg
          width="24"
          height="24"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>
    </div>
  </div>

  <!-- Dropdown Menu -->
  {#if menuOpen}
    <div class="menu-dropdown">
      {#each allMenuRoutes as route}
        {#if route.separator}
          <div class="menu-separator"></div>
          <div class="menu-label">{route.label}</div>
        {:else}
          <button
            class="menu-item {currentRoute === route.id ? 'active' : ''}"
            on:click={() => handleNavigate(route.id)}
          >
            {route.label}
          </button>
        {/if}
      {/each}
    </div>
  {/if}
</div>
