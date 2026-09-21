"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, setCsrfToken } from "@/services/api";
import type { Admin } from "@/types";
const AuthContext = createContext<{
  admin: Admin | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}>({
  admin: null,
  loading: true,
  login: async () => {},
  logout: async () => {},
});
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [admin, setAdmin] = useState<Admin | null>(null),
    [loading, setLoading] = useState(true);
  const router = useRouter(),
    path = usePathname();
  useEffect(() => {
    api<{ admin: Admin; csrf_token: string }>("/auth/me")
      .then((data) => {
        setAdmin(data.admin);
        setCsrfToken(data.csrf_token);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
    const expire = () => {
      setAdmin(null);
      setCsrfToken("");
      router.replace("/login");
    };
    window.addEventListener("session-expired", expire);
    return () => window.removeEventListener("session-expired", expire);
  }, [router]);
  useEffect(() => {
    if (!loading && !admin && path !== "/login") router.replace("/login");
  }, [loading, admin, path, router]);
  async function login(email: string, password: string) {
    const data = await api<{ admin: Admin; csrf_token: string }>(
      "/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) },
    );
    setAdmin(data.admin);
    setCsrfToken(data.csrf_token);
    router.replace("/");
  }
  async function logout() {
    await api("/auth/logout", { method: "POST" });
    setAdmin(null);
    setCsrfToken("");
    router.replace("/login");
  }
  return (
    <AuthContext.Provider value={{ admin, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
export function useAuth() {
  return useContext(AuthContext);
}
