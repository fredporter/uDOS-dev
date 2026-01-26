/**
 * System7 UI Component Library
 *
 * Classic Macintosh System 7 styled components
 * Based on https://sakofchit.github.io/system.css/
 * Adapted for Tailwind + modern web
 */

/**
 * System7 Window Component Structure
 */
export interface System7Window {
  title: string;
  active?: boolean;
  resizable?: boolean;
  closable?: boolean;
  width?: number;
  height?: number;
}

/**
 * System7 Alert Types
 */
export type AlertType = "stop" | "caution" | "note";

export interface System7Alert {
  type: AlertType;
  title: string;
  message: string;
  buttons?: string[];
  defaultButton?: number;
}

/**
 * System7 Color Palette (Classic Mac)
 */
export const SYSTEM7_COLORS = {
  // Window chrome
  windowFrame: "#000000",
  titleBarActive: "#000000",
  titleBarInactive: "#ffffff",
  titleTextActive: "#ffffff",
  titleTextInactive: "#000000",

  // Backgrounds
  windowBackground: "#ffffff",
  desktopBackground: "#c0c0c0",
  menuBackground: "#ffffff",

  // Controls
  buttonFace: "#dddddd",
  buttonShadow: "#888888",
  buttonHighlight: "#ffffff",
  buttonText: "#000000",

  // Scrollbars
  scrollbarTrack: "#ffffff",
  scrollbarThumb: "#dddddd",
  scrollbarArrow: "#000000",

  // Text
  textPrimary: "#000000",
  textSecondary: "#666666",
  textDisabled: "#aaaaaa",

  // Selection
  highlightBlue: "#0000ff",
  highlightText: "#ffffff",

  // Alerts
  alertStop: "#ff0000",
  alertCaution: "#ffcc00",
  alertNote: "#0000ff",
};

/**
 * System7 Typography
 */
export const SYSTEM7_FONTS = {
  system: 'Chicago, "Press Start 2P", monospace',
  menu: 'Geneva, "SF Pro", -apple-system, system-ui, sans-serif',
  mono: 'Monaco, "SF Mono", "Courier New", monospace',
  dialog: 'Charcoal, "Helvetica Neue", sans-serif',
};

/**
 * System7 Window Dimensions
 */
export const SYSTEM7_SIZES = {
  titleBarHeight: 20,
  closeBoxSize: 12,
  scrollbarWidth: 16,
  borderWidth: 1,
  windowMinWidth: 200,
  windowMinHeight: 100,

  // Icon sizes
  iconSmall: 16,
  iconMedium: 32,
  iconLarge: 64,

  // Button sizes
  buttonHeight: 20,
  buttonMinWidth: 60,
  buttonPadding: 8,
};

/**
 * Convert system.css classes to Tailwind-compatible styles
 */
export const SYSTEM7_TAILWIND_MAP = {
  ".window":
    "bg-white border-2 border-black shadow-[2px_2px_0_0_rgba(0,0,0,1)]",
  ".title-bar":
    "h-5 bg-black text-white font-bold text-xs px-2 flex items-center justify-between",
  ".title-bar.inactive": "bg-white text-black",
  ".window-body": "p-4",
  ".btn":
    "px-4 py-1 border-2 border-black bg-[#dddddd] shadow-[2px_2px_0_0_rgba(0,0,0,0.25)] active:shadow-none",
  ".btn-default": "border-4",
  ".field": "border-2 border-black px-2 py-1 bg-white",
  ".checkbox": "w-4 h-4 border-2 border-black",
  ".radio": "w-4 h-4 border-2 border-black rounded-full",
  ".slider": "appearance-none bg-white border-2 border-black h-2",
  ".status-bar": "border-t-2 border-black px-2 py-1 text-xs bg-[#dddddd]",
};

/**
 * System7 Pattern (for desktop background)
 */
export const DESKTOP_PATTERN = `
<svg width="4" height="4" xmlns="http://www.w3.org/2000/svg">
  <rect width="4" height="4" fill="#c0c0c0"/>
  <rect x="0" y="0" width="2" height="2" fill="#b0b0b0"/>
  <rect x="2" y="2" width="2" height="2" fill="#b0b0b0"/>
</svg>
`;

/**
 * Generate System7 window SVG sprite
 */
export function generateWindowSprite(options: System7Window): string {
  const {
    title = "Untitled",
    active = true,
    width = 400,
    height = 300,
  } = options;

  return `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}">
  <!-- Window frame -->
  <rect x="0" y="0" width="${width}" height="${height}" fill="white" stroke="black" stroke-width="2"/>
  
  <!-- Title bar -->
  <rect x="1" y="1" width="${width - 2}" height="18" fill="${active ? "black" : "white"}" stroke="black"/>
  
  <!-- Close box -->
  <rect x="4" y="4" width="12" height="12" fill="white" stroke="black"/>
  <line x1="6" y1="6" x2="14" y2="14" stroke="black" stroke-width="2"/>
  <line x1="14" y1="6" x2="6" y2="14" stroke="black" stroke-width="2"/>
  
  <!-- Title text -->
  <text x="${width / 2}" y="14" text-anchor="middle" font-family="Chicago, monospace" font-size="12" fill="${active ? "white" : "black"}">${title}</text>
  
  <!-- Window content area -->
  <rect x="2" y="20" width="${width - 4}" height="${height - 22}" fill="white"/>
</svg>
  `.trim();
}
