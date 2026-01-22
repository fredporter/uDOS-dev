<script lang="ts">
  import Header from "./components/Header.svelte";
  import StatusGrid from "./components/StatusGrid.svelte";
  import WarningBanner from "./components/WarningBanner.svelte";
  import Features from "./components/Features.svelte";
  import QuickLinks from "./components/QuickLinks.svelte";
  import Footer from "./components/Footer.svelte";
</script>

<main>
  <div class="container">
    <Header />
    <StatusGrid />
    <WarningBanner />
    <Features />
    <QuickLinks />
    <Footer />
  </div>
</main>

<style>
  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
      sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    margin: 0;
    padding: 0;
  }

  main {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 20px;
  }

  .container {
    max-width: 900px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    padding: 50px;
  }
</style>
