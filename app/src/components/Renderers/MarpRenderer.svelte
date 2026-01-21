<script lang="ts">
  /**
   * MarpRenderer
   * Renders -marp.md files as presentation slides
   * Uses Marp for slide rendering
   */

  export let slides: any[] = [];

  let currentSlide = 0;

  function nextSlide() {
    if (currentSlide < slides.length - 1) currentSlide++;
  }

  function prevSlide() {
    if (currentSlide > 0) currentSlide--;
  }
</script>

<div class="marp-renderer">
  <div class="slide-container">
    <div class="slide">
      {@html slides[currentSlide]?.content || "<h1>Presentation</h1>"}
    </div>
  </div>

  <div class="controls">
    <button
      class="btn btn-icon"
      on:click={prevSlide}
      disabled={currentSlide === 0}
    >
      ← Previous
    </button>

    <div class="counter">
      {currentSlide + 1} / {slides.length || 1}
    </div>

    <button
      class="btn btn-icon"
      on:click={nextSlide}
      disabled={currentSlide === slides.length - 1}
    >
      Next →
    </button>
  </div>
</div>

<style lang="postcss">
  .marp-renderer {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100vh;
    background-color: #0f172a;
    color: #f3f4f6;
    overflow: hidden;
  }

  .slide-container {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem 2rem 8rem 2rem;
    background: linear-gradient(135deg, #0f172a, #1e293b);
    overflow-y: auto;
  }

  .slide {
    width: 100%;
    max-width: 1200px;
    aspect-ratio: 16 / 9;
    color: #0f172a;
    border-radius: 0.5rem;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
    overflow: auto;
  }

  .slide :global(h1) {
    margin: 0 0 1.5rem 0;
    font-size: 3rem;
    font-weight: 700;
  }

  .slide :global(h2) {
    margin: 1.5rem 0 1rem 0;
    font-size: 2rem;
    font-weight: 700;
  }

  .slide :global(p) {
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
  }

  .controls {
    position: fixed;
    bottom: 60px;
    left: 0;
    right: 0;
    padding: 1.25rem 1.5rem;
    background-color: #020617;
    border-top: 1px solid #1e293b;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
    z-index: 40;
  }

  .btn {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
    font-weight: 600;
    border: 2px solid #334155;
    border-radius: 0.5rem;
    cursor: pointer;
    background-color: #1e293b;
    color: #e5e7eb;
    transition: all 200ms ease-out;
  }

  .btn:hover:not(:disabled) {
    background-color: #2563eb;
    border-color: #2563eb;
    color: white;
    transform: translateY(-1px);
  }

  .btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .counter {
    color: #94a3b8;
    font-weight: 600;
    min-width: 100px;
    text-align: center;
    font-size: 0.95rem;
  }

  @media (max-width: 768px) {
    .slide-container {
      padding: 1rem 1rem 8rem 1rem;
    }

    .slide {
      padding: 1.5rem;
      font-size: 0.875rem;
    }

    .slide :global(h1) {
      font-size: 2rem;
    }

    .slide :global(h2) {
      font-size: 1.5rem;
    }
  }
</style>
