"use client";

import { ExternalLink } from "lucide-react";
import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { PhotoLightbox } from "@/components/applications/PhotoLightbox";
import { PriorityBadge } from "@/components/applications/PriorityBadge";
import { StatusBadge } from "@/components/applications/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import { ApiError, apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  APPLICATION_TYPE_LABELS,
  STATUS_LABELS,
  type AdminOut,
  type ApplicationDetailOut,
  type ApplicationStatus,
} from "@/lib/types";
import { formatDate, formatDateTime } from "@/lib/utils";

const MapView = dynamic(() => import("@/components/applications/MapView"), { ssr: false });

export default function ApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const { admin } = useAuth();
  const { toast } = useToast();

  const [application, setApplication] = useState<ApplicationDetailOut | null>(null);
  const [admins, setAdmins] = useState<AdminOut[]>([]);
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);

  const canAssign = admin?.role === "SUPER_ADMIN" || admin?.role === "DISPATCHER";

  async function load() {
    const app = await apiRequest<ApplicationDetailOut>(`/applications/${params.id}`);
    setApplication(app);
    setComment(app.admin_comment ?? "");
  }

  useEffect(() => {
    load();
    if (canAssign) {
      apiRequest<AdminOut[]>("/admins").then(setAdmins).catch(() => setAdmins([]));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  async function handleStatusChange(status: ApplicationStatus) {
    if (!application) return;
    setSaving(true);
    try {
      const updated = await apiRequest<ApplicationDetailOut>(`/applications/${application.id}/status`, {
        method: "PATCH",
        body: { status, comment: comment || undefined },
      });
      setApplication(updated);
      toast({ title: "Статус жаңартылды", description: STATUS_LABELS[status] });
    } catch (err) {
      toast({ title: "Қате", description: err instanceof ApiError ? String(err.detail) : "Белгісіз қате", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  }

  async function handleAssign(adminId: string) {
    if (!application) return;
    setSaving(true);
    try {
      const updated = await apiRequest<ApplicationDetailOut>(`/applications/${application.id}/assign`, {
        method: "PATCH",
        body: { admin_id: Number(adminId) },
      });
      setApplication(updated);
      toast({ title: "Орындаушы тағайындалды" });
    } catch (err) {
      toast({ title: "Қате", description: err instanceof ApiError ? String(err.detail) : "Белгісіз қате", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveComment() {
    if (!application) return;
    setSaving(true);
    try {
      const updated = await apiRequest<ApplicationDetailOut>(`/applications/${application.id}/comments`, {
        method: "POST",
        body: { comment },
      });
      setApplication(updated);
      toast({ title: "Пікір сақталды" });
    } catch (err) {
      toast({ title: "Қате", description: err instanceof ApiError ? String(err.detail) : "Белгісіз қате", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  }

  if (!application) {
    return <p className="text-muted-foreground">Жүктелуде...</p>;
  }

  const isCritical = application.priority === "CRITICAL";
  const mapsLink = application.latitude && application.longitude
    ? `https://www.openstreetmap.org/?mlat=${application.latitude}&mlon=${application.longitude}#map=17/${application.latitude}/${application.longitude}`
    : null;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{application.application_number}</h1>
            {isCritical && (
              <span className="rounded-full bg-critical px-3 py-1 text-xs font-bold text-critical-foreground">
                🚨 АВАРИЯ
              </span>
            )}
          </div>
          <p className="text-sm text-muted-foreground">{formatDateTime(application.created_at)}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={application.status} />
          <PriorityBadge priority={application.priority} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Өтінім мәліметтері</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4 text-sm">
              <Info label="Дербес шот" value={application.personal_account} />
              <Info label="Өтінім түрі" value={APPLICATION_TYPE_LABELS[application.application_type]} />
              <Info
                label="Telegram пайдаланушысы"
                value={
                  application.user.first_name ??
                  (application.user.telegram_username ? `@${application.user.telegram_username}` : String(application.user.telegram_user_id))
                }
              />
              {application.requested_date && <Info label="МПИ күні" value={formatDate(application.requested_date)} />}
            </CardContent>
          </Card>

          {application.files.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Фотосуреттер</CardTitle>
              </CardHeader>
              <CardContent>
                <PhotoLightbox files={application.files} />
              </CardContent>
            </Card>
          )}

          {application.latitude && application.longitude && (
            <Card>
              <CardHeader className="flex-row items-center justify-between">
                <CardTitle>Геолокация</CardTitle>
                {mapsLink && (
                  <a href={mapsLink} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-xs text-primary hover:underline">
                    Картадан ашу <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                <p className="text-xs text-muted-foreground">
                  Latitude: {application.latitude} · Longitude: {application.longitude}
                </p>
                <div className="h-72 overflow-hidden rounded-md">
                  <MapView latitude={application.latitude} longitude={application.longitude} label={application.application_number} />
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Өзгерістер тарихы</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {application.history.map((h) => (
                <div key={h.id} className="border-l-2 border-border pl-3 text-sm">
                  <p className="font-medium">{STATUS_LABELS[h.new_status]}</p>
                  {h.comment && <p className="text-muted-foreground">{h.comment}</p>}
                  <p className="text-xs text-muted-foreground">
                    {h.admin_name ?? "Жүйе"} · {formatDateTime(h.created_at)}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Статусты өзгерту</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {(Object.keys(STATUS_LABELS) as ApplicationStatus[]).map((s) => (
                <Button
                  key={s}
                  variant={s === application.status ? "default" : "outline"}
                  disabled={saving || s === application.status}
                  onClick={() => handleStatusChange(s)}
                >
                  {STATUS_LABELS[s]}
                </Button>
              ))}
            </CardContent>
          </Card>

          {canAssign && (
            <Card>
              <CardHeader>
                <CardTitle>Орындаушыны тағайындау</CardTitle>
              </CardHeader>
              <CardContent>
                <Select value={application.assigned_admin ? String(application.assigned_admin.id) : undefined} onValueChange={handleAssign}>
                  <SelectTrigger>
                    <SelectValue placeholder="Қызметкерді таңдаңыз" />
                  </SelectTrigger>
                  <SelectContent>
                    {admins.map((a) => (
                      <SelectItem key={a.id} value={String(a.id)}>
                        {a.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Комментарий</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              <Textarea value={comment} onChange={(e) => setComment(e.target.value)} rows={4} />
              <Button size="sm" onClick={handleSaveComment} disabled={saving}>
                Сақтау
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}
