// frontend/src/app/calc/page.tsx
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
const ROW_H = 'h-7'; // 1.75rem ≈ 28px
const INPUT = `${ROW_H} px-2 py-0 border rounded w-full`;
const BTN = `${ROW_H} aspect-square p-0 grid place-items-center border rounded transition-transform active:scale-95`;
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
  const [lengthStr, setLengthStr] = useState<string>(''); // порожньо, доки не введуть
  const [width, setWidth] = useState<number>(DEFAULTS.W);
  const [height, setHeight] = useState<number>(DEFAULTS.H);
  const [position, setPosition] = useState<string>('');

  // outputs
  const [out, setOut] = useState<CalcOutput | null>(null);
  const [err, setErr] = useState<string>('');

  // плавна індикація статусу
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
        setLengthStr('');
      } catch (e: any) {
        setErr(String(e?.message || e));
      }
    })();
    setTimeout(() => lengthRef.current?.focus(), 0);
  }, []);

  /* ---------- авто-обчислення (debounce) ---------- */
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
          L,
          W: width,
          H: height,
          position,
        });
        setOut(res);
      } catch (e: any) {
        setErr(String(e?.message || e));
        setOut(null);
      }
    }, 800);

    return () => clearTimeout(handle);
  }, [lengthStr, width, height, position]);

  /* ---------- плавний перехід між повідомленнями ---------- */
  useEffect(() => {
    let next: typeof status = 'needLength';
    if (lengthStr && Number(lengthStr) > 0 && out) next = 'price';
    if (next !== status) {
      setStatus('empty');
      const t = setTimeout(() => setStatus(next), 160);
      return () => clearTimeout(t);
    }
  }, [lengthStr, out, status]);

  /* ---------- піднімати липку панель над моб. клавіатурою ---------- */
  useEffect(() => {
    const vv = (window as any).visualViewport;
    if (!vv) return;
    const handler = () => {
      const extra = Math.max(0, (vv.height + vv.offsetTop) - window.innerHeight);
      document.documentElement.style.setProperty('--vv-bottom', `${extra}px`);
    };
    vv.addEventListener('resize', handler);
    handler();
    return () => vv.removeEventListener('resize', handler);
  }, []);

  /* ================== UI ================== */
  return (
    <main className="p-6 flex justify-center">
      <div className="w-full max-w-[418px] mx-auto px-3 pb-28">
        {/* Шапка */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-semibold">Калькулятор</h1>
            <span
              className={
                'inline-flex h-5 w-5 rounded-full border-2 border-black bg-white items-center justify-center overflow-hidden transition-all duration-200 ' +
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
          >
            Admin
          </a>
        </div>

        <div className="mb-6 border rounded-2xl p-4">
          <h2 className="text-lg font-medium mb-3">Розміри умивальника в &quot;мм&quot;</h2>

          {/* ---------- L ---------- */}
          <div className="mb-3">
            <div className="row">
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
                className={`step-btn ${BTN}`}
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
                className={`step-btn ${BTN}`}
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
                className={`step-btn ${BTN}`}
                title="Скинути всі поля"
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
            <div className="row">
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
                className={`step-btn ${BTN}`}
                onClick={() => {
                  setWidth(width + 10);
                  ok.flash();
                }}
                title="+10"
              >
                <img src="/icons/increase.png" alt="+" className={ICON} />
              </button>
              <button
                className={`step-btn ${BTN}`}
                onClick={() => {
                  setWidth(Math.max(1, width - 10));
                  ok.flash();
                }}
                title="-10"
              >
                <img src="/icons/decrease.png" alt="-" className={ICON} />
              </button>
              <button
                className={`step-btn ${BTN}`}
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
            <div className="row">
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
                className={`step-btn ${BTN}`}
                onClick={() => {
                  setHeight(height + 10);
                  ok.flash();
                }}
                title="+10"
              >
                <img src="/icons/increase.png" alt="+" className={ICON} />
              </button>
              <button
                className={`step-btn ${BTN}`}
                onClick={() => {
                  setHeight(Math.max(1, height - 10));
                  ok.flash();
                }}
                title="-10"
              >
                <img src="/icons/decrease.png" alt="-" className={ICON} />
              </button>
              <button
                className={`step-btn ${BTN}`}
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
            <div className="colors-grid">
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
          <div className="actions-grid">
            <button
              className="px-4 py-2 border rounded transition active:scale-95"
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
              className="px-4 py-2 border rounded transition active:scale-95 disabled:opacity-50"
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
        </div>
      </div>

      {/* Липка панель ціни (видима завжди, вміст змінюється) */}
      <div className="price-sticky">
        <div className="price-inner">
          {/* need length */}
          <span
            className={`transition-opacity duration-200 ${
              status === 'needLength' ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
          >
            Введіть довжину!
          </span>

          {/* price */}
          <span
            className={`transition-opacity duration-200 ${
              status === 'price' && out ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
          >
            {out && <>Вартість виробу — {formatUA(out.price_total)} грн</>}
          </span>
        </div>
      </div>

      {/* помилки API (не блокує лейаут) */}
      {err && (
        <div className="fixed left-1/2 -translate-x-1/2 bottom-[calc(96px+env(safe-area-inset-bottom))] z-50">
          <p className="bg-red-50 text-red-700 border border-red-200 rounded px-3 py-1 text-sm shadow">
            {err}
          </p>
        </div>
      )}

      {/* локальні стилі для нових класів */}
      <style jsx global>{`
        /* рядок з інпутом та трьома кнопками */
        .row {
          display: grid;
          grid-template-columns: 20px 1fr repeat(3, 28px);
          align-items: center;
          gap: 8px;
        }
        /* універсальний стиль для +/-/× */
        .step-btn {
          display: grid;
          place-items: center;
          border-radius: 6px;
        }

        /* сітка кольорів: у 2 колонки на вузьких екранах, далі — в один стовпчик */
        .colors-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 8px;
        }
        @media (max-width: 420px) {
          .colors-grid {
            grid-template-columns: 1fr;
          }
        }
        @media (min-width: 421px) {
          .colors-grid {
            grid-template-columns: 1fr;
          }
        }

        /* дві нижні кнопки — у ряд на широких, у стовпчик на вузьких */
        .actions-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 8px;
          margin-top: 10px;
        }
        @media (min-width: 440px) {
          .actions-grid {
            grid-template-columns: 1fr 1fr;
          }
        }

        /* липка панель ціни унизу екрана */
        .price-sticky {
          position: fixed;
          left: 0;
          right: 0;
          bottom: max(10px, calc(env(safe-area-inset-bottom) + var(--vv-bottom, 0px)));
          z-index: 40;
          pointer-events: none; /* щоб не перекривала натискання по UI */
        }
        .price-inner {
          pointer-events: auto;
          width: fit-content;
          max-width: calc(100vw - 24px);
          margin: 0 auto;
          background: #0f766e0d;            /* легенький бірюзовий фон */
          border: 1px solid #0f766e33;
          color: #065f46;
          backdrop-filter: blur(4px);
          border-radius: 12px;
          padding: 10px 14px;
          font-weight: 700;
          text-align: center;
          box-shadow:
            0 6px 20px rgba(0,0,0,.08),
            0 2px 6px rgba(0,0,0,.06);
        }
      `}</style>
    </main>
  );
}
