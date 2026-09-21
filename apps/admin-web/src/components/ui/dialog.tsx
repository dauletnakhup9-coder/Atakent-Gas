"use client";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;
export function DialogContent({
  title,
  description,
  children,
  wide = false,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
  wide?: boolean;
}) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="dialog-overlay" />
      <DialogPrimitive.Content
        className={`dialog-content ${wide ? "dialog-wide" : ""}`}
        {...(!description ? { "aria-describedby": undefined } : {})}
      >
        <DialogPrimitive.Title className="dialog-title">
          {title}
        </DialogPrimitive.Title>
        {description && (
          <DialogPrimitive.Description>
            {description}
          </DialogPrimitive.Description>
        )}
        <DialogPrimitive.Close className="dialog-close" aria-label="Жабу">
          <X size={20} />
        </DialogPrimitive.Close>
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}
