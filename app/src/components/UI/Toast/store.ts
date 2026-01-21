import { writable } from "svelte/store";
import type { Toast } from "./types";

export const MAX_TOASTS = 10;
const AUTO_DISMISS_DURATION = 7000; // 7 seconds for better visibility
const ERROR_DURATION = 0; // Errors don't auto-dismiss

// Create the writable toast store
function createToastStore() {
  const { subscribe, set, update } = writable<Toast[]>([]);
  let toastId = 0;

  return {
    subscribe,

    // Add a new toast to the queue (prevent exact duplicates)
    add: (toast: Omit<Toast, "id">) => {
      const id = ++toastId;
      const newToast: Toast = {
        id,
        ...toast,
        duration:
          toast.duration ??
          (toast.type === "error" ? ERROR_DURATION : AUTO_DISMISS_DURATION),
      };

      update((toasts) => {
        // Prevent duplicate toasts with same type, title, and message
        const isDuplicate = toasts.some(
          (t) =>
            t.type === newToast.type &&
            t.title === newToast.title &&
            t.message === newToast.message,
        );
        if (isDuplicate) return toasts;
        // Remove oldest toast if at max capacity
        if (toasts.length >= MAX_TOASTS) {
          return [...toasts.slice(1), newToast];
        }
        return [...toasts, newToast];
      });

      return id;
    },

    // Remove a toast by ID
    remove: (id: number) => {
      update((toasts) => toasts.filter((t) => t.id !== id));
    },

    // Clear all toasts
    clear: () => {
      set([]);
    },

    // Convenience methods
    info: (title: string, message?: string) => {
      const id = ++toastId;
      update((toasts) => [
        ...toasts.slice(Math.max(0, toasts.length - (MAX_TOASTS - 1))),
        { id, type: "info", title, message, duration: AUTO_DISMISS_DURATION },
      ]);
      return id;
    },

    success: (title: string, message?: string) => {
      const id = ++toastId;
      update((toasts) => [
        ...toasts.slice(Math.max(0, toasts.length - (MAX_TOASTS - 1))),
        {
          id,
          type: "success",
          title,
          message,
          duration: AUTO_DISMISS_DURATION,
        },
      ]);
      return id;
    },

    warning: (title: string, message?: string) => {
      const id = ++toastId;
      update((toasts) => [
        ...toasts.slice(Math.max(0, toasts.length - (MAX_TOASTS - 1))),
        {
          id,
          type: "warning",
          title,
          message,
          duration: AUTO_DISMISS_DURATION,
        },
      ]);
      return id;
    },

    error: (title: string, message?: string) => {
      const id = ++toastId;
      update((toasts) => [
        ...toasts.slice(Math.max(0, toasts.length - (MAX_TOASTS - 1))),
        { id, type: "error", title, message, duration: ERROR_DURATION },
      ]);
      return id;
    },

    // File operation callbacks
    onFileOpen: (filename: string) => {
      const id = ++toastId;
      update((toasts) => [
        ...toasts.slice(Math.max(0, toasts.length - (MAX_TOASTS - 1))),
        {
          id,
          type: "info",
          title: "Opening...",
          message: filename,
          duration: 2000,
        },
      ]);
      return id;
    },

    onFileOpenSuccess: (filename: string) => {
      const id = ++toastId;
      update((toasts) => [
        ...toasts.slice(Math.max(0, toasts.length - (MAX_TOASTS - 1))),
        {
          id,
          type: "success",
          title: "✅ Opened",
          message: filename,
          duration: AUTO_DISMISS_DURATION,
        },
      ]);
      return id;
    },

    onFileSave: (filename: string) => {
      const id = ++toastId;
      update((toasts) => [
        ...toasts.slice(Math.max(0, toasts.length - (MAX_TOASTS - 1))),
        {
          id,
          type: "info",
          title: "Saving...",
          message: filename,
          duration: 2000,
        },
      ]);
      return id;
    },

    onFileSaveSuccess: (filename: string) => {
      const id = ++toastId;
      update((toasts) => [
        ...toasts.slice(Math.max(0, toasts.length - (MAX_TOASTS - 1))),
        {
          id,
          type: "success",
          title: "✅ Saved",
          message: filename,
          duration: AUTO_DISMISS_DURATION,
        },
      ]);
      return id;
    },

    onFormatApply: (format: string) => {
      const id = ++toastId;
      update((toasts) => [
        ...toasts.slice(Math.max(0, toasts.length - (MAX_TOASTS - 1))),
        {
          id,
          type: "info",
          title: "Formatting...",
          message: `Applied ${format}`,
          duration: 2000,
        },
      ]);
      return id;
    },

    onFormatApplySuccess: (format: string) => {
      const id = ++toastId;
      update((toasts) => [
        ...toasts.slice(Math.max(0, toasts.length - (MAX_TOASTS - 1))),
        {
          id,
          type: "success",
          title: "✅ Formatted",
          message: `${format} applied`,
          duration: AUTO_DISMISS_DURATION,
        },
      ]);
      return id;
    },

    onFullscreen: (entering: boolean) => {
      const id = ++toastId;
      update((toasts) => [
        ...toasts.slice(Math.max(0, toasts.length - (MAX_TOASTS - 1))),
        {
          id,
          type: "info",
          title: entering ? "🖥️ Fullscreen" : "📱 Windowed",
          message: entering ? "Press ESC to exit" : "Fullscreen exited",
          duration: 2000,
        },
      ]);
      return id;
    },

    onError: (title: string, message?: string) => {
      const id = ++toastId;
      update((toasts) => [
        ...toasts.slice(Math.max(0, toasts.length - (MAX_TOASTS - 1))),
        {
          id,
          type: "error",
          title: `❌ ${title}`,
          message,
          duration: ERROR_DURATION,
        },
      ]);
      return id;
    },
  };
}

// Export singleton store
export const toasts = createToastStore();
