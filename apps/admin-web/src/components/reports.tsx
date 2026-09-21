"use client";
import { useState } from "react";
import { Download, FileSpreadsheet, Timer } from "lucide-react";
import { useApi } from "@/hooks/use-api";
import { downloadReport } from "@/services/api";
import type { Admin, Stats } from "@/types";
import { TYPE_LABELS } from "@/types";
import {
  Empty,
  ErrorBox,
  Filters,
  Loading,
  PageTitle,
  StatsCards,
} from "./common";
import { Button } from "./ui/button";
export function Reports({ revision }: { revision: number }) {
  const [query, setQuery] = useState(new URLSearchParams()),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const stats = useApi<Stats>(`/reports?${query}`, revision),
    admins = useApi<Admin[]>("/admins");
  function change(key: string, value: string) {
    setQuery((old) => {
      const next =
        key === "reset" ? new URLSearchParams() : new URLSearchParams(old);
      if (key !== "reset") {
        if (value) next.set(key, value);
        else next.delete(key);
      }
      return next;
    });
  }
  async function download(format: "csv" | "xlsx") {
    setBusy(true);
    setError("");
    try {
      await downloadReport(query.toString(), format);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="ТАЛДАУ ЖӘНЕ ЕСЕП"
        title="Есептер"
        description="Өтінімдердің орындалуын және қызмет көрсету уақытын бақылаңыз."
        action={
          <div className="actions">
            <Button
              variant="outline"
              disabled={busy}
              onClick={() => download("csv")}
            >
              <Download size={16} /> CSV
            </Button>
            <Button disabled={busy} onClick={() => download("xlsx")}>
              <FileSpreadsheet size={16} /> Excel
            </Button>
          </div>
        }
      />
      <section className="panel report-filters">
        <Filters
          value={query}
          onChange={change}
          admins={admins.data || []}
          reports
        />
      </section>
      <ErrorBox message={error || stats.error} />
      {stats.loading ? (
        <Loading />
      ) : (
        <>
          <StatsCards data={stats.data} />
          <div className="report-summary">
            <section className="panel report-time">
              <span className="report-icon">
                <Timer size={28} />
              </span>
              <div>
                <p>Орташа өңдеу уақыты</p>
                <strong>
                  {stats.data?.average_processing_hours === null || !stats.data
                    ? "—"
                    : `${stats.data.average_processing_hours.toFixed(1)} сағ`}
                </strong>
                <small>
                  Жасалғаннан аяқталғанға дейін · тек аяқталған өтінімдер
                </small>
              </div>
            </section>
            <section className="panel report-rejected">
              <p>Қабылданбаған өтінімдер</p>
              <strong>{stats.data?.REJECTED || 0}</strong>
            </section>
          </div>
          <section className="panel">
            <div className="panel-heading">
              <h2>Түрлер бойынша қорытынды</h2>
            </div>
            {stats.data?.total ? (
              <div className="report-types">
                {Object.entries(TYPE_LABELS).map(([type, label]) => {
                  const count =
                    stats.data!.by_type.find((t) => t.type === type)?.count ||
                    0;
                  return (
                    <div key={type}>
                      <span>{label}</span>
                      <div className="progress-track">
                        <i
                          style={{
                            width: `${(count / stats.data!.total) * 100}%`,
                          }}
                        />
                      </div>
                      <strong>{count}</strong>
                    </div>
                  );
                })}
              </div>
            ) : (
              <Empty
                title="Таңдалған кезеңде өтінім жоқ"
                text="Басқа күн аралығын немесе сүзгілерді таңдаңыз."
              />
            )}
          </section>
        </>
      )}
    </>
  );
}
