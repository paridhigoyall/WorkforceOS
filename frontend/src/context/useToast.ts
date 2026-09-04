import { useContext } from 'react';
import { ToastContext } from './ToastContextDef';
import type { ToastContextValue } from './ToastContextDef';

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>');
  return ctx;
}
