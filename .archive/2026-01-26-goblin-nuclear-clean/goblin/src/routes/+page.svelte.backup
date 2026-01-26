<script lang="ts">
	import { onMount } from 'svelte';
	import { invoke } from '@tauri-apps/api/core';
	import { listen } from '@tauri-apps/api/event';
	import { goto } from '$app/navigation';

	onMount(() => {
		let unlisten: (() => void) | null = null;

		(async () => {
			// Listen for file-open events from Finder - redirect to Typo editor
			unlisten = await listen('file-open', (event) => {
				goto(`/editor?file=${encodeURIComponent(event.payload as string)}`);
			});

			// Check if app was launched with a file - redirect to Typo editor
			const filePath = await invoke<string | null>('get_file_path_from_args');
			if (filePath) {
				goto(`/editor?file=${encodeURIComponent(filePath)}`);
			} else {
				// No file - just go to editor (Typo loads its own content)
				goto('/editor');
			}
		})();

		return () => {
			unlisten?.();
		};
	});
</script>

<div class="min-h-screen bg-udos-bg text-udos-text flex items-center justify-center">
	<div class="text-center">
		<h1 class="text-4xl font-bold mb-4">Loading Typo Editor...</h1>
		<p class="text-udos-text/60">Redirecting...</p>
	</div>
</div>
