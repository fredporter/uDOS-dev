<script>
	import { onMount } from 'svelte';

	let schemes = [];
	let selectedScheme = 'default';
	let inputText = 'Sample terminal text';
	let fg = 'white';
	let bg = null;
	let style = null;
	let renderedOutput = null;
	let testResults = null;

	const colors = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'];
	const styles = [
		'bold',
		'dim',
		'italic',
		'underline',
		'blink',
		'reverse',
		'hidden',
		'strikethrough'
	];

	onMount(async () => {
		await loadSchemes();
		await renderText();
	});

	async function loadSchemes() {
		const res = await fetch('/api/v0/modes/terminal/schemes');
		const data = await res.json();
		schemes = data.schemes || [];
	}

	async function renderText() {
		const params = new URLSearchParams({
			text: inputText,
			fg: fg,
			...(bg && { bg }),
			...(style && { style })
		});
		const res = await fetch(`/api/v0/modes/terminal/render?${params}`);
		renderedOutput = await res.json();
	}

	async function applyScheme() {
		const res = await fetch(
			`/api/v0/modes/terminal/scheme?text=${encodeURIComponent(inputText)}&scheme=${selectedScheme}`
		);
		renderedOutput = await res.json();
	}

	async function runTests() {
		const res = await fetch('/api/v0/modes/terminal/test');
		testResults = await res.json();
	}
</script>

<div class="max-w-7xl mx-auto px-4 py-8">
	<div class="space-y-6">
		<!-- Header -->
		<div>
			<h2 class="text-3xl font-bold text-goblin-accent mb-2">💻 Terminal MODE</h2>
			<p class="text-gray-400">ANSI escape codes and terminal emulation testing</p>
		</div>

		<!-- Text Input -->
		<div class="bg-goblin-surface rounded-lg border border-goblin-border p-6">
			<h3 class="text-lg font-semibold mb-4 text-goblin-accent">Input Text</h3>
			<input
				type="text"
				bind:value={inputText}
				placeholder="Enter text to render..."
				class="w-full bg-goblin-bg border border-goblin-border rounded px-4 py-2 text-goblin-text"
			/>
		</div>

		<!-- Manual Controls -->
		<div class="bg-goblin-surface rounded-lg border border-goblin-border p-6">
			<h3 class="text-lg font-semibold mb-4 text-goblin-accent">Manual Controls</h3>
			<div class="grid md:grid-cols-3 gap-4">
				<div>
					<label class="block text-sm text-gray-400 mb-2">Foreground Color</label>
					<select
						bind:value={fg}
						class="w-full bg-goblin-bg border border-goblin-border rounded px-3 py-2 text-goblin-text"
					>
						{#each colors as color}
							<option value={color}>{color}</option>
						{/each}
					</select>
				</div>
				<div>
					<label class="block text-sm text-gray-400 mb-2">Background Color</label>
					<select
						bind:value={bg}
						class="w-full bg-goblin-bg border border-goblin-border rounded px-3 py-2 text-goblin-text"
					>
						<option value={null}>None</option>
						{#each colors as color}
							<option value={color}>{color}</option>
						{/each}
					</select>
				</div>
				<div>
					<label class="block text-sm text-gray-400 mb-2">Style</label>
					<select
						bind:value={style}
						class="w-full bg-goblin-bg border border-goblin-border rounded px-3 py-2 text-goblin-text"
					>
						<option value={null}>None</option>
						{#each styles as s}
							<option value={s}>{s}</option>
						{/each}
					</select>
				</div>
			</div>
			<button
				on:click={renderText}
				class="mt-4 px-4 py-2 bg-goblin-accent text-white rounded hover:bg-opacity-80 transition-colors"
			>
				Render Text
			</button>
		</div>

		<!-- Scheme Controls -->
		<div class="bg-goblin-surface rounded-lg border border-goblin-border p-6">
			<h3 class="text-lg font-semibold mb-4 text-goblin-accent">Color Schemes</h3>
			<div class="flex items-end space-x-4">
				<div class="flex-1">
					<label class="block text-sm text-gray-400 mb-2">Scheme</label>
					<select
						bind:value={selectedScheme}
						class="w-full bg-goblin-bg border border-goblin-border rounded px-3 py-2 text-goblin-text"
					>
						{#each schemes as scheme}
							<option value={scheme.name}>{scheme.name}</option>
						{/each}
					</select>
				</div>
				<button
					on:click={applyScheme}
					class="px-4 py-2 bg-goblin-accent text-white rounded hover:bg-opacity-80 transition-colors"
				>
					Apply Scheme
				</button>
			</div>
		</div>

		<!-- Output -->
		{#if renderedOutput}
			<div class="bg-goblin-surface rounded-lg border border-goblin-border p-6">
				<h3 class="text-lg font-semibold mb-4 text-goblin-accent">Output</h3>
				<div class="terminal-output">
					{renderedOutput.ansi}
				</div>
				<div class="mt-4 text-sm text-gray-500">
					<div>Codes: {JSON.stringify(renderedOutput.codes)}</div>
					<div class="mt-1">
						FG: {renderedOutput.fg} | BG: {renderedOutput.bg || 'none'} | Style: {renderedOutput.style ||
							'none'}
					</div>
				</div>
			</div>
		{/if}

		<!-- Capability Tests -->
		<div class="bg-goblin-surface rounded-lg border border-goblin-border p-6">
			<h3 class="text-lg font-semibold mb-4 text-goblin-accent">Capability Tests</h3>
			<button
				on:click={runTests}
				class="px-4 py-2 bg-goblin-success text-white rounded hover:bg-opacity-80 transition-colors"
			>
				Run Tests
			</button>
			{#if testResults}
				<div class="mt-4 space-y-2 max-h-96 overflow-y-auto">
					{#each testResults.tests as test}
						<div class="p-2 bg-goblin-bg rounded border border-goblin-border">
							<div class="text-sm text-gray-400">{test.test}</div>
							<div class="terminal-output mt-1 text-xs">{test.ansi}</div>
						</div>
					{/each}
					<div class="text-sm text-gray-500 mt-2">Total tests: {testResults.total}</div>
				</div>
			{/if}
		</div>
	</div>
</div>
