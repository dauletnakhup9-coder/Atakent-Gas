import type { Metadata } from "next";
import { AuthProvider } from "@/components/auth-provider";
import "./globals.css";
export const metadata: Metadata = {
  title: "Qala · Өтінімдерді басқару",
  description: "Тұрғындардың өтінімдерін қабылдау және өңдеу",
  robots: { index: false, follow: false },
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="kk">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
