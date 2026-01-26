/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				goblin: {
					bg: '#0a0a0a',
					surface: '#1a1a1a',
					border: '#2a2a2a',
					text: '#e0e0e0',
					accent: '#9b59b6', // Purple for experimental
					success: '#27ae60',
					warning: '#f39c12',
					error: '#e74c3c',
				}
			}
		}
	},
	plugins: []
};
