/**
 * Clipboard Utilities
 * Centralized clipboard operations with fallback support
 */

import { toastStore } from "$lib/stores/toastStore";

/**
 * Copy text to clipboard with automatic fallback
 * Works across all browsers and Tauri contexts
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    // Try modern Clipboard API first
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    // Fallback to execCommand for older browsers or restricted contexts
    try {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      textarea.style.pointerEvents = "none";
      document.body.appendChild(textarea);
      textarea.select();
      const success = document.execCommand("copy");
      document.body.removeChild(textarea);
      return success;
    } catch (fallbackError) {
      console.error("Clipboard copy failed:", error, fallbackError);
      return false;
    }
  }
}

/**
 * Read text from clipboard
 * Note: Requires user permission
 */
export async function readFromClipboard(): Promise<string | null> {
  try {
    const text = await navigator.clipboard.readText();
    return text;
  } catch (error) {
    console.error("Clipboard read failed:", error);
    return null;
  }
}

/**
 * Copy text with user feedback via toast notification
 */
export async function copyWithFeedback(
  text: string,
  successMessage: string = "Copied to clipboard"
): Promise<void> {
  const success = await copyToClipboard(text);
  if (success) {
    toastStore.success(successMessage, 2000);
    console.info("📋 " + successMessage);
  } else {
    toastStore.error("Failed to copy to clipboard", 3000);
    console.error("❌ Failed to copy to clipboard");
  }
}
