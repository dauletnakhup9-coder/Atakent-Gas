"use client";

import { AlertTriangle, CheckCircle2, Clock, FileStack, Sparkles } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { StatCard } from "@/components/dashboard/StatCard";
import { PriorityBadge } from "@/components/applications/PriorityBadge";
import { StatusBadge } from "@/components/applications/StatusBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiRequest } from "@/lib/api";
import { APPLICATION_TYPE_LABELS, type ApplicationListOut, type DashboardStats } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recent, setRecent] = useState<ApplicationListOut | null>(null);
  const [critical, setCritical] = useState<ApplicationListOut | null>(null);

  async function load() {
    const [statsData, recentData, criticalData] = await Promise.all([
      apiRequest<DashboardStats>("/dashboard/stats"),
      apiRequest<ApplicationListOut>("/applications", { params: { page: 1, page_size: 5 } }),
      apiRequest<ApplicationListOut>("/applications", { params: { priority: "CRITICAL", page: 1, page_size: 5 } }),
    ]);
    setStats(statsData);
    setRecent(recentData);
    setCritical(criticalData);
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) {
    return <p className="text-muted-foreground">Жүктелуде...</p>;
  }

  const typeChartData = Object.entries(stats.type_distribution).map(([key, value]) => ({
    name: APPLICATION_TYPE_LABELS[key as keyof typeof APPLICATION_TYPE_LABELS] ?? key,
    value,
  }));

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard label="Барлық өтінімдер" value={stats.total} icon={FileStack} />
        <StatCard label="Жаңа" value={stats.new} icon={Sparkles} />
        <StatCard label="Өңделуде" value={stats.in_progress} icon={Clock} />
        <StatCard label="Аяқталды" value={stats.completed} icon={CheckCircle2} />
        <StatCard label="🚨 Авариялық" value={stats.critical} icon={AlertTriangle} variant="critical" />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Өтінімдер саны (күндер бойынша)</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats.daily_counts}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="date" fontSize={12} />
                <YAxis fontSize={12} allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="hsl(var(--primary))" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Түрлері бойынша үлестірім</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typeChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="name" fontSize={11} interval={0} angle={-10} textAnchor="end" height={60} />
                <YAxis fontSize={12} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Соңғы өтінімдер</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {recent?.items.length ? (
              recent.items.map((app) => (
                <Link
                  key={app.id}
                  href={`/applications/${app.id}`}
                  className="flex items-center justify-between rounded-md border border-border p-3 text-sm hover:bg-accent"
                >
                  <div>
                    <p className="font-medium">{app.application_number}</p>
                    <p className="text-xs text-muted-foreground">{formatDateTime(app.created_at)}</p>
                  </div>
                  <StatusBadge status={app.status} />
                </Link>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">Өтінімдер жоқ</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-critical">
              <AlertTriangle className="h-4 w-4" /> Авариялық өтінімдер
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {critical?.items.length ? (
              critical.items.map((app) => (
                <Link
                  key={app.id}
                  href={`/applications/${app.id}`}
                  className="flex items-center justify-between rounded-md border border-critical/40 bg-critical/5 p-3 text-sm hover:bg-critical/10"
                >
                  <div>
                    <p className="font-medium">{app.application_number}</p>
                    <p className="text-xs text-muted-foreground">{formatDateTime(app.created_at)}</p>
                  </div>
                  <PriorityBadge priority={app.priority} />
                </Link>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">Авариялық өтінімдер жоқ</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
