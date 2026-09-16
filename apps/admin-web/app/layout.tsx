import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AuthProvider } from "@/lib/auth";
import { ToastProvider } from "@/components/ui/toast";

import "./globals.css";

export const metadata: Metadata = {
  title: "Газ қызметі — Админ панель",
  description: "Тұрғындардың өтінімдерін басқару жүйесі",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="kk">
      <body>
        <ToastProvider>
          <AuthProvider>{children}</AuthProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
