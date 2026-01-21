export type ToastType = 'info' | 'success' | 'warning' | 'error';

export interface Toast {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number; // milliseconds (0 = no auto-dismiss)
  action?: {
    label: string;
    onClick: () => void;
  };
}
