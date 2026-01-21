<script lang="ts">
	import type { Snippet } from 'svelte';
	import '../../app.css';
	import { page } from '$app/stores';

	let { children }: { children?: Snippet } = $props();
</script>

<!-- Desktop mode bypasses the main app shell - full screen System 7 experience -->
{#if children}{@render (children as any)()}{/if}
