"use client";

import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

interface Toast {
  id: number;
  title: string;
  description?: string;
  variant?: "default" | "destructive" | "critical";
}

interface ToastContextValue {
  toast: (toast: Omit<Toast, "id">) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((t: Omit<Toast, "id">) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { ...t, id }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((item) => item.id !== id));
    }, 6000);
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "w-80 rounded-lg border border-border bg-card p-4 shadow-lg",
              t.variant === "destructive" && "border-destructive/50 bg-destructive/10",
              t.variant === "critical" && "border-critical bg-critical/10"
            )}
          >
            <p className="text-sm font-semibold">{t.title}</p>
            {t.description && <p className="mt-1 text-xs text-muted-foreground">{t.description}</p>}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
