/**
 * Style Manager - Centralized style control for uDOS
 *
 * Single source of truth for:
 * - Font families (heading, body, mono)
 * - Dark/light mode
 * - Font size (zoom)
 * - CSS variable application
 *
 * All components should use this manager, not apply styles directly.
 */

import type { FontFamily, MonoVariant } from "../types/fonts";
import { FONT_CSS, MONO_VARIANT_CSS } from "../util/fontConfig";

interface StyleState {
  headingFont: FontFamily;
  bodyFont: FontFamily;
  monoVariant: MonoVariant;
  fontSize: number;
  darkMode: boolean;
}

// Default state
const DEFAULT_STATE: StyleState = {
  headingFont: "sans",
  bodyFont: "sans",
  monoVariant: "jetbrains",
  fontSize: 20,
  darkMode: true,
};

// Current state (singleton)
let currentState: StyleState = { ...DEFAULT_STATE };
let initialized = false;

/**
 * Initialize the style manager
 * Loads saved preferences and applies them
 */
export function initStyleManager(): StyleState {
  if (initialized) return currentState;

  // DO NOT load from global localStorage - mode-specific state is managed by ModeState
  // Just use defaults and let the layout restore mode-specific settings
  currentState = { ...DEFAULT_STATE };

  // Apply all styles immediately
  applyAllStyles();
  initialized = true;

  return currentState;
}

/**
 * Get current style state
 */
export function getStyleState(): StyleState {
  if (!initialized) initStyleManager();
  return { ...currentState };
}

/**
 * Set heading font family
 */
export function setHeadingFont(font: FontFamily, skipSave = false) {
  if (!initialized) initStyleManager();
  currentState.headingFont = font;
  console.log("[StyleManager] Setting heading font:", font, FONT_CSS[font]);
  applyHeadingFont();
  if (!skipSave) savePreferences();
}

/**
 * Set body font family
 */
export function setBodyFont(font: FontFamily, skipSave = false) {
  if (!initialized) initStyleManager();
  currentState.bodyFont = font;
  console.log("[StyleManager] Setting body font:", font, FONT_CSS[font]);
  applyBodyFont();
  if (!skipSave) savePreferences();
}

/**
 * Set font size (zoom)
 */
export function setFontSize(size: number, skipSave = false) {
  currentState.fontSize = Math.max(10, Math.min(32, size));
  console.log(
    "[StyleManager] Setting font size:",
    currentState.fontSize + "px"
  );
  applyFontSize();
  if (!skipSave) savePreferences();
}

/**
 * Increase font size
 */
export function zoomIn() {
  setFontSize(currentState.fontSize + 2);
}

/**
 * Decrease font size
 */
export function zoomOut() {
  setFontSize(currentState.fontSize - 2);
}

/**
 * Toggle dark mode
 */
export function toggleDarkMode(): boolean {
  currentState.darkMode = !currentState.darkMode;
  applyDarkMode();
  savePreferences();
  return currentState.darkMode;
}

/**
 * Set dark mode explicitly
 */
export function setDarkMode(enabled: boolean, skipSave = false) {
  currentState.darkMode = enabled;
  applyDarkMode();
  if (!skipSave) savePreferences();
}

/**
 * Cycle through font families
 * H selections: Inter, Merriweather, Libre Baskerville, VAG Primer, JetBrains Mono, SF Mono, ChicagoFLF, Sanfrisco, Playfair Display, UnifrakturCook, UnifrakturMaguntia, Great Vibes
 */
export function cycleHeadingFont(): FontFamily {
  const fonts: FontFamily[] = [
    "sans",
    "serif",
    "librebaskerville",
    "vag",
    "mono",
    "sfmono",
    "chicagoflf",
    "sanfrisco",
    "playfair",
    "unifraktur",
    "unifrakturmaguntia",
    "greatvibes",
  ];
  const idx = fonts.indexOf(currentState.headingFont);
  const next = fonts[(idx + 1) % fonts.length];
  setHeadingFont(next);
  return next;
}

/**
 * Cycle through body fonts
 * B selections: Inter, Merriweather, Libre Baskerville, VAG Primer, JetBrains Mono, SF Mono, ChicagoFLF, Los Altos, Monaco, Playfair Display
 */
export function cycleBodyFont(): FontFamily {
  const fonts: FontFamily[] = [
    "sans",
    "serif",
    "librebaskerville",
    "vag",
    "mono",
    "sfmono",
    "chicagoflf",
    "losaltos",
    "monaco",
    "playfair",
  ];
  const idx = fonts.indexOf(currentState.bodyFont);
  const next = fonts[(idx + 1) % fonts.length];
  setBodyFont(next);
  return next;
}

/**
 * Set monospace variant
 */
export function setMonoVariant(variant: MonoVariant, skipSave = false) {
  if (!initialized) initStyleManager();
  currentState.monoVariant = variant;
  console.log(
    "[StyleManager] Setting mono variant:",
    variant,
    MONO_VARIANT_CSS[variant]
  );
  applyMonoVariant();
  if (!skipSave) savePreferences();
}

/**
 * Cycle through monospace variants
 *
 * Primary Tailwind code font: JetBrains Mono
 * Additional variants for Pixel Editor: Monaco, Teletext50, PetMe64, PressStart2P
 * Note: SF Mono removed from M button (now in H/B buttons)
 */
export function cycleMonoVariant(mode?: string): MonoVariant {
  const variants: MonoVariant[] = [
    "jetbrains",
    "monaco",
    "teletext",
    "c64",
    "pressstart",
  ];
  const idx = variants.indexOf(currentState.monoVariant);
  const next = variants[(idx + 1) % variants.length];
  setMonoVariant(next);
  return next;
}

// === Internal Application Functions ===

function applyHeadingFont() {
  if (typeof document === "undefined") return;
  const fontValue = FONT_CSS[currentState.headingFont];
  console.log("[StyleManager] Applying heading font to DOM:", fontValue);
  document.documentElement.style.setProperty("--font-heading", fontValue);
  // Set data attribute for font-specific styling (e.g., disabling bold)
  document.documentElement.setAttribute(
    "data-heading-font",
    currentState.headingFont
  );
  // Force reflow to ensure CSS variable takes effect
  void document.documentElement.offsetHeight;
}

function applyBodyFont() {
  if (typeof document === "undefined") return;
  const fontValue = FONT_CSS[currentState.bodyFont];
  console.log("[StyleManager] Applying body font to DOM:", fontValue);
  document.documentElement.style.setProperty("--font-body", fontValue);
  // Force reflow to ensure CSS variable takes effect
  void document.documentElement.offsetHeight;
}

function applyMonoVariant() {
  if (typeof document === "undefined") return;
  const fontValue = MONO_VARIANT_CSS[currentState.monoVariant];
  console.log("[StyleManager] Applying mono variant to DOM:", fontValue);
  document.documentElement.style.setProperty("--font-mono-variant", fontValue);
  // Set data attribute for font-specific styling (e.g., Teletext50 spacing)
  document.documentElement.setAttribute(
    "data-mono-variant",
    currentState.monoVariant
  );
  // Force reflow to ensure CSS variable takes effect
  void document.documentElement.offsetHeight;
}

function applyFontSize() {
  if (typeof document === "undefined") return;
  const size = `${currentState.fontSize}px`;
  console.log("[StyleManager] Applying font size to DOM:", size);
  document.documentElement.style.setProperty("--content-font-size", size);
  document.documentElement.style.fontSize = size;

  // Calculate zoom scale for menu bar (base size is 20px)
  const zoomScale = currentState.fontSize / 20;
  document.documentElement.style.setProperty(
    "--zoom-scale",
    zoomScale.toString()
  );
}

function applyDarkMode() {
  if (typeof document === "undefined") return;
  if (currentState.darkMode) {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }
}

function applyAllStyles() {
  applyHeadingFont();
  applyBodyFont();
  applyMonoVariant();
  applyFontSize();
  applyDarkMode();
}

/**
 * Apply all current styles (exported for mode switching)
 */
export function applyStyles() {
  applyAllStyles();
}

function savePreferences() {
  // Emit event to trigger mode-specific save in layout
  // Layout will handle saving to the correct mode via ModeState manager
  if (typeof window !== "undefined" && window.dispatchEvent) {
    window.dispatchEvent(
      new CustomEvent("udos-style-changed", {
        detail: { ...currentState },
      })
    );
  }
}

// === Export utility functions ===

/**
 * Get human-readable font name
 */
export function getFontName(font: FontFamily): string {
  const names = {
    sans: "Inter",
    serif: "Merriweather",
    mono: "JetBrains",
    sfmono: "SF Mono",
    chicagoflf: "Chicago",
    losaltos: "Los Altos",
    monaco: "Monaco",
    sanfrisco: "Sanfrisco",
    playfair: "Playfair",
    unifraktur: "Unifraktur",
    unifrakturmaguntia: "UnifrakturMaguntia",
    vag: "VAG Primer",
    librebaskerville: "Libre Baskerville",
    greatvibes: "Great Vibes",
  };
  return names[font];
}

/**
 * Get human-readable mono variant name
 */
export function getMonoVariantName(variant: MonoVariant): string {
  const names: Record<MonoVariant, string> = {
    jetbrains: "JetBrains",
    pressstart: "PressStart",
    c64: "C64",
    teletext: "Teletext",
    monaco: "Monaco",
  };
  return names[variant];
}

/**
 * Get font CSS value
 */
export function getFontValue(font: FontFamily): string {
  return FONT_CSS[font];
}
