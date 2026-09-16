import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: number;
  icon: LucideIcon;
  variant?: "default" | "critical";
}

export function StatCard({ label, value, icon: Icon, variant = "default" }: StatCardProps) {
  return (
    <Card className={cn(variant === "critical" && value > 0 && "border-critical bg-critical/5")}>
      <CardContent className="flex items-center justify-between p-5">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className={cn("mt-1 text-2xl font-bold", variant === "critical" && value > 0 && "text-critical")}>
            {value}
          </p>
        </div>
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary",
            variant === "critical" && value > 0 && "bg-critical/10 text-critical"
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  );
}
