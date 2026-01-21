/// <reference types="svelte" />
/// <reference types="svelte/experimental" />
/// <reference path="../node_modules/svelte-check/dist/src/svelte-shims.d.ts" />

// Minimal shim declarations for Svelte runes helpers used in transformed output
declare global {
	function __sveltets_2_ensureSnippet(
		val: import("svelte").Snippet | undefined | null
	): any;

	// See https://svelte.dev/docs/kit/types#app.d.ts
	// for information about these interfaces
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
