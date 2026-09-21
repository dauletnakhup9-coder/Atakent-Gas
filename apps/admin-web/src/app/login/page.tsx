"use client";
import { useState } from "react";
import { ArrowRight, Flame, LockKeyhole, ShieldCheck } from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
export default function LoginPage() {
  const { login } = useAuth();
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);
    try {
      await login(String(data.get("email")), String(data.get("password")));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login-page">
      <section className="login-brand">
        <div className="brand">
          <span className="brand-icon">
            <Flame />
          </span>
          <span>
            ATA<span className="brand-gas">K</span>
          </span>
        </div>
        <div className="login-intro">
          <span className="eyebrow">ТҰРҒЫНДАРҒА ЖАҚЫН</span>
          <h1>
            Әр өтінім —<br />
            назарда.
          </h1>
          <p>
            Тұрғындардың өтінімдері, жедел әрекет және қызмет сапасы. Барлығы
            бір кеңістікте.
          </p>
          <div className="login-orbit">
            <Flame size={80} strokeWidth={1} />
          </div>
        </div>
        <span className="login-foot">Қалалық қызметтерді басқару жүйесі</span>
      </section>
      <section className="login-form-side">
        <form className="login-form" onSubmit={submit}>
          <span className="login-lock">
            <LockKeyhole size={24} />
          </span>
          <h2>Қош келдіңіз</h2>
          <p className="muted">
            Жұмыс кеңістігіне кіру үшін деректеріңізді енгізіңіз.
          </p>
          <label>
            Email
            <input
              name="email"
              type="email"
              autoComplete="username"
              placeholder="name@organization.kz"
              required
              maxLength={254}
            />
          </label>
          <label>
            Құпиясөз
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              required
              maxLength={128}
              placeholder="Құпиясөзіңіз"
            />
          </label>
          {error && (
            <div role="alert" className="error">
              {error}
            </div>
          )}
          <Button disabled={busy} type="submit">
            {busy ? "Кіру…" : "Кіру"}
            <ArrowRight size={17} />
          </Button>
          <p className="login-security">
            <ShieldCheck size={15} /> Тек уәкілетті қызметкерлерге арналған
          </p>
        </form>
      </section>
    </main>
  );
}
