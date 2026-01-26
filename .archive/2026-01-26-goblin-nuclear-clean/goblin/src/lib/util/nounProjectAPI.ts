/**
 * Noun Project API Integration
 *
 * Search and download icons from The Noun Project
 * Requires API key: https://thenounproject.com/developers/
 */

import type { IconData } from "./emojiLibrary";

interface NounProjectConfig {
  apiKey: string;
  apiSecret: string;
}

interface NounProjectIcon {
  id: number;
  term: string;
  preview_url: string;
  thumbnail_url: string;
  attribution: string;
  uploader: {
    name: string;
  };
}

interface NounProjectResponse {
  icons: NounProjectIcon[];
}

/**
 * Noun Project API client
 */
export class NounProjectAPI {
  private config: NounProjectConfig | null = null;
  private baseURL = "https://api.thenounproject.com/v2";

  /**
   * Configure API credentials
   */
  setConfig(apiKey: string, apiSecret: string) {
    this.config = { apiKey, apiSecret };
  }

  /**
   * Check if API is configured
   */
  isConfigured(): boolean {
    return this.config !== null;
  }

  /**
   * Search for icons
   */
  async search(query: string, limit: number = 20): Promise<NounProjectIcon[]> {
    if (!this.config) {
      throw new Error("Noun Project API not configured");
    }

    try {
      const url = `${this.baseURL}/icon?query=${encodeURIComponent(query)}&limit=${limit}`;
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${this.config.apiKey}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const data: NounProjectResponse = await response.json();
      return data.icons || [];
    } catch (error) {
      console.error("Noun Project API error:", error);
      throw error;
    }
  }

  /**
   * Download icon SVG
   */
  async downloadIcon(iconId: number): Promise<string> {
    if (!this.config) {
      throw new Error("Noun Project API not configured");
    }

    try {
      const url = `${this.baseURL}/icon/${iconId}`;
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${this.config.apiKey}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const data = await response.json();
      return data.icon.icon_url; // URL to SVG
    } catch (error) {
      console.error("Noun Project download error:", error);
      throw error;
    }
  }

  /**
   * Fetch SVG content
   */
  async fetchSVG(url: string): Promise<string> {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to fetch SVG: ${response.status}`);
      }
      return await response.text();
    } catch (error) {
      console.error("SVG fetch error:", error);
      throw error;
    }
  }

  /**
   * Import icon to library
   */
  async importIcon(
    nounIcon: NounProjectIcon,
    svgURL: string
  ): Promise<IconData> {
    const svg = await this.fetchSVG(svgURL);

    const icon: IconData = {
      id: `noun-${nounIcon.id}`,
      name: nounIcon.term,
      tags: [nounIcon.term],
      svg,
      source: "nounproject",
      attribution: `${nounIcon.term} by ${nounIcon.uploader.name} from The Noun Project`,
      mono: true, // Noun Project icons are typically monochrome
    };

    return icon;
  }
}

export const nounProjectAPI = new NounProjectAPI();

/**
 * Load API config from storage
 */
export async function loadNounProjectConfig(): Promise<void> {
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    const configPath = "../memory/data/state/nounproject-config.json";
    const json = await invoke<string>("read_file", { path: configPath });
    const config = JSON.parse(json);

    if (config.apiKey && config.apiSecret) {
      nounProjectAPI.setConfig(config.apiKey, config.apiSecret);
    }
  } catch (error) {
    console.warn("No Noun Project config found");
  }
}

/**
 * Save API config to storage
 */
export async function saveNounProjectConfig(
  apiKey: string,
  apiSecret: string
): Promise<void> {
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    const configPath = "../memory/data/state/nounproject-config.json";
    const config = { apiKey, apiSecret };
    await invoke("write_file", {
      path: configPath,
      contents: JSON.stringify(config, null, 2),
    });
    nounProjectAPI.setConfig(apiKey, apiSecret);
  } catch (error) {
    throw new Error(`Failed to save config: ${error}`);
  }
}
