<script lang="ts">
  import { toastStore } from "$lib/stores/toastStore";
</script>

<div class="p-8 space-y-4">
  <h1 class="text-3xl font-bold mb-6">Toast Notification Test</h1>

  <div class="grid grid-cols-2 gap-4 max-w-2xl">
    <button
      class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
      onclick={() =>
        toastStore.success("Success! Operation completed successfully.")}
    >
      Show Success Toast
    </button>

    <button
      class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
      onclick={() => toastStore.error("Error! Something went wrong.")}
    >
      Show Error Toast
    </button>

    <button
      class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      onclick={() => toastStore.info("Info: Here is some useful information.")}
    >
      Show Info Toast
    </button>

    <button
      class="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600"
      onclick={() => toastStore.warning("Warning! Please be careful.")}
    >
      Show Warning Toast
    </button>

    <button
      class="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
      onclick={() => {
        toastStore.info("Toast 1");
        setTimeout(() => toastStore.success("Toast 2"), 500);
        setTimeout(() => toastStore.warning("Toast 3"), 1000);
      }}
    >
      Show Multiple Toasts
    </button>

    <button
      class="px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600"
      onclick={() =>
        toastStore.info("This toast will stay for 10 seconds", 10000)}
    >
      Long Duration Toast (10s)
    </button>

    <button
      class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
      onclick={() => toastStore.dismiss()}
    >
      Clear All Toasts
    </button>
  </div>

  <div class="mt-8">
    <h2 class="text-xl font-bold mb-2">Instructions</h2>
    <ul class="list-disc list-inside space-y-1">
      <li>Click buttons to trigger different toast types</li>
      <li>Toasts auto-dismiss after 3 seconds (default)</li>
      <li>Click the X button on any toast to dismiss it manually</li>
      <li>Multiple toasts stack vertically in the top-right corner</li>
    </ul>
  </div>
</div>
