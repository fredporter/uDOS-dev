<script lang="ts">
  import { onMount } from 'svelte';
  import { fly, fade } from 'svelte/transition';
  import type { NotificationData } from '$lib/stores/notificationStore';

  export let notification: NotificationData;
  export let onDismiss: (id: number) => void;

  let progress = 100;
  let progressInterval: number;
  let isPaused = false;

  const icons = {
    info: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>`,
    success: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>`,
    warning: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>`,
    error: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>`,
  };

  const typeClasses = {
    info: 'bg-blue-50 border-blue-200 dark:bg-blue-950 dark:border-blue-800',
    success: 'bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800',
    warning: 'bg-yellow-50 border-yellow-200 dark:bg-yellow-950 dark:border-yellow-800',
    error: 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800',
  };

  const iconColorClasses = {
    info: 'text-blue-600 dark:text-blue-400',
    success: 'text-green-600 dark:text-green-400',
    warning: 'text-yellow-600 dark:text-yellow-400',
    error: 'text-red-600 dark:text-red-400',
  };

  const textColorClasses = {
    info: 'text-blue-900 dark:text-blue-100',
    success: 'text-green-900 dark:text-green-100',
    warning: 'text-yellow-900 dark:text-yellow-100',
    error: 'text-red-900 dark:text-red-100',
  };

  const progressColorClasses = {
    info: 'bg-blue-500 dark:bg-blue-400',
    success: 'bg-green-500 dark:bg-green-400',
    warning: 'bg-yellow-500 dark:bg-yellow-400',
    error: 'bg-red-500 dark:bg-red-400',
  };

  onMount(() => {
    if (notification.duration && notification.duration > 0) {
      const interval = 50; // Update every 50ms
      const decrement = (interval / notification.duration) * 100;

      progressInterval = window.setInterval(() => {
        if (!isPaused) {
          progress -= decrement;
          if (progress <= 0) {
            clearInterval(progressInterval);
            onDismiss(notification.id);
          }
        }
      }, interval);

      return () => clearInterval(progressInterval);
    }
  });

  function handleMouseEnter() {
    isPaused = true;
  }

  function handleMouseLeave() {
    isPaused = false;
  }

  function handleDismiss() {
    clearInterval(progressInterval);
    onDismiss(notification.id);
  }

  function handleAction() {
    if (notification.action) {
      notification.action.callback();
      handleDismiss();
    }
  }
</script>

<div
  class="relative w-full max-w-sm overflow-hidden rounded-lg border shadow-lg {typeClasses[notification.type]}"
  in:fly={{ x: 300, duration: 300 }}
  out:fade={{ duration: 200 }}
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  role="alert"
>
  <!-- Progress bar -->
  {#if notification.duration && notification.duration > 0}
    <div class="absolute bottom-0 left-0 h-1 w-full bg-gray-200 dark:bg-gray-700">
      <div
        class="h-full {progressColorClasses[notification.type]} transition-all duration-100 ease-linear"
        style="width: {progress}%"
      />
    </div>
  {/if}

  <div class="p-4">
    <div class="flex items-start gap-3">
      <!-- Icon -->
      <div class="flex-shrink-0 {iconColorClasses[notification.type]}">
        {@html icons[notification.type]}
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <h4 class="text-sm font-semibold {textColorClasses[notification.type]}">
          {notification.title}
        </h4>
        {#if notification.message}
          <p class="mt-1 text-sm {textColorClasses[notification.type]} opacity-90">
            {notification.message}
          </p>
        {/if}

        <!-- Action button -->
        {#if notification.action}
          <button
            on:click={handleAction}
            class="mt-2 text-xs font-medium {textColorClasses[notification.type]} hover:underline"
          >
            {notification.action.label}
          </button>
        {/if}
      </div>

      <!-- Dismiss button -->
      {#if notification.dismissible !== false}
        <button
          on:click={handleDismiss}
          class="flex-shrink-0 rounded-md p-1 {textColorClasses[notification.type]} opacity-60 hover:opacity-100 transition-opacity"
          aria-label="Dismiss"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      {/if}
    </div>
  </div>
</div>
