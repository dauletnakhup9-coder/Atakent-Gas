"use client";
import { Button } from "@/components/ui/button";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main className="auth-loading">
      <h1>Бетті жүктеу мүмкін болмады</h1>
      <Button onClick={reset}>Қайта көру</Button>
    </main>
  );
}
