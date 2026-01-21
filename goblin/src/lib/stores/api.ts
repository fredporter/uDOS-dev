/**
 * API Client for uDOS Tauri App v1.0.0.43+
 *
 * Provides typed HTTP client for communicating with uDOS API server.
 * Used by stores for data synchronization.
 */

/** API base URL - defaults to local development server */
const API_BASE = 'http://127.0.0.1:8765';

/** Generic API response type */
export interface ApiResponse<T> {
  ok: boolean;
  success?: boolean;
  error?: string;
  message?: string;
  data?: T;
}

/** HTTP request options */
interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
}

/**
 * Make an API request to the uDOS server.
 *
 * @param endpoint - API endpoint path (e.g., '/api/user/config')
 * @param options - Request options
 * @returns Promise with typed response
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<ApiResponse<T>> {
  const { method = 'GET', body, headers = {} } = options;

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        ok: false,
        success: false,
        error: data.error || `HTTP ${response.status}`,
      };
    }

    return { ok: true, success: true, data };
  } catch (error) {
    return {
      ok: false,
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
    };
  }
}

/**
 * Check if API server is available.
 *
 * @returns Promise<boolean> - true if server responds
 */
export async function isApiAvailable(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/api/system/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(2000),
    });
    return response.ok;
  } catch {
    return false;
  }
}
