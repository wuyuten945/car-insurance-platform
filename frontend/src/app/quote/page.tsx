'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { ChevronLeft, Calculator, Loader2, Star, Check, MessageCircle, Phone, AlertTriangle } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api-client';
import { useAuthGuard } from '@/lib/useAuthGuard';
import { useIdleLogout } from '@/lib/useIdleLogout';
import { useEligibility } from '@/lib/useEligibility';
import { VEHICLE_TYPE_GROUPS } from '@/lib/vehicleTypes';

interface VehicleLite {
  id: string;
  plate_number: string;
  brand: string | null;
  model: string | null;
  year: number | null;
  engine_cc: number | null;
  vehicle_type: string | null;
}

interface QuoteResult {
  insurer_name: string;
  logo?: string | null;
  quoted_premium: number;
  coverage_items: string[];
  rating: number;
  claim_speed_days: number;
  features: string;
  valid_until: string;
  is_recommended: boolean;
}

const TIERS = [
  { value: 'basic',    label: '基本型',    desc: '強制險 + 第三人責任險',                  badge: '#0288D1' },
  { value: 'standard', label: '標準型',    desc: '+ 第三人加強 + 超額責任',                badge: '#2E7D32' },
  { value: 'premium',  label: '全方位型',  desc: '+ 車體損失險 + 竊盜險 + 道路救援',        badge: '#E65100' },
];

export default function QuotePage() {
  const { ready: __authReady } = useAuthGuard();
  useIdleLogout();
  const { eligibility } = useEligibility();

  const [vehicleMode, setVehicleMode] = useState<'pick' | 'manual'>('pick');
  const [vehicleId, setVehicleId] = useState('');
  const [manualType, setManualType] = useState('');
  const [manualYear, setManualYear] = useState<string>('');
  const [manualCC, setManualCC] = useState<string>('');
  const [driverAge, setDriverAge] = useState<string>('');
  const [tier, setTier] = useState('standard');
  const [includeCompulsory, setIncludeCompulsory] = useState(true);

  const { data: vehicles } = useQuery({
    queryKey: ['my-vehicles-for-quote'],
    queryFn: async () => {
      const res = await api.get('/api/v1/customers/vehicles');
      return res.data.data as VehicleLite[];
    },
  });

  const mutation = useMutation({
    mutationFn: async () => {
      const body: Record<string, unknown> = {
        coverage_tier: tier,
        include_compulsory: includeCompulsory,
      };
      if (vehicleMode === 'pick' && vehicleId) {
        body.vehicle_id = vehicleId;
      } else {
        if (manualType) body.vehicle_type = manualType;
        if (manualYear) body.year = parseInt(manualYear, 10);
        if (manualCC) body.engine_cc = parseInt(manualCC, 10);
      }
      if (driverAge) body.driver_age = parseInt(driverAge, 10);
      const res = await api.post('/api/v1/renewal/estimate', body);
      return res.data.data as { quotes: QuoteResult[]; disclaimer: string };
    },
  });

  if (!__authReady) return null;

  const labelClass = 'block text-xs font-medium text-gray-600 mb-1';
  const inputClass = 'w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:border-primary-500';

  return (
    <div className="px-4 py-5 space-y-4 pb-24">
      <div className="flex items-center gap-3">
        <Link href="/profile" className="p-1"><ChevronLeft className="h-5 w-5 text-gray-600" /></Link>
        <div className="flex-1">
          <h1 className="text-lg font-bold text-gray-900">續保保費報價</h1>
          <p className="text-xs text-gray-500">填寫車輛資訊，立即試算各家保險公司預估保費</p>
        </div>
        <Calculator className="h-6 w-6 text-primary-500" />
      </div>

      {/* 表單 */}
      <div className="rounded-2xl bg-white p-4 shadow-sm border border-gray-100 space-y-4">
        <div>
          <label className={labelClass}>車輛資料來源</label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setVehicleMode('pick')}
              className={`flex-1 rounded-lg border px-3 py-2 text-xs font-semibold transition ${vehicleMode === 'pick' ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-gray-200 text-gray-500'}`}
            >
              從我的車輛挑選
            </button>
            <button
              type="button"
              onClick={() => setVehicleMode('manual')}
              className={`flex-1 rounded-lg border px-3 py-2 text-xs font-semibold transition ${vehicleMode === 'manual' ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-gray-200 text-gray-500'}`}
            >
              手動輸入車輛
            </button>
          </div>
        </div>

        {vehicleMode === 'pick' ? (
          <div>
            <label className={labelClass}>選擇車輛</label>
            <select className={inputClass} value={vehicleId} onChange={(e) => setVehicleId(e.target.value)}>
              <option value="">— 請選擇 —</option>
              {(vehicles ?? []).map((v) => (
                <option key={v.id} value={v.id}>
                  {v.plate_number}{v.brand || v.model ? ` — ${v.brand || ''} ${v.model || ''}`.trim() : ''}{v.year ? ` (${v.year})` : ''}
                </option>
              ))}
            </select>
            {(vehicles ?? []).length === 0 && (
              <p className="text-[11px] text-gray-400 mt-1">名下尚無車輛 — 可先去「車輛 / 行照」新增，或切換到手動輸入</p>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <div>
              <label className={labelClass}>車輛型式</label>
              <select className={inputClass} value={manualType} onChange={(e) => setManualType(e.target.value)}>
                <option value="">— 請選擇 —</option>
                {VEHICLE_TYPE_GROUPS.map((g) => (
                  <optgroup key={g.label} label={g.label}>
                    {g.types.map((t) => <option key={t} value={t}>{t}</option>)}
                  </optgroup>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>出廠年</label>
                <input type="number" className={inputClass} value={manualYear} onChange={(e) => setManualYear(e.target.value)} placeholder="2020" />
              </div>
              <div>
                <label className={labelClass}>排氣量 (cc)</label>
                <input type="number" className={inputClass} value={manualCC} onChange={(e) => setManualCC(e.target.value)} placeholder="1800" />
              </div>
            </div>
          </div>
        )}

        <div>
          <label className={labelClass}>駕駛人年齡（選填，影響費率）</label>
          <input type="number" className={inputClass} value={driverAge} onChange={(e) => setDriverAge(e.target.value)} placeholder="35" />
          <p className="text-[10px] text-gray-400 mt-1">25 歲以下 +20%、65 歲以上 +10%</p>
        </div>

        <div>
          <label className={labelClass}>保障等級</label>
          <div className="grid grid-cols-1 gap-2">
            {TIERS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setTier(opt.value)}
                className={`w-full text-left rounded-lg border px-3 py-2.5 transition ${
                  tier === opt.value ? 'border-primary-500 bg-primary-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="rounded-full px-2 py-0.5 text-[10px] font-bold text-white" style={{ backgroundColor: opt.badge }}>{opt.label}</span>
                  {tier === opt.value && <Check className="h-4 w-4 text-primary-500" />}
                </div>
                <p className="text-[11px] text-gray-500 mt-1">{opt.desc}</p>
              </button>
            ))}
          </div>
        </div>

        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={includeCompulsory} onChange={(e) => setIncludeCompulsory(e.target.checked)} className="h-4 w-4" />
          <span className="text-sm text-gray-700">含強制險（不含的話約打 85 折）</span>
        </label>

        <button
          type="button"
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="w-full flex items-center justify-center gap-2 rounded-xl bg-primary-500 hover:bg-primary-700 px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
        >
          {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Calculator className="h-4 w-4" />}
          試算保費
        </button>
      </div>

      {/* 結果 */}
      {mutation.isSuccess && mutation.data && (
        <div className="space-y-3">
          <div className="rounded-lg bg-blue-50 p-3 text-xs text-blue-900 leading-relaxed flex gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{mutation.data.disclaimer}</span>
          </div>

          {mutation.data.quotes.map((q, i) => (
            <div key={i} className={`relative rounded-2xl bg-white p-4 shadow-sm border-2 ${q.is_recommended ? 'border-orange-400' : 'border-gray-100'}`}>
              {q.is_recommended && (
                <div className="absolute -top-3 left-4 flex items-center gap-1 rounded-full bg-orange-500 px-3 py-0.5 text-[10px] font-bold text-white">
                  <Star className="h-3 w-3" /> 最划算
                </div>
              )}
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-bold text-gray-900">{q.insurer_name}</p>
                  <div className="flex items-center gap-1 text-[11px] text-gray-500 mt-0.5">
                    <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                    {q.rating} · 平均理賠 {q.claim_speed_days} 天
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-primary-600">
                    ${q.quoted_premium.toLocaleString()}
                  </p>
                  <p className="text-[10px] text-gray-400">年繳指示價</p>
                </div>
              </div>
              <ul className="space-y-1 mb-2">
                {q.coverage_items.map((it, j) => (
                  <li key={j} className="text-xs text-gray-600 flex items-start gap-1">
                    <Check className="h-3 w-3 text-green-500 mt-0.5 shrink-0" /> {it}
                  </li>
                ))}
              </ul>
              <p className="text-[10px] text-gray-400">{q.features} · 報價有效期至 {q.valid_until}</p>
            </div>
          ))}

          {/* 投保 CTA */}
          <div className="rounded-2xl bg-gradient-to-br from-green-50 to-blue-50 p-4 border border-green-200">
            <p className="text-sm font-bold text-gray-900 mb-1">想正式投保？</p>
            <p className="text-xs text-gray-600 mb-3 leading-relaxed">
              {eligibility.has_agent_policy
                ? '您是 BOPINAN 已服務客戶，請聯繫您專屬的業務員報價並核保。'
                : '透過 LINE 與我們聯繫，由專人為您正式核保並辦理投保。'}
            </p>
            <div className="flex gap-2">
              {!eligibility.has_agent_policy && eligibility.line_oa_url && (
                <a href={eligibility.line_oa_url} target="_blank" rel="noopener noreferrer"
                   className="flex-1 flex items-center justify-center gap-1 rounded-lg bg-green-500 hover:bg-green-600 px-3 py-2.5 text-xs font-semibold text-white">
                  <MessageCircle className="h-4 w-4" /> LINE 聯繫
                </a>
              )}
              <a href="tel:" onClick={(e) => { e.preventDefault(); alert('請撥打您熟悉的業務員電話辦理。'); }}
                 className="flex-1 flex items-center justify-center gap-1 rounded-lg bg-white border border-gray-300 hover:bg-gray-50 px-3 py-2.5 text-xs font-semibold text-gray-700">
                <Phone className="h-4 w-4" /> 致電業務員
              </a>
            </div>
          </div>
        </div>
      )}

      {mutation.isError && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
          試算失敗，請稍後再試。
        </div>
      )}
    </div>
  );
}
