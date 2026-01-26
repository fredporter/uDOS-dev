/**
 * Typed Event Bus Service
 *
 * Centralized event management with type safety.
 * Supports both browser CustomEvents and Tauri IPC events.
 *
 * Usage:
 *   import { eventBus } from '$lib/services/eventBus';
 *
 *   // Emit event
 *   eventBus.emit('file-opened', { path: '/foo.md', content: '...' });
 *
 *   // Listen to event
 *   const unsubscribe = eventBus.on('file-opened', (data) => {
 *     console.log('File opened:', data.path);
 *   });
 *
 *   // Cleanup
 *   unsubscribe();
 */

import type { AppEventName, AppEventPayload } from "../types/events";

type EventHandler<T extends AppEventName> = (
  payload: AppEventPayload<T>
) => void;

type UnsubscribeFn = () => void;

class EventBus {
  private handlers: Map<AppEventName, Set<EventHandler<any>>> = new Map();
  private tauriUnsubscribers: Map<string, UnsubscribeFn> = new Map();

  /**
   * Emit an event to all listeners
   *
   * Events are broadcast to:
   * 1. Local handlers (eventBus subscribers)
   * 2. Browser window (CustomEvent)
   * 3. Tauri IPC (if available)
   *
   * @param eventName - Type-safe event name from AppEventName
   * @param payload - Event data matching the event type
   *
   * @example
   * ```typescript
   * eventBus.emit('file-opened', {
   *   path: '/documents/readme.md',
   *   content: 'Hello world'
   * });
   * ```
   */
  emit<T extends AppEventName>(
    eventName: T,
    payload: AppEventPayload<T>
  ): void {
    // Emit to local handlers
    const handlers = this.handlers.get(eventName);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(payload);
        } catch (error) {
          console.error(`Error in event handler for ${eventName}:`, error);
        }
      });
    }

    // Emit as browser CustomEvent for legacy support
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent(eventName, {
          detail: payload,
          bubbles: true,
        })
      );
    }

    // Emit as Tauri event if available
    this.emitTauriEvent(eventName, payload);
  }

  /**
   * Subscribe to an event
   *
   * Returns an unsubscribe function that should be called to cleanup.
   * Always call this in component cleanup (onDestroy) to prevent memory leaks.
   *
   * @param eventName - Type-safe event name to listen for
   * @param handler - Callback function receiving typed event payload
   * @returns Unsubscribe function to remove the listener
   *
   * @example
   * ```typescript
   * const unsubscribe = eventBus.on('file-opened', (data) => {
   *   console.log('File:', data.path);
   * });
   *
   * onDestroy(() => {
   *   unsubscribe();
   * });
   * ```
   */
  on<T extends AppEventName>(
    eventName: T,
    handler: EventHandler<T>
  ): UnsubscribeFn {
    if (!this.handlers.has(eventName)) {
      this.handlers.set(eventName, new Set());
    }

    this.handlers.get(eventName)!.add(handler);

    // Also listen to Tauri events if available
    this.listenTauriEvent(eventName, handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.handlers.get(eventName);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.handlers.delete(eventName);
        }
      }
    };
  }

  /**
   * Subscribe to an event, but only fire once
   *
   * Handler is automatically unsubscribed after first invocation.
   * Useful for one-time initialization or confirmation dialogs.
   *
   * @param eventName - Type-safe event name to listen for
   * @param handler - Callback function (runs once then unsubscribes)
   * @returns Unsubscribe function (in case you need to cancel early)
   *
   * @example
   * ```typescript
   * eventBus.once('app-initialized', () => {
   *   console.log('App ready!');
   * });
   * ```
   */
  once<T extends AppEventName>(
    eventName: T,
    handler: EventHandler<T>
  ): UnsubscribeFn {
    const wrappedHandler = (payload: AppEventPayload<T>) => {
      handler(payload);
      unsubscribe();
    };

    const unsubscribe = this.on(eventName, wrappedHandler);
    return unsubscribe;
  }

  /**
   * Remove all listeners for an event (or all events if no name provided)
   */
  off<T extends AppEventName>(eventName?: T): void {
    if (eventName) {
      this.handlers.delete(eventName);
    } else {
      this.handlers.clear();
    }
  }

  /**
   * Get number of listeners for an event
   */
  listenerCount<T extends AppEventName>(eventName: T): number {
    return this.handlers.get(eventName)?.size || 0;
  }

  /**
   * Emit Tauri event (for IPC communication)
   */
  private async emitTauriEvent<T extends AppEventName>(
    eventName: T,
    payload: AppEventPayload<T>
  ): Promise<void> {
    try {
      // Dynamic import to avoid build errors when Tauri is not available
      const { emit } = await import("@tauri-apps/api/event");
      await emit(eventName, payload);
    } catch (error) {
      // Tauri not available or emit failed - this is fine
      // Events will still work via local handlers and CustomEvents
    }
  }

  /**
   * Listen to Tauri event (for IPC communication)
   */
  private async listenTauriEvent<T extends AppEventName>(
    eventName: T,
    handler: EventHandler<T>
  ): Promise<void> {
    try {
      // Dynamic import to avoid build errors when Tauri is not available
      const { listen } = await import("@tauri-apps/api/event");

      const unlistenFn = await listen(eventName, (event: any) => {
        handler(event.payload);
      });

      // Store unlisten function for cleanup
      const key = `${eventName}-${handler.toString()}`;
      this.tauriUnsubscribers.set(key, unlistenFn);
    } catch (error) {
      // Tauri not available - this is fine
      // Events will still work via local handlers and CustomEvents
    }
  }
}

// Export singleton instance
export const eventBus = new EventBus();

// Export type helpers
export type { EventHandler, UnsubscribeFn };
