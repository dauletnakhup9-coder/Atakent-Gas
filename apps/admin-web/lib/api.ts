const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";
const TOKEN_KEY = "gas_service_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : "Сұраныс қатесі");
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined | null>;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = getToken();
  const url = new URL(`${API_BASE_URL}${path}`);

  if (options.params) {
    for (const [key, value] of Object.entries(options.params)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }

  const resp = await fetch(url.toString(), {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  if (resp.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new ApiError(401, "Авторизация мерзімі аяқталды");
  }

  if (!resp.ok) {
    let detail: unknown = resp.statusText;
    try {
      const data = await resp.json();
      detail = data.detail ?? detail;
    } catch {
      // ignore parse errors, keep statusText
    }
    throw new ApiError(resp.status, detail);
  }

  if (resp.status === 204) {
    return undefined as T;
  }

  const contentType = resp.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return (await resp.json()) as T;
  }
  return (await resp.blob()) as unknown as T;
}

export function apiBaseUrl(): string {
  return API_BASE_URL;
}

export function assetUrl(storageUrl: string): string {
  if (storageUrl.startsWith("http")) return storageUrl;
  const origin = API_BASE_URL.replace(/\/api\/?$/, "");
  return `${origin}${storageUrl}`;
}

export function wsUrl(): string {
  if (/^https?:\/\//.test(API_BASE_URL)) {
    return `${API_BASE_URL.replace(/^http/, "ws")}/ws/applications`;
  }
  // Relative API base (e.g. "/api" behind an nginx reverse proxy): build an
  // absolute ws(s):// URL from the current page origin.
  const protocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss" : "ws";
  const host = typeof window !== "undefined" ? window.location.host : "localhost";
  const path = API_BASE_URL.startsWith("/") ? API_BASE_URL : `/${API_BASE_URL}`;
  return `${protocol}://${host}${path}/ws/applications`;
}
