"use client";
import Link from "next/link";
import {
  ArrowRight,
  CalendarDays,
  CircleAlert,
  Download,
  Radio,
} from "lucide-react";
import { useApi } from "@/hooks/use-api";
import type { ApplicationList, Stats } from "@/types";
import { TYPE_LABELS } from "@/types";
import {
  ApplicationTable,
  Empty,
  ErrorBox,
  Loading,
  PageTitle,
  StatsCards,
} from "./common";
import { Button } from "./ui/button";

export function Dashboard({ revision }: { revision: number }) {
  const stats = useApi<Stats>("/dashboard/stats", revision),
    recent = useApi<ApplicationList>("/applications?page_size=6", revision);
  const urgent = useApi<ApplicationList>(
    "/applications?priority=CRITICAL&status=NEW&page_size=3",
    revision,
  );
  const daily = stats.data?.daily || [],
    max = Math.max(1, ...daily.map((d) => d.count));
  const total = stats.data?.total || 0;
  return (
    <>
      <PageTitle
        eyebrow="ЖҰМЫС КЕҢІСТІГІ"
        title="Бақылау тақтасы"
        description="Қала өтінімдері. Бір жерден — толық бақылау."
        action={
          <Button variant="outline" asChild>
            <Link href="/reports">
              <Download size={16} /> Есепке өту
            </Link>
          </Button>
        }
      />
      <ErrorBox message={stats.error} />
      <StatsCards data={stats.data} />
      {(urgent.data?.total || 0) > 0 && (
        <Link href="/emergencies" className="urgent-banner">
          <span className="urgent-icon">
            <CircleAlert size={23} />
          </span>
          <div>
            <strong>{urgent.data!.total} жаңа авариялық өтінім</strong>
            <p>
              {urgent.data!.items.map((a) => a.application_number).join(" · ")}
            </p>
          </div>
          <span>
            Шұғыл қарау <ArrowRight size={17} />
          </span>
        </Link>
      )}
      <div className="chart-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Өтінімдер динамикасы</h2>
              <p>Соңғы 30 белсенді күн</p>
            </div>
            <span className="quiet-chip">
              <CalendarDays size={14} /> Күндер бойынша
            </span>
          </div>
          {daily.length ? (
            <div className="chart">
              <div className="chart-guide">
                <span>{max}</span>
                <span>{Math.round(max / 2)}</span>
                <span>0</span>
              </div>
              <div className="chart-bars">
                {daily.map((d, i) => (
                  <div
                    className="chart-column"
                    key={d.date}
                    title={`${d.date}: ${d.count}`}
                  >
                    <span className="bar-value">{d.count}</span>
                    <div
                      className={`chart-bar ${i === daily.length - 1 ? "last" : ""}`}
                      style={{
                        height: `${Math.max(3, (d.count / max) * 150)}px`,
                      }}
                    />
                    <span className="bar-date">
                      {d.date.slice(5).replace("-", ".")}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <Empty
              title="График үшін деректер жоқ"
              text="Алғашқы өтінімнен кейін динамика көрсетіледі."
            />
          )}
        </section>
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Өтінім түрлері</h2>
              <p>Барлық өтінімдердің үлесі</p>
            </div>
            <span className="tiny-dot" />
          </div>
          <div className="distribution">
            <div
              className="donut"
              style={{
                background: total
                  ? `conic-gradient(#147b67 0% ${(100 * (stats.data?.by_type.find((t) => t.type === "METER_NOT_WORKING")?.count || 0)) / total}%, #dda853 0% ${100 * (1 - (stats.data?.by_type.find((t) => t.type === "GAS_LEAK")?.count || 0) / total)}%, #df6b61 0% 100%)`
                  : "#edf1ef",
              }}
            >
              <div>
                <strong>{total}</strong>
                <span>өтінім</span>
              </div>
            </div>
            <div className="legend">
              {Object.entries(TYPE_LABELS).map(([type, label], i) => (
                <div key={type}>
                  <i
                    style={{ background: ["#147b67", "#dda853", "#df6b61"][i] }}
                  />
                  <span>{label}</span>
                  <strong>
                    {stats.data?.by_type.find((x) => x.type === type)?.count ||
                      0}
                  </strong>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>
              Соңғы өтінімдер{" "}
              <span className="count-chip">{recent.data?.total || 0}</span>
            </h2>
            <p>Тұрғындардан келіп түскен жаңа сұраныстар</p>
          </div>
          <Link className="text-link" href="/applications">
            Барлығын көру <ArrowRight size={15} />
          </Link>
        </div>
        <ErrorBox message={recent.error} />
        {recent.loading && !recent.data ? (
          <Loading />
        ) : (
          recent.data && <ApplicationTable rows={recent.data.items} compact />
        )}
        <div className="panel-foot">
          <Radio size={14} /> Өтінімдер автоматты түрде жаңартылады
        </div>
      </section>
    </>
  );
}
