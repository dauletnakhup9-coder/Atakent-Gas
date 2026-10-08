"use client";
import { useState } from "react";
import { MapPin, Plus } from "lucide-react";
import { useApi } from "@/hooks/use-api";
import { api, downloadSealInstallationsExport } from "@/services/api";
import { useAuth } from "./auth-provider";
import { Empty, ErrorBox, Loading, PageTitle } from "./common";
import { Button } from "./ui/button";
import { Dialog, DialogContent } from "./ui/dialog";

type TechnicianRow = {
  id: number; telegram_user_id: number; full_name: string; active: boolean; version: number; created_at: string;
};
type SealInstallation = {
  id: string; technician_id: number; technician_name: string; account_number: string; meter_number: string;
  reading_value: string; seal_number: string; latitude: number; longitude: number; created_at: string;
};

function TechnicianForm({ editing, busy, error, onSubmit }: {
  editing: TechnicianRow | "new" | null; busy: boolean; error: string; onSubmit: (body: unknown) => void;
}) {
  const current = editing && editing !== "new" ? editing : null;
  return <form key={current?.id || "new"} className="form-stack" onSubmit={(e) => {
    e.preventDefault(); const form = new FormData(e.currentTarget);
    const body = current
      ? { full_name: String(form.get("full_name")), active: form.get("active") === "true", version: current.version }
      : { telegram_user_id: Number(form.get("telegram_user_id")), full_name: String(form.get("full_name")) };
    onSubmit(body);
  }}>
    <label>Telegram ID<input name="telegram_user_id" required inputMode="numeric" pattern="[0-9]+" maxLength={16}
      readOnly={!!current} defaultValue={current?.telegram_user_id || ""} />
      <small>Техниктің Telegram ID-сын ол боттың /start командасын басқанда шыққан хабарламадан алыңыз.</small></label>
    <label>Аты-жөні<input name="full_name" required minLength={2} maxLength={200} defaultValue={current?.full_name} /></label>
    {current && <label>Күйі<select name="active" defaultValue={String(current.active)}>
      <option value="true">Белсенді</option><option value="false">Бұғатталған</option></select></label>}
    <ErrorBox message={error} /><Button type="submit" disabled={busy}>{busy ? "Сақталуда…" : "Сақтау"}</Button>
  </form>;
}

export function Technicians({ revision }: { revision: number }) {
  const { admin } = useAuth();
  const allowed = admin?.role === "SUPER_ADMIN";
  const [tab, setTab] = useState<"installations" | "technicians">("installations");
  const [page, setPage] = useState(1);
  const [local, setLocal] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<TechnicianRow | "new" | null>(null);
  const [photo, setPhoto] = useState<SealInstallation | null>(null);
  const technicians = useApi<{ items: TechnicianRow[] }>(
    allowed && tab === "technicians" ? "/technicians" : null, revision + local,
  );
  const installations = useApi<{ items: SealInstallation[]; total: number }>(
    allowed && tab === "installations" ? `/technicians/seal-installations?page=${page}` : null, revision + local,
  );

  async function mutate(path: string, method: string, body: unknown) {
    setBusy(true); setError("");
    try {
      await api(path, { method, body: JSON.stringify(body) });
      setLocal((n) => n + 1); setEditing(null);
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }

  if (!allowed) return <Empty title="Қолжетімділік шектелген" text="Техниктер мен пломба жазбаларын бас әкімші басқарады." />;
  return <>
    <PageTitle eyebrow="ПЛОМБАЛАР" title="Техниктер және пломба орнату"
      description="Далалық техниктерге Telegram арқылы қолжетімділік беру және олардың пломба орнату есептерін қарау."
      action={tab === "installations" ? <div className="subscriber-toolbar">
        <Button variant="outline" onClick={() => void downloadSealInstallationsExport("csv")}>CSV экспорт</Button>
        <Button variant="outline" onClick={() => void downloadSealInstallationsExport("xlsx")}>Excel экспорт</Button>
      </div> : <Button onClick={() => { setError(""); setEditing("new"); }}><Plus size={17} /> Техник қосу</Button>} />
    <div className="subscriber-toolbar">
      <Button variant={tab === "installations" ? "default" : "outline"}
        onClick={() => { setTab("installations"); setPage(1); }}>Пломба орнату есептері</Button>
      <Button variant={tab === "technicians" ? "default" : "outline"} onClick={() => setTab("technicians")}>Техниктер</Button>
    </div>
    <ErrorBox message={editing || photo ? "" : error || (tab === "technicians" ? technicians.error : installations.error)} />
    {tab === "technicians" ? (
      <section className="panel">
        <div className="panel-heading"><h2>Тіркелген техниктер <span className="count-chip">{technicians.data?.items.length || 0}</span></h2></div>
        {technicians.loading ? <Loading /> : !technicians.data?.items.length ? (
          <Empty title="Техник жоқ" text="Телефонмен емес, Telegram ID арқылы техник қосыңыз." />
        ) : (
          <div className="table-scroll"><table><thead><tr>
            {["TELEGRAM ID", "АТЫ-ЖӨНІ", "КҮЙІ", "ТІРКЕЛГЕН", "ӘРЕКЕТ"].map((l) => <th key={l}>{l}</th>)}
          </tr></thead><tbody>
            {technicians.data.items.map((t) => <tr key={t.id}>
              <td className="mono">{t.telegram_user_id}</td><td>{t.full_name}</td>
              <td>{t.active ? "Белсенді" : "Бұғатталған"}</td><td>{t.created_at.slice(0, 10)}</td>
              <td><Button size="sm" variant="ghost" onClick={() => { setError(""); setEditing(t); }}>Өзгерту</Button></td>
            </tr>)}
          </tbody></table></div>
        )}
      </section>
    ) : (
      <section className="panel">
        <div className="panel-heading"><h2>Пломба орнату есептері <span className="count-chip">{installations.data?.total || 0}</span></h2></div>
        {installations.loading ? <Loading /> : !installations.data?.items.length ? (
          <Empty title="Жазба жоқ" text="Техниктер орнатқан пломбалар осы жерде пайда болады." />
        ) : (
          <div className="table-scroll"><table><thead><tr>
            {["КҮНІ", "ТЕХНИК", "ДЕРБЕС ШОТ", "ЕСЕПТЕГІШ", "ПЛОМБА", "КӨРСЕТКІШ", "КООРДИНАТТАР", "ФОТО"].map((l) => <th key={l}>{l}</th>)}
          </tr></thead><tbody>
            {installations.data.items.map((s) => <tr key={s.id}>
              <td>{s.created_at.slice(0, 16).replace("T", " ")}</td><td>{s.technician_name}</td>
              <td className="mono">{s.account_number}</td><td>{s.meter_number}</td><td>{s.seal_number}</td>
              <td>{s.reading_value}</td>
              <td><a className="map-link" href={`https://www.google.com/maps?q=${s.latitude},${s.longitude}`}
                target="_blank" rel="noreferrer"><MapPin size={13} /> {s.latitude.toFixed(5)}, {s.longitude.toFixed(5)}</a></td>
              <td><Button size="sm" variant="ghost" onClick={() => setPhoto(s)}>Фото</Button></td>
            </tr>)}
          </tbody></table></div>
        )}
        <div className="subscriber-toolbar"><Button variant="outline" disabled={page <= 1} onClick={() => setPage(page - 1)}>Алдыңғы</Button>
          <span>{page}-бет</span><Button variant="outline" disabled={page * 25 >= (installations.data?.total || 0)}
            onClick={() => setPage(page + 1)}>Келесі</Button></div>
      </section>
    )}
    <Dialog open={editing !== null} onOpenChange={(open) => { if (!open && !busy) setEditing(null); }}>
      <DialogContent title={editing && editing !== "new" ? "Техникті өзгерту" : "Жаңа техник"}
        description="Техник Telegram ID-сын ол боттың /start командасын басқанда шыққан хабарламадан алыңыз.">
        <TechnicianForm editing={editing} busy={busy} error={error}
          onSubmit={(body) => mutate(editing && editing !== "new" ? `/technicians/${(editing as TechnicianRow).id}` : "/technicians",
            editing && editing !== "new" ? "PUT" : "POST", body)} />
      </DialogContent>
    </Dialog>
    <Dialog open={photo !== null} onOpenChange={(open) => { if (!open) setPhoto(null); }}>
      <DialogContent title="Пломба орнату фотосы" description={photo ? `${photo.account_number} · ${photo.seal_number}` : ""}>
        {photo && <img className="lightbox-image" src={`/api/technicians/seal-installations/${photo.id}/photo`} alt="Пломба орнату фотосы" />}
      </DialogContent>
    </Dialog>
  </>;
}
