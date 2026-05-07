'use client';

import { useState } from 'react';
import { ChevronLeft, Sparkles, Loader2 } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api-client';
import { useAuthGuard } from '@/lib/useAuthGuard';
import { useIdleLogout } from '@/lib/useIdleLogout';

type TabKey = 'auto' | 'manual' | 'recommend';

const GOOD = ['天醫', '生氣', '延年', '伏位'];
const BAD = ['絕命', '五鬼', '六煞', '禍害'];
const ALL = [...GOOD, ...BAD];

const MAGNET_INFO: Record<string, { kind: '吉' | '凶'; brief: string; desc: string; color: string }> = {
  天醫: { kind: '吉', brief: '貴人財富', desc: '貴人相助、財運穩固、化險為夷', color: '#F9A825' },
  生氣: { kind: '吉', brief: '機會人緣', desc: '正能量、機會多、人緣亨通',           color: '#2E7D32' },
  延年: { kind: '吉', brief: '長久穩定', desc: '感情和諧、健康長壽、做事持久',       color: '#388E3C' },
  伏位: { kind: '吉', brief: '平穩守成', desc: '按部就班、安守本分、穩中求進',       color: '#558B2F' },
  絕命: { kind: '凶', brief: '破財損傷', desc: '破財、健康危機、意外損失',           color: '#B71C1C' },
  五鬼: { kind: '凶', brief: '是非小人', desc: '口舌官司、小人作祟、心神不寧',       color: '#C62828' },
  六煞: { kind: '凶', brief: '感情糾葛', desc: '桃花是非、人際困擾、感情風波',       color: '#D84315' },
  禍害: { kind: '凶', brief: '爭執病災', desc: '病災、爭執糾紛、運勢起伏',           color: '#E65100' },
};

interface PairItem {
  raw_pair?: string;
  after_assimilation?: string;
  magnet: string;
  active?: boolean;
  continues?: string;
  extended?: boolean;
}

interface AnalysisOut {
  input?: string;
  pairs?: PairItem[];
  magnet_count?: Record<string, number>;
  duplicate_marks?: string[];
  fuwei_breakdown?: Record<string, number>;
  error?: string;
}

interface RecommendOut {
  rank: number;
  number: string;
  magnet_count?: Record<string, number>;
  duplicate_marks?: string[];
}

export default function NumerologyPage() {
  const { ready: __authReady } = useAuthGuard();
  useIdleLogout();
  const [tab, setTab] = useState<TabKey>('auto');

  if (!__authReady) return null;

  return (
    <div className="px-4 py-5 space-y-4 pb-24">
      <div className="flex items-center gap-3">
        <Link href="/profile" className="p-1"><ChevronLeft className="h-5 w-5 text-gray-600" /></Link>
        <div className="flex-1">
          <h1 className="text-lg font-bold text-gray-900 flex items-center gap-1">
            <Sparkles className="h-5 w-5 text-purple-500" /> 幫人生拿副好牌
          </h1>
          <p className="text-xs text-gray-500">數字易經分析 · 八磁場吉凶判讀</p>
        </div>
      </div>

      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 text-xs font-semibold">
        {[
          { k: 'auto',      l: '個人分析' },
          { k: 'manual',    l: '進階分析' },
          { k: 'recommend', l: '智能建議' },
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

      {tab === 'auto'      && <AutoTab />}
      {tab === 'manual'    && <ManualTab />}
      {tab === 'recommend' && <RecommendTab topN={3} />}

      <p className="text-[10px] text-gray-400 text-center pt-4 border-t border-gray-100">
        本系統僅供參考，不構成任何決策依據。
      </p>
    </div>
  );
}

// ───── 共用：分析結果卡片 ─────

function AnalysisCard({ label, result }: { label: string; result: AnalysisOut }) {
  if (result.error) {
    return <div className="rounded-xl bg-red-50 p-3 text-sm text-red-600">{label}：{result.error}</div>;
  }
  const counts = result.magnet_count || {};
  const goodSum = GOOD.reduce((s, m) => s + (counts[m] || 0), 0);
  const badSum = BAD.reduce((s, m) => s + (counts[m] || 0), 0);
  const totalSum = goodSum + badSum;
  const pct = totalSum > 0 ? Math.round(goodSum / totalSum * 100) : 0;
  let level: string, levelColor: string;
  if (pct >= 75) { level = '極佳'; levelColor = '#2E7D32'; }
  else if (pct >= 60) { level = '良好'; levelColor = '#558B2F'; }
  else if (pct >= 45) { level = '持平'; levelColor = '#9E9D24'; }
  else if (pct >= 30) { level = '偏弱'; levelColor = '#E65100'; }
  else { level = '需注意'; levelColor = '#C62828'; }

  const pairs = (result.pairs || []).filter((p) => !p.extended);

  return (
    <div className="rounded-xl bg-white border border-gray-200 p-3 space-y-2 mb-3">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div>
          <p className="text-xs text-gray-500">{label}</p>
          <p className="text-sm font-mono font-bold text-gray-900">{result.input}</p>
        </div>
        <div className="text-right">
          <p className="text-base font-bold" style={{ color: levelColor }}>{level} {pct}%</p>
          <p className="text-[10px] text-gray-400">吉 {goodSum} · 凶 {badSum}</p>
        </div>
      </div>

      {pairs.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {pairs.map((p, i) => {
            const meta = MAGNET_INFO[p.magnet];
            if (!meta) return null;
            const display = p.raw_pair && p.after_assimilation && p.raw_pair !== p.after_assimilation
              ? `${p.raw_pair}→${p.after_assimilation}`
              : (p.raw_pair || '');
            const note = p.magnet === '伏位' && p.continues ? `（延續${p.continues}）` : '';
            const opacity = p.active === false ? 0.4 : 1;
            return (
              <span
                key={i}
                className="inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-semibold"
                style={{ backgroundColor: meta.color + '20', color: meta.color, opacity }}
                title={meta.desc}
              >
                <span className="opacity-70">{display}</span>
                <span>{p.magnet}</span>
                {note && <span className="opacity-60">{note}</span>}
              </span>
            );
          })}
        </div>
      )}

      {/* 8 磁場 count grid */}
      <div className="grid grid-cols-4 gap-1 pt-2 border-t border-gray-100">
        {ALL.map((m) => {
          const meta = MAGNET_INFO[m];
          const n = counts[m] || 0;
          return (
            <div
              key={m}
              className="text-center rounded p-1.5 text-[10px]"
              style={{ backgroundColor: n > 0 ? meta.color + '15' : '#F5F5F5', color: n > 0 ? meta.color : '#aaa' }}
            >
              <div className="font-bold">{m}</div>
              <div className="text-[14px] font-bold">{n}</div>
              <div className="opacity-70">{meta.brief}</div>
            </div>
          );
        })}
      </div>

      {result.duplicate_marks && result.duplicate_marks.length > 0 && (
        <div className="text-[10px] text-purple-700 bg-purple-50 rounded p-1.5">
          <b>重複磁場：</b>{result.duplicate_marks.join('、')}
        </div>
      )}
    </div>
  );
}

// ───── Tab A: 個人分析 ─────

function AutoTab() {
  const [idNum, setIdNum] = useState('');
  const [phone, setPhone] = useState('');
  const [license, setLicense] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [result, setResult] = useState<{ id?: AnalysisOut; phone?: AnalysisOut; license?: AnalysisOut; id_error?: string; phone_error?: string; license_error?: string } | null>(null);

  const submit = async () => {
    if (!idNum.trim() && !phone.trim() && !license.trim()) {
      setErr('請至少輸入一項');
      return;
    }
    setErr(''); setBusy(true);
    try {
      const res = await api.post('/api/v1/numerology/auto', {
        id: idNum.trim(), phone: phone.trim(), license: license.trim(),
      });
      setResult(res.data?.data || null);
    } catch (e: unknown) {
      const errObj = e as { response?: { data?: { message?: string; detail?: string } } };
      setErr(errObj?.response?.data?.message || errObj?.response?.data?.detail || '分析失敗');
    } finally { setBusy(false); }
  };

  const inputClass = 'w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:border-purple-500';

  return (
    <div className="space-y-3">
      <div className="rounded-xl bg-purple-50 p-3 text-xs text-purple-900 leading-relaxed">
        💡 輸入身分證、電話、車牌（4 位數字），系統會分析每組號碼的磁場分布。三項可以只填部分。
      </div>
      <div className="rounded-xl bg-white border border-gray-100 p-4 space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">身分證字號</label>
          <input className={inputClass} value={idNum} onChange={(e) => setIdNum(e.target.value.toUpperCase())} placeholder="A123456789" maxLength={10} />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">電話</label>
          <input className={inputClass} value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="0912345678" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">車牌（4 位數字）</label>
          <input className={inputClass} value={license} onChange={(e) => setLicense(e.target.value)} placeholder="1234" maxLength={4} />
        </div>
        <button
          onClick={submit}
          disabled={busy}
          className="w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 px-4 py-3 text-sm font-bold text-white disabled:opacity-50"
        >
          {busy && <Loader2 className="h-4 w-4 animate-spin" />}
          {busy ? '分析中⋯（首次請等 30 秒喚醒服務）' : '分析'}
        </button>
        {err && <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{err}</div>}
      </div>

      {result && (
        <div>
          {result.id && <AnalysisCard label="身分證" result={result.id} />}
          {result.id_error && <div className="rounded-xl bg-red-50 p-3 text-sm text-red-600 mb-3">身分證：{result.id_error}</div>}
          {result.phone && <AnalysisCard label="電話" result={result.phone} />}
          {result.phone_error && <div className="rounded-xl bg-red-50 p-3 text-sm text-red-600 mb-3">電話：{result.phone_error}</div>}
          {result.license && <AnalysisCard label="車牌" result={result.license} />}
          {result.license_error && <div className="rounded-xl bg-red-50 p-3 text-sm text-red-600 mb-3">車牌：{result.license_error}</div>}
        </div>
      )}
    </div>
  );
}

// ───── Tab B: 進階分析 ─────

function ManualTab() {
  const [n1, setN1] = useState('');
  const [n2, setN2] = useState('');
  const [n3, setN3] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [result, setResult] = useState<{ combined?: AnalysisOut; individual?: AnalysisOut[] } | null>(null);

  const submit = async () => {
    const inputs = [n1, n2, n3].map((s) => s.trim()).filter(Boolean);
    if (inputs.length === 0) { setErr('請至少輸入一組'); return; }
    setErr(''); setBusy(true);
    try {
      const individual: AnalysisOut[] = [];
      for (const inp of inputs) {
        const r = await api.post('/api/v1/numerology/analyze', { input: inp, mode: 'general' });
        individual.push(r.data?.data || {});
      }
      let combined: AnalysisOut;
      if (inputs.length > 1) {
        const r = await api.post('/api/v1/numerology/analyze', { input: inputs.join(''), mode: 'general' });
        combined = r.data?.data || {};
      } else {
        combined = individual[0];
      }
      setResult({ individual, combined });
    } catch (e: unknown) {
      const errObj = e as { response?: { data?: { message?: string; detail?: string } } };
      setErr(errObj?.response?.data?.message || errObj?.response?.data?.detail || '分析失敗');
    } finally { setBusy(false); }
  };

  const inputClass = 'w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:border-purple-500 font-mono';

  return (
    <div className="space-y-3">
      <div className="rounded-xl bg-purple-50 p-3 text-xs text-purple-900 leading-relaxed">
        🔍 1–3 組號碼，系統合併計算交互作用（A1 天醫消絕命、A3 延年壓六煞、生氣消禍害等規則）。
      </div>
      <div className="rounded-xl bg-white border border-gray-100 p-4 space-y-3">
        <input className={inputClass} value={n1} onChange={(e) => setN1(e.target.value)} placeholder="號碼 1（如 13311331）" />
        <input className={inputClass} value={n2} onChange={(e) => setN2(e.target.value)} placeholder="號碼 2（如 0912345678）" />
        <input className={inputClass} value={n3} onChange={(e) => setN3(e.target.value)} placeholder="號碼 3（如 A1234）" />
        <button
          onClick={submit}
          disabled={busy}
          className="w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 px-4 py-3 text-sm font-bold text-white disabled:opacity-50"
        >
          {busy && <Loader2 className="h-4 w-4 animate-spin" />}
          {busy ? '分析中⋯' : '分析'}
        </button>
        {err && <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{err}</div>}
      </div>

      {result?.combined && (
        <div>
          {result.individual && result.individual.length > 1 && (
            <>
              <p className="text-xs font-bold text-gray-700 mb-2">逐組分析：</p>
              {result.individual.map((r, i) => <AnalysisCard key={i} label={`號碼 ${i + 1}`} result={r} />)}
              <p className="text-xs font-bold text-gray-700 mb-2 mt-3">合併分析（含交互作用）：</p>
            </>
          )}
          <AnalysisCard label={result.individual && result.individual.length > 1 ? '合併' : '分析'} result={result.combined} />
        </div>
      )}
    </div>
  );
}

// ───── Tab C: 智能建議 ─────

function RecommendTab({ topN }: { topN: number }) {
  const [purpose, setPurpose] = useState<'phone' | 'license' | 'pin'>('phone');
  const [length, setLength] = useState(10);
  const [prefix, setPrefix] = useState('09');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [recs, setRecs] = useState<RecommendOut[]>([]);

  const submit = async () => {
    setErr(''); setBusy(true);
    try {
      const r = await api.post('/api/v1/numerology/recommend', {
        purpose, length, prefix: prefix.trim(),
        exclude_magnets: [], require_magnets: [],
        top_n: topN,
      });
      setRecs(r.data?.data?.recommendations || []);
    } catch (e: unknown) {
      const errObj = e as { response?: { data?: { message?: string; detail?: string } } };
      setErr(errObj?.response?.data?.message || errObj?.response?.data?.detail || '產生失敗');
    } finally { setBusy(false); }
  };

  const inputClass = 'w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:border-purple-500';

  return (
    <div className="space-y-3">
      <div className="rounded-xl bg-purple-50 p-3 text-xs text-purple-900 leading-relaxed">
        🎯 自動產生 {topN} 組高分吉祥號碼。可在「個人分析」分頁先做分析，建議內容會自動避凶補吉（進階版規則由後端主導）。
      </div>
      <div className="rounded-xl bg-white border border-gray-100 p-4 space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">用途</label>
          <select className={inputClass} value={purpose} onChange={(e) => setPurpose(e.target.value as 'phone'|'license'|'pin')}>
            <option value="phone">📱 電話</option>
            <option value="license">🚗 車牌</option>
            <option value="pin">🔢 PIN / 密碼</option>
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">長度</label>
            <input type="number" className={inputClass} value={length} onChange={(e) => setLength(parseInt(e.target.value, 10) || 10)} min={2} max={12} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">開頭</label>
            <input className={inputClass} value={prefix} onChange={(e) => setPrefix(e.target.value)} placeholder="09" />
          </div>
        </div>
        <button
          onClick={submit}
          disabled={busy}
          className="w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 px-4 py-3 text-sm font-bold text-white disabled:opacity-50"
        >
          {busy && <Loader2 className="h-4 w-4 animate-spin" />}
          {busy ? '產生中⋯' : `產生 ${topN} 組`}
        </button>
        {err && <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{err}</div>}
      </div>

      {recs.length > 0 && (
        <div className="space-y-2">
          {recs.map((r) => {
            const counts = r.magnet_count || {};
            const goodSum = GOOD.reduce((s, m) => s + (counts[m] || 0), 0);
            const badSum = BAD.reduce((s, m) => s + (counts[m] || 0), 0);
            return (
              <div key={r.rank} className="rounded-xl bg-white border-2 border-purple-200 p-3 shadow-sm">
                <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-bold px-2 py-0.5">#{r.rank}</span>
                    <span className="text-2xl font-mono font-bold text-gray-900">{r.number}</span>
                    <button
                      onClick={() => { navigator.clipboard.writeText(r.number); }}
                      className="text-[11px] bg-blue-50 text-blue-600 rounded px-2 py-0.5 hover:bg-blue-100"
                    >複製</button>
                  </div>
                  <span className="text-xs text-green-600 font-bold">吉 {goodSum} · 凶 {badSum}</span>
                </div>
                <div className="grid grid-cols-4 gap-1">
                  {ALL.map((m) => {
                    const meta = MAGNET_INFO[m];
                    const n = counts[m] || 0;
                    if (n === 0) return null;
                    return (
                      <span
                        key={m}
                        className="text-[10px] text-center rounded px-1 py-0.5 font-semibold"
                        style={{ backgroundColor: meta.color + '20', color: meta.color }}
                      >
                        {m} ×{n}
                      </span>
                    );
                  })}
                </div>
                {r.duplicate_marks && r.duplicate_marks.length > 0 && (
                  <p className="text-[10px] text-purple-700 mt-1">{r.duplicate_marks.join('、')}</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
