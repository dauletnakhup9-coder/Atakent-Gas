"use client";
import { useState } from "react";
import { Plus, ShieldCheck } from "lucide-react";
import { useApi } from "@/hooks/use-api";
import { api } from "@/services/api";
import { useAuth } from "./auth-provider";
import type { Admin } from "@/types";
import { ROLE_LABELS } from "@/types";
import { ErrorBox, Loading, PageTitle } from "./common";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogTrigger } from "./ui/dialog";
export function Staff({ revision }: { revision: number }) {
  const { admin } = useAuth();
  const [local, setLocal] = useState(0),
    [open, setOpen] = useState(false),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const result = useApi<Admin[]>("/admins", revision + local);
  async function create(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setBusy(true);
    const data = Object.fromEntries(new FormData(e.currentTarget));
    try {
      await api("/admins", { method: "POST", body: JSON.stringify(data) });
      setOpen(false);
      setLocal((n) => n + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function toggle(a: Admin) {
    setBusy(true);
    setError("");
    try {
      await api(`/admins/${a.id}`, {
        method: "PATCH",
        body: JSON.stringify({ active: !a.active }),
      });
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
        eyebrow="КОМАНДА"
        title="Қызметкерлер"
        description="Қызметкерлер және олардың жүйедегі қолжетімділік құқықтары."
        action={
          admin?.role === "SUPER_ADMIN" && (
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus size={17} /> Қызметкер қосу
                </Button>
              </DialogTrigger>
              <DialogContent
                title="Жаңа қызметкер"
                description="Қызметкерге берілетін рөлді мұқият таңдаңыз."
              >
                <form className="form-stack" onSubmit={create}>
                  <label>
                    Аты-жөні
                    <input name="name" required minLength={2} maxLength={200} />
                  </label>
                  <label>
                    Email
                    <input name="email" type="email" required maxLength={254} />
                  </label>
                  <label>
                    Құпиясөз
                    <input
                      name="password"
                      type="password"
                      autoComplete="new-password"
                      required
                      minLength={12}
                      maxLength={128}
                    />
                    <small>Кемінде 12 таңба</small>
                  </label>
                  <label>
                    Рөл
                    <select name="role" defaultValue="OPERATOR">
                      {Object.entries(ROLE_LABELS).map(([key, label]) => (
                        <option key={key} value={key}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <ErrorBox message={error} />
                  <Button type="submit" disabled={busy}>
                    Қызметкерді жасау
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          )
        }
      />
      <ErrorBox message={open ? "" : error || result.error} />
      <section className="panel">
        <div className="panel-heading">
          <h2>
            Команда{" "}
            <span className="count-chip">{result.data?.length || 0}</span>
          </h2>
          <ShieldCheck size={18} />
        </div>
        {result.loading ? (
          <Loading />
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>ҚЫЗМЕТКЕР</th>
                  <th>EMAIL</th>
                  <th>РӨЛ</th>
                  <th>ҚОЛЖЕТІМДІЛІК</th>
                  <th>ӘРЕКЕТ</th>
                </tr>
              </thead>
              <tbody>
                {result.data?.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <div className="person">
                        <span className="avatar">
                          {a.name.slice(0, 2).toUpperCase()}
                        </span>
                        <strong>
                          {a.name}
                          {a.id === admin?.id && <small> · Сіз</small>}
                        </strong>
                      </div>
                    </td>
                    <td>{a.email}</td>
                    <td>{ROLE_LABELS[a.role]}</td>
                    <td>
                      <span
                        className={`badge ${a.active ? "status-COMPLETED" : "status-REJECTED"}`}
                      >
                        <i />
                        {a.active ? "Белсенді" : "Бұғатталған"}
                      </span>
                    </td>
                    <td>
                      {admin?.role === "SUPER_ADMIN" && a.id !== admin.id && (
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={busy}
                          onClick={() => toggle(a)}
                        >
                          {a.active ? "Бұғаттау" : "Белсендіру"}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      <p className="section-note">
        Оператор тек өзіне тағайындалған өтінімдермен жұмыс істейді. Диспетчер
        өтінімдерді басқарады. Бас әкімші қызметкерлер мен жүйе баптауларын
        өзгертеді.
      </p>
    </>
  );
}
