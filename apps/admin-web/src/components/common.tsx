"use client";
import Link from "next/link";
import {
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Inbox,
  LoaderCircle,
  Search,
  SlidersHorizontal,
  X,
} from "lucide-react";
import type {
  Admin,
  Application,
  ApplicationList,
  Priority,
  Stats,
  Status,
} from "@/types";
import { PRIORITY_LABELS, STATUS_LABELS, TYPE_LABELS } from "@/types";
import { dateTime } from "@/lib/utils";
import { Button } from "./ui/button";

export function Loading() {
  return (
    <div className="loading" role="status">
      <LoaderCircle size={20} className="spin" /> Деректер жүктелуде…
    </div>
  );
}
export function ErrorBox({ message }: { message: string }) {
  return message ? (
    <div role="alert" className="error">
      {message}
    </div>
  ) : null;
}
export function Empty({
  title = "Әзірге өтінімдер жоқ",
  text = "Жаңа өтінімдер түскенде осы жерде пайда болады.",
}: {
  title?: string;
  text?: string;
}) {
  return (
    <div className="empty">
      <span>
        <Inbox size={28} strokeWidth={1.4} />
      </span>
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}
export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`badge status-${status}`}>
      <i />
      {STATUS_LABELS[status]}
    </span>
  );
}
export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <span className={`priority priority-${priority}`}>
      {priority === "CRITICAL" ? "⚑ " : priority === "HIGH" ? "↑ " : ""}
      {PRIORITY_LABELS[priority]}
    </span>
  );
}
export function PageTitle({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-title">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}
export function StatsCards({ data }: { data: Stats | null }) {
  const cards = [
    ["Барлық өтінімдер", data?.total, "all", "01"],
    ["Жаңа", data?.NEW, "new", "02"],
    ["Өңделуде", data?.IN_PROGRESS, "progress", "03"],
    ["Аяқталды", data?.COMPLETED, "done", "04"],
    ["Авариялық", data?.critical, "critical", "05"],
  ];
  return (
    <div className="stats-grid">
      {cards.map(([label, value, kind, number]) => (
        <div className={`stat-card stat-${kind}`} key={label}>
          <div className="stat-top">
            <span>{label}</span>
            <span className="stat-index">{number}</span>
          </div>
          <strong>{value ?? "—"}</strong>
          <div className="stat-bottom">
            <span className="stat-dot" />
            {kind === "critical"
              ? "Шұғыл назар аудару"
              : kind === "all"
                ? "Барлық кезең бойынша"
                : "Ағымдағы мәртебе"}
          </div>
        </div>
      ))}
    </div>
  );
}
export function ApplicationTable({
  rows,
  compact = false,
}: {
  rows: Application[];
  compact?: boolean;
}) {
  if (!rows.length) return <Empty />;
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>ӨТІНІМ / КҮНІ</th>
            <th>ДЕРБЕС ШОТ</th>
            <th>ӨТІНІМ ТҮРІ</th>
            <th>МӘРТЕБЕ</th>
            <th>БАСЫМДЫҚ</th>
            {!compact && (
              <>
                <th>ТҰРҒЫН</th>
                <th>ОРЫНДАУШЫ</th>
              </>
            )}
            <th>
              <span className="sr-only">Ашу</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((a) => (
            <tr
              key={a.id}
              className={a.priority === "CRITICAL" ? "urgent-row" : ""}
            >
              <td>
                <Link className="request-number" href={`/applications/${a.id}`}>
                  {a.application_number}
                </Link>
                <span className="table-sub">{dateTime(a.created_at)}</span>
              </td>
              <td className="mono">{a.personal_account}</td>
              <td>
                <span className={`type-symbol type-${a.application_type}`}>
                  {a.application_type === "GAS_LEAK"
                    ? "!"
                    : a.application_type === "MPI_REMOVAL"
                      ? "◷"
                      : "⌁"}
                </span>
                <span className="type-label">
                  {TYPE_LABELS[a.application_type]}
                </span>
              </td>
              <td>
                <StatusBadge status={a.status} />
              </td>
              <td>
                <PriorityBadge priority={a.priority} />
              </td>
              {!compact && (
                <>
                  <td>
                    {a.user.first_name}
                    <span className="table-sub">
                      {a.user.telegram_username
                        ? `@${a.user.telegram_username}`
                        : a.user.telegram_user_id}
                    </span>
                  </td>
                  <td>
                    {a.assignee_name || (
                      <span className="muted">Тағайындалмаған</span>
                    )}
                  </td>
                </>
              )}
              <td>
                <Link
                  className="row-open"
                  href={`/applications/${a.id}`}
                  aria-label={`${a.application_number} ашу`}
                >
                  <ArrowUpRight size={18} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function Pagination({
  data,
  onPage,
}: {
  data: ApplicationList;
  onPage: (page: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(data.total / data.page_size));
  return (
    <div className="pagination">
      <span>
        {data.total} өтінім · {data.page} / {pages} бет
      </span>
      <div>
        <Button
          variant="outline"
          size="icon"
          aria-label="Алдыңғы бет"
          disabled={data.page <= 1}
          onClick={() => onPage(data.page - 1)}
        >
          <ChevronLeft size={17} />
        </Button>
        <Button
          variant="outline"
          size="icon"
          aria-label="Келесі бет"
          disabled={data.page >= pages}
          onClick={() => onPage(data.page + 1)}
        >
          <ChevronRight size={17} />
        </Button>
      </div>
    </div>
  );
}
export function Filters({
  value,
  onChange,
  admins,
  emergency = false,
  reports = false,
}: {
  value: URLSearchParams;
  onChange: (key: string, value: string) => void;
  admins?: Admin[];
  emergency?: boolean;
  reports?: boolean;
}) {
  const fields = [
    ["application_type", "Барлық түрлер", TYPE_LABELS],
    ["status", "Барлық мәртебелер", STATUS_LABELS],
    ...(!emergency && !reports
      ? [["priority", "Барлық басымдықтар", PRIORITY_LABELS]]
      : []),
  ] as [string, string, Record<string, string>][];
  return (
    <div className="filters">
      <div className="filter-main">
        <div className="search-field">
          <Search size={17} />
          <input
            aria-label="Өтінім іздеу"
            placeholder="Өтінім нөмірі немесе дербес шот…"
            value={value.get("q") || ""}
            onChange={(e) => onChange("q", e.target.value)}
          />
        </div>
        <span className="filter-icon">
          <SlidersHorizontal size={17} />
        </span>
        {fields.map(([key, label, labels]) => (
          <select
            key={key}
            aria-label={label}
            value={value.get(key) || ""}
            onChange={(e) => onChange(key, e.target.value)}
          >
            <option value="">{label}</option>
            {Object.entries(labels).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        ))}
      </div>
      <div className="filter-dates">
        <label>
          Бастап
          <input
            aria-label="Бастап"
            type="date"
            value={value.get("date_from") || ""}
            onChange={(e) => onChange("date_from", e.target.value)}
          />
        </label>
        <label>
          Дейін
          <input
            aria-label="Дейін"
            type="date"
            value={value.get("date_to") || ""}
            onChange={(e) => onChange("date_to", e.target.value)}
          />
        </label>
        {admins && (
          <select
            aria-label="Орындаушы"
            value={value.get("assigned_to") || ""}
            onChange={(e) => onChange("assigned_to", e.target.value)}
          >
            <option value="">Барлық орындаушылар</option>
            {admins.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        )}
        <Button variant="ghost" size="sm" onClick={() => onChange("reset", "")}>
          <X size={14} /> Тазалау
        </Button>
      </div>
    </div>
  );
}
