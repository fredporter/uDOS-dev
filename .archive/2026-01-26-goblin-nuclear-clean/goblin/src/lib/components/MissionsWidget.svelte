<script lang="ts">
	import { onMount } from 'svelte';

	let { apiBase = 'http://localhost:8765' }: { apiBase?: string } = $props();

	interface Task {
		id: string;
		title: string;
		priority: string;
		status: string;
		provider?: string;
		estimated_cost?: number;
		attempts?: number;
	}

	interface Milestone {
		id: string;
		title: string;
		description: string;
		status: string;
		progress_threshold: number;
		is_current: boolean;
		progress_to_reach: number;
		celebration_message?: string;
	}

	interface Mission {
		id: string;
		title: string;
		status: string;
		progress: number;
		tasks: Task[];
		milestones?: Milestone[];
		checklist?: string[];
		actual_cost?: number;
		budget?: number;
	}

	let activeMissions: Mission[] = $state([]);
	let pendingTasks: Task[] = $state([]);
	let loading = $state(true);
	let error = $state('');
	let expanded = $state(false);

	const priorityIcons: Record<string, string> = {
		low: '🟢',
		normal: '🔵',
		high: '🟠',
		urgent: '🔴',
		critical: '⚡'
	};

	const statusIcons: Record<string, string> = {
		pending: '⏳',
		in_progress: '🔄',
		completed: '✅',
		failed: '❌',
		cancelled: '🚫',
		reached: '🎯',
		skipped: '⏭️'
	};

	const milestoneIcons: Record<string, string> = {
		pending: '○',
		in_progress: '◐',
		reached: '●',
		skipped: '◌'
	};

	async function fetchMissions() {
		try {
			const response = await fetch(`${apiBase}/api/missions/active`);
			if (!response.ok) throw new Error('Failed to fetch missions');
			
			const data = await response.json();
			activeMissions = data.missions || [];
			pendingTasks = data.pending_tasks || [];
			
			// Fetch milestones for each mission
			for (const mission of activeMissions) {
				try {
					const msResponse = await fetch(`${apiBase}/api/missions/${mission.id}/milestones`);
					if (msResponse.ok) {
						const msData = await msResponse.json();
						mission.milestones = msData.milestones || [];
					}
				} catch {
					// Milestone fetch failed - continue without milestones
				}
			}
			
			error = '';
		} catch (e) {
			// Missions API might not exist yet - fail silently
			error = '';
			activeMissions = [];
			pendingTasks = [];
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		fetchMissions();
		const interval = setInterval(fetchMissions, 15000);
		return () => clearInterval(interval);
	});

	function getProgressColor(percent: number): string {
		if (percent >= 100) return 'bg-green-500';
		if (percent >= 50) return 'bg-blue-500';
		return 'bg-gray-500';
	}
</script>

<div class="missions-widget rounded-lg border border-gray-700 bg-gray-900 p-3 text-sm">
	<!-- Header -->
	<button 
		class="flex w-full items-center justify-between"
		onclick={() => expanded = !expanded}
	>
		<div class="flex items-center gap-2">
			<span class="text-lg">🎯</span>
			<span class="font-medium text-gray-200">Missions</span>
		</div>
		<div class="flex items-center gap-3">
			{#if activeMissions.length > 0 || pendingTasks.length > 0}
				<span class="text-blue-400">{activeMissions.length} active</span>
				{#if pendingTasks.length > 0}
					<span class="text-gray-500">|</span>
					<span class="text-yellow-400">{pendingTasks.length} pending</span>
				{/if}
			{:else}
				<span class="text-gray-500">No active missions</span>
			{/if}
			<span class="text-gray-500">{expanded ? '▼' : '▶'}</span>
		</div>
	</button>

	{#if loading}
		<div class="mt-2 text-center text-gray-500">Loading...</div>
	{:else if error}
		<div class="mt-2 text-center text-red-400">⚠️ {error}</div>
	{:else if expanded}
		<div class="mt-3 space-y-3">
			<!-- Active Missions -->
			{#if activeMissions.length > 0}
				<div class="space-y-2">
					<div class="text-xs font-medium text-gray-400">Active Missions</div>
					{#each activeMissions as mission}
						<div class="rounded bg-gray-800 p-2">
							<div class="flex items-center justify-between">
								<span class="font-medium text-gray-200">
									{statusIcons[mission.status] || '❓'} {mission.title}
								</span>
								<span class="text-xs text-gray-400">
									{mission.progress}%
								</span>
							</div>
							<!-- Progress Bar -->
							<div class="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-gray-700">
								<div 
									class={`h-full ${getProgressColor(mission.progress)}`}
									style={`width: ${Math.min(mission.progress, 100)}%`}
								></div>
							</div>
							<!-- Milestones/Waypoints -->
							{#if mission.milestones && mission.milestones.length > 0}
								<div class="mt-2 flex items-center gap-1">
									{#each mission.milestones as milestone, idx}
										<div 
											class="group relative"
											title={milestone.title}
										>
											<span class={`text-xs ${milestone.status === 'reached' ? 'text-green-400' : milestone.is_current ? 'text-yellow-400' : 'text-gray-500'}`}>
												{milestoneIcons[milestone.status] || '○'}
											</span>
											{#if idx < mission.milestones.length - 1}
												<span class={`text-xs ${milestone.status === 'reached' ? 'text-green-400' : 'text-gray-600'}`}>──</span>
											{/if}
											<!-- Tooltip -->
											<div class="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1 hidden -translate-x-1/2 whitespace-nowrap rounded bg-black px-2 py-1 text-xs text-white group-hover:block">
												{milestone.title}
												{#if milestone.is_current}
													<span class="text-yellow-400"> (current)</span>
												{/if}
											</div>
										</div>
									{/each}
								</div>
								<!-- Current milestone label -->
								{#each mission.milestones as milestone}
									{#if milestone.is_current}
										<div class="mt-1 text-xs text-yellow-400">
											🎯 Next: {milestone.title}
										</div>
									{/if}
								{/each}
							{/if}
							<!-- Tasks preview -->
							{#if mission.tasks && mission.tasks.length > 0}
								<div class="mt-2 space-y-1">
									{#each mission.tasks.slice(0, 3) as task}
										<div class="flex items-center gap-2 text-xs">
											<span>{priorityIcons[task.priority] || '⚪'}</span>
											<span class="text-gray-400">{task.title}</span>
											<span class="ml-auto text-gray-500">{statusIcons[task.status] || ''}</span>
										</div>
									{/each}
									{#if mission.tasks.length > 3}
										<div class="text-xs text-gray-500">
											+{mission.tasks.length - 3} more tasks
										</div>
									{/if}
								</div>
							{/if}
							<!-- Budget -->
							{#if mission.budget}
								<div class="mt-1 flex justify-between text-xs text-gray-500">
									<span>Budget: ${mission.budget.toFixed(2)}</span>
									<span>Spent: ${(mission.actual_cost || 0).toFixed(2)}</span>
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}

			<!-- Pending Tasks (not in missions) -->
			{#if pendingTasks.length > 0}
				<div class="space-y-2">
					<div class="text-xs font-medium text-gray-400">Pending Tasks</div>
					{#each pendingTasks.slice(0, 5) as task}
						<div class="flex items-center justify-between rounded bg-gray-800 p-2">
							<div class="flex items-center gap-2">
								<span>{priorityIcons[task.priority] || '⚪'}</span>
								<span class="text-gray-200">{task.title}</span>
							</div>
							{#if task.provider}
								<span class="rounded bg-gray-700 px-2 py-0.5 text-xs text-gray-400">
									{task.provider}
								</span>
							{/if}
						</div>
					{/each}
					{#if pendingTasks.length > 5}
						<div class="text-center text-xs text-gray-500">
							+{pendingTasks.length - 5} more tasks
						</div>
					{/if}
				</div>
			{/if}

			<!-- Empty State -->
			{#if activeMissions.length === 0 && pendingTasks.length === 0}
				<div class="rounded bg-gray-800 p-3 text-center text-gray-500">
					<div class="text-2xl">🎯</div>
					<div class="mt-1 text-xs">No active missions</div>
					<div class="text-xs text-gray-600">Use MISSION NEW to create one</div>
				</div>
			{/if}

			<!-- Refresh Button -->
			<button 
				class="w-full rounded bg-gray-700 py-1 text-xs text-gray-300 hover:bg-gray-600"
				onclick={fetchMissions}
			>
				🔄 Refresh
			</button>
		</div>
	{/if}
</div>

<style>
	.missions-widget {
		min-width: 250px;
	}
</style>
