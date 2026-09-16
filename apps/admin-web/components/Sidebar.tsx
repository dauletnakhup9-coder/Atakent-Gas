"use client";

import { AlertTriangle, FileText, LayoutDashboard, Settings, Users, BarChart3 } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/lib/auth";
import type { AdminRole } from "@/lib/types";
import { cn } from "@/lib/utils";

const NAV_ITEMS: { href: string; label: string; icon: typeof LayoutDashboard; roles: AdminRole[] | null }[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard, roles: null },
  { href: "/applications", label: "Өтінімдер", icon: FileText, roles: null },
  { href: "/applications?priority=CRITICAL", label: "Авариялық өтінімдер", icon: AlertTriangle, roles: null },
  { href: "/employees", label: "Қызметкерлер", icon: Users, roles: ["SUPER_ADMIN"] },
  { href: "/reports", label: "Есептер", icon: BarChart3, roles: null },
  { href: "/settings", label: "Баптаулар", icon: Settings, roles: null },
];

export function Sidebar() {
  const pathname = usePathname();
  const { admin } = useAuth();

  return (
    <aside className="hidden w-64 shrink-0 border-r border-border bg-card md:flex md:flex-col">
      <div className="flex h-16 items-center gap-2 border-b border-border px-6">
        <span className="text-lg font-bold text-primary">Газ қызметі</span>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {NAV_ITEMS.filter((item) => !item.roles || (admin && item.roles.includes(admin.role))).map((item) => {
          const basePath = item.href.split("?")[0];
          const active = basePath === "/" ? pathname === "/" : pathname.startsWith(basePath);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
                active && "bg-primary/10 text-primary"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
