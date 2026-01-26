/**
 * User Configuration Store for uDOS Tauri App v1.0.0.43+
 *
 * Svelte store that syncs user config with uDOS API server.
 * Single source of truth via UserConfigManager on backend.
 *
 * Usage:
 *   import { userConfig, loadUserConfig, updateUserConfig } from '$lib/stores/user';
 *
 *   // Load on app start
 *   await loadUserConfig();
 *
 *   // Read reactively
 *   $: username = $userConfig?.user_profile?.username;
 *
 *   // Update (deep merge)
 *   await updateUserConfig({ user_profile: { preferred_mode: 'advanced' } });
 */

import { writable, derived, type Writable } from 'svelte/store';
import { apiRequest, isApiAvailable } from './api';

/** User profile section */
export interface UserProfile {
  username: string;
  timezone: string;
  password_hash: string;
  preferred_mode: 'standard' | 'minimal' | 'advanced';
}

/** Project section */
export interface Project {
  name: string;
  description: string;
  start_date: string;
}

/** Location data section */
export interface LocationData {
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  tile_code: string;
  map_position: { x: number; y: number };
  current_layer: string;
}

/** Spatial data section */
export interface SpatialData {
  planet: string;
  planet_id: string;
  galaxy: string;
  galaxy_id: string;
}

/** Session data section */
export interface SessionData {
  current_session: string;
  session_count: number;
  last_login: string;
  viewport: Record<string, unknown>;
}

/** System settings section */
export interface SystemSettings {
  interface: {
    theme: string;
    show_hints: boolean;
    animation_speed: 'slow' | 'normal' | 'fast';
  };
  workspace_preference: string;
  auto_save: boolean;
  backup_on_edit: boolean;
}

/** Full user config matching core/config/user_schema.json */
export interface UserConfig {
  version: string;
  user_profile: UserProfile;
  project: Project;
  location_data: LocationData;
  spatial_data: SpatialData;
  session_data: SessionData;
  system_settings: SystemSettings;
}

/** Store state */
interface UserStoreState {
  config: UserConfig | null;
  loading: boolean;
  error: string | null;
  apiAvailable: boolean;
}

/** Initial state */
const initialState: UserStoreState = {
  config: null,
  loading: false,
  error: null,
  apiAvailable: false,
};

/** Main user store */
const store: Writable<UserStoreState> = writable(initialState);

/** Derived store for just the config */
export const userConfig = derived(store, ($s) => $s.config);

/** Derived store for loading state */
export const userLoading = derived(store, ($s) => $s.loading);

/** Derived store for error state */
export const userError = derived(store, ($s) => $s.error);

/** Derived store for API availability */
export const apiOnline = derived(store, ($s) => $s.apiAvailable);

/**
 * Load user config from API server.
 * Call this on app initialization.
 */
export async function loadUserConfig(): Promise<boolean> {
  store.update((s) => ({ ...s, loading: true, error: null }));

  // Check API availability
  const available = await isApiAvailable();
  if (!available) {
    store.update((s) => ({
      ...s,
      loading: false,
      apiAvailable: false,
      error: 'API server not available',
    }));
    return false;
  }

  // Fetch config
  const response = await apiRequest<{ config: UserConfig }>('/api/user/config');

  if (response.success && response.data) {
    store.update((s) => ({
      ...s,
      config: response.data!.config,
      loading: false,
      apiAvailable: true,
      error: null,
    }));
    return true;
  } else {
    store.update((s) => ({
      ...s,
      loading: false,
      apiAvailable: true,
      error: response.error || 'Failed to load config',
    }));
    return false;
  }
}

/**
 * Update user config (deep merge).
 *
 * @param updates - Partial config updates to apply
 * @returns Promise<boolean> - true if successful
 */
export async function updateUserConfig(
  updates: Partial<UserConfig>
): Promise<boolean> {
  store.update((s) => ({ ...s, loading: true, error: null }));

  const response = await apiRequest<void>('/api/user/config', {
    method: 'PUT',
    body: updates,
  });

  if (response.success) {
    // Reload to get merged config
    await loadUserConfig();
    return true;
  } else {
    store.update((s) => ({
      ...s,
      loading: false,
      error: response.error || 'Failed to update config',
    }));
    return false;
  }
}

/**
 * Get specific config value by dot-notation key.
 *
 * @param key - Dot-notation path (e.g., 'user_profile.username')
 * @returns Config value or undefined
 */
export async function getConfigValue<T>(key: string): Promise<T | undefined> {
  const response = await apiRequest<{ value: T }>(`/api/user/config/${key}`);
  return response.success ? response.data?.value : undefined;
}

/**
 * Reset store to initial state.
 * Call on logout or disconnect.
 */
export function resetUserStore(): void {
  store.set(initialState);
}

/** Export the raw store for advanced usage */
export { store as userStore };
