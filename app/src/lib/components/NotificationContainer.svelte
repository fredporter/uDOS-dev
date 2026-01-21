<script lang="ts">
  import { notifications } from '$lib/stores/notificationStore';
  import EnhancedToast from './EnhancedToast.svelte';

  let activeNotifications: any[] = [];

  notifications.active.subscribe((toasts) => {
    activeNotifications = toasts;
  });

  function handleDismiss(id: number) {
    notifications.remove(id);
  }
</script>

<!-- Toast container - fixed position at top-right -->
<div
  class="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none"
  aria-live="polite"
  aria-atomic="true"
>
  {#each activeNotifications as notification (notification.id)}
    <div class="pointer-events-auto">
      <EnhancedToast {notification} onDismiss={handleDismiss} />
    </div>
  {/each}
</div>
