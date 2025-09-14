// src/lib/api.ts
export const API_BASE =
  (process.env.NEXT_PUBLIC_API_BASE || "").replace(/\/$/, ""); // "" у деві = той самий домен

async function toJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const tail = (await res.text()).slice(0, 200); // не показувати кілометр HTML у помилці
    throw new Error(`${res.status} ${res.statusText}: ${tail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  get:  <T>(path: string) =>
    fetch(`${API_BASE}${path}`, { credentials: "omit" }).then(toJson<T>),

  post: <T>(path: string, body: unknown) =>
    fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      credentials: "omit",
    }).then(toJson<T>),

  put:  <T>(path: string, body: unknown) =>
    fetch(`${API_BASE}${path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      credentials: "omit",
    }).then(toJson<T>),
};
