<script lang="ts">
	/**
	 * FormViewer - Typeform-style form renderer
	 * 
	 * Renders markdown form definitions as interactive typeform-style
	 * single-question-per-screen forms.
	 * 
	 * Markdown Format:
	 * ```yaml
	 * form:
	 *   title: Survey Title
	 *   questions:
	 *     - type: text
	 *       label: What is your name?
	 *       required: true
	 *     - type: select
	 *       label: Choose an option
	 *       options: [A, B, C]
	 * ```
	 */

	import { onMount } from 'svelte';

	interface FormQuestion {
		type: 'text' | 'email' | 'number' | 'select' | 'multiselect' | 'textarea' | 'rating';
		label: string;
		description?: string;
		required?: boolean;
		options?: string[];
		min?: number;
		max?: number;
		placeholder?: string;
	}

	interface FormDefinition {
		title: string;
		description?: string;
		questions: FormQuestion[];
		submitLabel?: string;
	}

	interface Props {
		formContent?: string;
		onSubmit?: (data: Record<string, any>) => void;
		onClose?: () => void;
	}

	let { 
		formContent = '',
		onSubmit = () => {},
		onClose = () => {}
	}: Props = $props();

	let form = $state<FormDefinition | null>(null);
	let currentQuestion = $state(0);
	let answers = $state<Record<number, any>>({});
	let error = $state('');
	let submitted = $state(false);
	let parseError = $state('');

	// Helper to get current question
	function getCurrentQuestion(): FormQuestion | null {
		if (!form || currentQuestion >= form.questions.length) return null;
		return form.questions[currentQuestion];
	}

	$effect(() => {
		if (formContent) {
			parseForm(formContent);
		}
	});

	function parseForm(content: string) {
		try {
			// Simple YAML-like parser for form definitions
			const lines = content.split('\n');
			const result: FormDefinition = { title: 'Form', questions: [] };
			let currentQ: Partial<FormQuestion> | null = null;
			let inForm = false;
			let inQuestions = false;

			for (const line of lines) {
				const trimmed = line.trim();
				
				if (trimmed.startsWith('form:')) {
					inForm = true;
					continue;
				}
				
				if (!inForm) continue;

				if (trimmed.startsWith('title:')) {
					result.title = trimmed.replace('title:', '').trim().replace(/['"]/g, '');
				} else if (trimmed.startsWith('description:')) {
					result.description = trimmed.replace('description:', '').trim().replace(/['"]/g, '');
				} else if (trimmed.startsWith('submitLabel:')) {
					result.submitLabel = trimmed.replace('submitLabel:', '').trim().replace(/['"]/g, '');
				} else if (trimmed.startsWith('questions:')) {
					inQuestions = true;
				} else if (inQuestions && trimmed.startsWith('- type:')) {
					if (currentQ && currentQ.type && currentQ.label) {
						result.questions.push(currentQ as FormQuestion);
					}
					currentQ = { type: trimmed.replace('- type:', '').trim() as any };
				} else if (currentQ && trimmed.startsWith('label:')) {
					currentQ.label = trimmed.replace('label:', '').trim().replace(/['"]/g, '');
				} else if (currentQ && trimmed.startsWith('description:')) {
					currentQ.description = trimmed.replace('description:', '').trim().replace(/['"]/g, '');
				} else if (currentQ && trimmed.startsWith('required:')) {
					currentQ.required = trimmed.includes('true');
				} else if (currentQ && trimmed.startsWith('placeholder:')) {
					currentQ.placeholder = trimmed.replace('placeholder:', '').trim().replace(/['"]/g, '');
				} else if (currentQ && trimmed.startsWith('options:')) {
					const optStr = trimmed.replace('options:', '').trim();
					if (optStr.startsWith('[') && optStr.endsWith(']')) {
						currentQ.options = optStr.slice(1, -1).split(',').map(o => o.trim().replace(/['"]/g, ''));
					}
				} else if (currentQ && trimmed.startsWith('min:')) {
					currentQ.min = parseInt(trimmed.replace('min:', '').trim());
				} else if (currentQ && trimmed.startsWith('max:')) {
					currentQ.max = parseInt(trimmed.replace('max:', '').trim());
				}
			}

			// Push last question
			if (currentQ && currentQ.type && currentQ.label) {
				result.questions.push(currentQ as FormQuestion);
			}

			if (result.questions.length === 0) {
				throw new Error('No questions found in form');
			}

			form = result;
			parseError = '';
		} catch (e) {
			parseError = `Failed to parse form: ${e}`;
			form = null;
		}
	}

	function validateCurrent(): boolean {
		if (!form) return false;
		const q = form.questions[currentQuestion];
		const answer = answers[currentQuestion];

		if (q.required && (answer === undefined || answer === '' || answer === null)) {
			error = 'This field is required';
			return false;
		}

		if (q.type === 'email' && answer) {
			if (!answer.includes('@') || !answer.includes('.')) {
				error = 'Please enter a valid email';
				return false;
			}
		}

		if (q.type === 'number' && answer !== undefined) {
			const num = parseFloat(answer);
			if (q.min !== undefined && num < q.min) {
				error = `Minimum value is ${q.min}`;
				return false;
			}
			if (q.max !== undefined && num > q.max) {
				error = `Maximum value is ${q.max}`;
				return false;
			}
		}

		error = '';
		return true;
	}

	function next() {
		if (!form) return;
		if (!validateCurrent()) return;

		if (currentQuestion < form.questions.length - 1) {
			currentQuestion++;
		} else {
			submit();
		}
	}

	function prev() {
		if (currentQuestion > 0) {
			currentQuestion--;
			error = '';
		}
	}

	function submit() {
		if (!form) return;
		
		// Build result object with question labels as keys
		const result: Record<string, any> = {};
		form.questions.forEach((q, i) => {
			result[q.label] = answers[i];
		});

		submitted = true;
		onSubmit(result);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			next();
		}
	}

	function selectOption(option: string) {
		const q = form?.questions[currentQuestion];
		if (!q) return;

		if (q.type === 'multiselect') {
			const current = answers[currentQuestion] || [];
			if (current.includes(option)) {
				answers[currentQuestion] = current.filter((o: string) => o !== option);
			} else {
				answers[currentQuestion] = [...current, option];
			}
		} else {
			answers[currentQuestion] = option;
			// Auto-advance on select
			setTimeout(() => next(), 300);
		}
	}

	function setRating(value: number) {
		answers[currentQuestion] = value;
		setTimeout(() => next(), 300);
	}
</script>

{#if parseError}
	<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
		<div class="bg-white p-6 rounded-lg shadow-xl max-w-md">
			<h2 class="text-lg font-bold mb-4 text-red-600">Form Error</h2>
			<p class="text-gray-700 mb-4">{parseError}</p>
			<button 
				class="px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-700"
				onclick={onClose}
			>
				Close
			</button>
		</div>
	</div>
{:else if form}
	<div class="fixed inset-0 bg-gradient-to-br from-indigo-900 to-purple-900 flex flex-col z-50">
		<!-- Header -->
		<div class="flex items-center justify-between p-4 text-white/80">
			<button 
				class="p-2 hover:bg-white/10 rounded"
				onclick={onClose}
			>
				✕
			</button>
			<div class="text-sm">
				{currentQuestion + 1} / {form.questions.length}
			</div>
		</div>

		<!-- Progress bar -->
		<div class="w-full h-1 bg-white/20">
			<div 
				class="h-full bg-white transition-all duration-300"
				style="width: {((currentQuestion + 1) / form.questions.length) * 100}%"
			></div>
		</div>

		{#if submitted}
			<!-- Success screen -->
			<div class="flex-1 flex flex-col items-center justify-center text-white p-8">
				<div class="text-6xl mb-6">✓</div>
				<h2 class="text-3xl font-light mb-4">Thank you!</h2>
				<p class="text-white/70 mb-8">Your response has been recorded.</p>
				<button
					class="px-6 py-3 bg-white text-indigo-900 rounded-full font-medium hover:bg-white/90"
					onclick={onClose}
				>
					Done
				</button>
			</div>
		{:else}
			<!-- Question -->
			{#if getCurrentQuestion()}
			{@const q = getCurrentQuestion()}
			<div class="flex-1 flex flex-col items-center justify-center p-8 overflow-auto">
				
				<div class="max-w-2xl w-full space-y-8">
					<!-- Question number -->
					<div class="text-indigo-300 text-sm">
						{currentQuestion + 1} →
					</div>

					<!-- Question label -->
					<h2 class="text-3xl text-white font-light leading-relaxed">
						{q?.label}
						{#if q?.required}
							<span class="text-pink-400">*</span>
						{/if}
					</h2>

					<!-- Description -->
					{#if q?.description}
						<p class="text-white/60">{q.description}</p>
					{/if}

					<!-- Input based on type -->
					<div class="space-y-4">
						{#if q?.type === 'text' || q?.type === 'email' || q?.type === 'number'}
							<input
								type={q.type}
								class="w-full bg-transparent border-b-2 border-white/30 focus:border-white py-4 text-2xl text-white placeholder-white/40 outline-none"
								placeholder={q.placeholder || 'Type your answer here...'}
								bind:value={answers[currentQuestion]}
								onkeydown={handleKeydown}
								min={q.min}
								max={q.max}
							/>
						{:else if q?.type === 'textarea'}
							<textarea
								class="w-full bg-white/10 rounded-lg p-4 text-lg text-white placeholder-white/40 outline-none resize-none"
								placeholder={q.placeholder || 'Type your answer here...'}
								rows={4}
								bind:value={answers[currentQuestion]}
							></textarea>
						{:else if q?.type === 'select' || q?.type === 'multiselect'}
							<div class="space-y-3">
								{#each q.options || [] as option, i}
									{@const isSelected = q.type === 'multiselect' 
										? (answers[currentQuestion] || []).includes(option)
										: answers[currentQuestion] === option}
									<button
										class="w-full flex items-center gap-4 p-4 rounded-lg border-2 transition-all text-left
											{isSelected 
												? 'border-white bg-white/20 text-white' 
												: 'border-white/30 hover:border-white/60 text-white/80 hover:text-white'}"
										onclick={() => selectOption(option)}
									>
										<span class="w-8 h-8 flex items-center justify-center border-2 rounded
											{isSelected ? 'border-white bg-white text-indigo-900' : 'border-white/50'}">
											{String.fromCharCode(65 + i)}
										</span>
										<span class="text-lg">{option}</span>
									</button>
								{/each}
							</div>
						{:else if q?.type === 'rating'}
							<div class="flex gap-4">
								{#each Array.from({ length: q.max || 5 }, (_, i) => i + 1) as num}
									<button
										class="w-14 h-14 rounded-lg border-2 text-xl font-medium transition-all
											{answers[currentQuestion] === num 
												? 'border-white bg-white text-indigo-900' 
												: 'border-white/30 hover:border-white text-white'}"
										onclick={() => setRating(num)}
									>
										{num}
									</button>
								{/each}
							</div>
						{/if}

						<!-- Error message -->
						{#if error}
							<p class="text-pink-400 text-sm">{error}</p>
						{/if}
					</div>

					<!-- Navigation -->
					<div class="flex items-center gap-4 pt-8">
						<button
							class="px-6 py-3 bg-white text-indigo-900 rounded-lg font-medium hover:bg-white/90 flex items-center gap-2"
							onclick={next}
						>
							{form && currentQuestion === form.questions.length - 1 ? (form.submitLabel || 'Submit') : 'OK'}
							<span class="text-sm opacity-60">↵</span>
						</button>

						{#if currentQuestion > 0}
							<button
								class="px-4 py-2 text-white/60 hover:text-white"
								onclick={prev}
							>
								← Back
							</button>
						{/if}
					</div>
				</div>
			</div>
			{/if}
		{/if}

		<!-- Footer hint -->
		{#if !submitted}
			<div class="p-4 text-center text-white/40 text-sm">
				Press <kbd class="px-2 py-1 bg-white/10 rounded">Enter ↵</kbd> to continue
			</div>
		{/if}
	</div>
{/if}
