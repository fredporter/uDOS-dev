/**
 * Feed Store - Universal content feed system
 * 
 * Supports multiple feed sources (knowledge, logs, emails, notifications)
 * with various display modes (Ticker, Page, Panel) and natural typing output.
 */

// Feed item from any source
export interface FeedItem {
	id: string;
	source: FeedSource;
	timestamp: Date;
	title: string;
	content: string;
	priority: 'low' | 'normal' | 'high' | 'urgent';
	read: boolean;
	metadata?: Record<string, unknown>;
}

// Available feed sources
export type FeedSource = 
	| 'knowledge'    // Knowledge bank articles
	| 'logs'         // System/session logs
	| 'notifications' // System notifications
	| 'email'        // Email (via Wizard)
	| 'mesh'         // Mesh network messages
	| 'commands'     // Command history/output
	| 'custom';      // User-defined feeds

// Display modes for feeds
export type FeedDisplayMode = 
	| 'ticker'  // Horizontal scrolling bar
	| 'page'    // Full-screen teletext style
	| 'panel';  // Side panel overlay

// Scroll behavior
export type ScrollBehavior = 
	| 'instant'     // Jump to position
	| 'smooth'      // CSS smooth scroll
	| 'typewriter'  // Character by character
	| 'line'        // Line by line reveal
	| 'word';       // Word by word

// Feed configuration
export interface FeedConfig {
	source: FeedSource;
	displayMode: FeedDisplayMode;
	scrollBehavior: ScrollBehavior;
	scrollSpeed: number;       // Characters per second (for typewriter)
	autoAdvance: boolean;      // Auto-advance to next item
	advanceDelay: number;      // ms between items
	maxItems: number;          // Buffer size
	filter?: (item: FeedItem) => boolean;
}

// Default configurations per display mode
export const DEFAULT_CONFIGS: Record<FeedDisplayMode, Partial<FeedConfig>> = {
	ticker: {
		scrollBehavior: 'smooth',
		scrollSpeed: 60,
		autoAdvance: true,
		advanceDelay: 5000,
		maxItems: 50
	},
	page: {
		scrollBehavior: 'typewriter',
		scrollSpeed: 30,
		autoAdvance: false,
		advanceDelay: 0,
		maxItems: 100
	},
	panel: {
		scrollBehavior: 'line',
		scrollSpeed: 120,
		autoAdvance: true,
		advanceDelay: 3000,
		maxItems: 20
	}
};

// Feed state for a single feed instance
export interface FeedState {
	id: string;
	config: FeedConfig;
	items: FeedItem[];
	currentIndex: number;
	displayedContent: string;  // Currently visible (for typewriter effect)
	isTyping: boolean;
	isPaused: boolean;
	charIndex: number;         // Position in typewriter output
}

// Global feed manager state
interface FeedManagerState {
	feeds: Map<string, FeedState>;
	activeFeedId: string | null;
	globalPaused: boolean;
}

// Create singleton state
const state: FeedManagerState = {
	feeds: new Map(),
	activeFeedId: null,
	globalPaused: false
};

// Subscriptions for reactive updates
type Subscriber = () => void;
const subscribers = new Set<Subscriber>();

function notify() {
	subscribers.forEach(fn => fn());
}

/**
 * Subscribe to feed state changes
 */
export function subscribeFeed(fn: Subscriber): () => void {
	subscribers.add(fn);
	return () => subscribers.delete(fn);
}

/**
 * Create a new feed instance
 */
export function createFeed(
	id: string,
	source: FeedSource,
	displayMode: FeedDisplayMode,
	overrides?: Partial<FeedConfig>
): FeedState {
	const defaultConfig = DEFAULT_CONFIGS[displayMode];
	const config: FeedConfig = {
		source,
		displayMode,
		scrollBehavior: defaultConfig.scrollBehavior ?? 'smooth',
		scrollSpeed: defaultConfig.scrollSpeed ?? 60,
		autoAdvance: defaultConfig.autoAdvance ?? true,
		advanceDelay: defaultConfig.advanceDelay ?? 3000,
		maxItems: defaultConfig.maxItems ?? 50,
		...overrides
	};

	const feedState: FeedState = {
		id,
		config,
		items: [],
		currentIndex: 0,
		displayedContent: '',
		isTyping: false,
		isPaused: false,
		charIndex: 0
	};

	state.feeds.set(id, feedState);
	notify();
	return feedState;
}

/**
 * Get feed state by ID
 */
export function getFeed(id: string): FeedState | undefined {
	return state.feeds.get(id);
}

/**
 * Get all active feeds
 */
export function getAllFeeds(): FeedState[] {
	return Array.from(state.feeds.values());
}

/**
 * Add items to a feed
 */
export function addFeedItems(feedId: string, items: FeedItem[]): void {
	const feed = state.feeds.get(feedId);
	if (!feed) return;

	// Apply filter if configured
	const filtered = feed.config.filter 
		? items.filter(feed.config.filter)
		: items;

	feed.items.push(...filtered);

	// Trim to max items
	if (feed.items.length > feed.config.maxItems) {
		feed.items = feed.items.slice(-feed.config.maxItems);
	}

	notify();
}

/**
 * Clear a feed's items
 */
export function clearFeed(feedId: string): void {
	const feed = state.feeds.get(feedId);
	if (!feed) return;

	feed.items = [];
	feed.currentIndex = 0;
	feed.displayedContent = '';
	feed.charIndex = 0;
	notify();
}

/**
 * Remove a feed instance
 */
export function removeFeed(feedId: string): void {
	state.feeds.delete(feedId);
	if (state.activeFeedId === feedId) {
		state.activeFeedId = null;
	}
	notify();
}

/**
 * Set active feed for focus
 */
export function setActiveFeed(feedId: string | null): void {
	state.activeFeedId = feedId;
	notify();
}

/**
 * Pause/resume a specific feed
 */
export function toggleFeedPause(feedId: string): void {
	const feed = state.feeds.get(feedId);
	if (!feed) return;
	feed.isPaused = !feed.isPaused;
	notify();
}

/**
 * Pause/resume all feeds globally
 */
export function toggleGlobalPause(): void {
	state.globalPaused = !state.globalPaused;
	notify();
}

/**
 * Advance to next item in feed
 */
export function nextItem(feedId: string): void {
	const feed = state.feeds.get(feedId);
	if (!feed || feed.items.length === 0) return;

	feed.currentIndex = (feed.currentIndex + 1) % feed.items.length;
	feed.displayedContent = '';
	feed.charIndex = 0;
	feed.isTyping = feed.config.scrollBehavior === 'typewriter';
	notify();
}

/**
 * Go to previous item in feed
 */
export function prevItem(feedId: string): void {
	const feed = state.feeds.get(feedId);
	if (!feed || feed.items.length === 0) return;

	feed.currentIndex = feed.currentIndex === 0 
		? feed.items.length - 1 
		: feed.currentIndex - 1;
	feed.displayedContent = '';
	feed.charIndex = 0;
	feed.isTyping = feed.config.scrollBehavior === 'typewriter';
	notify();
}

/**
 * Get current item for a feed
 */
export function getCurrentItem(feedId: string): FeedItem | null {
	const feed = state.feeds.get(feedId);
	if (!feed || feed.items.length === 0) return null;
	return feed.items[feed.currentIndex];
}

// Typewriter animation frame
let typewriterFrame: number | null = null;
let lastTypewriterTime = 0;

/**
 * Start typewriter animation for a feed
 */
export function startTypewriter(feedId: string): void {
	const feed = state.feeds.get(feedId);
	if (!feed) return;

	feed.isTyping = true;
	feed.charIndex = 0;
	feed.displayedContent = '';

	const item = getCurrentItem(feedId);
	if (!item) return;

	const fullContent = `${item.title}\n\n${item.content}`;
	const msPerChar = 1000 / feed.config.scrollSpeed;
	const config = feed.config; // Capture for closure

	function tick(timestamp: number) {
		const currentFeed = state.feeds.get(feedId);
		if (!currentFeed || !currentFeed.isTyping || currentFeed.isPaused || state.globalPaused) {
			typewriterFrame = requestAnimationFrame(tick);
			return;
		}

		const elapsed = timestamp - lastTypewriterTime;
		if (elapsed >= msPerChar) {
			lastTypewriterTime = timestamp;
			
			if (currentFeed.charIndex < fullContent.length) {
				currentFeed.charIndex++;
				currentFeed.displayedContent = fullContent.slice(0, currentFeed.charIndex);
				notify();
			} else {
				// Typing complete
				currentFeed.isTyping = false;
				
				// Auto-advance if configured
				if (config.autoAdvance && config.advanceDelay > 0) {
					setTimeout(() => {
						const f = state.feeds.get(feedId);
						if (f && !f.isPaused && !state.globalPaused) {
							nextItem(feedId);
							if (config.scrollBehavior === 'typewriter') {
								startTypewriter(feedId);
							}
						}
					}, config.advanceDelay);
				}
				return;
			}
		}

		typewriterFrame = requestAnimationFrame(tick);
	}

	lastTypewriterTime = performance.now();
	typewriterFrame = requestAnimationFrame(tick);
}

/**
 * Stop typewriter animation
 */
export function stopTypewriter(feedId: string): void {
	const feed = state.feeds.get(feedId);
	if (!feed) return;

	feed.isTyping = false;
	
	// Show full content immediately
	const item = getCurrentItem(feedId);
	if (item) {
		feed.displayedContent = `${item.title}\n\n${item.content}`;
	}
	notify();
}

/**
 * Skip to end of current typewriter
 */
export function skipTypewriter(feedId: string): void {
	stopTypewriter(feedId);
}

// ============================================================================
// FEED SOURCE LOADERS
// ============================================================================

const API_BASE = 'http://localhost:5001';

/**
 * Load knowledge feed items from a category
 */
export async function loadKnowledgeFeed(
	feedId: string,
	category?: string
): Promise<void> {
	try {
		const url = category 
			? `${API_BASE}/api/feed/knowledge?category=${category}`
			: `${API_BASE}/api/feed/knowledge`;
		
		const response = await fetch(url);
		if (!response.ok) throw new Error('Failed to load knowledge feed');
		
		const data = await response.json();
		if (data.items) {
			addFeedItems(feedId, data.items.map((item: Record<string, unknown>) => ({
				id: item.id as string || crypto.randomUUID(),
				source: 'knowledge' as FeedSource,
				timestamp: new Date(item.timestamp as string || Date.now()),
				title: item.title as string || 'Untitled',
				content: item.content as string || '',
				priority: 'normal' as const,
				read: false,
				metadata: item.metadata as Record<string, unknown>
			})));
		}
	} catch (e) {
		console.error('Knowledge feed load error:', e);
	}
}

/**
 * Load log feed from session logs
 */
export async function loadLogFeed(
	feedId: string,
	logType: 'session' | 'system' | 'error' = 'session',
	lines = 50
): Promise<void> {
	try {
		const response = await fetch(
			`${API_BASE}/api/feed/logs?type=${logType}&lines=${lines}`
		);
		if (!response.ok) throw new Error('Failed to load log feed');
		
		const data = await response.json();
		if (data.items) {
			addFeedItems(feedId, data.items.map((item: Record<string, unknown>) => ({
				id: item.id as string || crypto.randomUUID(),
				source: 'logs' as FeedSource,
				timestamp: new Date(item.timestamp as string || Date.now()),
				title: item.level as string || 'LOG',
				content: item.message as string || '',
				priority: item.level === 'ERROR' ? 'high' as const : 'normal' as const,
				read: false,
				metadata: { logType, ...item.metadata as Record<string, unknown> }
			})));
		}
	} catch (e) {
		console.error('Log feed load error:', e);
	}
}

/**
 * Load notification feed
 */
export async function loadNotificationFeed(feedId: string): Promise<void> {
	try {
		const response = await fetch(`${API_BASE}/api/feed/notifications`);
		if (!response.ok) throw new Error('Failed to load notifications');
		
		const data = await response.json();
		if (data.items) {
			addFeedItems(feedId, data.items.map((item: Record<string, unknown>) => ({
				id: item.id as string || crypto.randomUUID(),
				source: 'notifications' as FeedSource,
				timestamp: new Date(item.timestamp as string || Date.now()),
				title: item.title as string || 'Notification',
				content: item.message as string || '',
				priority: (item.priority as 'low' | 'normal' | 'high' | 'urgent') || 'normal',
				read: item.read as boolean || false,
				metadata: item.metadata as Record<string, unknown>
			})));
		}
	} catch (e) {
		console.error('Notification feed load error:', e);
	}
}

// ============================================================================
// TICKER HELPERS
// ============================================================================

/**
 * Format items for ticker display (single line)
 */
export function formatTickerContent(items: FeedItem[]): string {
	return items
		.map(item => {
			// Include title and first sentence/line of content
			const firstLine = item.content.split('\n')[0] || '';
			const fullText = firstLine ? `${item.title}: ${firstLine}` : item.title;
			return fullText;
		})
		.join(' | ');
}

/**
 * Get icon for priority level
 */
function getPriorityIcon(priority: FeedItem['priority']): string {
	switch (priority) {
		case 'urgent': return '🔴';
		case 'high': return '🟠';
		case 'normal': return '🔵';
		case 'low': return '⚪';
		default: return '📌';
	}
}

/**
 * Format timestamp for display
 */
export function formatTimestamp(date: Date): string {
	const now = new Date();
	const diff = now.getTime() - date.getTime();
	
	if (diff < 60000) return 'Just now';
	if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
	if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
	return date.toLocaleDateString();
}

// ============================================================================
// PRESET FEEDS
// ============================================================================

/**
 * Create a knowledge ticker feed
 */
export function createKnowledgeTicker(): FeedState {
	return createFeed('knowledge-ticker', 'knowledge', 'ticker', {
		scrollSpeed: 40,
		autoAdvance: true,
		advanceDelay: 8000
	});
}

/**
 * Create a log panel feed
 */
export function createLogPanel(): FeedState {
	return createFeed('log-panel', 'logs', 'panel', {
		scrollBehavior: 'line',
		scrollSpeed: 200,
		autoAdvance: true,
		advanceDelay: 2000,
		maxItems: 30
	});
}

/**
 * Create a notification ticker
 */
export function createNotificationTicker(): FeedState {
	return createFeed('notification-ticker', 'notifications', 'ticker', {
		scrollSpeed: 50,
		autoAdvance: true,
		advanceDelay: 5000
	});
}

/**
 * Create a full-page knowledge reader
 */
export function createKnowledgeReader(): FeedState {
	return createFeed('knowledge-reader', 'knowledge', 'page', {
		scrollBehavior: 'typewriter',
		scrollSpeed: 60,
		autoAdvance: false
	});
}
