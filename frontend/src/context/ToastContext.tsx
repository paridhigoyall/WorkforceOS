import React, { useState, useCallback, useRef } from 'react';
import { CheckCircle2, XCircle, Info, AlertTriangle, X } from 'lucide-react';
import { ToastContext } from './ToastContextDef';
import type { Toast, ToastType, ToastContextValue } from './ToastContextDef';

const ICON_MAP: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle2 size={18} />,
  error:   <XCircle size={18} />,
  info:    <Info size={18} />,
  warning: <AlertTriangle size={18} />,
};

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
  const [exiting, setExiting] = useState(false);

  const handleClose = useCallback(() => {
    setExiting(true);
    setTimeout(() => onRemove(toast.id), 280);
  }, [toast.id, onRemove]);

  React.useEffect(() => {
    const t = setTimeout(handleClose, toast.duration ?? 4500);
    return () => clearTimeout(t);
  }, [handleClose, toast.duration]);

  return (
    <div className={`toast toast-${toast.type}${exiting ? ' exit' : ''}`} role="alert">
      <span className="toast-icon">{ICON_MAP[toast.type]}</span>
      <div className="toast-message">
        {toast.title && <div className="toast-title">{toast.title}</div>}
        <div>{toast.message}</div>
      </div>
      <button className="toast-close" onClick={handleClose} aria-label="Dismiss">
        <X size={14} />
      </button>
    </div>
  );
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const idRef = useRef(0);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const addToast = useCallback((opts: Omit<Toast, 'id'>) => {
    const id = `toast-${++idRef.current}`;
    setToasts(prev => [...prev.slice(-4), { ...opts, id }]);
  }, []);

  const ctx: ToastContextValue = {
    toast: addToast,
    success: (message, title) => addToast({ type: 'success', message, title }),
    error:   (message, title) => addToast({ type: 'error',   message, title }),
    info:    (message, title) => addToast({ type: 'info',    message, title }),
    warning: (message, title) => addToast({ type: 'warning', message, title }),
  };

  return (
    <ToastContext.Provider value={ctx}>
      {children}
      <div className="toast-container" aria-live="polite">
        {toasts.map(t => (
          <ToastItem key={t.id} toast={t} onRemove={removeToast} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}
