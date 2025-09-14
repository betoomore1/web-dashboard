// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? ""; // залишаємо "", якщо використовуєш rewrites
const ADMIN_TOKEN = process.env.NEXT_PUBLIC_ADMIN_TOKEN ?? "";

type JSONValue = any;

async function request<T = JSONValue>(
  path: string,
  init: RequestInit = {},
  auth = false
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(auth ? { "x-token": ADMIN_TOKEN } : {}),
      ...(init.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText} — ${text || "request failed"}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get: <T = JSONValue>(p: string, auth = false) =>
    request<T>(p, { method: "GET" }, auth),

  post: <T = JSONValue>(p: string, body: unknown, auth = false) =>
    request<T>(
      p,
      { method: "POST", body: JSON.stringify(body ?? {}) },
      auth
    ),

  put: <T = JSONValue>(p: string, body: unknown, auth = false) =>
    request<T>(
      p,
      { method: "PUT", body: JSON.stringify(body ?? {}) },
      auth
    ),

  del: <T = JSONValue>(p: string, auth = false) =>
    request<T>(p, { method: "DELETE" }, auth),
};

// зручні константи ендпоінтів
export const endpoints = {
  calcConfig: "/api/calc/config",
  calcCompute: "/api/calc/compute",
  adminPositions: "/api/admin/positions",
  adminPosition: (name: string) =>
    `/api/admin/positions/${encodeURIComponent(name)}`,
};
