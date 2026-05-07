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

interface PersonalSnapshot {
  id?: AnalysisOut;
  birthday?: AnalysisOut;
  phone?: AnalysisOut;
  phone2?: AnalysisOut;
  license?: AnalysisOut;
  license2?: AnalysisOut;
}

interface RecommendOut {
  rank: number;
  number: string;
  magnet_count?: Record<string, number>;
  duplicate_marks?: string[];
}

interface AgeMappingOut {
  id_decoded?: string;
  primary_ranges?: { start: number; end: number; magnet: string }[];
  timeline?: { age_start: number; age_end: number; pair: string; magnet: string; continues?: string }[];
  error?: string;
}

interface AutoOut {
  id?: AnalysisOut;
  birthday?: AnalysisOut;
  phone?: AnalysisOut;
  phone2?: AnalysisOut;
  license?: AnalysisOut;
  license2?: AnalysisOut;
  id_error?: string;
  birthday_error?: string;
  phone_error?: string;
  phone2_error?: string;
  license_error?: string;
  license2_error?: string;
  age_mapping?: AgeMappingOut;
}

const PERSONAL_KEYS = ['id', 'birthday', 'phone', 'phone2', 'license', 'license2'] as const;

// 凶星 → 對應吉星（用於智能建議避凶補吉，與原網站邏輯一致）
const COUNTER_MAGNET: Record<string, string> = {
  絕命: '天醫',
  五鬼: '生氣',
  六煞: '延年',
  禍害: '生氣',
};

function aggregatePersonalMagnets(snap: PersonalSnapshot): Record<string, number> {
  const total: Record<string, number> = {};
  PERSONAL_KEYS.forEach((k) => {
    const counts = (snap[k]?.magnet_count) || {};
    Object.entries(counts).forEach(([m, n]) => {
      if (m === '中性') return;
      total[m] = (total[m] || 0) + (n as number);
    });
  });
  return total;
}

/**
 * 車牌字母 → 數字轉換（送 API 前處理）
 * 規則：A=1, B=2, ..., I=9, J=10, K=11, ..., Z=26（單字單轉，無零填）
 * 連字符、空白會被去掉。
 * 範例：ABC-1234 → 1 2 3 1234 → "1231234"
 */
function convertLicenseToDigits(s: string): string {
  if (!s) return '';
  const clean = s.toUpperCase().replace(/[^A-Z0-9]/g, '');
  let out = '';
  for (const ch of clean) {
    if (ch >= 'A' && ch <= 'Z') {
      out += String(ch.charCodeAt(0) - 'A'.charCodeAt(0) + 1);
    } else {
      out += ch;
    }
  }
  return out;
}

export default function NumerologyPage() {
  const { ready: __authReady } = useAuthGuard();
  useIdleLogout();
  const [tab, setTab] = useState<TabKey>('auto');
  const [snapshot, setSnapshot] = useState<PersonalSnapshot | null>(null);

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

      {tab === 'auto'      && <AutoTab onAnalyzed={setSnapshot} />}
      {tab === 'manual'    && <ManualTab />}
      {tab === 'recommend' && <RecommendTab topN={3} snapshot={snapshot} onGoToAuto={() => setTab('auto')} />}

      <p className="text-[10px] text-gray-400 text-center pt-4 border-t border-gray-100">
        本系統僅供參考，不構成任何決策依據。
      </p>
    </div>
  );
}

// ───── 視覺組件 ─────

/** 半圓指針儀表（吉星比例 0–100%） */
function Gauge({ score, level, color }: { score: number; level: string; color: string }) {
  const angleRad = Math.PI * (1 - score / 100);
  const pointerLen = 78;
  const px = 100 + pointerLen * Math.cos(angleRad);
  const py = 110 - pointerLen * Math.sin(angleRad);
  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 130" className="w-full max-w-[220px]">
        <path d="M 22 110 A 78 78 0 0 1 178 110" stroke="#e6e8eb" strokeWidth="14" fill="none" strokeLinecap="round" />
        <path d="M 22 110 A 78 78 0 0 1 60 41"   stroke="#dc2626" strokeWidth="14" fill="none" strokeLinecap="round" />
        <path d="M 60 41 A 78 78 0 0 1 100 32"   stroke="#f59e0b" strokeWidth="14" fill="none" strokeLinecap="round" />
        <path d="M 100 32 A 78 78 0 0 1 140 41"  stroke="#84cc16" strokeWidth="14" fill="none" strokeLinecap="round" />
        <path d="M 140 41 A 78 78 0 0 1 178 110" stroke="#059669" strokeWidth="14" fill="none" strokeLinecap="round" />
        <line x1="100" y1="110" x2={px.toFixed(1)} y2={py.toFixed(1)} stroke="#1a1d21" strokeWidth="3" strokeLinecap="round" />
        <circle cx="100" cy="110" r="7" fill="#1a1d21" />
        <circle cx="100" cy="110" r="3" fill="#fff" />
      </svg>
      <div className="text-center -mt-3">
        <div className="text-3xl font-extrabold" style={{ color }}>
          {score}<span className="text-base">%</span>
        </div>
        <div className="text-sm font-bold" style={{ color }}>{level}</div>
        <div className="text-[10px] text-gray-400">吉星比例</div>
      </div>
    </div>
  );
}

/** 環形圖 — 吉/凶 比例 */
function Donut({ goodSum, badSum }: { goodSum: number; badSum: number }) {
  const total = Math.max(1, goodSum + badSum);
  const goodPct = (goodSum / total) * 100;
  return (
    <div className="relative flex items-center justify-center">
      <div
        className="w-32 h-32 rounded-full"
        style={{ background: `conic-gradient(#059669 0% ${goodPct}%, #dc2626 ${goodPct}% 100%)` }}
      />
      <div className="absolute w-20 h-20 rounded-full bg-white flex flex-col items-center justify-center shadow-inner">
        <div className="text-sm font-bold text-gray-800">
          <span className="text-green-700">{goodSum}</span>
          <span className="text-gray-400 mx-1">/</span>
          <span className="text-red-600">{badSum}</span>
        </div>
        <div className="text-[10px] text-gray-400">吉 / 凶</div>
      </div>
    </div>
  );
}

/** 8 磁場 vol-bars（音量條） */
function VolBars({ counts }: { counts: Record<string, number> }) {
  const max = Math.max(1, ...ALL.map((m) => counts[m] || 0));
  return (
    <div className="grid grid-cols-8 gap-1">
      {ALL.map((m) => {
        const meta = MAGNET_INFO[m];
        const n = counts[m] || 0;
        const pct = (n / max) * 100;
        return (
          <div key={m} className="flex flex-col items-center">
            <div className="relative h-20 w-full bg-gray-100 rounded overflow-hidden flex items-end">
              <div
                className="w-full transition-all"
                style={{
                  height: `${pct}%`,
                  backgroundColor: meta.kind === '吉' ? '#059669' : '#dc2626',
                  minHeight: n > 0 ? '4px' : '0',
                }}
              >
                {n > 0 && <div className="text-[10px] text-white text-center font-bold pt-0.5">{n}</div>}
              </div>
            </div>
            <div className="text-[10px] font-bold mt-1" style={{ color: meta.color }}>{m}</div>
            <div className="text-[9px] text-gray-400">{meta.brief}</div>
          </div>
        );
      })}
    </div>
  );
}

/** 8 磁場 bar chart（大長條圖，給每張 AnalysisCard 用） */
function MagnetBarChart({ counts }: { counts: Record<string, number> }) {
  const max = Math.max(1, ...ALL.map((m) => counts[m] || 0));
  return (
    <div className="flex items-end gap-1 h-24 px-1">
      {ALL.map((m) => {
        const meta = MAGNET_INFO[m];
        const n = counts[m] || 0;
        const pct = (n / max) * 100;
        return (
          <div key={m} className="flex-1 flex flex-col items-center gap-1">
            <div className="text-[10px] font-bold text-gray-600">{n > 0 ? n : ''}</div>
            <div className="w-full relative" style={{ height: `${Math.max(2, pct)}%`, minHeight: '4px' }}>
              <div
                className="absolute inset-0 rounded-t"
                style={{ backgroundColor: meta.kind === '吉' ? '#059669' : '#dc2626' }}
              />
            </div>
            <div className="text-[9px] text-gray-500">{m}</div>
          </div>
        );
      })}
    </div>
  );
}

/** 重點摘要卡片 */
function InsightCards({ counts }: { counts: Record<string, number> }) {
  const goodList = GOOD.map((m) => ({ m, n: counts[m] || 0 })).filter((x) => x.n > 0).sort((a, b) => b.n - a.n);
  const badList = BAD.map((m) => ({ m, n: counts[m] || 0 })).filter((x) => x.n > 0).sort((a, b) => b.n - a.n);
  const sg = goodList[0];
  const sb = badList[0];
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
      {sg && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-2">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold text-green-600 bg-green-100 px-2 py-0.5 rounded">最強吉星</span>
            <span className="text-sm font-bold text-green-700">{sg.m} ×{sg.n}</span>
          </div>
          <p className="text-[11px] text-green-900">{MAGNET_INFO[sg.m].desc}</p>
        </div>
      )}
      {sb && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-2">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold text-red-600 bg-red-100 px-2 py-0.5 rounded">最需注意</span>
            <span className="text-sm font-bold text-red-700">{sb.m} ×{sb.n}</span>
          </div>
          <p className="text-[11px] text-red-900">{MAGNET_INFO[sb.m].desc}</p>
        </div>
      )}
    </div>
  );
}

/** 綜合儀表面板 — 整合 id/phone/license 的磁場 */
function PersonalSummaryCard({ data }: { data: AutoOut }) {
  const total: Record<string, number> = {};
  PERSONAL_KEYS.forEach((k) => {
    const c = (data[k]?.magnet_count) || {};
    Object.entries(c).forEach(([m, n]) => {
      if (m === '中性') return;
      total[m] = (total[m] || 0) + (n as number);
    });
  });
  const goodSum = GOOD.reduce((s, m) => s + (total[m] || 0), 0);
  const badSum = BAD.reduce((s, m) => s + (total[m] || 0), 0);
  const totalSum = goodSum + badSum;
  if (totalSum === 0) return null;

  const score = Math.round((goodSum / totalSum) * 100);
  let level: string, color: string;
  if (score >= 75) { level = '極佳';   color = '#059669'; }
  else if (score >= 60) { level = '良好';   color = '#65a30d'; }
  else if (score >= 45) { level = '持平';   color = '#9e9d24'; }
  else if (score >= 30) { level = '偏弱';   color = '#ea580c'; }
  else                  { level = '需注意'; color = '#dc2626'; }

  return (
    <div className="rounded-2xl bg-white border-2 border-purple-200 p-4 shadow-sm">
      <div className="text-center mb-2">
        <h3 className="font-bold text-gray-900">綜合磁場儀表</h3>
        <p className="text-xs text-gray-500">身分證・生日・電話・車牌 整合分析</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center mb-4">
        <Gauge score={score} level={level} color={color} />
        <Donut goodSum={goodSum} badSum={badSum} />
      </div>

      <div className="text-xs font-bold text-gray-600 mb-2">磁場強度</div>
      <VolBars counts={total} />

      <div className="text-xs font-bold text-gray-600 mt-4 mb-2">重點摘要</div>
      <InsightCards counts={total} />
    </div>
  );
}

/** 年齡分區 — 從身分證解碼出來的人生時間軸 */
function AgeMappingCard({ am }: { am: AgeMappingOut }) {
  if (am.error) return <div className="rounded-xl bg-red-50 p-3 text-sm text-red-600">{am.error}</div>;
  const ranges = am.primary_ranges || [];
  const timeline = (am.timeline || []).filter((e) => e.age_start <= 70);
  if (ranges.length === 0 && timeline.length === 0) return null;

  const maxAge = Math.max(70, ...ranges.map((r) => r.end));
  const axisTicks = [0, 10, 20, 30, 40, 50, 60, 70].filter((a) => a <= maxAge);

  return (
    <div className="rounded-xl bg-white border border-gray-200 p-3 mb-3">
      <h3 className="font-bold text-gray-900 text-sm">年齡分區</h3>
      <p className="text-xs text-gray-500 mb-3">{am.id_decoded}</p>

      {ranges.length > 0 && (
        <>
          <div className="text-[11px] font-bold text-gray-600 mb-1">主磁場影響範圍（可重疊）</div>
          <div className="flex justify-between mb-1 px-12 text-[10px] text-gray-400">
            {axisTicks.map((a) => <span key={a}>{a}</span>)}
          </div>
          <div className="space-y-1.5">
            {ranges.map((r, i) => {
              const left = (r.start / maxAge) * 100;
              const width = ((r.end - r.start) / maxAge) * 100;
              const meta = MAGNET_INFO[r.magnet];
              if (!meta) return null;
              return (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-20 shrink-0">
                    <div className="text-[11px] font-bold" style={{ color: meta.color }}>{r.magnet}</div>
                    <div className="text-[9px] text-gray-400">{meta.brief}</div>
                  </div>
                  <div className="flex-1 relative h-5 bg-gray-100 rounded">
                    <div
                      className="absolute top-0 h-full rounded text-[9px] text-white font-bold flex items-center justify-center"
                      style={{
                        left: `${left}%`, width: `${width}%`,
                        backgroundColor: meta.kind === '吉' ? meta.color : meta.color,
                      }}
                    >
                      {r.start}–{r.end}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {timeline.length > 0 && (
        <>
          <div className="text-[11px] font-bold text-gray-600 mt-3 mb-1">年齡細節</div>
          <div className="overflow-x-auto -mx-1 px-1">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="bg-gray-50">
                  <th className="text-left p-1 font-bold text-gray-600">年齡</th>
                  <th className="text-left p-1 font-bold text-gray-600">數字組</th>
                  <th className="text-left p-1 font-bold text-gray-600">磁場</th>
                  <th className="text-left p-1 font-bold text-gray-600">說明</th>
                </tr>
              </thead>
              <tbody>
                {timeline.map((e, i) => {
                  const meta = MAGNET_INFO[e.magnet];
                  const note = e.magnet === '伏位' && e.continues ? `（延續${e.continues}）` : '';
                  return (
                    <tr key={i} className="border-t border-gray-100">
                      <td className="p-1 whitespace-nowrap">{e.age_start}–{e.age_end} 歲</td>
                      <td className="p-1 font-mono">{e.pair}</td>
                      <td className="p-1 font-bold" style={{ color: meta?.color }}>{e.magnet}</td>
                      <td className="p-1 text-gray-600">{meta?.desc}{note}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
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

      {/* 8 磁場 bar chart */}
      <div className="pt-2 border-t border-gray-100">
        <div className="text-[10px] font-bold text-gray-500 mb-1">磁場分布</div>
        <MagnetBarChart counts={counts} />
      </div>

      {/* 伏位細分 */}
      {result.fuwei_breakdown && Object.keys(result.fuwei_breakdown).length > 0 && (
        <div className="pt-2 border-t border-gray-100">
          <div className="text-[10px] font-bold text-gray-500 mb-1">伏位細分</div>
          <div className="flex flex-wrap gap-1">
            {Object.entries(result.fuwei_breakdown).map(([k, v]) => (
              <span key={k} className="text-[10px] bg-gray-100 px-2 py-0.5 rounded">
                {k === '純伏位' ? '純伏位' : `延續${k}`} <strong>×{v as number}</strong>
              </span>
            ))}
          </div>
        </div>
      )}

      {result.duplicate_marks && result.duplicate_marks.length > 0 && (
        <div className="text-[10px] text-purple-700 bg-purple-50 rounded p-1.5">
          <b>重複磁場：</b>{result.duplicate_marks.join('、')}
        </div>
      )}
    </div>
  );
}

// ───── 智能建議視覺元件 ─────

/** 5 瓣梅花 SVG（台灣新式車牌底紋） */
function PlumBlossom({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg" className="h-7 w-7 sm:h-8 sm:w-8">
      <g fill={color}>
        <circle cx="20" cy="9" r="6.5" />
        <circle cx="30.5" cy="16" r="6.5" />
        <circle cx="26.5" cy="28" r="6.5" />
        <circle cx="13.5" cy="28" r="6.5" />
        <circle cx="9.5" cy="16" r="6.5" />
      </g>
      <circle cx="20" cy="20" r="3" fill="#fde68a" />
      <g fill="#a16207" opacity="0.8">
        <circle cx="20" cy="16.5" r="0.7" />
        <circle cx="22.5" cy="20" r="0.7" />
        <circle cx="17.5" cy="20" r="0.7" />
        <circle cx="20" cy="22.5" r="0.7" />
      </g>
    </svg>
  );
}

/** iPhone 整機外觀（電話建議用） */
function PhoneGraphic({ number }: { number: string }) {
  let display = number;
  if (number.length === 10) display = `${number.slice(0, 4)}-${number.slice(4, 7)}-${number.slice(7)}`;
  else if (number.length === 9) display = `${number.slice(0, 3)}-${number.slice(3, 6)}-${number.slice(6)}`;

  return (
    <div className="flex justify-center py-2">
      <div
        className="relative rounded-[2.2rem] bg-gradient-to-b from-gray-900 to-black shadow-xl"
        style={{ width: 180, height: 360, padding: 6 }}
      >
        {/* 側鍵 */}
        <span className="absolute left-[-2px] top-[60px] h-2 w-1 rounded-l bg-gray-700" />
        <span className="absolute left-[-2px] top-[100px] h-9 w-1 rounded-l bg-gray-700" />
        <span className="absolute left-[-2px] top-[145px] h-9 w-1 rounded-l bg-gray-700" />
        <span className="absolute right-[-2px] top-[110px] h-12 w-1 rounded-r bg-gray-700" />
        {/* 螢幕 */}
        <div
          className="relative h-full w-full rounded-[1.9rem] bg-gradient-to-b from-purple-600 via-pink-500 to-purple-700 overflow-hidden flex flex-col items-center"
        >
          {/* 動態島 */}
          <div className="mt-2 h-5 w-20 rounded-full bg-black flex items-center justify-end pr-1">
            <span className="block h-1.5 w-1.5 rounded-full bg-gray-700" />
          </div>
          {/* 狀態列 */}
          <div className="w-full px-4 mt-1 flex justify-between text-[10px] text-white/90 font-semibold">
            <span>9:41</span>
            <span>● ● ● ●</span>
          </div>
          {/* 號碼 */}
          <div className="flex-1 flex flex-col items-center justify-center w-full px-3">
            <p className="text-[11px] text-white/70 mb-2 tracking-wider">建議號碼</p>
            <p className="text-2xl font-mono font-bold text-white tracking-wider drop-shadow break-all text-center">{display}</p>
          </div>
          {/* Home 指示條 */}
          <div className="mb-2 h-1 w-24 rounded-full bg-white/70" />
        </div>
      </div>
    </div>
  );
}

/** 台灣新式自小客車牌（車牌建議用） */
function PlateGraphic({ number }: { number: string }) {
  // 拆字母前綴 + 數字後綴
  let i = 0;
  while (i < number.length && /[A-Za-z]/.test(number[i])) i++;
  const prefix = number.slice(0, i);
  const suffix = number.slice(i);
  const display = prefix && suffix ? `${prefix}-${suffix}` : number;

  return (
    <div className="flex justify-center py-2">
      <div className="relative rounded-md bg-white border-2 border-gray-300 shadow-md px-3 sm:px-4 pt-4 pb-1.5 w-full max-w-[320px]">
        {/* 上方螺絲孔 */}
        <div className="absolute top-1 left-3 h-1.5 w-7 rounded-full bg-gray-200" />
        <div className="absolute top-1 right-3 h-1.5 w-7 rounded-full bg-gray-200" />
        {/* 號碼 */}
        <p className="text-center text-2xl sm:text-3xl font-mono font-black tracking-widest text-gray-900 leading-tight">
          {display}
        </p>
        {/* 三朵梅花（左紫、中灰、右紫） */}
        <div className="flex items-center justify-center gap-1 sm:gap-1.5 mt-0.5">
          <PlumBlossom color="#c4b5fd" />
          <PlumBlossom color="#d1d5db" />
          <PlumBlossom color="#c4b5fd" />
        </div>
      </div>
    </div>
  );
}

/** PIN / 一般用途：純數字大字顯示 */
function PinGraphic({ number, prefix }: { number: string; prefix: string }) {
  const hasPrefix = prefix && number.startsWith(prefix);
  return (
    <div className="flex justify-center py-3">
      <div className="rounded-lg bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200 px-5 py-4 shadow-sm">
        <p className="text-[11px] text-purple-600 mb-1 text-center">建議號碼</p>
        <p className="text-3xl font-mono font-bold tracking-wider text-center break-all">
          {hasPrefix ? (
            <>
              <span className="text-purple-400">{prefix}</span>
              <span className="text-gray-900">{number.slice(prefix.length)}</span>
            </>
          ) : (
            <span className="text-gray-900">{number}</span>
          )}
        </p>
      </div>
    </div>
  );
}

/** 吉星 → 它能消的凶星（用於說明每組推薦的功效） */
const GOOD_COUNTERS_BAD: Record<string, string[]> = {
  天醫: ['絕命'],
  延年: ['六煞'],
  生氣: ['禍害', '五鬼'],
};

// ───── Tab A: 個人分析 ─────

function AutoTab({ onAnalyzed }: { onAnalyzed: (s: PersonalSnapshot) => void }) {
  const [idNum, setIdNum] = useState('');
  const [birthday, setBirthday] = useState('');
  const [phone, setPhone] = useState('');
  const [phone2, setPhone2] = useState('');
  const [license, setLicense] = useState('');
  const [license2, setLicense2] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [result, setResult] = useState<AutoOut | null>(null);
  // 使用者實際輸入的車牌（給結果卡片顯示用，避免暴露轉換後的數字）
  const [licenseShown, setLicenseShown] = useState('');
  const [license2Shown, setLicense2Shown] = useState('');

  const submit = async () => {
    const anyFilled = [idNum, birthday, phone, phone2, license, license2]
      .some((s) => s.trim());
    if (!anyFilled) {
      setErr('請至少輸入一項');
      return;
    }
    setErr(''); setBusy(true);
    try {
      const licenseSend = license.trim() ? convertLicenseToDigits(license) : '';
      const license2Send = license2.trim() ? convertLicenseToDigits(license2) : '';
      const res = await api.post('/api/v1/numerology/auto', {
        id: idNum.trim(),
        birthday: birthday.trim(),
        phone: phone.trim(),
        phone2: phone2.trim(),
        license: licenseSend,
        license2: license2Send,
      });
      const data: AutoOut | null = res.data?.data || null;
      setResult(data);
      setLicenseShown(license.trim().toUpperCase());
      setLicense2Shown(license2.trim().toUpperCase());
      // 將結果 lift up 給智能建議 tab 用（避凶補吉的依據）— 6 個欄位全納入
      if (data && PERSONAL_KEYS.some((k) => data[k])) {
        onAnalyzed({
          id: data.id, birthday: data.birthday,
          phone: data.phone, phone2: data.phone2,
          license: data.license, license2: data.license2,
        });
      }
    } catch (e: unknown) {
      const errObj = e as { response?: { data?: { message?: string; detail?: string } } };
      setErr(errObj?.response?.data?.message || errObj?.response?.data?.detail || '分析失敗');
    } finally { setBusy(false); }
  };

  const inputClass = 'w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:border-purple-500';
  const hasAny = result && PERSONAL_KEYS.some((k) => result[k]);

  return (
    <div className="space-y-3">
      <div className="rounded-xl bg-purple-50 p-3 text-xs text-purple-900 leading-relaxed">
        💡 輸入身分證、生日、電話、車牌（每項可填可不填，至少填一項）。同個人有兩支電話 / 兩台車可分別填入，會一起整合分析。
      </div>
      <div className="rounded-xl bg-white border border-gray-100 p-4 space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">身分證字號</label>
          <input className={inputClass} value={idNum} onChange={(e) => setIdNum(e.target.value.toUpperCase())} placeholder="A123456789" maxLength={10} />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">生日（西元）</label>
          <input className={inputClass} value={birthday} onChange={(e) => setBirthday(e.target.value)} placeholder="1985/03/15" maxLength={10} />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">電話</label>
          <input className={inputClass} value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="0912345678" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">電話 2（選填）</label>
          <input className={inputClass} value={phone2} onChange={(e) => setPhone2(e.target.value)} placeholder="0987654321" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">車牌（含英文字也可）</label>
          <input
            className={inputClass}
            value={license}
            onChange={(e) => setLicense(e.target.value.toUpperCase())}
            placeholder="如 ABC-1234"
            maxLength={12}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">車牌 2（含英文字也可，選填）</label>
          <input
            className={inputClass}
            value={license2}
            onChange={(e) => setLicense2(e.target.value.toUpperCase())}
            placeholder="如 XYZ-5678"
            maxLength={12}
          />
        </div>
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

      {result && (
        <div>
          {/* 綜合儀表面板（吉/凶比例 + 8 磁場強度 + 重點摘要）— 6 欄位整合 */}
          {hasAny && <PersonalSummaryCard data={result} />}

          {result.id && <AnalysisCard label="身分證" result={result.id} />}
          {result.id_error && <div className="rounded-xl bg-red-50 p-3 text-sm text-red-600 mb-3">身分證：{result.id_error}</div>}

          {/* 年齡分區（從身分證解碼出的人生時間軸） */}
          {result.age_mapping && <AgeMappingCard am={result.age_mapping} />}

          {result.birthday && <AnalysisCard label="生日" result={result.birthday} />}
          {result.birthday_error && <div className="rounded-xl bg-red-50 p-3 text-sm text-red-600 mb-3">生日：{result.birthday_error}</div>}

          {result.phone && <AnalysisCard label="電話" result={result.phone} />}
          {result.phone_error && <div className="rounded-xl bg-red-50 p-3 text-sm text-red-600 mb-3">電話：{result.phone_error}</div>}

          {result.phone2 && <AnalysisCard label="電話 2" result={result.phone2} />}
          {result.phone2_error && <div className="rounded-xl bg-red-50 p-3 text-sm text-red-600 mb-3">電話 2：{result.phone2_error}</div>}

          {result.license && (
            <AnalysisCard
              label="車牌"
              result={licenseShown ? { ...result.license, input: licenseShown } : result.license}
            />
          )}
          {result.license_error && <div className="rounded-xl bg-red-50 p-3 text-sm text-red-600 mb-3">車牌：{result.license_error}</div>}

          {result.license2 && (
            <AnalysisCard
              label="車牌 2"
              result={license2Shown ? { ...result.license2, input: license2Shown } : result.license2}
            />
          )}
          {result.license2_error && <div className="rounded-xl bg-red-50 p-3 text-sm text-red-600 mb-3">車牌 2：{result.license2_error}</div>}
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

function RecommendTab({
  topN, snapshot, onGoToAuto,
}: {
  topN: number;
  snapshot: PersonalSnapshot | null;
  onGoToAuto: () => void;
}) {
  const [purpose, setPurpose] = useState<'phone' | 'license' | 'pin'>('phone');
  const [length, setLength] = useState(10);
  const [prefix, setPrefix] = useState('09');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [recs, setRecs] = useState<RecommendOut[]>([]);
  const [debugInfo, setDebugInfo] = useState<{ exclude: string[]; require: string[] } | null>(null);

  const hasSnapshot = !!snapshot && (!!snapshot.id || !!snapshot.phone || !!snapshot.license);

  const submit = async () => {
    if (!hasSnapshot) {
      setErr('請先在「個人分析」分頁完成身分證 / 電話 / 車牌的分析，建議才能依您的磁場狀況客製');
      return;
    }
    setErr(''); setBusy(true);
    try {
      // 從個人分析結果推導 exclude / require（跟原網站邏輯一致）
      const total = aggregatePersonalMagnets(snapshot!);
      const exclude: string[] = [];
      const require: string[] = [];
      for (const bad of BAD) {
        if ((total[bad] || 0) > 0) {
          exclude.push(bad);
          const counter = COUNTER_MAGNET[bad];
          if (counter && !require.includes(counter)) require.push(counter);
        }
      }
      setDebugInfo({ exclude, require });

      const r = await api.post('/api/v1/numerology/recommend', {
        purpose, length, prefix: prefix.trim(),
        exclude_magnets: exclude, require_magnets: require,
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
        🎯 自動產生 {topN} 組高分吉祥號碼。系統會根據「個人分析」結果<b>自動避開您身上既有的凶星、補對應的吉星</b>，所以**必須先完成個人分析**。
      </div>

      {/* 必須先做個人分析的提示 */}
      {!hasSnapshot && (
        <div className="rounded-xl bg-amber-50 border border-amber-300 p-4 text-center">
          <p className="text-sm font-bold text-amber-900 mb-2">⚠️ 還沒做個人分析</p>
          <p className="text-xs text-amber-800 mb-3 leading-relaxed">
            智能建議需要您的個人磁場狀況才能客製化。
            <br />請先到「個人分析」分頁，輸入身分證 / 電話 / 車牌（任一即可）並按分析。
          </p>
          <button
            onClick={onGoToAuto}
            className="rounded-lg bg-amber-500 hover:bg-amber-600 px-4 py-2 text-xs font-bold text-white"
          >
            前往個人分析 →
          </button>
        </div>
      )}

      {/* 已有快照時顯示摘要 */}
      {hasSnapshot && (
        <div className="rounded-xl bg-green-50 border border-green-200 p-3 text-xs text-green-900">
          ✓ 已讀取您的個人分析結果，建議會自動依您的磁場避凶補吉。
          <button onClick={onGoToAuto} className="ml-2 text-green-700 underline">重新分析</button>
        </div>
      )}

      <div className="rounded-xl bg-white border border-gray-100 p-4 space-y-3" style={{ opacity: hasSnapshot ? 1 : 0.5, pointerEvents: hasSnapshot ? 'auto' : 'none' }}>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">用途</label>
          <select
            className={inputClass}
            value={purpose}
            onChange={(e) => {
              const p = e.target.value as 'phone' | 'license' | 'pin';
              setPurpose(p);
              // 依用途調整預設值（仿原網站）
              if (p === 'license') {
                if (length > 7) setLength(7);
                setPrefix('');
              } else if (p === 'phone') {
                setPrefix('09');
              } else {
                setPrefix('');
              }
            }}
          >
            <option value="phone">📱 電話</option>
            <option value="license">🚗 車牌</option>
            <option value="pin">🔢 PIN / 密碼</option>
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">長度</label>
            <input
              type="number"
              className={inputClass}
              value={length}
              onChange={(e) => setLength(parseInt(e.target.value, 10) || 10)}
              min={2}
              max={purpose === 'license' ? 7 : 12}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">開頭</label>
            <input
              className={inputClass}
              value={prefix}
              onChange={(e) => setPrefix(e.target.value)}
              placeholder={
                purpose === 'license' ? '如 ABC、AAA（監理站發的英文字）'
                : purpose === 'phone' ? '如 09'
                : '（可留空）'
              }
            />
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

      {debugInfo && hasSnapshot && (debugInfo.exclude.length > 0 || debugInfo.require.length > 0) && (
        <div className="rounded-lg bg-blue-50 border border-blue-200 p-3 text-xs text-blue-900">
          <b>建議邏輯：</b>
          {debugInfo.exclude.length > 0 && (
            <div>已避開您身上的凶星：<span className="font-semibold text-red-600">{debugInfo.exclude.join('、')}</span></div>
          )}
          {debugInfo.require.length > 0 && (
            <div>已加強對應吉星：<span className="font-semibold text-green-600">{debugInfo.require.join('、')}</span></div>
          )}
        </div>
      )}

      {recs.length > 0 && (
        <div className="space-y-3">
          {recs.map((r) => {
            const counts = r.magnet_count || {};
            const goodSum = GOOD.reduce((s, m) => s + (counts[m] || 0), 0);
            const badSum = BAD.reduce((s, m) => s + (counts[m] || 0), 0);
            // 推算這組推薦能消除使用者身上哪些凶星
            const userTotal = snapshot ? aggregatePersonalMagnets(snapshot) : {};
            const cancelled = new Set<string>();
            for (const [good, bads] of Object.entries(GOOD_COUNTERS_BAD)) {
              if ((counts[good] || 0) > 0) {
                for (const bad of bads) {
                  if ((userTotal[bad] || 0) > 0) cancelled.add(bad);
                }
              }
            }
            const goodPresent = GOOD
              .filter((g) => (counts[g] || 0) > 0)
              .map((g) => `${g}×${counts[g]}`);
            return (
              <div key={r.rank} className="rounded-xl bg-white border-2 border-purple-200 p-3 shadow-sm">
                {/* 排名 + 吉凶 + 複製 */}
                <div className="flex items-center justify-between mb-1 flex-wrap gap-2">
                  <span className="rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-bold px-2 py-0.5">#{r.rank}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-green-600 font-bold">吉 {goodSum} · 凶 {badSum}</span>
                    <button
                      onClick={() => { navigator.clipboard.writeText(r.number); }}
                      className="text-[11px] bg-blue-50 text-blue-600 rounded px-2 py-0.5 hover:bg-blue-100"
                    >複製號碼</button>
                  </div>
                </div>

                {/* 視覺化容器（依用途切換） */}
                {purpose === 'phone' && <PhoneGraphic number={r.number} />}
                {purpose === 'license' && <PlateGraphic number={r.number} />}
                {purpose === 'pin' && <PinGraphic number={r.number} prefix={prefix.trim()} />}

                {/* 推薦邏輯說明（仿原站「含 ...，以消除您身上的 ...」） */}
                <p className="text-xs text-gray-700 mt-2 leading-relaxed">
                  含 <b className="text-green-700">{goodPresent.length ? goodPresent.join('、') : '—'}</b>
                  {cancelled.size > 0 && (
                    <>
                      ，以消除您身上的 <b className="text-red-600">{[...cancelled].join('、')}</b>
                    </>
                  )}
                </p>

                {/* 完整 8 磁場標籤（只列有 ≥1 個的） */}
                <div className="flex flex-wrap gap-1 mt-2">
                  {ALL.map((m) => {
                    const meta = MAGNET_INFO[m];
                    const n = counts[m] || 0;
                    if (n === 0) return null;
                    return (
                      <span
                        key={m}
                        className="text-[10px] rounded px-1.5 py-0.5 font-semibold"
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
