"use client";
import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowDownUp, CircleAlert } from "lucide-react";
import { useApi } from "@/hooks/use-api";
import type { Admin, ApplicationList } from "@/types";
import {
  ApplicationTable,
  ErrorBox,
  Filters,
  Loading,
  PageTitle,
  Pagination,
} from "./common";
export function Applications({
  revision,
  emergency = false,
}: {
  revision: number;
  emergency?: boolean;
}) {
  const initial = useSearchParams();
  const [query, setQuery] = useState(
    () => new URLSearchParams(initial.toString()),
  );
  const params = new URLSearchParams(query);
  if (emergency) params.set("priority", "CRITICAL");
  const result = useApi<ApplicationList>(`/applications?${params}`, revision),
    admins = useApi<Admin[]>("/admins", revision);
  function change(key: string, value: string) {
    setQuery((old) => {
      const next =
        key === "reset" ? new URLSearchParams() : new URLSearchParams(old);
      if (key !== "reset") {
        if (value) next.set(key, value);
        else next.delete(key);
      }
      if (key !== "page") next.delete("page");
      return next;
    });
  }
  return (
    <>
      <PageTitle
        eyebrow={emergency ? "ЖЕДЕЛ ӘРЕКЕТ" : "ӨТІНІМДЕР ТІЗІЛІМІ"}
        title={emergency ? "Авариялық өтінімдер" : "Барлық өтінімдер"}
        description={
          emergency
            ? "Газ шығуы туралы өтінімдерге бірінші кезекте назар аударыңыз."
            : "Өтінімдерді іздеңіз, сұрыптаңыз және орындаушыға бағыттаңыз."
        }
      />
      {emergency && (
        <div className="emergency-note">
          <CircleAlert size={20} /> Бұл өтінімдерде CRITICAL басымдығы
          сақталады.
        </div>
      )}
      <section className="panel">
        <Filters
          value={query}
          onChange={change}
          admins={admins.data || []}
          emergency={emergency}
        />
        <div className="list-toolbar">
          <span>
            <strong>{result.data?.total ?? "—"}</strong> өтінім табылды
          </span>
          <label>
            <ArrowDownUp size={15} />
            <select
              aria-label="Сұрыптау"
              value={query.get("sort") || "created_at"}
              onChange={(e) => change("sort", e.target.value)}
            >
              <option value="created_at">Күні бойынша</option>
              <option value="application_number">Нөмірі бойынша</option>
              <option value="priority">Басымдық бойынша</option>
              <option value="status">Мәртебе бойынша</option>
            </select>
            <select
              aria-label="Сұрыптау бағыты"
              value={query.get("order") || "desc"}
              onChange={(e) => change("order", e.target.value)}
            >
              <option value="desc">Кему ретімен</option>
              <option value="asc">Өсу ретімен</option>
            </select>
          </label>
        </div>
        <ErrorBox message={result.error} />
        {result.loading ? (
          <Loading />
        ) : (
          result.data && (
            <>
              <ApplicationTable rows={result.data.items} />
              <Pagination
                data={result.data}
                onPage={(page) => change("page", String(page))}
              />
            </>
          )
        )}
      </section>
    </>
  );
}
