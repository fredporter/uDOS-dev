<script lang="ts">
	import { invoke } from '@tauri-apps/api/core';
	
	interface TableCell {
		value: string;
		editable: boolean;
	}

	interface TableData {
		headers: string[];
		rows: TableCell[][];
	}

	let {
		data = $bindable<TableData>({ headers: [], rows: [] }),
		onCellChange = (rowIndex: number, colIndex: number, newValue: string) => {}
	} = $props();

	let editingCell = $state<{row: number, col: number} | null>(null);
	let editValue = $state("");

	const startEdit = (rowIndex: number, colIndex: number, currentValue: string) => {
		if (data.rows[rowIndex][colIndex].editable) {
			editingCell = { row: rowIndex, col: colIndex };
			editValue = currentValue;
		}
	};

	const saveEdit = async () => {
		if (editingCell) {
			const { row, col } = editingCell;
			data.rows[row][col].value = editValue;
			await onCellChange(row, col, editValue);
			editingCell = null;
		}
	};

	const cancelEdit = () => {
		editingCell = null;
		editValue = "";
	};

	const isEditing = (rowIndex: number, colIndex: number) => {
		return editingCell?.row === rowIndex && editingCell?.col === colIndex;
	};

	const handleKeydown = (e: KeyboardEvent) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			saveEdit();
		} else if (e.key === 'Escape') {
			e.preventDefault();
			cancelEdit();
		}
	};
</script>

<div class="overflow-auto rounded-lg border border-gray-300 dark:border-gray-700 bg-gray-200 dark:bg-gray-900">
	<table class="min-w-full divide-y divide-gray-300 dark:divide-gray-700">
		<thead class="bg-gray-100 dark:bg-gray-800">
			<tr>
				{#each data.headers as header, i}
					<th
						scope="col"
						class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-700 dark:text-gray-300"
					>
						{header}
					</th>
				{/each}
			</tr>
		</thead>
		<tbody class="divide-y divide-gray-300 dark:divide-gray-700 bg-white dark:bg-gray-900">
			{#each data.rows as row, rowIndex}
				<tr class="hover:bg-gray-900/50 transition-colors">
					{#each row as cell, colIndex}
						<td class="px-6 py-4 whitespace-nowrap text-sm">
							{#if isEditing(rowIndex, colIndex)}
								<input
									type="text"
									class="w-full bg-gray-800 border border-sky-500 rounded px-2 py-1 text-gray-50 focus:outline-none focus:ring-2 focus:ring-sky-500"
									bind:value={editValue}
									onkeydown={handleKeydown}
									onblur={saveEdit}
								/>
							{:else}
								{#if cell.editable}
									<button
										type="button"
										class="text-gray-200 cursor-pointer hover:text-sky-400 hover:underline"
										onclick={() => startEdit(rowIndex, colIndex, cell.value)}
									>
										{cell.value || '—'}
									</button>
								{:else}
									<div class="text-gray-200">{cell.value || '—'}</div>
								{/if}
							{/if}
						</td>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>

	{#if data.rows.length === 0}
		<div class="text-center py-12 text-gray-500">
			<p class="text-lg">No data available</p>
			<p class="text-sm mt-2">Load a markdown database file to display data</p>
		</div>
	{/if}
</div>

<style>
	/* Custom scrollbar for table */
	:global(.overflow-auto::-webkit-scrollbar) {
		width: 8px;
		height: 8px;
	}

	:global(.overflow-auto::-webkit-scrollbar-track) {
		background: rgb(17 24 39); /* gray-900 */
	}

	:global(.overflow-auto::-webkit-scrollbar-thumb) {
		background: rgb(75 85 99); /* gray-600 */
		border-radius: 4px;
	}

	:global(.overflow-auto::-webkit-scrollbar-thumb:hover) {
		background: rgb(107 114 128); /* gray-500 */
	}
</style>
