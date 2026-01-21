<script lang="ts">
  import { toasts } from "./store";
  import Toast from "./Toast.svelte";
  import type { Toast as ToastType } from "./types";

  // Subscribe to toasts store
  let toastList: ToastType[] = [];
  const unsubscribe = toasts.subscribe((value) => {
    toastList = value;
  });

  // Cleanup subscription on unmount
  import { onDestroy } from "svelte";
  onDestroy(unsubscribe);
</script>

<!-- Toast Container -->
<div
  class="fixed top-4 right-4 p-2 flex flex-col gap-3 pointer-events-none max-h-[calc(100vh-8rem)] overflow-y-auto z-[9999]"
>
  {#each toastList as toast (toast.id)}
    <div class="pointer-events-auto">
      <Toast {toast} on:dismiss={() => toasts.remove(Number(toast.id))} />
    </div>
  {/each}
</div>

<style lang="postcss">
  div {
    @apply transition-all duration-200;
  }
</style>
