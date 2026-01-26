<script lang="ts">
	import * as svg from '$lib/components/svg';
	import printCss from '$lib/styles/print.css?raw';

	interface Props {
		content?: string;
		html?: string;
		currentFilePath?: string | null;
		onOpen?: () => void;
		onSaveAs?: () => void;
		onFormat?: () => void;
		onToggleView?: () => void;
		onToggleSidebar?: () => void;
		sidebarOpen?: boolean;
		viewMode?: boolean;
		showSidebarToggle?: boolean;
		showFileActions?: boolean;
		showFormatActions?: boolean;
		showViewToggle?: boolean;
	}

	let {
		content = '',
		html = '',
		currentFilePath = null,
		onOpen = () => {},
		onSaveAs = () => {},
		onFormat = () => {},
		onToggleView = () => {},
		onToggleSidebar = () => {},
		sidebarOpen = false,
		viewMode = false,
		showSidebarToggle = true,
		showFileActions = true,
		showFormatActions = true,
		showViewToggle = true
	}: Props = $props();

	let copyMarkdownSuccess = $state(false);
	let copyHtmlSuccess = $state(false);

	const copyMarkdown = async () => {
		try {
			await navigator.clipboard.writeText(content);
			copyMarkdownSuccess = true;
			setTimeout(() => copyMarkdownSuccess = false, 2000);
		} catch (err) {
			console.error('Failed to copy:', err);
		}
	};

	const copyHtml = async () => {
		try {
			await navigator.clipboard.writeText(html);
			copyHtmlSuccess = true;
			setTimeout(() => copyHtmlSuccess = false, 2000);
		} catch (err) {
			console.error('Failed to copy HTML:', err);
		}
	};

	const printContent = () => {
		const printWindow = window.open('', '_blank');
		if (printWindow) {
			printWindow.document.write(
				`<html><head><title>Print</title><${''}style>${printCss}</style></head><body>`
			);
			printWindow.document.write(html);
			printWindow.document.write('</body></html>');
			printWindow.document.close();
			printWindow.onload = () => {
				printWindow.print();
				printWindow.onafterprint = () => {};
				printWindow.close();
			};
		}
	};
</script>

<header class="flex justify-between border-b border-gray-800 p-2 text-sm flex-shrink-0">
	<nav class="flex w-full items-center justify-between sm:w-fit">
		<div class="flex flex-wrap gap-0.5">
			<!-- Sidebar Toggle -->
			{#if showSidebarToggle}
				<button
					title={sidebarOpen ? 'Close Sidebar' : 'Open Sidebar'}
					class="button"
					onclick={onToggleSidebar}
				>
					{#if sidebarOpen}
						<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
						</svg>
					{:else}
						<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
						</svg>
					{/if}
					<span class="hidden lg:inline">{sidebarOpen ? 'Close' : 'Files'}</span>
				</button>
			{/if}

			<!-- File Actions -->
			{#if showFileActions}
				<button title="Open File... (⌘O)" class="button" onclick={onOpen}>
					<svg.Open />
					<span class="hidden lg:inline">Open</span>
				</button>
				<button title="Save As... (⌘⇧S)" class="button" onclick={onSaveAs}>
					<svg.Save />
					<span class="hidden lg:inline">Save As</span>
				</button>
			{/if}

			<!-- Copy Actions -->
			{#if showFormatActions}
				<button
					title="Copy Markdown"
					class="button"
					onclick={copyMarkdown}
				>
					{#if copyMarkdownSuccess}
						<svg.CopyComplete />
					{:else}
						<svg.Copy />
					{/if}
					<span class="hidden lg:inline">Copy</span>
				</button>
				<button
					title="Copy as HTML"
					class="button"
					onclick={copyHtml}
				>
					{#if copyHtmlSuccess}
						<svg.CopyComplete />
					{:else}
						<svg.Code />
					{/if}
					<span class="hidden lg:inline">HTML</span>
				</button>
				<button title="Print Preview (⌘P)" class="button" onclick={printContent}>
					<svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
						<path fill-rule="evenodd" d="M7.875 1.5C6.839 1.5 6 2.34 6 3.375v2.99c-.426.053-.851.11-1.274.174-1.454.218-2.476 1.483-2.476 2.917v6.294a3 3 0 003 3h.27l-.155 1.705A1.875 1.875 0 007.232 22.5h9.536a1.875 1.875 0 001.867-2.045l-.155-1.705h.27a3 3 0 003-3V9.456c0-1.434-1.022-2.7-2.476-2.917A48.716 48.716 0 0018 6.366V3.375c0-1.036-.84-1.875-1.875-1.875h-8.25zM16.5 6.205v-2.83A.375.375 0 0016.125 3h-8.25a.375.375 0 00-.375.375v2.83a49.353 49.353 0 019 0zm-.217 8.265c.178.018.317.16.333.337l.526 5.784a.375.375 0 01-.374.409H7.232a.375.375 0 01-.374-.409l.526-5.784a.373.373 0 01.333-.337 41.741 41.741 0 018.566 0zm.967-3.97a.75.75 0 01.75-.75h.008a.75.75 0 01.75.75v.008a.75.75 0 01-.75.75H18a.75.75 0 01-.75-.75V10.5zM15 9.75a.75.75 0 00-.75.75v.008c0 .414.336.75.75.75h.008a.75.75 0 00.75-.75V10.5a.75.75 0 00-.75-.75H15z" clip-rule="evenodd" />
					</svg>
					<span class="hidden lg:inline">Print</span>
				</button>
				<button title="Format Document (⌘S)" class="button" onclick={onFormat}>
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7" />
					</svg>
					<span class="hidden lg:inline">Format</span>
				</button>
			{/if}

			<!-- View Toggle (mobile) -->
			{#if showViewToggle}
				<button title={viewMode ? 'Edit' : 'View'} class="button lg:hidden" onclick={onToggleView}>
					{#if viewMode}
						<svg.Edit />
					{:else}
						<svg.View />
					{/if}
				</button>
			{/if}
		</div>
	</nav>

	<!-- File Name -->
	<div class="hidden px-4 py-2 font-bold sm:block truncate max-w-xs">
		{currentFilePath ? currentFilePath.split('/').pop() : 'Typo'}
	</div>
</header>
