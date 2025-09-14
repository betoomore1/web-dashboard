'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';

type BaseSettings = { rounding: string; price_high: number; price_low: number };
type Mode = 'single'|'multi';
type Op = 'mul'|'add'|'sub'|'div';
type GroupItem = { id: string; label: string; op: Op; value: number };
type Group = { id: string; name: string; mode: Mode; items: GroupItem[] };

export default function AdminPage() {
  const [token, setToken] = useState('');
  const [draft, setDraft] = useState('');
  const [base, setBase] = useState<BaseSettings | null>(null);
  const [groups, setGroups] = useState<Group[]>([]);
  const [err, setErr] = useState('');

  useEffect(() => {
    const t = localStorage.getItem('admin_token') || '';
    if (t) { setToken(t); setDraft(t); }
  }, []);

  async function loadAll() {
    setErr('');
    try {
      const [b, g] = await Promise.all([
        api.get<BaseSettings>('/api/admin/base', true),
        api.get<Group[]>('/api/admin/groups', true),
      ]);
      setBase(b);
      setGroups(g);
    } catch (e:any) { setErr(e?.message || String(e)); }
  }

  useEffect(() => { if (token) loadAll(); }, [token]);

  if (!token) {
    return (
      <main className="p-6 max-w-3xl mx-auto">
        <h1 className="text-3xl font-semibold mb-4">Адмінка</h1>
        <div className="border rounded-xl p-4">
          <h2 className="text-lg font-medium mb-2">Введіть токен…</h2>
          <div className="flex gap-2">
            <input type="password" className="border rounded px-3 py-2 w-full"
              value={draft} onChange={e=>setDraft(e.target.value)} />
            <button className="px-4 py-2 border rounded bg-emerald-600 text-white"
              onClick={()=>{ if(!draft.trim())return; localStorage.setItem('admin_token', draft.trim()); setToken(draft.trim()); }}>
              Зберегти
            </button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-semibold">Адмінка</h1>
        <button className="text-sm px-3 py-1 border rounded"
          onClick={()=>{ localStorage.removeItem('admin_token'); setToken(''); setDraft(''); }}>
          Вийти
        </button>
      </div>

      {err && <div className="mb-4 text-red-600">Помилка: {err}</div>}

      {/* ====== БАЗОВІ СТАВКИ ====== */}
      <section className="border rounded-xl p-4 mb-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-medium">Базові ставки</h2>
        </div>
        {base && (
          <div className="grid sm:grid-cols-3 gap-3">
            <label>
              <div className="text-sm text-gray-600 mb-1">Rounding</div>
              <input className="border rounded px-3 py-2 w-full"
                value={base.rounding}
                onChange={e=>setBase({...base, rounding: e.target.value})}/>
            </label>
            <label>
              <div className="text-sm text-gray-600 mb-1">Ціна/м (High)</div>
              <input className="border rounded px-3 py-2 w-full" inputMode="numeric"
                value={base.price_high}
                onChange={e=>setBase({...base, price_high: Number(e.target.value)})}/>
            </label>
            <label>
              <div className="text-sm text-gray-600 mb-1">Ціна/м (Low)</div>
              <input className="border rounded px-3 py-2 w-full" inputMode="numeric"
                value={base.price_low}
                onChange={e=>setBase({...base, price_low: Number(e.target.value)})}/>
            </label>
          </div>
        )}
        <div className="mt-3">
          <button className="px-4 py-2 border rounded bg-emerald-600 text-white"
            onClick={async()=>{
              try { await api.put('/api/admin/base', base, true); alert('Збережено'); }
              catch(e:any){ setErr(e?.message||String(e)); }
            }}>
            Зберегти базові ставки
          </button>
        </div>
      </section>

      {/* ====== ГРУПИ ====== */}
      <section className="border rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-medium">Групи категорій</h2>
          <button className="px-3 py-1 border rounded"
            onClick={async()=>{
              const name = prompt('Назва групи:', 'Колір') || '';
              if (!name.trim()) return;
              try {
                const g = await api.post<Group>('/api/admin/groups', { name, mode:'single', items:[] }, true);
                setGroups(s=>[...s, g]);
              } catch(e:any){ setErr(e?.message||String(e)); }
            }}>
            + Додати групу
          </button>
        </div>

        {groups.length===0 ? <div className="text-sm text-gray-500">Немає груп.</div> : (
          <div className="space-y-4">
            {groups.map(g=>(
              <div key={g.id} className="border rounded p-3">
                <div className="flex items-center justify-between">
                  <div className="font-medium">{g.name} <span className="text-xs text-gray-500">({g.mode})</span></div>
                  <div className="flex gap-2">
                    <button className="px-3 py-1 border rounded"
                      onClick={async()=>{
                        const name = prompt('Нова назва групи', g.name) || g.name;
                        const mode = (prompt('Режим (single|multi)', g.mode) || g.mode) as Mode;
                        try{
                          const upd = await api.put<Group>(`/api/admin/groups/${g.id}`, {name, mode, items:g.items}, true);
                          setGroups(s=>s.map(x=>x.id===g.id?upd:x));
                        }catch(e:any){ setErr(e?.message||String(e)); }
                      }}>
                      Редагувати
                    </button>
                    <button className="px-3 py-1 border rounded text-red-600"
                      onClick={async()=>{
                        if(!confirm('Видалити групу?')) return;
                        try{ await api.del(`/api/admin/groups/${g.id}`, true);
                          setGroups(s=>s.filter(x=>x.id!==g.id));
                        }catch(e:any){ setErr(e?.message||String(e)); }
                      }}>
                      Видалити
                    </button>
                  </div>
                </div>

                {/* items */}
                {g.items.length===0 ? (
                  <div className="text-sm text-gray-500 mt-2">Немає елементів.</div>
                ) : (
                  <ul className="mt-2 list-disc pl-6">
                    {g.items.map(it=>(
                      <li key={it.id} className="flex items-center gap-2">
                        <span className="flex-1">{it.label}</span>
                        <span className="text-sm text-gray-600">{it.op} {it.value}</span>
                      </li>
                    ))}
                  </ul>
                )}

                <div className="mt-2">
                  <button className="px-3 py-1 border rounded"
                    onClick={async()=>{
                      const label = prompt('Назва елемента:','базовий сірий колір') || '';
                      if(!label.trim()) return;
                      const op = (prompt('Операція (mul|add|sub|div):','mul')||'mul') as Op;
                      const value = Number(prompt('Значення:', '0')||'0');
                      const id = String(Date.now());
                      const next = {...g, items:[...g.items, {id,label,op,value}]};
                      try{
                        const upd = await api.put<Group>(`/api/admin/groups/${g.id}`, {name:g.name, mode:g.mode, items:next.items}, true);
                        setGroups(s=>s.map(x=>x.id===g.id?upd:x));
                      }catch(e:any){ setErr(e?.message||String(e)); }
                    }}>
                    + Додати елемент
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
