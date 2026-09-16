"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/components/ui/toast";
import { ApiError, apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const FIELDS: { key: string; label: string; superAdminOnly?: boolean; type?: string }[] = [
  { key: "organization_name", label: "Ұйым атауы" },
  { key: "contact_phone", label: "Байланыс телефоны" },
  { key: "emergency_phone", label: "Авариялық қызмет нөмірі", superAdminOnly: true },
  { key: "max_photo_size_mb", label: "Фотоның максималды өлшемі (MB)", superAdminOnly: true, type: "number" },
];

export default function SettingsPage() {
  const { admin } = useAuth();
  const { toast } = useToast();
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiRequest<Record<string, string>>("/settings").then(setValues);
  }, []);

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await apiRequest<Record<string, string>>("/settings", { method: "PATCH", body: { values } });
      setValues(updated);
      toast({ title: "Баптаулар сақталды" });
    } catch (err) {
      toast({ title: "Қате", description: err instanceof ApiError ? String(err.detail) : "Белгісіз қате", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Баптаулар</h1>

      <Card>
        <CardHeader>
          <CardTitle>Жалпы параметрлер</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {FIELDS.filter((f) => !f.superAdminOnly || admin?.role === "SUPER_ADMIN").map((field) => (
            <div key={field.key} className="flex flex-col gap-1.5">
              <Label>{field.label}</Label>
              <Input
                type={field.type ?? "text"}
                value={values[field.key] ?? ""}
                onChange={(e) => setValues((v) => ({ ...v, [field.key]: e.target.value }))}
              />
            </div>
          ))}
          <div className="sm:col-span-2">
            <Button onClick={handleSave} disabled={saving}>
              Сақтау
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
