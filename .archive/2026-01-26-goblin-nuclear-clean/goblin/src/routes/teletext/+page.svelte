<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";

  onMount(() => {
    goto("/teledesk", { replaceState: true });
  });
</script>

<div class="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center">
  <p class="text-sm text-slate-400">Redirecting to Teledesk…</p>
</div>
