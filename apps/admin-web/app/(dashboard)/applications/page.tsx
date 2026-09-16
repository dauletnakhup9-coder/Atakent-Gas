"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { PriorityBadge } from "@/components/applications/PriorityBadge";
import { StatusBadge } from "@/components/applications/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { apiRequest } from "@/lib/api";
import { APPLICATION_TYPE_LABELS, PRIORITY_LABELS, STATUS_LABELS, type ApplicationListOut } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

const PAGE_SIZE = 20;

type SortBy = "created_at" | "application_number" | "priority" | "status";

export default function ApplicationsPage() {
  const searchParams = useSearchParams();

  const [data, setData] = useState<ApplicationListOut | null>(null);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [personalAccount, setPersonalAccount] = useState(searchParams.get("personal_account") ?? "");
  const [applicationType, setApplicationType] = useState(searchParams.get("application_type") ?? "");
  const [status, setStatus] = useState(searchParams.get("status") ?? "");
  const [priority, setPriority] = useState(searchParams.get("priority") ?? "");
  const [page, setPage] = useState(Number(searchParams.get("page") ?? 1));
  const [sortBy, setSortBy] = useState<SortBy>("created_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  function toggleSort(column: SortBy) {
    if (sortBy === column) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(column);
      setSortDir("desc");
    }
    setPage(1);
  }

  useEffect(() => {
    setLoading(true);
    apiRequest<ApplicationListOut>("/applications", {
      params: {
        search: search || undefined,
        personal_account: personalAccount || undefined,
        application_type: applicationType || undefined,
        status: status || undefined,
        priority: priority || undefined,
        page,
        page_size: PAGE_SIZE,
        sort_by: sortBy,
        sort_dir: sortDir,
      },
    })
      .then(setData)
      .finally(() => setLoading(false));
  }, [search, personalAccount, applicationType, status, priority, page, sortBy, sortDir]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  function resetToFirstPage() {
    setPage(1);
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-bold">Өтінімдер</h1>
        <p className="text-sm text-muted-foreground">Барлығы: {data?.total ?? "..."}</p>
      </div>

      <Card className="flex flex-wrap items-end gap-3 p-4">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Іздеу (нөмір / дербес шот)</label>
          <Input
            className="w-56"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              resetToFirstPage();
            }}
            placeholder="REQ-... немесе 123456789"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Дербес шот</label>
          <Input
            className="w-40"
            value={personalAccount}
            onChange={(e) => {
              setPersonalAccount(e.target.value);
              resetToFirstPage();
            }}
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Түрі</label>
          <Select
            value={applicationType || "ALL"}
            onValueChange={(v) => {
              setApplicationType(v === "ALL" ? "" : v);
              resetToFirstPage();
            }}
          >
            <SelectTrigger className="w-56">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Барлығы</SelectItem>
              {Object.entries(APPLICATION_TYPE_LABELS).map(([key, label]) => (
                <SelectItem key={key} value={key}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Статус</label>
          <Select
            value={status || "ALL"}
            onValueChange={(v) => {
              setStatus(v === "ALL" ? "" : v);
              resetToFirstPage();
            }}
          >
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Барлығы</SelectItem>
              {Object.entries(STATUS_LABELS).map(([key, label]) => (
                <SelectItem key={key} value={key}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Приоритет</label>
          <Select
            value={priority || "ALL"}
            onValueChange={(v) => {
              setPriority(v === "ALL" ? "" : v);
              resetToFirstPage();
            }}
          >
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Барлығы</SelectItem>
              {Object.entries(PRIORITY_LABELS).map(([key, label]) => (
                <SelectItem key={key} value={key}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button
          variant="outline"
          onClick={() => {
            setSearch("");
            setPersonalAccount("");
            setApplicationType("");
            setStatus("");
            setPriority("");
            resetToFirstPage();
          }}
        >
          Тазарту
        </Button>
      </Card>

      <Card className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-muted/50 text-left text-xs uppercase text-muted-foreground">
            <tr>
              <SortableHeader label="№ Өтінім" column="application_number" sortBy={sortBy} sortDir={sortDir} onSort={toggleSort} />
              <SortableHeader label="Күні" column="created_at" sortBy={sortBy} sortDir={sortDir} onSort={toggleSort} />
              <th className="px-4 py-3">Дербес шот</th>
              <th className="px-4 py-3">Түрі</th>
              <SortableHeader label="Статус" column="status" sortBy={sortBy} sortDir={sortDir} onSort={toggleSort} />
              <SortableHeader label="Приоритет" column="priority" sortBy={sortBy} sortDir={sortDir} onSort={toggleSort} />
              <th className="px-4 py-3">Пайдаланушы</th>
              <th className="px-4 py-3">Орындаушы</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-muted-foreground">
                  Жүктелуде...
                </td>
              </tr>
            )}
            {!loading && data?.items.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-muted-foreground">
                  Өтінімдер табылмады
                </td>
              </tr>
            )}
            {!loading &&
              data?.items.map((app) => (
                <tr
                  key={app.id}
                  className={app.priority === "CRITICAL" ? "bg-critical/5 hover:bg-critical/10" : "hover:bg-accent"}
                >
                  <td className="px-4 py-3 font-medium">{app.application_number}</td>
                  <td className="px-4 py-3 text-muted-foreground">{formatDateTime(app.created_at)}</td>
                  <td className="px-4 py-3">{app.personal_account}</td>
                  <td className="px-4 py-3">{APPLICATION_TYPE_LABELS[app.application_type]}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={app.status} />
                  </td>
                  <td className="px-4 py-3">
                    <PriorityBadge priority={app.priority} />
                  </td>
                  <td className="px-4 py-3">
                    {app.user.first_name ?? app.user.telegram_username ?? app.user.telegram_user_id}
                  </td>
                  <td className="px-4 py-3">{app.assigned_admin?.name ?? "—"}</td>
                  <td className="px-4 py-3 text-right">
                    <Link href={`/applications/${app.id}`}>
                      <Button size="sm" variant="outline">
                        Ашу
                      </Button>
                    </Link>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </Card>

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Бет {page} / {totalPages}
        </p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Алдыңғы
          </Button>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Келесі
          </Button>
        </div>
      </div>
    </div>
  );
}

function SortableHeader({
  label,
  column,
  sortBy,
  sortDir,
  onSort,
}: {
  label: string;
  column: SortBy;
  sortBy: SortBy;
  sortDir: "asc" | "desc";
  onSort: (column: SortBy) => void;
}) {
  const active = sortBy === column;
  return (
    <th className="px-4 py-3">
      <button
        type="button"
        onClick={() => onSort(column)}
        className={`flex items-center gap-1 ${active ? "text-foreground" : ""}`}
      >
        {label}
        <span className="text-[10px]">{active ? (sortDir === "asc" ? "▲" : "▼") : ""}</span>
      </button>
    </th>
  );
}
