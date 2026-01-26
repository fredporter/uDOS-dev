<script lang="ts">
  /**
   * ToastContainer - Uses svelte-sonner for toast notifications
   * Import Toaster component from svelte-sonner in your root layout instead
   */
  import { Toaster } from "svelte-sonner";

  // svelte-sonner ships Svelte 4 component typing; cast loosely for Svelte 5 markup
  const ToastHost: any = Toaster;
</script>

<!-- Svelte Sonner Toast Container -->
<ToastHost position="top-right" richColors />
