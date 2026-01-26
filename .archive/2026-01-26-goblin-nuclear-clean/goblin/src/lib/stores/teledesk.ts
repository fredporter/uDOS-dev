/**
 * Teledesk Page Service
 *
 * Loads and manages teletext-style pages from:
 * - Built-in pages (100-199)
 * - Knowledge bank pages (200-899)
 * - System reference pages (900-999)
 */

import { apiRequest, isApiAvailable } from "$lib/stores/api";

export interface TeletextPage {
  number: number;
  title: string;
  content: Array<
    | string
    | {
        text: string;
        font?: "title" | "heading" | "heading-double" | "alt-heading" | "body";
        color?: string;
      }
  >;
  links: Array<{ page: number; label: string }>;
  category: string;
  updated?: string;
  source?: "builtin" | "knowledge" | "api";
}

// Page ranges
export const PAGE_RANGES = {
  INDEX: { start: 100, end: 199, label: "Index & Getting Started" },
  SURVIVAL: { start: 200, end: 299, label: "Survival Knowledge" },
  TECHNICAL: { start: 300, end: 399, label: "Technical Reference" },
  MEDICAL: { start: 400, end: 499, label: "Medical & First Aid" },
  NAVIGATION: { start: 500, end: 599, label: "Navigation & Maps" },
  COMMUNICATION: { start: 600, end: 699, label: "Communication" },
  TOOLS: { start: 700, end: 799, label: "Tools & Making" },
  FOOD: { start: 800, end: 899, label: "Food & Water" },
  SYSTEM: { start: 900, end: 999, label: "System Commands" },
};

// Built-in pages (always available offline)
const BUILTIN_PAGES: Record<number, TeletextPage> = {
  100: {
    number: 100,
    title: "uDOS TELEDESK",
    category: "index",
    source: "builtin",
    content: [
      { text: "P100", font: "alt-heading", color: "text-udos-white" },
      {
        text: "          ___",
        font: "alt-heading",
        color: "text-udos-white",
      },
      {
        text: "          uDOS TELEDESK        [INDEX       ]",
        font: "alt-heading",
        color: "text-udos-cyan",
      },
      { text: "○", font: "alt-heading", color: "text-udos-white" },
      {
        text: "          OFFLINE",
        font: "alt-heading",
        color: "text-udos-danger",
      },
      {
        text: "          │ 0-9:Page ←→:Browse HOME:Index ESC:Exit",
        font: "alt-heading",
        color: "text-udos-white",
      },
      "",
      "╔════════════════════════════════════════════════════════════╗",
      "║            ███   ▀█▀   ▀█▀  █  █  █▀▀▀                    ║",
      "║           █   █   █     █   ██  █    █▀                   ║",
      "║           █   █   █     █   █ █ █  █                      ║",
      "║            ███   ▀▀▀    █   █  ██   █▀▀                   ║",
      "║                                    KNOWLEDGE BROWSER       ║",
      "╠════════════════════════════════════════════════════════════╣",
      "║                                                            ║",
      "║  ▄▄▄▓▓▓▄▄▄ SURVIVAL         ▄▄▄▓▓▓▄▄▄ TECHNICAL ▄▄▄▓▓▓    ║",
      "║  █ 200 █ Essential skills   █ 300 █ Reference  █ 400 █   ║",
      "║  █ 201 █ Water safety       █ 301 █ Systems    █ 401 █   ║",
      "║  █ 202 █ Fire & shelter     █ 302 █ Networks   █ 402 █   ║",
      "║  █ 203 █ Navigation         █ 303 █ Protocols  █ 403 █   ║",
      "║  ▀▀▀▓▓▓▀▀▀                  ▀▀▀▓▓▓▀▀▀           ▀▀▀▓▓▓    ║",
      "║                                                            ║",
      "║  ▄▄▄▒▒▒▄▄▄ FOOD & WATER     ▄▄▄▒▒▒▄▄▄ TOOLS     ▄▄▄▒▒▒    ║",
      "║  █ 800 █ Edible plants      █ 700 █ Making     █ 600 █   ║",
      "║  █ 801 █ Cooking methods    █ 701 █ Building   █ 601 █   ║",
      "║  █ 802 █ Water treatment    █ 702 █ Repair     █ 602 █   ║",
      "║  █ 803 █ Preservation       █ 703 █ Improvised █ 603 █   ║",
      "║  ▀▀▀▒▒▒▀▀▀                  ▀▀▀▒▒▒▀▀▀           ▀▀▀▒▒▒    ║",
      "║                                                            ║",
      "║  ▄▄▄░░░▄▄▄ NAVIGATION       ▄▄▄▓▓▓▄▄▄ SYSTEM   ▄▄▄░░░    ║",
      "║  █ 500 █ Maps & compass     █ 900 █ Commands  █ 101 █   ║",
      "║  █ 501 █ Landmarks          █ 901 █ Help      █ 102 █   ║",
      "║  █ 502 █ Celestial nav      █ 902 █ Settings  █ 103 █   ║",
      "║  █ 503 █ Way-finding        █ 903 █ Status    █ 104 █   ║",
      "║  ▀▀▀░░░▀▀▀                  ▀▀▀▓▓▓▀▀▀           ▀▀▀░░░    ║",
      "║                                                            ║",
      "╠════════════════════════════════════════════════════════════╣",
      "║  Type PAGE NUMBER:  [___]     Use ← → to browse             ║",
      "║  STATUS: ONLINE ● │ ESC to Terminal                         ║",
      "╚════════════════════════════════════════════════════════════╝",
    ],
    links: [
      { page: 101, label: "Getting Started" },
      { page: 200, label: "Survival" },
      { page: 300, label: "Technical" },
      { page: 900, label: "Commands" },
    ],
  },
  101: {
    number: 101,
    title: "GETTING STARTED",
    category: "guide",
    source: "builtin",
    content: [
      "╔══════════════════════════════════════╗",
      "║          GETTING STARTED             ║",
      "║            with uDOS                 ║",
      "╚══════════════════════════════════════╝",
      "",
      "  Welcome to uDOS - your offline-first ",
      "  knowledge and command system.        ",
      "",
      "  QUICK START:                         ",
      "  ─────────────────────────────────────",
      "  1. Use ⌘K to open command palette    ",
      "  2. Type HELP for command list        ",
      "  3. Browse pages with number keys     ",
      "",
      "  NAVIGATION:                          ",
      "  ─────────────────────────────────────",
      "  ← →   Previous/Next page             ",
      "  0-9   Type page number directly      ",
      "  ESC   Return to Terminal             ",
      "  HOME  Go to page 100 (Index)         ",
      "",
      "  Next: 102 System Overview            ",
    ],
    links: [
      { page: 100, label: "Index" },
      { page: 102, label: "Next" },
    ],
  },
  102: {
    number: 102,
    title: "SYSTEM OVERVIEW",
    category: "guide",
    source: "builtin",
    content: [
      "╔══════════════════════════════════════╗",
      "║         SYSTEM OVERVIEW              ║",
      "║          uDOS Architecture           ║",
      "╚══════════════════════════════════════╝",
      "",
      "  uDOS has four modes:                 ",
      "",
      "  ⌘ TERMINAL (⌘1)                      ",
      "    Command-line interface for power  ",
      "    users. Run commands, scripts.     ",
      "",
      "  📝 DESKTOP (⌘2)                       ",
      "    Markdown editor with live preview.",
      "    Edit .udos.md executable docs.    ",
      "",
      "  📺 TELEDESK (⌘3)                      ",
      "    This mode! Browse knowledge bank  ",
      "    in offline-friendly teletext style",
      "",
      "  📊 DASHBOARD (⌘4)                     ",
      "    System status, quick actions.     ",
      "",
      "  ← 101 Back    103 Next →             ",
    ],
    links: [
      { page: 101, label: "Back" },
      { page: 103, label: "Next" },
    ],
  },
  // ===== SURVIVAL SECTION (200-299) =====
  200: {
    number: 200,
    title: "SURVIVAL KNOWLEDGE",
    category: "survival",
    source: "builtin",
    content: [
      "╔══════════════════════════════════════╗",
      "║        SURVIVAL KNOWLEDGE            ║",
      "║         Essential Skills             ║",
      "╚══════════════════════════════════════╝",
      "",
      "  THE RULE OF THREES:                  ",
      "  ─────────────────────────────────────",
      "  3 minutes without AIR                ",
      "  3 hours without SHELTER (exposure)   ",
      "  3 days without WATER                 ",
      "  3 weeks without FOOD                 ",
      "",
      "  SUB-SECTIONS:                        ",
      "  ─────────────────────────────────────",
      "  201 ... Shelter Building             ",
      "  210 ... Water Finding                ",
      "  220 ... Fire Starting                ",
      "  230 ... Food Foraging                ",
      "  240 ... Navigation                   ",
      "  250 ... Signaling                    ",
      "",
      "  ← 100 Index                          ",
    ],
    links: [
      { page: 100, label: "Index" },
      { page: 201, label: "Shelter" },
    ],
  },
  201: {
    number: 201,
    title: "SHELTER BUILDING",
    category: "survival",
    source: "builtin",
    content: [
      "╔══════════════════════════════════════╗",
      "║         SHELTER BUILDING             ║",
      "║        Protection First              ║",
      "╚══════════════════════════════════════╝",
      "",
      "  LOCATION CRITERIA:                   ",
      "  ─────────────────────────────────────",
      "  • High ground (avoid flooding)       ",
      "  • Natural windbreak                  ",
      "  • Near water but not too close       ",
      "  • Away from dead trees               ",
      "  • Clear of insect nests              ",
      "",
      "  QUICK SHELTERS:                      ",
      "  ─────────────────────────────────────",
      "  202 ... Debris Hut                   ",
      "  203 ... Lean-To Shelter              ",
      "  204 ... A-Frame Shelter              ",
      "  205 ... Snow Shelter                 ",
      "",
      "  ← 200 Survival    210 Water →        ",
    ],
    links: [
      { page: 200, label: "Back" },
      { page: 202, label: "Debris Hut" },
    ],
  },
  210: {
    number: 210,
    title: "WATER FINDING",
    category: "survival",
    source: "builtin",
    content: [
      "╔══════════════════════════════════════╗",
      "║          WATER FINDING               ║",
      "║         Sources & Safety             ║",
      "╚══════════════════════════════════════╝",
      "",
      "  WATER SOURCES (ranked by safety):    ",
      "  ─────────────────────────────────────",
      "  1. Rainwater (cleanest)              ",
      "  2. Springs (generally safe)          ",
      "  3. Streams (flowing better)          ",
      "  4. Lakes/ponds (needs purifying)     ",
      "  5. Ground seepage (last resort)      ",
      "",
      "  ALWAYS PURIFY WHEN POSSIBLE:         ",
      "  ─────────────────────────────────────",
      "  211 ... Boiling Method               ",
      "  212 ... Solar Disinfection           ",
      "  213 ... Chemical Treatment           ",
      "  214 ... Filtration Methods           ",
      "",
      "  ← 201 Shelter    220 Fire →          ",
    ],
    links: [
      { page: 201, label: "Back" },
      { page: 211, label: "Boiling" },
    ],
  },
  220: {
    number: 220,
    title: "FIRE STARTING",
    category: "survival",
    source: "builtin",
    content: [
      "╔══════════════════════════════════════╗",
      "║          FIRE STARTING               ║",
      "║         Methods & Materials          ║",
      "╚══════════════════════════════════════╝",
      "",
      "  FIRE MATERIALS:                      ",
      "  ─────────────────────────────────────",
      "  TINDER: Dry leaves, bark shavings,   ",
      "          cotton, char cloth           ",
      "  KINDLING: Small twigs, dry grass     ",
      "  FUEL: Progressively larger wood      ",
      "",
      "  FIRE LAY TYPES:                      ",
      "  ─────────────────────────────────────",
      "  221 ... Teepee Fire                  ",
      "  222 ... Log Cabin Fire               ",
      "  223 ... Dakota Fire Hole             ",
      "",
      "  IGNITION METHODS:                    ",
      "  224 ... Friction (Bow Drill)         ",
      "  225 ... Flint & Steel                ",
      "",
      "  ← 210 Water    230 Food →            ",
    ],
    links: [
      { page: 210, label: "Back" },
      { page: 221, label: "Teepee" },
    ],
  },
  // ===== SYSTEM COMMANDS (900-999) =====
  900: {
    number: 900,
    title: "SYSTEM COMMANDS",
    category: "reference",
    source: "builtin",
    content: [
      "╔══════════════════════════════════════╗",
      "║         SYSTEM COMMANDS              ║",
      "║         Quick Reference              ║",
      "╚══════════════════════════════════════╝",
      "",
      "  FILE OPERATIONS:                     ",
      "  ─────────────────────────────────────",
      "  NEW file.txt    Create new file      ",
      "  EDIT file.txt   Open in editor       ",
      "  DELETE file.txt Remove file          ",
      "  LIST            Show directory       ",
      "",
      "  SYSTEM:                              ",
      "  ─────────────────────────────────────",
      "  HELP            Show help            ",
      "  STATUS          System status        ",
      "  BACKUP          Create backup        ",
      "  TIDY            Clean temp files     ",
      "",
      "  901 ... File Commands                ",
      "  902 ... System Commands              ",
      "  903 ... uPY Scripting                ",
    ],
    links: [
      { page: 100, label: "Index" },
      { page: 901, label: "Files" },
    ],
  },
  901: {
    number: 901,
    title: "FILE COMMANDS",
    category: "reference",
    source: "builtin",
    content: [
      "╔══════════════════════════════════════╗",
      "║          FILE COMMANDS               ║",
      "║         Detailed Reference           ║",
      "╚══════════════════════════════════════╝",
      "",
      "  NEW <filename>                       ",
      "    Create a new empty file            ",
      "    Example: NEW notes.txt             ",
      "",
      "  EDIT <filename>                      ",
      "    Open file in the editor            ",
      "    Example: EDIT config.json          ",
      "",
      "  DELETE <filename>                    ",
      "    Remove a file (careful!)           ",
      "    Example: DELETE old_notes.txt      ",
      "",
      "  LIST [path]                          ",
      "    List files in directory            ",
      "    Example: LIST /memory/ucode        ",
      "",
      "  ← 900 Commands    902 System →       ",
    ],
    links: [
      { page: 900, label: "Back" },
      { page: 902, label: "System" },
    ],
  },
  902: {
    number: 902,
    title: "SYSTEM COMMANDS",
    category: "reference",
    source: "builtin",
    content: [
      "╔══════════════════════════════════════╗",
      "║        SYSTEM COMMANDS               ║",
      "║         Detailed Reference           ║",
      "╚══════════════════════════════════════╝",
      "",
      "  STATUS                               ",
      "    Show system status & versions      ",
      "",
      "  BACKUP [file]                        ",
      "    Create timestamped backup          ",
      "    Example: BACKUP notes.txt          ",
      "",
      "  TIDY                                 ",
      "    Clean temporary files              ",
      "",
      "  UNDO                                 ",
      "    Undo last file operation           ",
      "",
      "  REDO                                 ",
      "    Redo undone operation              ",
      "",
      "  ← 901 Files    903 uPY →             ",
    ],
    links: [
      { page: 901, label: "Back" },
      { page: 903, label: "uPY" },
    ],
  },
  903: {
    number: 903,
    title: "uPY SCRIPTING",
    category: "reference",
    source: "builtin",
    content: [
      "╔══════════════════════════════════════╗",
      "║          uPY SCRIPTING               ║",
      "║        Language Reference            ║",
      "╚══════════════════════════════════════╝",
      "",
      "  uPY is uDOS's scripting language:   ",
      "",
      "  VARIABLES:                           ",
      '  LET name = "uDOS"                    ',
      "  SET count = 42                       ",
      "",
      "  CONTROL FLOW:                        ",
      "  IF condition THEN ... END            ",
      "  FOR i = 1 TO 10 ... NEXT             ",
      "  WHILE condition ... WEND             ",
      "",
      "  FUNCTIONS:                           ",
      "  FUNCTION greet(name)                 ",
      '    RETURN "Hello, " + name            ',
      "  END                                  ",
      "",
      "  ← 902 System                         ",
    ],
    links: [
      { page: 902, label: "Back" },
      { page: 100, label: "Index" },
    ],
  },
};

// Cache for loaded pages
const pageCache = new Map<number, TeletextPage>();

/**
 * Get a page by number
 */
export async function getPage(pageNum: number): Promise<TeletextPage | null> {
  // Check cache first
  if (pageCache.has(pageNum)) {
    return pageCache.get(pageNum)!;
  }

  // Check built-in pages
  if (BUILTIN_PAGES[pageNum]) {
    return BUILTIN_PAGES[pageNum];
  }

  // Try to load from API (knowledge bank)
  const apiAvailable = await isApiAvailable();
  if (apiAvailable) {
    try {
      const response = await apiRequest<{ page: TeletextPage }>(
        `/api/teledesk/page/${pageNum}`
      );
      if (response.ok && response.data?.page) {
        const page = { ...response.data.page, source: "api" as const };
        pageCache.set(pageNum, page);
        return page;
      }
    } catch (e) {
      console.log("Failed to load page from API:", e);
    }
  }

  return null;
}

/**
 * Get page range info
 */
export function getPageRangeInfo(
  pageNum: number
): { label: string; range: { start: number; end: number } } | null {
  for (const [key, range] of Object.entries(PAGE_RANGES)) {
    if (pageNum >= range.start && pageNum <= range.end) {
      return {
        label: range.label,
        range: { start: range.start, end: range.end },
      };
    }
  }
  return null;
}

/**
 * Generate a "not found" page
 */
export function getNotFoundPage(pageNum: number): TeletextPage {
  const rangeInfo = getPageRangeInfo(pageNum);

  return {
    number: pageNum,
    title: "NOT FOUND",
    category: "error",
    source: "builtin",
    content: [
      "╔══════════════════════════════════════╗",
      `║         PAGE ${String(pageNum).padStart(3, "0")} NOT FOUND         ║`,
      "╚══════════════════════════════════════╝",
      "",
      "  This page is not yet available.      ",
      "",
      rangeInfo ? `  This page should be in:              ` : "",
      rangeInfo ? `  ${rangeInfo.label}                   `.slice(0, 40) : "",
      "",
      "  SUGGESTIONS:                         ",
      "  ─────────────────────────────────────",
      "  • Press HOME for Index (page 100)   ",
      "  • Use ← → to find nearby pages      ",
      "  • Check the page number             ",
      "",
      "  The knowledge bank is being built.  ",
      "  Content will be added over time.    ",
      "",
      "  ─────────────────────────────────────",
      "  ← 100 Index                          ",
    ],
    links: [{ page: 100, label: "Index" }],
  };
}

/**
 * Format content to fit teletext grid
 */
export function formatContent(
  lines: Array<
    | string
    | {
        text: string;
        font?: "title" | "heading" | "heading-double" | "alt-heading" | "body";
        color?: string;
      }
  >,
  cols: number = 40,
  rows: number = 23
): Array<
  | string
  | {
      text: string;
      font?: "title" | "heading" | "heading-double" | "alt-heading" | "body";
      color?: string;
    }
> {
  const formatted = lines.map((line) => {
    // Handle object format
    if (typeof line === "object") {
      const text =
        line.text.length > cols
          ? line.text.slice(0, cols)
          : line.text.padEnd(cols);
      return { ...line, text };
    }
    // Handle string format
    if (line.length > cols) {
      return line.slice(0, cols);
    }
    return line.padEnd(cols);
  });

  // Pad to fill screen
  while (formatted.length < rows) {
    formatted.push(" ".repeat(cols));
  }

  return formatted.slice(0, rows);
}

/**
 * Convert markdown to teletext content
 */
export function markdownToTeletext(
  markdown: string,
  pageNum: number
): TeletextPage {
  const lines: string[] = [];
  const mdLines = markdown.split("\n");

  let title = `PAGE ${pageNum}`;
  let inCodeBlock = false;

  for (const line of mdLines) {
    // Extract title from first heading
    if (line.startsWith("# ") && lines.length === 0) {
      title = line.slice(2).toUpperCase().slice(0, 36);
      lines.push("╔══════════════════════════════════════╗");
      lines.push(`║ ${title.padEnd(36)} ║`);
      lines.push("╚══════════════════════════════════════╝");
      lines.push("");
      continue;
    }

    // Handle code blocks
    if (line.startsWith("```")) {
      inCodeBlock = !inCodeBlock;
      lines.push("  ─────────────────────────────────────");
      continue;
    }

    // Convert markdown to teletext
    let converted = line
      .replace(/^## /, "  ")
      .replace(/^### /, "   ")
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\*(.*?)\*/g, "$1")
      .replace(/`(.*?)`/g, "$1")
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");

    // Indent and truncate
    if (inCodeBlock) {
      converted = "  " + converted;
    }

    lines.push(converted.slice(0, 40));
  }

  return {
    number: pageNum,
    title,
    category: "knowledge",
    source: "knowledge",
    content: formatContent(lines),
    links: [{ page: 100, label: "Index" }],
  };
}

/**
 * Clear page cache
 */
export function clearCache(): void {
  pageCache.clear();
}
