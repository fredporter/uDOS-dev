/**
 * Noun Project API Service
 * 
 * Fetches icons from The Noun Project API v2
 * API Docs: https://api.thenounproject.com/documentation
 * 
 * Setup:
 * 1. Get API key from https://thenounproject.com/developers/
 * 2. Add to .env.local:
 *    VITE_NOUN_PROJECT_API_KEY=your_key_here
 */

interface NounIcon {
	id: number;
	term: string;
	preview_url: string;
	thumbnail_url: string;
	icon_url: string;
	attribution: string;
	attribution_preview_url: string;
	uploader: {
		name: string;
		username: string;
	};
}

interface NounSearchResponse {
	icons: NounIcon[];
	generated_at: string;
}

// Cache for downloaded icons
const iconCache = new Map<number, string>();

// Track if we've already warned about missing API key
let hasWarnedAboutApiKey = false;

/**
 * Search for icons by term
 */
export async function searchIcons(term: string, limit: number = 10): Promise<NounIcon[]> {
	const apiKey = import.meta.env.VITE_NOUN_PROJECT_API_KEY;
	
	if (!apiKey) {
		if (!hasWarnedAboutApiKey) {
			console.warn('[NounProject] API key not configured. Set VITE_NOUN_PROJECT_API_KEY in .env.local');
			hasWarnedAboutApiKey = true;
		}
		return [];
	}

	try {
		const url = new URL('https://api.thenounproject.com/v2/icon');
		url.searchParams.set('query', term);
		url.searchParams.set('limit', limit.toString());

		const response = await fetch(url.toString(), {
			headers: {
				'Authorization': `Bearer ${apiKey}`,
			},
		});

		if (!response.ok) {
			throw new Error(`Noun Project API error: ${response.status}`);
		}

		const data: NounSearchResponse = await response.json();
		return data.icons;
	} catch (error) {
		console.error('[NounProject] Search failed:', error);
		return [];
	}
}

/**
 * Get icon SVG by ID
 */
export async function getIconSvg(iconId: number): Promise<string | null> {
	// Check cache first
	if (iconCache.has(iconId)) {
		return iconCache.get(iconId)!;
	}

	const apiKey = import.meta.env.VITE_NOUN_PROJECT_API_KEY;
	
	if (!apiKey) {
		if (!hasWarnedAboutApiKey) {
			console.warn('[NounProject] API key not configured. Set VITE_NOUN_PROJECT_API_KEY in .env.local');
			hasWarnedAboutApiKey = true;
		}
		return null;
	}

	try {
		const response = await fetch(`https://api.thenounproject.com/v2/icon/${iconId}`, {
			headers: {
				'Authorization': `Bearer ${apiKey}`,
			},
		});

		if (!response.ok) {
			throw new Error(`Noun Project API error: ${response.status}`);
		}

		const data = await response.json();
		const svg = data.icon.icon_url; // This is the SVG URL
		
		// Fetch the actual SVG content
		const svgResponse = await fetch(svg);
		const svgContent = await svgResponse.text();
		
		// Cache it
		iconCache.set(iconId, svgContent);
		
		return svgContent;
	} catch (error) {
		console.error('[NounProject] Failed to get icon:', error);
		return null;
	}
}

/**
 * Get multiple icons by search terms
 * Returns a map of term -> icon SVG
 */
export async function getIconSet(terms: string[]): Promise<Map<string, string>> {
	const result = new Map<string, string>();

	for (const term of terms) {
		const icons = await searchIcons(term, 1);
		if (icons.length > 0) {
			const svg = await getIconSvg(icons[0].id);
			if (svg) {
				result.set(term, svg);
			}
		}
	}

	return result;
}

/**
 * Core desktop icon set for uDOS
 */
export const CORE_DESKTOP_ICONS = [
	'document',
	'folder',
	'book',
	'terminal',
	'settings',
	'calendar',
	'clock',
	'mail',
	'trash',
	'search',
	'lightbulb',
	'compass',
];

/**
 * Load the core icon set
 */
export async function loadCoreIcons(): Promise<Map<string, string>> {
	return getIconSet(CORE_DESKTOP_ICONS);
}

/**
 * Save icons to local storage
 */
export function saveIconsToCache(icons: Map<string, string>) {
	const obj: Record<string, string> = {};
	icons.forEach((svg, term) => {
		obj[term] = svg;
	});
	localStorage.setItem('noun-project-icons', JSON.stringify(obj));
}

/**
 * Load icons from local storage
 */
export function loadIconsFromCache(): Map<string, string> | null {
	const cached = localStorage.getItem('noun-project-icons');
	if (!cached) return null;

	try {
		const obj = JSON.parse(cached);
		const map = new Map<string, string>();
		Object.entries(obj).forEach(([term, svg]) => {
			map.set(term, svg as string);
		});
		return map;
	} catch {
		return null;
	}
}
