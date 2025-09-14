// frontend/src/lib/api.ts
const BASE =
  process.env.NEXT_PUBLIC_API_BASE ||
  "https://web-dashboard-production.up.railway.app"; // ← ВСТАВ свій бекенд URL БЕЗ кінцевого '/'

async function toJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} — ${text.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  get:  <T>(path: string)              => fetch(`${BASE}${path}`, { headers:{'Content-Type':'application/json'} }).then(toJson<T>),
  post: <T>(path: string, body:unknown)=> fetch(`${BASE}${path}`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) }).then(toJson<T>),
  put:  <T>(path: string, body:unknown)=> fetch(`${BASE}${path}`, { method:'PUT',  headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) }).then(toJson<T>),
};
