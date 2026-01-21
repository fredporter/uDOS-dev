<script lang="ts">
  import { onMount, onDestroy, createEventDispatcher } from "svelte";
  import { fade } from "svelte/transition";
  import type { Toast } from "./types";
  import { Info, Check, Warning, Close } from "../../icons";

  export let toast: Toast;

  const dispatch = createEventDispatcher();

  let isVisible = true;
  let timeoutId: ReturnType<typeof setTimeout>;

  onMount(() => {
    if (toast.duration && toast.duration > 0) {
      timeoutId = setTimeout(() => {
        isVisible = false;
        dispatch("dismiss", { id: toast.id });
      }, toast.duration);
    }
  });

  onDestroy(() => {
    if (timeoutId) clearTimeout(timeoutId);
  });

  function close() {
    isVisible = false;
    dispatch("dismiss", { id: toast.id });
  }

  const typeStyles = {
    info: "bg-blue-50 dark:bg-blue-900 border-blue-200 dark:border-blue-700 text-blue-900 dark:text-blue-100",
    success:
      "bg-green-50 dark:bg-green-900 border-green-200 dark:border-green-700 text-green-900 dark:text-green-100",
    warning:
      "bg-yellow-50 dark:bg-yellow-900 border-yellow-200 dark:border-yellow-700 text-yellow-900 dark:text-yellow-100",
    error:
      "bg-red-50 dark:bg-red-900 border-red-200 dark:border-red-700 text-red-900 dark:text-red-100",
  };

  const iconComponents: Record<string, any> = {
    info: Info,
    success: Check,
    warning: Warning,
    error: Close,
  };
</script>

{#if isVisible}
  <div
    class="w-96 animate-slide-in {typeStyles[
      toast.type
    ]} border rounded-lg shadow-lg px-6 py-5 gap-4 flex items-start"
    role="alert"
    transition:fade
  >
    <span class="h-5 w-5 shrink-0">
      <svelte:component this={iconComponents[toast.type]} />
    </span>
    <div class="flex-1 min-w-0">
      {#if toast.title}
        <h3 class="font-semibold mb-1">{toast.title}</h3>
      {/if}
      <p class="text-sm">{toast.message}</p>
    </div>
    <button
      on:click={close}
      class="shrink-0 ml-2 opacity-70 hover:opacity-100 transition-opacity"
      aria-label="Close notification"
    >
      <Close />
    </button>
  </div>
{/if}

<style lang="postcss">
  @keyframes slideIn {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(400px);
      opacity: 0;
    }
  }

  :global(.animate-slide-in) {
    animation: slideIn 0.3s ease-out;
  }

  div {
    @apply transition-all duration-300;
  }
</style>
