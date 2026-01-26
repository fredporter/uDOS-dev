<script lang="ts">
	import { onMount } from 'svelte';

	let { apiBase = 'http://localhost:8765' }: { apiBase?: string } = $props();

	interface QuotaSummary {
		cost_today: string;
		cost_this_month: string;
		requests_today: number;
		active_providers: number;
		queue_size: number;
		warnings: string[];
	}

	interface ProviderStatus {
		provider: string;
		status: string;
		daily: {
			requests: number;
			limit: number;
			cost: number;
			budget: number;
			usage_percent: number;
		};
	}

	let summary: QuotaSummary | null = $state(null);
	let providers: Record<string, ProviderStatus> = $state({});
	let loading = $state(true);
	let error = $state('');
	let expanded = $state(false);

	const statusIcons: Record<string, string> = {
		ok: '✅',
		warning: '🟡',
		critical: '🔴',
		exceeded: '⛔',
		rate_limited: '⏳'
	};

	async function fetchQuotas() {
		try {
			const response = await fetch(`${apiBase}/api/quota/status`);
			if (!response.ok) throw new Error('Failed to fetch quotas');
			
			const data = await response.json();
			summary = data.summary;
			providers = data.all_providers?.providers || {};
			error = '';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Unknown error';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		fetchQuotas();
		// Refresh every 30 seconds
		const interval = setInterval(fetchQuotas, 30000);
		return () => clearInterval(interval);
	});

	function getProgressColor(percent: number): string {
		if (percent >= 95) return 'bg-red-500';
		if (percent >= 80) return 'bg-yellow-500';
		return 'bg-green-500';
	}
</script>

<div class="quota-widget rounded-lg border border-gray-700 bg-gray-900 p-3 text-sm">
	<!-- Header -->
	<button 
		class="flex w-full items-center justify-between"
		onclick={() => expanded = !expanded}
	>
		<div class="flex items-center gap-2">
			<span class="text-lg">📊</span>
			<span class="font-medium text-gray-200">API Quotas</span>
		</div>
		<div class="flex items-center gap-3">
			{#if summary}
				<span class="text-green-400">{summary.cost_today}</span>
				<span class="text-gray-500">|</span>
				<span class="text-gray-400">{summary.requests_today} req</span>
			{/if}
			<span class="text-gray-500">{expanded ? '▼' : '▶'}</span>
		</div>
	</button>

	{#if loading}
		<div class="mt-2 text-center text-gray-500">Loading...</div>
	{:else if error}
		<div class="mt-2 text-center text-red-400">⚠️ {error}</div>
	{:else if expanded && summary}
		<!-- Expanded View -->
		<div class="mt-3 space-y-3">
			<!-- Summary Cards -->
			<div class="grid grid-cols-2 gap-2 text-xs">
				<div class="rounded bg-gray-800 p-2">
					<div class="text-gray-500">Today</div>
					<div class="text-lg font-bold text-green-400">{summary.cost_today}</div>
				</div>
				<div class="rounded bg-gray-800 p-2">
					<div class="text-gray-500">This Month</div>
					<div class="text-lg font-bold text-blue-400">{summary.cost_this_month}</div>
				</div>
			</div>

			<!-- Warnings -->
			{#if summary.warnings && summary.warnings.length > 0}
				<div class="rounded border border-yellow-600 bg-yellow-900/30 p-2">
					{#each summary.warnings as warning}
						<div class="text-xs text-yellow-300">{warning}</div>
					{/each}
				</div>
			{/if}

			<!-- Provider List -->
			<div class="space-y-2">
				<div class="text-xs font-medium text-gray-400">Providers</div>
				{#each Object.entries(providers) as [name, provider]}
					<div class="rounded bg-gray-800 p-2">
						<div class="flex items-center justify-between">
							<span class="font-medium text-gray-200">
								{statusIcons[provider.status] || '❓'} {name}
							</span>
							<span class="text-xs text-gray-400">
								${provider.daily?.cost?.toFixed(2) || '0.00'} / ${provider.daily?.budget?.toFixed(2) || '0.00'}
							</span>
						</div>
						<!-- Progress Bar -->
						<div class="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-gray-700">
							<div 
								class={`h-full ${getProgressColor(provider.daily?.usage_percent || 0)}`}
								style={`width: ${Math.min(provider.daily?.usage_percent || 0, 100)}%`}
							></div>
						</div>
						<div class="mt-1 flex justify-between text-xs text-gray-500">
							<span>{provider.daily?.requests || 0} / {provider.daily?.limit || 0} requests</span>
							<span>{(provider.daily?.usage_percent || 0).toFixed(0)}%</span>
						</div>
					</div>
				{/each}
			</div>

			<!-- Queue Status -->
			{#if summary.queue_size > 0}
				<div class="rounded bg-gray-800 p-2">
					<div class="flex items-center justify-between">
						<span class="text-gray-400">📋 Queue</span>
						<span class="font-medium text-yellow-400">{summary.queue_size} pending</span>
					</div>
				</div>
			{/if}

			<!-- Refresh Button -->
			<button 
				class="w-full rounded bg-gray-700 py-1 text-xs text-gray-300 hover:bg-gray-600"
				onclick={fetchQuotas}
			>
				🔄 Refresh
			</button>
		</div>
	{/if}
</div>

<style>
	.quota-widget {
		min-width: 250px;
	}
</style>
