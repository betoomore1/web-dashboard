'use client';

import { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';

/* ================== Types ================== */
type CalcConfig = {
  variables: {
    min_length: number;
    max_length: number;
    min_width: number;
    min_height: number;
    extra_price: number;
    rounding?: string;
  };
  price_per_meter: { high: number; low: number };
  positions: Record<string, number>;
};

type CalcOutput = {
  price_per_meter: number;
  price_base: number;
  surcharge_width: number;
  surcharge_height: number;
  surcharge_color_percent: number;
  surcharge_color_amount: number;
  price_total: number;
};

/* ================== UI consts ================== */
/** зменшили висоту рядка ~ на 1/3 */
const ROW_H = 'h-7'; // 1.75rem ≈ 28px
const INPUT = `${ROW_H} px-2 py-0 border rounded w-full`;
/** квадратні кнопки, ширина дорівнює висоті рядка */
const BTN = `${ROW_H} aspect-square p-0 grid place-items-center border rounded transition-transform active:scale-95`;
/** не деформуємо іконки */
const ICON = 'w-4 h-4 object-contain';

const DEFAULTS = { L: 500, W: 500, H: 150 };
const BASE_KEY = 'базовий сірий колір';

/* ================== Helpers ================== */
function useFlash(ms = 900) {
  const [on, setOn] = useState(false);
  const flash = () => {
    setOn(true);
    setTimeout(() => setOn(false), ms);
  };
  return { on, flash };
}
// Формат числа з пробілами між тисячами (uk-UA дає нерозривні — міняємо на звичайні)
function formatUA(n: number) {
  return n.toLocaleString('uk-UA').replace(/\u202F|\u00A0/g, ' ');
}
const parseFirstNumber = (s: string) => {
  const m = s.match(/\d+/);
  return m ? Number(m[0]) : NaN;
};

/* ================== Page ================== */
export default function CalcPage() {
  // config
  const [cfg, setCfg] = useState<CalcConfig | null>(null);

  // inputs (length як РЯДОК — дозволяє порожній стан)
  const [lengthStr, setLengthStr] = useState<string>(''); // пусто за замовчуванням
  const [width, setWidth] = useState<number>(DEFAULTS.W);
  const [height, setHeight] = useState<number>(DEFAULTS.H);
  const [position, setPosition] = useState<string>('');

  // outputs
  const [out, setOut] = useState<CalcOutput | null>(null);
  const [err, setErr] = useState<string>('');

  // статус тексту знизу: плавний перехід через "порожньо"
  const [status, setStatus] = useState<'empty' | 'needLength' | 'price'>('needLength');

  // refs & flash
  const lengthRef = useRef<HTMLInputElement>(null);
  const ok = useFlash(900);

  /* ---------- load config + autofocus ---------- */
  useEffect(() => {
    (async () => {
      try {
        const c = await api.get<CalcConfig>('/api/calc/config');
        setCfg(c);
        const keys = Object.keys(c.positions ?? {});
        const base = keys.find((k) => k === BASE_KEY) || keys[0] || '';
        setPosition(base);
        setLengthStr(''); // довжина лишається пустою
      } catch (e: any) {
        setErr(String(e?.message || e));
      }
    })();

    // курсор одразу в полі L
    setTimeout(() => lengthRef.current?.focus(), 0);
  }, []);

  /* ---------- auto compute (debounce) ---------- */
  useEffect(() => {
    setErr('');
    const handle = setTimeout(async () => {
      const L = Number(lengthStr);
      if (!lengthStr || isNaN(L) || L <= 0) {
        setOut(null);
        return;
      }
      try {
        const res = await api.post<CalcOutput>('/api/calc/compute', {
          L: L,            // було length_mm
          W: width,        // було width_mm
          H: height,       // було height_mm
          position,        // назва вибраної опції
        });
        setOut(res);
      } catch (e: any) {
        setErr(String(e?.message || e));
        setOut(null);
      }
    }, 1000); // ↑ зробив більшу паузу перед підрахунком

    return () => clearTimeout(handle);
  }, [lengthStr, width, height, position]);

  /* ---------- плавний перехід між повідомленнями ---------- */
  useEffect(() => {
    let next: typeof status = 'needLength';
    if (lengthStr && Number(lengthStr) > 0 && out) next = 'price';

    if (next !== status) {
      setStatus('empty'); // на мить ховаємо все
      const t = setTimeout(() => setStatus(next), 180); // і показуємо нове
      return () => clearTimeout(t);
    }
  }, [lengthStr, out, status]);

  /* ================== UI ================== */
  return (
    <main className="p-6 flex justify-center">
      <div className="w-full max-w-[418px] mx-auto px-3">
        {/* Шапка: заголовок + індикатор успіху + Admin */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-semibold">Калькулятор</h1>

            {/* Індикатор «успішно» (замість плаваючого вгорі) */}
            <span
              className={
                'inline-flex h-5 w-5 rounded-full border-2 border-black bg-white ' +
                'items-center justify-center overflow-hidden transition-all duration-200 ease-out ' +
                (ok.on ? 'opacity-100 scale-100' : 'opacity-0 scale-75 pointer-events-none')
              }
              title="Готово"
              aria-hidden={!ok.on}
            >
              <img src="/icons/check.png" alt="ok" className="w-5 h-5 object-contain" />
            </span>
          </div>

          <a
            href="/admin"
            className="text-sm px-3 py-1 border rounded hover:bg-gray-50 active:scale-95 transition"
            title="Перейти до адмінки"
          >
            Admin
          </a>
        </div>

        <div className="mb-6 border rounded-2xl p-4">
          <h2 className="text-lg font-medium mb-2">Розміри умивальника в &quot;мм&quot;</h2>

          {/* ---------- L ---------- */}
          <div className="mb-3">
            <div className="flex items-center gap-2">
              <img src="/icons/length.png" alt="L" className={ICON} />
              <input
                ref={lengthRef}
                autoFocus
                inputMode="numeric"
                className={INPUT}
                placeholder="Введіть довжину"
                value={lengthStr}
                onChange={(e) => setLengthStr(e.target.value.trim())}
                onBlur={ok.flash}
              />
              <button
                className={BTN}
                onClick={() => {
                  const v = Number(lengthStr || 0) + 10;
                  setLengthStr(String(v));
                  ok.flash();
                }}
                title="+10"
              >
                <img src="/icons/increase.png" alt="+" className={ICON} />
              </button>
              <button
                className={BTN}
                onClick={() => {
                  const v = Math.max(0, Number(lengthStr || 0) - 10);
                  setLengthStr(String(v));
                  ok.flash();
                }}
                title="-10"
              >
                <img src="/icons/decrease.png" alt="-" className={ICON} />
              </button>
              <button
                className={BTN}
                title="Скинути ВСЕ до початкового стану"
                onClick={() => {
                  setLengthStr('');
                  setWidth(DEFAULTS.W);
                  setHeight(DEFAULTS.H);
                  if (cfg?.positions && cfg.positions[BASE_KEY] !== undefined) {
                    setPosition(BASE_KEY);
                  }
                  setOut(null);
                  setErr('');
                  setStatus('needLength');
                  ok.flash();
                  setTimeout(() => lengthRef.current?.focus(), 0);
                }}
              >
                <img src="/icons/clear.png" alt="×" className={ICON} />
              </button>
            </div>
          </div>

          {/* ---------- W ---------- */}
          <div className="mb-3">
            <div className="flex items-center gap-2">
              <img src="/icons/width.png" alt="W" className={ICON} />
              <input
                type="number"
                min={1}
                className={INPUT}
                value={width}
                onChange={(e) => {
                  setWidth(Number(e.target.value));
                  ok.flash();
                }}
              />
              <button
                className={BTN}
                onClick={() => {
                  setWidth(width + 10);
                  ok.flash();
                }}
                title="+10"
              >
                <img src="/icons/increase.png" alt="+" className={ICON} />
              </button>
              <button
                className={BTN}
                onClick={() => {
                  setWidth(Math.max(1, width - 10));
                  ok.flash();
                }}
                title="-10"
              >
                <img src="/icons/decrease.png" alt="-" className={ICON} />
              </button>
              <button
                className={BTN}
                onClick={() => {
                  setWidth(DEFAULTS.W);
                  ok.flash();
                }}
                title="Скинути"
              >
                <img src="/icons/clear.png" alt="×" className={ICON} />
              </button>
            </div>
          </div>

          {/* ---------- H ---------- */}
          <div className="mb-3">
            <div className="flex items-center gap-2">
              <img src="/icons/height.png" alt="H" className={ICON} />
              <input
                type="number"
                min={1}
                className={INPUT}
                value={height}
                onChange={(e) => {
                  setHeight(Number(e.target.value));
                  ok.flash();
                }}
              />
              <button
                className={BTN}
                onClick={() => {
                  setHeight(height + 10);
                  ok.flash();
                }}
                title="+10"
              >
                <img src="/icons/increase.png" alt="+" className={ICON} />
              </button>
              <button
                className={BTN}
                onClick={() => {
                  setHeight(Math.max(1, height - 10));
                  ok.flash();
                }}
                title="-10"
              >
                <img src="/icons/decrease.png" alt="-" className={ICON} />
              </button>
              <button
                className={BTN}
                onClick={() => {
                  setHeight(DEFAULTS.H);
                  ok.flash();
                }}
                title="Скинути"
              >
                <img src="/icons/clear.png" alt="×" className={ICON} />
              </button>
            </div>
          </div>

          {/* ---------- Колір (радіо) ---------- */}
          <fieldset className="mb-3 pl-6">
            <legend className="text-sm font-medium mb-1">Колір:</legend>
            <div className="space-y-2">
              {Object.keys(cfg?.positions ?? {}).map((k) => (
                <label key={k} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="position"
                    value={k}
                    checked={position === k}
                    onChange={() => setPosition(k)}
                  />
                  <span>{k}</span>
                </label>
              ))}
            </div>
          </fieldset>

          {/* ---------- Дії ---------- */}
          <div className="mt-2 flex flex-col items-center gap-2 min-[440px]:flex-row min-[440px]:justify-center">
            <button
              className="w-full min-[440px]:w-auto whitespace-nowrap px-4 py-2 border rounded transition active:scale-95"
              onClick={async () => {
                try {
                  const text = await navigator.clipboard.readText();
                  const n = parseFirstNumber(text);
                  if (isNaN(n)) return alert('У буфері немає числа');
                  setLengthStr(String(n));
                  ok.flash();
                } catch {
                  alert('Бракує доступу до буфера обміну');
                }
              }}
            >
              Вставити довжину
            </button>

            <button
              className="w-full min-[440px]:w-auto whitespace-nowrap px-4 py-2 border rounded transition active:scale-95"
              disabled={!out}
              onClick={async () => {
                if (!out) return;
                await navigator.clipboard.writeText(`${formatUA(out.price_total)} грн`);
                ok.flash();
              }}
            >
              Скопіювати вартість
            </button>
          </div>

          {/* ---------- Підсумок/статус (без «карти результатів») ---------- */}
          <div className="mt-3">
            <div className="relative h-8 text-center overflow-hidden" aria-live="polite">
              {/* "Введіть довжину!" */}
              <span
                className={`absolute inset-0 flex items-center justify-center text-red-600 font-bold text-xl transition-opacity duration-200 ${
                  status === 'needLength' ? 'opacity-100' : 'opacity-0 pointer-events-none'
                }`}
              >
                Введіть довжину!
              </span>

              {/* "Вартість виробу…" — показуємо лише коли Є out */}
              <span
                className={`absolute inset-0 flex items-center justify-center text-emerald-700 font-bold text-xl transition-opacity duration-200 ${
                  status === 'price' && out ? 'opacity-100' : 'opacity-0 pointer-events-none'
                }`}
              >
                {out && <>Вартість виробу - {formatUA(out.price_total)} грн</>}
              </span>
            </div>

            {err && <p className="w-full text-center text-red-600 text-sm mt-2">{err}</p>}
          </div>
        </div>
      </div>
    </main>
  );
}
