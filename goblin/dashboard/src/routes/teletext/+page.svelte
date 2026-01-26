<script>
	import { onMount } from 'svelte';

	let patterns = [];
	let selectedPattern = 'chevrons';
	let width = 80;
	let asciiOnly = false;
	let renderedFrame = null;
	let isAnimating = false;
	let animationFrames = [];
	let currentFrame = 0;

	onMount(async () => {
		await loadPatterns();
		await renderPattern();
	});

	async function loadPatterns() {
		const res = await fetch('/api/v0/modes/teletext/patterns');
		const data = await res.json();
		patterns = data.patterns || [];
	}

	async function renderPattern() {
		const res = await fetch(
			`/api/v0/modes/teletext/render?pattern=${selectedPattern}&width=${width}&ascii_only=${asciiOnly}`
		);
		renderedFrame = await res.json();
	}

	async function startAnimation() {
		isAnimating = true;
		const res = await fetch(
			`/api/v0/modes/teletext/animate?pattern=${selectedPattern}&frames=20&width=${width}`
		);
		const data = await res.json();
		animationFrames = data.animation || [];
		currentFrame = 0;

		// Animate loop
		const interval = setInterval(() => {
			if (!isAnimating) {
				clearInterval(interval);
				return;
			}
			currentFrame = (currentFrame + 1) % animationFrames.length;
		}, 100);
	}

	function stopAnimation() {
		isAnimating = false;
		animationFrames = [];
	}
</script>

<div class="max-w-7xl mx-auto px-4 py-8">
	<div class="space-y-6">
		<!-- Header -->
		<div>
			<h2 class="text-3xl font-bold text-goblin-accent mb-2">📺 Teletext MODE</h2>
			<p class="text-gray-400">Retro teletext patterns and ANSI art rendering</p>
		</div>

		<!-- Controls -->
		<div class="bg-goblin-surface rounded-lg border border-goblin-border p-6">
			<h3 class="text-lg font-semibold mb-4 text-goblin-accent">Controls</h3>
			<div class="grid md:grid-cols-3 gap-4">
				<div>
					<label class="block text-sm text-gray-400 mb-2">Pattern</label>
					<select
						bind:value={selectedPattern}
						on:change={renderPattern}
						class="w-full bg-goblin-bg border border-goblin-border rounded px-3 py-2 text-goblin-text"
					>
						{#each patterns as pattern}
							<option value={pattern.name}>{pattern.name}</option>
						{/each}
					</select>
				</div>
				<div>
					<label class="block text-sm text-gray-400 mb-2">Width</label>
					<input
						type="range"
						min="20"
						max="80"
						bind:value={width}
						on:change={renderPattern}
						class="w-full"
					/>
					<div class="text-sm text-gray-500 mt-1">{width} chars</div>
				</div>
				<div class="flex items-end">
					<label class="flex items-center space-x-2 cursor-pointer">
						<input
							type="checkbox"
							bind:checked={asciiOnly}
							on:change={renderPattern}
							class="form-checkbox"
						/>
						<span class="text-sm text-gray-400">ASCII Only</span>
					</label>
				</div>
			</div>
			<div class="mt-4 flex space-x-2">
				<button
					on:click={renderPattern}
					class="px-4 py-2 bg-goblin-accent text-white rounded hover:bg-opacity-80 transition-colors"
				>
					Render Frame
				</button>
				{#if !isAnimating}
					<button
						on:click={startAnimation}
						class="px-4 py-2 bg-goblin-success text-white rounded hover:bg-opacity-80 transition-colors"
					>
						Start Animation
					</button>
				{:else}
					<button
						on:click={stopAnimation}
						class="px-4 py-2 bg-goblin-error text-white rounded hover:bg-opacity-80 transition-colors"
					>
						Stop Animation
					</button>
				{/if}
			</div>
		</div>

		<!-- Pattern Info -->
		{#if renderedFrame && patterns.length > 0}
			{@const patternInfo = patterns.find((p) => p.name === selectedPattern)}
			<div class="bg-goblin-surface rounded-lg border border-goblin-border p-4">
				<div class="flex items-center justify-between">
					<div>
						<h4 class="font-semibold capitalize">{selectedPattern}</h4>
						<p class="text-sm text-gray-400">{patternInfo?.description}</p>
					</div>
					<div class="text-sm text-gray-500">
						{renderedFrame.width} × {renderedFrame.lines?.length || 0}
					</div>
				</div>
			</div>
		{/if}

		<!-- Display -->
		<div class="bg-goblin-surface rounded-lg border border-goblin-border p-6">
			<h3 class="text-lg font-semibold mb-4 text-goblin-accent">Output</h3>
			{#if isAnimating && animationFrames.length > 0}
				<div class="pattern-display">
					{animationFrames[currentFrame]}
				</div>
				<div class="mt-2 text-sm text-gray-500 text-center">
					Frame {currentFrame + 1} / {animationFrames.length}
				</div>
			{:else if renderedFrame && renderedFrame.raw}
				<div class="pattern-display">
					{renderedFrame.raw}
				</div>
			{:else}
				<div class="text-gray-500 text-center py-8">
					Select a pattern and click "Render Frame" to see output
				</div>
			{/if}
		</div>
	</div>
</div>
