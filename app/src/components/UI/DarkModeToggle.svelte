<script lang="ts">
  import { createEventDispatcher } from "svelte";

  export let isDark: boolean = true;

  const dispatch = createEventDispatcher<{ toggle: void }>();

  function handleToggle() {
    dispatch("toggle");
  }
</script>

<button
  on:click={handleToggle}
  title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
  class="p-2 rounded-lg transition-colors duration-200 hover:bg-slate-100 dark:hover:bg-slate-800"
  aria-label="Toggle dark mode"
>
  {#if isDark}
    <!-- Moon icon for dark mode (click to switch to light) -->
    <svg
      class="w-5 h-5 text-slate-600 dark:text-yellow-400"
      fill="currentColor"
      viewBox="0 0 20 20"
    >
      <path
        d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"
      />
    </svg>
  {:else}
    <!-- Sun icon for light mode (click to switch to dark) -->
    <svg
      class="w-5 h-5 text-slate-400 dark:text-slate-500"
      fill="currentColor"
      viewBox="0 0 20 20"
    >
      <path
        fill-rule="evenodd"
        d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4.293 2.293a1 1 0 011.414 0l.707.707a1 1 0 11-1.414 1.414l-.707-.707a1 1 0 010-1.414zm2.828 2.829a1 1 0 011.415 0l.707.707a1 1 0 11-1.414 1.414l-.707-.707a1 1 0 010-1.414zm2.828 2.828a1 1 0 011.415 0l.707.707a1 1 0 11-1.414 1.414l-.707-.707a1 1 0 010-1.414zM10 11a1 1 0 110 2h1a1 1 0 110-2h-1zm4.293-1.293a1 1 0 011.414 0l.707.707a1 1 0 11-1.414 1.414l-.707-.707a1 1 0 010-1.414zm2.828 2.829a1 1 0 011.415 0l.707.707a1 1 0 11-1.414 1.414l-.707-.707a1 1 0 010-1.414zM10 15a1 1 0 110 2v1a1 1 0 110-2v-1zm-4.293 2.293a1 1 0 011.414 0l.707.707a1 1 0 11-1.414 1.414l-.707-.707a1 1 0 010-1.414zm-2.828-2.829a1 1 0 011.415 0l.707.707a1 1 0 11-1.414 1.414l-.707-.707a1 1 0 010-1.414zM5.707 5.707a1 1 0 010 1.414L5 7.828a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zm-2.828 2.829a1 1 0 010 1.415l-.707.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM5.707 15.707a1 1 0 010-1.414l.707-.707a1 1 0 111.414 1.414l-.707.707a1 1 0 01-1.414 0z"
        clip-rule="evenodd"
      />
    </svg>
  {/if}
</button>

<style lang="postcss">
  button {
    transition: all 200ms ease-out;
  }

  button:active {
    transform: scale(0.95);
  }
</style>
