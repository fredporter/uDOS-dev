/**
 * Icon Library Sources
 *
 * Central registry for all icon collections used in uDOS
 * Integrates: Lucide (Svelte), System7 icons, Noun Project, Noto Emoji
 */

export interface IconSource {
  id: string;
  name: string;
  type: "font" | "svg" | "sprite" | "component";
  path?: string;
  license: string;
  count: number;
  usage: string;
}

export const ICON_SOURCES: IconSource[] = [
  {
    id: "lucide",
    name: "Lucide Icons",
    type: "component",
    license: "ISC License",
    count: 1000,
    usage: "npm install lucide-svelte",
  },
  {
    id: "system7",
    name: "System 7 Classic Icons",
    type: "sprite",
    path: "/sprites/system7/",
    license: "Custom (system.css inspired)",
    count: 0,
    usage: "Classic Mac UI elements",
  },
  {
    id: "noto-emoji",
    name: "Noto Emoji",
    type: "font",
    path: "/fonts/NotoEmoji-Regular.ttf",
    license: "SIL Open Font License",
    count: 3000,
    usage: "Emoji and symbols",
  },
  {
    id: "noun-project",
    name: "Noun Project Icons",
    type: "svg",
    path: "/sprites/noun-project/",
    license: "CC BY 3.0 (attribution required)",
    count: 0,
    usage: "Professional icons",
  },
  {
    id: "udos-system",
    name: "uDOS System Icons",
    type: "sprite",
    path: "/sprites/system/",
    license: "MIT",
    count: 0,
    usage: "Custom system icons",
  },
];

/**
 * System7 UI Element Categories
 */
export interface System7Element {
  id: string;
  name: string;
  category: "window" | "button" | "control" | "icon" | "cursor" | "alert";
  variants?: string[];
  size?: string;
}

export const SYSTEM7_ELEMENTS: System7Element[] = [
  // Windows
  {
    id: "window-chrome",
    name: "Window Frame",
    category: "window",
    variants: ["active", "inactive"],
  },
  {
    id: "window-title",
    name: "Title Bar",
    category: "window",
    variants: ["active", "inactive"],
  },
  { id: "window-close", name: "Close Box", category: "window" },
  { id: "window-resize", name: "Resize Handle", category: "window" },
  {
    id: "scrollbar",
    name: "Scrollbar",
    category: "control",
    variants: ["vertical", "horizontal"],
  },

  // Buttons
  { id: "button-default", name: "Default Button", category: "button" },
  { id: "button-cancel", name: "Cancel Button", category: "button" },
  {
    id: "button-radio",
    name: "Radio Button",
    category: "button",
    variants: ["on", "off"],
  },
  {
    id: "button-checkbox",
    name: "Checkbox",
    category: "button",
    variants: ["checked", "unchecked"],
  },

  // Controls
  { id: "slider", name: "Slider", category: "control" },
  { id: "dropdown", name: "Dropdown Menu", category: "control" },
  { id: "textfield", name: "Text Field", category: "control" },

  // Icons
  { id: "folder", name: "Folder", category: "icon", size: "32x32" },
  { id: "document", name: "Document", category: "icon", size: "32x32" },
  {
    id: "trash",
    name: "Trash",
    category: "icon",
    variants: ["empty", "full"],
    size: "32x32",
  },
  { id: "disk", name: "Disk", category: "icon", size: "32x32" },
  { id: "application", name: "Application", category: "icon", size: "32x32" },

  // Cursors
  { id: "cursor-pointer", name: "Pointer", category: "cursor" },
  { id: "cursor-hand", name: "Hand", category: "cursor" },
  { id: "cursor-text", name: "Text I-Beam", category: "cursor" },
  { id: "cursor-watch", name: "Watch", category: "cursor" },

  // Alerts
  { id: "alert-stop", name: "Stop Alert", category: "alert" },
  { id: "alert-caution", name: "Caution Alert", category: "alert" },
  { id: "alert-note", name: "Note Alert", category: "alert" },
];

/**
 * Get elements by category
 */
export function getElementsByCategory(
  category: System7Element["category"]
): System7Element[] {
  return SYSTEM7_ELEMENTS.filter((el) => el.category === category);
}

/**
 * Icon library integration points
 */
export interface IconLibraryIntegration {
  source: string;
  loader: () => Promise<any>;
  converter?: (data: any) => string; // Convert to SVG sprite format
}

export const INTEGRATIONS: Record<string, IconLibraryIntegration> = {
  lucide: {
    source: "lucide-svelte",
    loader: async () => {
      // Dynamic import of Lucide icons
      return import("lucide-svelte");
    },
  },
  system7: {
    source: "local",
    loader: async () => {
      return fetch("/sprites/system7/index.json").then((r) => r.json());
    },
  },
  "noto-emoji": {
    source: "font",
    loader: async () => {
      return fetch("/fonts/emoji.json").then((r) => r.json());
    },
  },
};
