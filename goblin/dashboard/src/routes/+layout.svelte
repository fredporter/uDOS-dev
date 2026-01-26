<script>
	import { onMount } from 'svelte';
	import '../app.css';

	let currentPath = '/';

	onMount(() => {
		currentPath = window.location.pathname;
	});

	const navItems = [
		{ path: '/', label: 'Home', icon: '🏠' },
		{ path: '/teletext', label: 'Teletext', icon: '📺' },
		{ path: '/terminal', label: 'Terminal', icon: '💻' }
	];
</script>

<div class="min-h-screen flex flex-col bg-goblin-bg text-goblin-text">
	<!-- Top Navigation -->
	<nav class="bg-goblin-surface border-b border-goblin-border">
		<div class="max-w-7xl mx-auto px-4">
			<div class="flex items-center justify-between h-16">
				<div class="flex items-center space-x-8">
					<h1 class="text-xl font-bold text-goblin-accent">
						🧪 Goblin MODE Playground
					</h1>
					<div class="flex space-x-1">
						{#each navItems as item}
							<a
								href={item.path}
								class="px-4 py-2 rounded transition-colors {currentPath === item.path
									? 'bg-goblin-accent text-white'
									: 'text-goblin-text hover:bg-goblin-border'}"
							>
								<span class="mr-2">{item.icon}</span>
								{item.label}
							</a>
						{/each}
					</div>
				</div>
				<div class="text-sm text-gray-500">
					<span class="px-2 py-1 bg-goblin-border rounded">v0.2.0.0</span>
				</div>
			</div>
		</div>
	</nav>

	<!-- Main Content -->
	<main class="flex-1 overflow-auto">
		<slot />
	</main>

	<!-- Bottom Bar -->
	<footer class="bg-goblin-surface border-t border-goblin-border">
		<div class="max-w-7xl mx-auto px-4 py-3">
			<div class="flex items-center justify-between text-sm">
				<div class="flex items-center space-x-4">
					<span class="text-gray-500">Server:</span>
					<span class="text-goblin-success">● localhost:8767</span>
				</div>
				<div class="flex items-center space-x-4 text-gray-500">
					<span>Experimental MODEs</span>
					<span>•</span>
					<span>Local-only</span>
					<span>•</span>
					<span>uDOS Alpha</span>
				</div>
				<div class="text-gray-500">
					<span>2026-01-26</span>
				</div>
			</div>
		</div>
	</footer>
</div>
