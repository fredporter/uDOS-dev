import { writable } from 'svelte/store';

export interface NotificationData {
  id: number;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message?: string;
  duration?: number;
  timestamp: Date;
  dismissible?: boolean;
  action?: {
    label: string;
    callback: () => void;
  };
}

export interface NotificationHistory extends NotificationData {
  dismissed: boolean;
  dismissedAt?: Date;
}

const MAX_TOASTS = 5;
const MAX_HISTORY = 50;
const DEFAULT_DURATION = 5000; // 5 seconds
const ERROR_DURATION = 0; // Errors don't auto-dismiss

// Create notification store
function createNotificationStore() {
  const activeToasts = writable<NotificationData[]>([]);
  const history = writable<NotificationHistory[]>([]);
  const doNotDisturb = writable<boolean>(false);

  let notificationId = 0;

  return {
    active: { subscribe: activeToasts.subscribe },
    history: { subscribe: history.subscribe },
    doNotDisturb: { subscribe: doNotDisturb.subscribe },

    // Add notification
    add: (
      type: NotificationData['type'],
      title: string,
      message?: string,
      options?: {
        duration?: number;
        dismissible?: boolean;
        action?: { label: string; callback: () => void };
      },
    ): number => {
      const id = ++notificationId;
      const notification: NotificationData = {
        id,
        type,
        title,
        message,
        timestamp: new Date(),
        duration:
          options?.duration ??
          (type === 'error' ? ERROR_DURATION : DEFAULT_DURATION),
        dismissible: options?.dismissible !== false,
        action: options?.action,
      };

      // Add to active toasts (respecting DND mode for non-errors)
      doNotDisturb.subscribe((dnd) => {
        if (!dnd || type === 'error') {
          activeToasts.update((toasts) => {
            // Prevent duplicates
            const isDuplicate = toasts.some(
              (t) => t.type === type && t.title === title && t.message === message,
            );
            if (isDuplicate) return toasts;

            // Limit max toasts
            if (toasts.length >= MAX_TOASTS) {
              return [...toasts.slice(1), notification];
            }
            return [...toasts, notification];
          });
        }
      })();

      // Add to history
      history.update((h) => {
        const historyEntry: NotificationHistory = {
          ...notification,
          dismissed: false,
        };

        if (h.length >= MAX_HISTORY) {
          return [...h.slice(1), historyEntry];
        }
        return [...h, historyEntry];
      });

      return id;
    },

    // Convenience methods
    info: (title: string, message?: string, options?: any) =>
      createNotificationStore().add('info', title, message, options),
    success: (title: string, message?: string, options?: any) =>
      createNotificationStore().add('success', title, message, options),
    warning: (title: string, message?: string, options?: any) =>
      createNotificationStore().add('warning', title, message, options),
    error: (title: string, message?: string, options?: any) =>
      createNotificationStore().add('error', title, message, options),

    // Remove notification
    remove: (id: number) => {
      activeToasts.update((toasts) => toasts.filter((t) => t.id !== id));
      history.update((h) =>
        h.map((item) =>
          item.id === id
            ? { ...item, dismissed: true, dismissedAt: new Date() }
            : item,
        ),
      );
    },

    // Clear all active toasts
    clearAll: () => {
      activeToasts.set([]);
    },

    // Toggle Do Not Disturb
    toggleDND: () => {
      doNotDisturb.update((value) => !value);
    },

    // Set Do Not Disturb
    setDND: (value: boolean) => {
      doNotDisturb.set(value);
    },

    // Clear history
    clearHistory: () => {
      history.set([]);
    },

    // Export history as JSON
    exportHistory: (): string => {
      let historyData: NotificationHistory[] = [];
      history.subscribe((h) => (historyData = h))();
      return JSON.stringify(historyData, null, 2);
    },
  };
}

export const notifications = createNotificationStore();
