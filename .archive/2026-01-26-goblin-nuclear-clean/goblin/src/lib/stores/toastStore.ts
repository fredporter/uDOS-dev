/**
 * Toast Notification Store
 *
 * Wrapper around svelte-sonner for centralized toast notifications
 */

import { toast } from "svelte-sonner";

export const toastStore = {
  /**
   * Show a success toast
   */
  success(message: string, duration: number = 3000) {
    toast.success(message, { duration });
  },

  /**
   * Show an error toast
   */
  error(message: string, duration: number = 4000) {
    toast.error(message, { duration });
  },

  /**
   * Show an info toast
   */
  info(message: string, duration: number = 3000) {
    toast.info(message, { duration });
  },

  /**
   * Show a warning toast
   */
  warning(message: string, duration: number = 3000) {
    toast.warning(message, { duration });
  },

  /**
   * Show a generic message toast
   */
  message(message: string, duration: number = 3000) {
    toast.message(message, { duration });
  },

  /**
   * Dismiss all toasts
   */
  dismiss() {
    toast.dismiss();
  },
};
