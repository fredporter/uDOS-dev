import { writable } from 'svelte/store';
import { invoke } from '@tauri-apps/api/core';

export type ThemeMode = 'light' | 'dark' | 'auto';

interface ThemeState {
  mode: ThemeMode;
  isDark: boolean;
}

const THEME_STORAGE_KEY = 'umarkdown-theme-preference';

// Get system preference
function getSystemPreference(): boolean {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  return true; // Default to dark
}

// Load saved preference
function loadThemePreference(): ThemeMode {
  if (typeof localStorage !== 'undefined') {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    if (saved === 'light' || saved === 'dark' || saved === 'auto') {
      return saved;
    }
  }
  return 'dark'; // Default to dark mode
}

// Calculate effective dark mode state
function calculateDarkMode(mode: ThemeMode): boolean {
  if (mode === 'auto') {
    return getSystemPreference();
  }
  return mode === 'dark';
}

// Create the theme store
function createThemeStore() {
  const initialMode = loadThemePreference();
  const initialIsDark = calculateDarkMode(initialMode);

  const { subscribe, set, update } = writable<ThemeState>({
    mode: initialMode,
    isDark: initialIsDark,
  });

  // Listen to system preference changes
  if (typeof window !== 'undefined' && window.matchMedia) {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', (e) => {
      update((state) => {
        if (state.mode === 'auto') {
          return { ...state, isDark: e.matches };
        }
        return state;
      });
    });
  }

  return {
    subscribe,

    // Set theme mode (light, dark, or auto)
    setMode: (mode: ThemeMode) => {
      const isDark = calculateDarkMode(mode);
      set({ mode, isDark });

      // Persist preference
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(THEME_STORAGE_KEY, mode);
      }

      // Update document class
      if (typeof document !== 'undefined') {
        if (isDark) {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      }
    },

    // Toggle between light and dark (stays in manual mode)
    toggle: () => {
      update((state) => {
        const newMode: ThemeMode = state.isDark ? 'light' : 'dark';
        const newIsDark = !state.isDark;

        // Persist preference
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem(THEME_STORAGE_KEY, newMode);
        }

        // Update document class
        if (typeof document !== 'undefined') {
          if (newIsDark) {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }
        }

        return { mode: newMode, isDark: newIsDark };
      });
    },

    // Initialize theme on app start
    initialize: () => {
      update((state) => {
        // Apply initial theme to document
        if (typeof document !== 'undefined') {
          if (state.isDark) {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }
        }
        return state;
      });
    },
  };
}

export const themeStore = createThemeStore();
