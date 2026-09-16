"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { apiRequest, clearToken, getToken, setToken } from "@/lib/api";
import type { AdminOut } from "@/lib/types";

interface AuthContextValue {
  admin: AdminOut | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<AdminOut | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    apiRequest<AdminOut>("/auth/me")
      .then(setAdmin)
      .catch(() => setAdmin(null))
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const result = await apiRequest<{ access_token: string; admin: AdminOut }>("/auth/login", {
      method: "POST",
      body: { email, password },
    });
    setToken(result.access_token);
    setAdmin(result.admin);
    router.push("/");
  }

  function logout() {
    clearToken();
    setAdmin(null);
    router.push("/login");
  }

  return <AuthContext.Provider value={{ admin, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
