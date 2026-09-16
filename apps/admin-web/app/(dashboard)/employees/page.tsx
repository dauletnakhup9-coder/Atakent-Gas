"use client";

import { useEffect, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/components/ui/toast";
import { ApiError, apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ROLE_LABELS, type AdminOut, type AdminRole } from "@/lib/types";

export default function EmployeesPage() {
  const { admin } = useAuth();
  const { toast } = useToast();
  const [admins, setAdmins] = useState<AdminOut[]>([]);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<AdminRole>("OPERATOR");
  const [creating, setCreating] = useState(false);

  async function load() {
    const data = await apiRequest<AdminOut[]>("/admins");
    setAdmins(data);
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      await apiRequest("/admins", { method: "POST", body: { name, email, password, role } });
      toast({ title: "Қызметкер қосылды" });
      setName("");
      setEmail("");
      setPassword("");
      setRole("OPERATOR");
      await load();
    } catch (err) {
      toast({ title: "Қате", description: err instanceof ApiError ? String(err.detail) : "Белгісіз қате", variant: "destructive" });
    } finally {
      setCreating(false);
    }
  }

  if (admin?.role !== "SUPER_ADMIN") {
    return <p className="text-muted-foreground">Бұл бетке қол жеткізу рұқсаты жоқ.</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Қызметкерлер</h1>

      <Card>
        <CardHeader>
          <CardTitle>Жаңа қызметкер қосу</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="flex flex-col gap-1.5">
              <Label>Аты-жөні</Label>
              <Input required value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Email</Label>
              <Input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Құпия сөз</Label>
              <Input required type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Рөлі</Label>
              <Select value={role} onValueChange={(v) => setRole(v as AdminRole)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(ROLE_LABELS).map(([key, label]) => (
                    <SelectItem key={key} value={key}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="sm:col-span-2 lg:col-span-4">
              <Button type="submit" disabled={creating}>
                Қосу
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-muted/50 text-left text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-3">Аты-жөні</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Рөлі</th>
              <th className="px-4 py-3">Белсенді</th>
            </tr>
          </thead>
          <tbody>
            {admins.map((a) => (
              <tr key={a.id} className="border-b border-border last:border-0">
                <td className="px-4 py-3">{a.name}</td>
                <td className="px-4 py-3">{a.email}</td>
                <td className="px-4 py-3">{ROLE_LABELS[a.role]}</td>
                <td className="px-4 py-3">{a.active ? "Иә" : "Жоқ"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
