"use client";

import { LogOut, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { useAuth } from "@/lib/auth";
import { ROLE_LABELS } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function Header() {
  const { admin, logout } = useAuth();
  const router = useRouter();
  const [query, setQuery] = useState("");

  function handleSearch(e: FormEvent) {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/applications?search=${encodeURIComponent(query.trim())}`);
    }
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-card px-6">
      <form onSubmit={handleSearch} className="flex max-w-sm flex-1 items-center gap-2">
        <Search className="h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Өтінім нөмірі немесе дербес шот бойынша іздеу"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="h-9 border-none bg-muted"
        />
      </form>
      <div className="flex items-center gap-4">
        {admin && (
          <div className="text-right text-sm">
            <p className="font-medium">{admin.name}</p>
            <p className="text-xs text-muted-foreground">{ROLE_LABELS[admin.role]}</p>
          </div>
        )}
        <Button variant="ghost" size="icon" onClick={logout} title="Шығу">
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
