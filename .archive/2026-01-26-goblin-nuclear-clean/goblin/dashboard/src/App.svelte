<script>
  import { onMount } from "svelte";
  import Dashboard from "./routes/Dashboard.svelte";
  import Binder from "./routes/Binder.svelte";
  import Screwdriver from "./routes/Screwdriver.svelte";
  import MeshCore from "./routes/MeshCore.svelte";
  import Config from "./routes/Config.svelte";
  import Logs from "./routes/Logs.svelte";
  import GoblinTopBar from "./components/GoblinTopBar.svelte";

  // Simple hash-based routing
  let currentRoute = "dashboard";
  let isDark = true;

  function navigate(route) {
    currentRoute = route;
    window.location.hash = route;
  }

  function handleHashChange() {
    const hash = window.location.hash.slice(1);
    currentRoute = hash || "dashboard";
  }

  function toggleDarkMode() {
    isDark = !isDark;
    applyTheme();
    localStorage.setItem("goblin-theme", isDark ? "dark" : "light");
  }

  function applyTheme() {
    const html = document.documentElement;
    if (isDark) {
      html.classList.add("dark");
      html.classList.remove("light");
    } else {
      html.classList.add("light");
      html.classList.remove("dark");
    }
  }

  window.addEventListener("hashchange", handleHashChange);

  onMount(() => {
    handleHashChange();
    // Load theme preference
    const savedTheme = localStorage.getItem("goblin-theme");
    if (savedTheme === "light") {
      isDark = false;
    }
    applyTheme();
  });
</script>

<div class="mdk-app">
  <!-- Top Navigation Bar -->
  <GoblinTopBar {currentRoute} onNavigate={navigate} />

  <div class="mdk-shell">
    <!-- Content -->
    <main class="mdk-main">
      {#if currentRoute === "dashboard"}
        <Dashboard />
      {:else if currentRoute === "binder"}
        <Binder />
      {:else if currentRoute === "screwdriver"}
        <Screwdriver />
      {:else if currentRoute === "meshcore"}
        <MeshCore />
      {:else if currentRoute === "config"}
        <Config />
      {:else if currentRoute === "logs"}
        <Logs />
      {/if}
    </main>
  </div>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
      sans-serif;
  }

  .mdk-app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }

  .mdk-shell {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .mdk-main {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
  }
</style>
