'use client';

import { useState } from 'react';
import { ChevronLeft, Sparkles, Loader2, RefreshCw, Plus, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import Link from 'next/link';
import { useAuthGuard } from '@/lib/useAuthGuard';
import { useIdleLogout } from '@/lib/useIdleLogout';
import {
  analyzeNumber, recommendNumbers, ENERGY_INFO, ALL_ENERGIES,
  type NumerologyAnalysis, type EnergyName,
} from '@/lib/numerology';

type TabKey = 'personal' | 'advanced' | 'recommend';

export default function NumerologyPage() {
  const { ready: __authReady } = useAuthGuard();
  useIdleLogout();
  const [tab, setTab] = useState<TabKey>('personal');

  if (!__authReady) return null;

  return (
    <div className="px-4 py-5 space-y-4 pb-24">
      <div className="flex items-center gap-3">
        <Link href="/profile" className="p-1"><ChevronLeft className="h-5 w-5 text-gray-600" /></Link>
        <div className="flex-1">
          <h1 className="text-lg font-bold text-gray-900 flex items-center gap-1">
            <Sparkles className="h-5 w-5 text-purple-500" /> 幫人生拿副好牌
          </h1>
          <p className="text-xs text-gray-500">數字易經分析 · 用八宅遊星看你的數字能量</p>
        </div>
      </div>

      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 text-xs font-semibold">
        {[
          { k: 'personal',  l: '個人分析' },
          { k: 'advanced',  l: '進階分析' },
          { k: 'recommend', l: '吉祥推薦' },
        ].map((t) => (
          <button
            key={t.k}
            onClick={() => setTab(t.k as TabKey)}
            className={`flex-1 py-2 rounded-lg transition ${tab === t.k ? 'bg-white text-purple-700 shadow-sm' : 'text-gray-500'}`}
          >
            {t.l}
          </button>
        ))}
      </div>

      {tab === 'personal' && <PersonalTab />}
      {tab === 'advanced' && <AdvancedTab />}
      {tab === 'recommend' && <RecommendTab />}
    </div>
  );
}

// ───────────────── 共用：分析結果展示卡片 ─────────────────

function AnalysisCard({ label, input, hideIfEmpty = true }: { label: string; input: string; hideIfEmpty?: boolean }) {
  if (hideIfEmpty && !input.trim()) return null;
  const [expanded, setExpanded] = useState(false);
  const a = analyzeNumber(input);
  if (a.digits.length < 2) {
    return (
      <div className="rounded-xl bg-gray-50 p-3 text-xs text-gray-500">
        <b>{label}</b>：{input || '（空）'} — 字數不足無法分析
      </div>
    );
  }
  return (
    <div className="rounded-xl bg-white border border-gray-200 p-3 space-y-2">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div>
          <p className="text-xs text-gray-500">{label}</p>
          <p className="text-sm font-mono font-bold text-gray-900">{input}</p>
        </div>
        <div className="text-right">
          <p className="text-base font-bold" style={{ color: a.ratingColor }}>{a.ratingLabel}</p>
          <p className="text-[10px] text-gray-400">分數 {a.totalScore.toFixed(1)} · 吉 {a.auspiciousCount} / 凶 {a.inauspiciousCount}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-1">
        {a.pairs.map((p, i) => {
          const meta = ENERGY_INFO[p.energy];
          return (
            <span
              key={i}
              className="inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-semibold"
              style={{ backgroundColor: meta.color + '20', color: meta.color }}
              title={`${p.a}${p.b}: ${meta.desc}`}
            >
              <span className="opacity-60">{p.a}{p.b}</span>
              {meta.emoji}{p.energy}
            </span>
          );
        })}
      </div>

      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-[11px] text-purple-600 hover:underline"
      >
        {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        {expanded ? '收起說明' : '看每個能量說明'}
      </button>
      {expanded && (
        <div className="space-y-1 pt-1 border-t border-gray-100">
          {Object.entries(a.energyCounts).sort((x, y) => (y[1] as number) - (x[1] as number)).map(([e, n]) => {
            const meta = ENERGY_INFO[e as EnergyName];
            return (
              <div key={e} className="text-[11px] flex items-start gap-1">
                <span style={{ color: meta.color }} className="font-bold">{meta.emoji} {e} ×{n}</span>
                <span className="text-gray-600">— {meta.desc}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ───────────────── Tab A: 個人分析 ─────────────────

function PersonalTab() {
  const [idNumber, setIdNumber] = useState('');
  const [birth, setBirth] = useState('');           // YYYY-MM-DD
  const [phone1, setPhone1] = useState('');
  const [phone2, setPhone2] = useState('');
  const [carPlate1, setCarPlate1] = useState('');
  const [carPlate2, setCarPlate2] = useState('');
  const [motoPlate1, setMotoPlate1] = useState('');
  const [motoPlate2, setMotoPlate2] = useState('');

  const inputClass = 'w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:border-purple-500';
  const labelClass = 'block text-xs font-medium text-gray-600 mb-1';

  return (
    <div className="space-y-3">
      <div className="rounded-xl bg-purple-50 p-3 text-xs text-purple-900 leading-relaxed">
        💡 填入下面的個人號碼，下方會即時顯示每組號碼的數字易經能量分析。可以多組同時看，比較出最有利的。
      </div>
      <div className="rounded-xl bg-white border border-gray-100 p-4 space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass}>身分證字號</label>
            <input className={inputClass} value={idNumber} onChange={(e) => setIdNumber(e.target.value.toUpperCase())} placeholder="A123456789" maxLength={10} />
          </div>
          <div>
            <label className={labelClass}>生日</label>
            <input type="date" className={inputClass} value={birth} onChange={(e) => setBirth(e.target.value)} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass}>手機 1</label>
            <input type="tel" className={inputClass} value={phone1} onChange={(e) => setPhone1(e.target.value)} placeholder="0912-345-678" />
          </div>
          <div>
            <label className={labelClass}>手機 2（選填）</label>
            <input type="tel" className={inputClass} value={phone2} onChange={(e) => setPhone2(e.target.value)} placeholder="0978-..." />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass}>汽車車牌 1</label>
            <input className={inputClass} value={carPlate1} onChange={(e) => setCarPlate1(e.target.value.toUpperCase())} placeholder="ABC-1234" />
          </div>
          <div>
            <label className={labelClass}>汽車車牌 2（選填）</label>
            <input className={inputClass} value={carPlate2} onChange={(e) => setCarPlate2(e.target.value.toUpperCase())} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass}>機車車牌 1（選填）</label>
            <input className={inputClass} value={motoPlate1} onChange={(e) => setMotoPlate1(e.target.value.toUpperCase())} placeholder="MNL-123" />
          </div>
          <div>
            <label className={labelClass}>機車車牌 2（選填）</label>
            <input className={inputClass} value={motoPlate2} onChange={(e) => setMotoPlate2(e.target.value.toUpperCase())} />
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <AnalysisCard label="身分證字號" input={idNumber} />
        <AnalysisCard label="生日" input={birth} />
        <AnalysisCard label="手機 1" input={phone1} />
        <AnalysisCard label="手機 2" input={phone2} />
        <AnalysisCard label="汽車車牌 1" input={carPlate1} />
        <AnalysisCard label="汽車車牌 2" input={carPlate2} />
        <AnalysisCard label="機車車牌 1" input={motoPlate1} />
        <AnalysisCard label="機車車牌 2" input={motoPlate2} />
      </div>
    </div>
  );
}

// ───────────────── Tab B: 進階分析 (5 個自定號碼) ─────────────────

function AdvancedTab() {
  const [items, setItems] = useState<{ label: string; value: string }[]>([
    { label: '自定 1', value: '' },
    { label: '自定 2', value: '' },
    { label: '自定 3', value: '' },
    { label: '自定 4', value: '' },
    { label: '自定 5', value: '' },
  ]);

  const updateItem = (i: number, key: 'label' | 'value', v: string) => {
    setItems((arr) => arr.map((it, idx) => idx === i ? { ...it, [key]: v } : it));
  };

  return (
    <div className="space-y-3">
      <div className="rounded-xl bg-purple-50 p-3 text-xs text-purple-900 leading-relaxed">
        🔍 自定 5 個常用號碼（信用卡末四、銀行帳號、密碼、員工編號、提款卡密碼…）一起分析。號碼長度不限。
      </div>
      <div className="rounded-xl bg-white border border-gray-100 p-4 space-y-3">
        {items.map((it, i) => (
          <div key={i} className="grid grid-cols-3 gap-2">
            <input
              className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
              value={it.label}
              onChange={(e) => updateItem(i, 'label', e.target.value)}
              placeholder="標籤"
            />
            <input
              className="col-span-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:border-purple-500 font-mono"
              value={it.value}
              onChange={(e) => updateItem(i, 'value', e.target.value)}
              placeholder="號碼（不限長度）"
            />
          </div>
        ))}
      </div>
      <div className="space-y-2">
        {items.map((it, i) => <AnalysisCard key={i} label={it.label} input={it.value} />)}
      </div>
    </div>
  );
}

// ───────────────── Tab C: 吉祥號碼推薦（3 組） ─────────────────

function RecommendTab() {
  const [type, setType] = useState<'phone' | 'plate_car' | 'plate_moto' | 'pin' | 'custom'>('phone');
  const [customLength, setCustomLength] = useState(8);
  const [busy, setBusy] = useState(false);
  const [results, setResults] = useState<{ number: string; analysis: NumerologyAnalysis }[]>([]);
  const [preferred, setPreferred] = useState<EnergyName[]>(['生氣', '延年', '天醫']);

  const togglePreferred = (e: EnergyName) => {
    setPreferred((arr) => arr.includes(e) ? arr.filter(x => x !== e) : [...arr, e]);
  };

  const generate = () => {
    setBusy(true);
    setTimeout(() => {
      let opts: Parameters<typeof recommendNumbers>[0];
      if (type === 'phone') {
        opts = { length: 10, count: 3, prefix: '09', minScore: 4, preferredEnergies: preferred };
      } else if (type === 'plate_car') {
        // 汽車：ABC-1234 → 4 數字（前 3 字母由 system 隨意挑常見字母）
        opts = { length: 4, count: 3, minScore: 3, preferredEnergies: preferred };
      } else if (type === 'plate_moto') {
        opts = { length: 3, count: 3, minScore: 2, preferredEnergies: preferred };
      } else if (type === 'pin') {
        opts = { length: 6, count: 3, minScore: 4, preferredEnergies: preferred };
      } else {
        opts = { length: customLength, count: 3, minScore: 3, preferredEnergies: preferred };
      }
      const res = recommendNumbers(opts);
      setResults(res);
      setBusy(false);
    }, 50);
  };

  return (
    <div className="space-y-3">
      <div className="rounded-xl bg-purple-50 p-3 text-xs text-purple-900 leading-relaxed">
        🎯 依您偏好的能量方向，自動產生 3 組高分吉祥號碼。每次點「重新產生」都會給新的組合。
      </div>
      <div className="rounded-xl bg-white border border-gray-100 p-4 space-y-3">
        <div>
          <p className="text-xs font-medium text-gray-600 mb-2">類型</p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {[
              { v: 'phone',     l: '📱 手機 (10 碼)' },
              { v: 'plate_car', l: '🚗 汽車車牌 (4 碼)' },
              { v: 'plate_moto', l: '🛵 機車車牌 (3 碼)' },
              { v: 'pin',       l: '🔢 PIN 密碼 (6 碼)' },
              { v: 'custom',    l: '✏️ 自訂長度' },
            ].map(o => (
              <button
                key={o.v}
                onClick={() => setType(o.v as 'phone'|'plate_car'|'plate_moto'|'pin'|'custom')}
                className={`rounded-lg border px-3 py-2 transition ${type === o.v ? 'border-purple-500 bg-purple-50 text-purple-700' : 'border-gray-200 text-gray-500'}`}
              >
                {o.l}
              </button>
            ))}
          </div>
          {type === 'custom' && (
            <input
              type="number" min={3} max={20}
              className="w-full mt-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
              value={customLength}
              onChange={(e) => setCustomLength(parseInt(e.target.value, 10) || 8)}
              placeholder="長度（3–20）"
            />
          )}
        </div>

        <div>
          <p className="text-xs font-medium text-gray-600 mb-2">偏好能量（會多加分）</p>
          <div className="flex flex-wrap gap-1">
            {ALL_ENERGIES.filter(e => ENERGY_INFO[e].type !== 'inauspicious').map((e) => {
              const meta = ENERGY_INFO[e];
              const on = preferred.includes(e);
              return (
                <button
                  key={e}
                  onClick={() => togglePreferred(e)}
                  className="rounded-full px-2.5 py-1 text-[11px] font-semibold border transition"
                  style={on
                    ? { backgroundColor: meta.color + '30', borderColor: meta.color, color: meta.color }
                    : { backgroundColor: '#fff', borderColor: '#ddd', color: '#999' }}
                >
                  {meta.emoji} {e}
                </button>
              );
            })}
          </div>
        </div>

        <button
          onClick={generate}
          disabled={busy}
          className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 px-4 py-3 text-sm font-bold text-white disabled:opacity-50"
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          {results.length > 0 ? '重新產生 3 組' : '產生 3 組吉祥號碼'}
        </button>
      </div>

      {results.length > 0 && (
        <div className="space-y-2">
          {results.map((r, i) => (
            <div key={i} className="rounded-xl bg-white border-2 p-4 shadow-sm" style={{ borderColor: r.analysis.ratingColor }}>
              <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-bold px-2 py-0.5">#{i + 1}</span>
                  <span className="text-2xl font-mono font-bold text-gray-900">{r.number}</span>
                </div>
                <span className="text-sm font-bold" style={{ color: r.analysis.ratingColor }}>
                  {r.analysis.ratingLabel} ({r.analysis.totalScore.toFixed(1)} 分)
                </span>
              </div>
              <div className="flex flex-wrap gap-1">
                {r.analysis.pairs.map((p, j) => {
                  const meta = ENERGY_INFO[p.energy];
                  return (
                    <span key={j} className="inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-semibold"
                      style={{ backgroundColor: meta.color + '20', color: meta.color }}>
                      {p.a}{p.b}{meta.emoji}{p.energy}
                    </span>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
