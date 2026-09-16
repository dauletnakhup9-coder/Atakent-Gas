"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth";
import { useRealtime } from "@/lib/useRealtime";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { admin, loading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  useEffect(() => {
    if (!loading && !admin) {
      router.replace("/login");
    }
  }, [loading, admin, router]);

  useRealtime((event) => {
    if (event.type === "application_created") {
      const isCritical = event.data.priority === "CRITICAL";
      toast({
        title: isCritical ? "🚨 Жаңа авариялық өтінім" : "🆕 Жаңа өтінім",
        description: String(event.data.application_number ?? ""),
        variant: isCritical ? "critical" : "default",
      });
    }
  });

  if (loading || !admin) {
    return <div className="flex min-h-screen items-center justify-center text-muted-foreground">Жүктелуде...</div>;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-y-auto bg-background p-6">{children}</main>
      </div>
    </div>
  );
}
