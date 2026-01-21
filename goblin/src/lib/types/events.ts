/**
 * Event Type Definitions for uDOS
 *
 * Defines all application events with their payload types.
 * Used by the event bus for type-safe event management.
 */

import type { FontFamily, MonoVariant } from "./fonts";

/**
 * File operation events
 */
export interface FileOpenedEvent {
  path: string;
  content: string;
  mode?: string;
}

export interface FileSavedEvent {
  path: string;
  success: boolean;
}

/**
 * UI state change events
 */
export interface SidebarToggledEvent {
  mode: string;
  isOpen: boolean;
}

export interface DarkModeChangedEvent {
  darkMode: boolean;
  mode?: string;
}

/**
 * Font change events
 */
export interface FontChangedEvent {
  fontType: "heading" | "body" | "mono";
  font: FontFamily | MonoVariant;
  mode?: string;
}

export interface StyleChangedEvent {
  type: "font" | "theme" | "size";
  value: string | number | boolean;
}

/**
 * Grid and display events
 */
export interface GridSettingsChangedEvent {
  cols?: number;
  rows?: number;
  cellSize?: number;
  preset?: string;
}

/**
 * System events
 */
export interface ThemeChangedEvent {
  theme: "light" | "dark";
}

export interface ModeChangedEvent {
  from: string;
  to: string;
}

/**
 * Complete event map
 * Maps event names to their payload types
 */
export interface AppEventMap {
  // File events
  "file-opened": FileOpenedEvent;
  "file-saved": FileSavedEvent;

  // UI events
  "sidebar-toggled": SidebarToggledEvent;
  "sidebar-state-changed": { open: boolean };
  "toggle-sidebar-request": void;
  "toggle-sidebar": { open: boolean };
  "dark-mode-changed": DarkModeChangedEvent;

  // Font events
  "font-changed": FontChangedEvent;
  "heading-font-changed": { font: FontFamily };
  "body-font-changed": { font: FontFamily };
  "mono-font-changed": { variant: MonoVariant };
  "udos-style-changed": StyleChangedEvent;

  // Grid events
  "grid-settings-changed": GridSettingsChangedEvent;

  // System events
  "theme-changed": ThemeChangedEvent;
  "mode-changed": ModeChangedEvent;

  // Custom component events
  "flyin-open-file": void;
  "sketch-insert": { markdown: string };
}

/**
 * Extract event names as a union type
 */
export type AppEventName = keyof AppEventMap;

/**
 * Get the payload type for a specific event
 */
export type AppEventPayload<T extends AppEventName> = AppEventMap[T];
