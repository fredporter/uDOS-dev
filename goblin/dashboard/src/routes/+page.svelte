<script>
	import { onMount } from 'svelte';

	let serverInfo = null;
	let modes = [];

	onMount(async () => {
		// Fetch server info
		const res = await fetch('/api/v0/modes/');
		const data = await res.json();
		modes = data.modes || [];

		// Fetch root info
		const rootRes = await fetch('/');
		serverInfo = await rootRes.json();
	});
</script>

<div class="max-w-7xl mx-auto px-4 py-8">
	<div class="space-y-8">
		<!-- Hero -->
		<div class="text-center space-y-4">
			<h2 class="text-4xl font-bold text-goblin-accent">🧪 MODE Playground</h2>
			<p class="text-xl text-gray-400">
				Experimental rendering modes for uDOS
			</p>
			<div class="flex justify-center space-x-4 text-sm">
				<span class="px-3 py-1 bg-goblin-surface rounded border border-goblin-border">
					Teletext Patterns
				</span>
				<span class="px-3 py-1 bg-goblin-surface rounded border border-goblin-border">
					Terminal Emulation
				</span>
				<span class="px-3 py-1 bg-goblin-surface rounded border border-goblin-border">
					ANSI Art
				</span>
			</div>
		</div>

		<!-- Server Status -->
		{#if serverInfo}
			<div class="bg-goblin-surface rounded-lg border border-goblin-border p-6">
				<h3 class="text-lg font-semibold mb-4 text-goblin-accent">Server Status</h3>
				<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
					<div>
						<div class="text-gray-500 text-sm">Version</div>
						<div class="font-mono">{serverInfo.version}</div>
					</div>
					<div>
						<div class="text-gray-500 text-sm">Port</div>
						<div class="font-mono">{serverInfo.port}</div>
					</div>
					<div>
						<div class="text-gray-500 text-sm">Status</div>
						<div class="text-goblin-success">● {serverInfo.status}</div>
					</div>
					<div>
						<div class="text-gray-500 text-sm">MODEs</div>
						<div class="font-mono">{serverInfo.modes?.length || 0}</div>
					</div>
				</div>
			</div>
		{/if}

		<!-- Available MODEs -->
		<div class="bg-goblin-surface rounded-lg border border-goblin-border p-6">
			<h3 class="text-lg font-semibold mb-4 text-goblin-accent">Available MODEs</h3>
			<div class="grid gap-4">
				{#each modes as mode}
					<div class="p-4 bg-goblin-bg rounded border border-goblin-border hover:border-goblin-accent transition-colors">
						<h4 class="font-semibold text-lg capitalize mb-2">{mode.name}</h4>
						<p class="text-gray-400 text-sm mb-3">{mode.description}</p>
						<div class="flex flex-wrap gap-2">
							{#each mode.endpoints as endpoint}
								<code class="text-xs px-2 py-1 bg-goblin-surface rounded font-mono text-goblin-accent">
									{endpoint}
								</code>
							{/each}
						</div>
					</div>
				{/each}
			</div>
		</div>

		<!-- Quick Start -->
		<div class="bg-goblin-surface rounded-lg border border-goblin-border p-6">
			<h3 class="text-lg font-semibold mb-4 text-goblin-accent">Quick Start</h3>
			<div class="space-y-3 text-sm">
				<p class="text-gray-400">Navigate using the top menu to explore MODEs:</p>
				<ul class="list-disc list-inside space-y-2 text-gray-400">
					<li><span class="text-goblin-accent">Teletext</span> - Test retro patterns and ANSI art</li>
					<li><span class="text-goblin-accent">Terminal</span> - Experiment with escape codes and color schemes</li>
				</ul>
			</div>
		</div>
	</div>
</div>
