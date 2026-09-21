"use client";
import { useState } from "react";
import { Check, Save, ShieldCheck } from "lucide-react";
import { useApi } from "@/hooks/use-api";
import { api } from "@/services/api";
import { dateTime } from "@/lib/utils";
import type { Settings as Config } from "@/types";
import { STATUS_LABELS } from "@/types";
import { useAuth } from "./auth-provider";
import { ErrorBox, Loading, PageTitle } from "./common";
import { Button } from "./ui/button";
export function Settings({ revision }: { revision: number }) {
  const { admin } = useAuth(),
    isSuper = admin?.role === "SUPER_ADMIN";
  const [local, setLocal] = useState(0),
    [error, setError] = useState(""),
    [saved, setSaved] = useState(false),
    [busy, setBusy] = useState(false);
  const result = useApi<Config>("/settings", revision + local),
    operations = useApi<{
      pending_notifications: number;
      failed_notifications: number;
    }>(isSuper ? "/operations" : null, revision + local),
    audit = useApi<
      {
        id: number;
        admin_id: number | null;
        action: string;
        target: string;
        created_at: string;
      }[]
    >(isSuper ? "/audit" : null, revision + local);
  async function save(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setSaved(false);
    const f = new FormData(e.currentTarget);
    const data = {
      organization_name: f.get("organization_name"),
      contact_phone: f.get("contact_phone"),
      emergency_phone: f.get("emergency_phone"),
      max_photo_mb: Number(f.get("max_photo_mb")),
      notification_texts: Object.fromEntries(
        ["IN_PROGRESS", "COMPLETED", "REJECTED"].map((s) => [s, f.get(s)]),
      ),
    };
    try {
      await api("/settings", { method: "PATCH", body: JSON.stringify(data) });
      setSaved(true);
      setLocal((n) => n + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function retry() {
    setBusy(true);
    setError("");
    try {
      await api("/operations/retry-notifications", { method: "POST" });
      setLocal((n) => n + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="ЖҮЙЕНІ БАСҚАРУ"
        title="Баптаулар"
        description="Ұйым ақпараты, байланыс нөмірлері және хабарландырулар."
      />
      <ErrorBox message={error || result.error} />
      {saved && (
        <div className="success" role="status">
          <Check size={16} />
          Баптаулар сақталды
        </div>
      )}
      {!result.data ? (
        <Loading />
      ) : (
        <form key={local} className="settings-form" onSubmit={save}>
          <fieldset disabled={!isSuper || busy}>
            <section className="panel">
              <div className="panel-heading">
                <h2>Ұйым туралы</h2>
                <ShieldCheck size={18} />
              </div>
              <div className="settings-fields">
                <label>
                  Ұйым атауы
                  <input
                    name="organization_name"
                    defaultValue={result.data.organization_name}
                    required
                    maxLength={200}
                  />
                </label>
                <label>
                  Байланыс нөмірі
                  <input
                    name="contact_phone"
                    defaultValue={result.data.contact_phone}
                    maxLength={40}
                  />
                </label>
                <label>
                  Авариялық қызмет нөмірі
                  <input
                    name="emergency_phone"
                    defaultValue={result.data.emergency_phone}
                    maxLength={40}
                    placeholder="Ұйым растаған нөмір"
                  />
                  <small>
                    Тек ұйыммен келісілген нөмірді енгізіңіз. Бос болса, бот
                    нөмір көрсетпейді.
                  </small>
                </label>
                <label>
                  Фотоның ең үлкен көлемі (МБ)
                  <input
                    name="max_photo_mb"
                    type="number"
                    min={1}
                    max={10}
                    required
                    defaultValue={result.data.max_photo_mb}
                  />
                </label>
              </div>
            </section>
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Telegram хабарландырулары</h2>
                  <p>Өтінім нөмірі үшін {"{number}"} белгісін пайдаланыңыз.</p>
                </div>
              </div>
              <div className="form-stack">
                {["IN_PROGRESS", "COMPLETED", "REJECTED"].map((s) => (
                  <label key={s}>
                    {STATUS_LABELS[s as keyof typeof STATUS_LABELS]}
                    <textarea
                      name={s}
                      defaultValue={result.data!.notification_texts[s]}
                      required
                      maxLength={1000}
                      rows={2}
                    />
                  </label>
                ))}
              </div>
            </section>
            {isSuper && (
              <Button type="submit" disabled={busy}>
                <Save size={16} /> Өзгерістерді сақтау
              </Button>
            )}
          </fieldset>
          {!isSuper && (
            <p className="section-note">
              Баптауларды тек бас әкімші өзгерте алады.
            </p>
          )}
        </form>
      )}
      {isSuper && (
        <>
          <section className="panel operations">
            <div className="panel-heading">
              <h2>Хабарландыруларды жеткізу</h2>
            </div>
            <div className="operations-body">
              <p>
                Кезекте:{" "}
                <strong>{operations.data?.pending_notifications ?? "—"}</strong>
              </p>
              <p>
                Жеткізілмеді:{" "}
                <strong>{operations.data?.failed_notifications ?? "—"}</strong>
              </p>
              <Button
                variant="outline"
                onClick={retry}
                disabled={busy || !operations.data?.failed_notifications}
              >
                Қайта жіберу
              </Button>
            </div>
          </section>
          <section className="panel">
            <div className="panel-heading">
              <h2>Аудит журналы</h2>
              <span className="muted">Соңғы 50 әрекет</span>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>КҮНІ</th>
                    <th>ӘКІМШІ ID</th>
                    <th>ӘРЕКЕТ</th>
                    <th>НЫСАН</th>
                  </tr>
                </thead>
                <tbody>
                  {audit.data?.map((a) => (
                    <tr key={a.id}>
                      <td>{dateTime(a.created_at)}</td>
                      <td>{a.admin_id ?? "—"}</td>
                      <td>{a.action}</td>
                      <td>{a.target}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </>
  );
}
