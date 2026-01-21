/**
 * Demo Content Generator for Grid Mode
 * Generates teletext, columns, and news-style layouts
 */

export type FontType = "body" | "title" | "heading" | "heading-double" | "alt-heading";
export type LineColor =
  | "green"
  | "cyan"
  | "orange"
  | "yellow"
  | "red"
  | "white";

export interface DemoLine {
  text: string;
  font?: FontType;
  color?: LineColor | string; // Allow both specific colors and custom strings
}

export interface DemoContent {
  title: string;
  lines: DemoLine[];
  colors?: string[];
}

// Teletext block graphics characters
const BLOCKS = {
  full: "█",
  dark: "▓",
  medium: "▒",
  light: "░",
  top: "▀",
  bottom: "▄",
  left: "▌",
  right: "▐",
  h: "─",
  v: "│",
  corner_tl: "┌",
  corner_tr: "┐",
  corner_bl: "└",
  corner_br: "┘",
  t_up: "┴",
  t_down: "┬",
  t_left: "┤",
  t_right: "├",
  cross: "┼",
};

/**
 * Generate a simple box border
 */
export function makeBorder(width: number, height: number): string[] {
  const lines: string[] = [];

  // Top border
  lines.push(
    BLOCKS.corner_tl +
      BLOCKS.h.repeat(Math.max(0, width - 2)) +
      BLOCKS.corner_tr
  );

  // Middle rows
  for (let i = 0; i < Math.max(0, height - 2); i++) {
    lines.push(BLOCKS.v + " ".repeat(Math.max(0, width - 2)) + BLOCKS.v);
  }

  // Bottom border
  if (height > 1) {
    lines.push(
      BLOCKS.corner_bl +
        BLOCKS.h.repeat(Math.max(0, width - 2)) +
        BLOCKS.corner_br
    );
  }

  return lines;
}

/**
 * Teletext style demo with bar chart and info
 */
export function generateTeletextDemo(cols: number, rows: number): DemoContent {
  const lines: DemoLine[] = [];

  // Header
  lines.push({
    text: "┌" + "─".repeat(Math.max(0, cols - 2)) + "┐",
    font: "body",
  });
  lines.push({
    text: "│ TELETEXT DEMO - BBC News Format       ".padEnd(cols - 1) + "│",
    font: "heading",
  });
  lines.push({
    text: "├" + "─".repeat(Math.max(0, cols - 2)) + "┤",
    font: "body",
  });

  // News headline
  lines.push({
    text: "│ BREAKING: Grid Mode Now Active!       ".padEnd(cols - 1) + "│",
    font: "title",
  });
  lines.push({
    text: "│ The display system is fully operational ".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text: "├" + "─".repeat(Math.max(0, cols - 2)) + "┤",
    font: "body",
  });

  // Chart section
  lines.push({
    text: "│ System Status Chart:                  ".padEnd(cols - 1) + "│",
    font: "heading",
  });
  lines.push({
    text: "│ CPU    ███████░░░░░░░░░░░░░░░░░░░░░░ 35% │".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text:
      "│ Memory ████████████░░░░░░░░░░░░░░░░░░ 52% │".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text:
      "│ Disk   ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 08% │".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text: "├" + "─".repeat(Math.max(0, cols - 2)) + "┤",
    font: "body",
  });

  // Grid info
  lines.push({
    text:
      `│ Grid: ${cols}×${rows} cells | Font: Teletext50 24×24px         │`.padEnd(
        cols - 1
      ) + "│",
    font: "body",
  });
  lines.push({
    text: "└" + "─".repeat(Math.max(0, cols - 2)) + "┘",
    font: "body",
  });

  // Pad to fill rows
  while (lines.length < rows) {
    lines.push({ text: "".padEnd(cols), font: "body" });
  }

  return {
    title: "Teletext Demo",
    lines: lines.slice(0, rows),
  };
}

/**
 * Columns layout demo
 */
export function generateColumnsDemo(cols: number, rows: number): DemoContent {
  const lines: DemoLine[] = [];
  const colWidth = Math.floor((cols - 4) / 3);

  // Header
  lines.push({ text: "═".repeat(cols), font: "body" });
  lines.push({
    text: "  THREE COLUMN LAYOUT - News & Information".padEnd(cols),
    font: "heading",
  });
  lines.push({ text: "═".repeat(cols), font: "body" });

  // Column headers
  const header =
    "  " +
    "Col 1".padEnd(colWidth) +
    "  Col 2".padEnd(colWidth) +
    "  Col 3".padEnd(colWidth);
  lines.push({ text: header.padEnd(cols), font: "title" });
  lines.push({
    text:
      "  " +
      "─".repeat(colWidth) +
      "  " +
      "─".repeat(colWidth) +
      "  " +
      "─".repeat(colWidth),
    font: "body",
  });

  // Content rows
  const contentLines = [
    "Top story   Breaking news  Special report",
    "━━━━━━━━━  ━━━━━━━━━━━━  ━━━━━━━━━━━━",
    "Lorem ipsum Dolor sit      Amet consectetur",
    "text here.  amet text here consectetur here",
    "Another ln  Another line   Another line txt",
    "",
    "Secondary  Secondary info Secondary update",
    "info item  item described item described",
    "Details on Details on     Details on topics",
    "various tp selected topic selected topics",
  ];

  for (const contentLine of contentLines) {
    if (lines.length < rows - 2) {
      lines.push({ text: ("  " + contentLine).padEnd(cols), font: "body" });
    }
  }

  // Footer
  lines.push({ text: "═".repeat(cols), font: "body" });

  // Pad to fill rows
  while (lines.length < rows) {
    lines.push({ text: "".padEnd(cols), font: "body" });
  }

  return {
    title: "Columns Demo",
    lines: lines.slice(0, rows),
  };
}

/**
 * News-style teledesk layout with blocks
 */
export function generateNewsDemo(cols: number, rows: number): DemoContent {
  const lines: DemoLine[] = [];

  // Main header with blocks
  lines.push({ text: "█".repeat(cols), font: "body" });
  lines.push({
    text: "█ TELEDESK NEWS NETWORK - GRID MODE DEMO".padEnd(cols - 1) + "█",
    font: "heading",
  });
  lines.push({ text: "█".repeat(cols), font: "body" });

  // Main headline section
  lines.push({
    text: "│ HEADLINE: Grid Mode Operational".padEnd(cols - 1) + "│",
    font: "title",
  });
  lines.push({
    text:
      "│ The new unified grid display is working perfectly.".padEnd(cols - 1) +
      "│",
    font: "body",
  });
  lines.push({
    text: "├" + "─".repeat(Math.max(0, cols - 2)) + "┤",
    font: "body",
  });

  // Left column
  lines.push({
    text: "│ Story A: Item 1       │ Story D: Topic A      │",
    font: "body",
  });
  lines.push({
    text: "│ ─────────────────     │ ─────────────────────│",
    font: "body",
  });
  lines.push({
    text: "│ Details about story   │ Details about topic │",
    font: "body",
  });
  lines.push({
    text: "│ in left column area   │ in right column area│",
    font: "body",
  });
  lines.push({
    text: "├──────────────────────┼─────────────────────┤",
    font: "body",
  });
  lines.push({
    text: "│ Story B: Item 2       │ Story E: Topic B      │",
    font: "body",
  });
  lines.push({
    text: "│ ─────────────────     │ ─────────────────────│",
    font: "body",
  });
  lines.push({
    text: "│ More detailed text    │ Additional informatio│",
    font: "body",
  });
  lines.push({
    text: "│ for the left side     │ for the right area  │",
    font: "body",
  });
  lines.push({
    text: "├──────────────────────┼─────────────────────┤",
    font: "body",
  });
  lines.push({
    text: "│ Story C: Item 3       │ Status: Live          │",
    font: "body",
  });
  lines.push({
    text: "│ ─────────────────     │ ─────────────────────│",
    font: "body",
  });
  lines.push({
    text: "│ Final story content   │ ▓▓▓▓▓▓▓▓▓▓ 100%      │",
    font: "body",
  });
  lines.push({
    text: "└──────────────────────┴─────────────────────┘",
    font: "body",
  });

  // Pad to fill rows
  while (lines.length < rows) {
    lines.push({ text: "".padEnd(cols), font: "body" });
  }

  return {
    title: "News Demo",
    lines: lines.slice(0, rows),
  };
}

/**
 * System boot demo with animated text
 */
export function generateBootDemo(cols: number, rows: number): DemoContent {
  const lines: DemoLine[] = [];

  lines.push({
    text: "┌" + "─".repeat(Math.max(0, cols - 2)) + "┐",
    font: "body",
  });
  lines.push({
    text: "│ uDOS 2.0 GRID MODE BOOT SEQUENCE      ".padEnd(cols - 1) + "│",
    font: "heading",
  });
  lines.push({
    text: "├" + "─".repeat(Math.max(0, cols - 2)) + "┤",
    font: "body",
  });

  lines.push({
    text: "│ > Initializing grid display system...".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text: "│ > Loading Teletext50 font (24×24)...  ".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text: "│ > Loading PetMe64 font (48×48)...    ".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text: "│ > Loading PressStart font (24×24)... ".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text: "│ > Initializing color palette...      ".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text: "│ > Setting up viewport border toggle. ".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text: "│                                       ".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text: "│ ✓ System Ready                        ".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text: "│                                       ".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text: "│ Welcome to Grid Mode! Press any key... ".padEnd(cols - 1) + "│",
    font: "body",
  });
  lines.push({
    text: "└" + "─".repeat(Math.max(0, cols - 2)) + "┘",
    font: "body",
  });

  // Pad to fill rows
  while (lines.length < rows) {
    lines.push({ text: "".padEnd(cols), font: "body" });
  }

  return {
    title: "Boot Demo",
    lines: lines.slice(0, rows),
  };
}

/**
 * Combine multiple demos into a single content block
 */
export function generateStartupSequence(
  cols: number,
  rows: number
): DemoLine[] {
  const demos = [
    generateBootDemo(cols, rows),
    generateTeletextDemo(cols, rows),
    generateColumnsDemo(cols, rows),
    generateNewsDemo(cols, rows),
  ];

  const allLines: DemoLine[] = [];

  for (const demo of demos) {
    allLines.push(...demo.lines);
    allLines.push({ text: "", font: "body" }); // Separator
  }

  return allLines.slice(0, rows);
}
