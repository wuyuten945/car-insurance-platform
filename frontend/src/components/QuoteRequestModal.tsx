'use client';

import { useState, useEffect } from 'react';
import { Loader2, Plus, X, Check, Info } from 'lucide-react';
import api from '@/lib/api-client';
import { VEHICLE_TYPE_GROUPS } from '@/lib/vehicleTypes';

interface VehicleLite {
  id: string;
  plate_number: string;
  brand: string | null;
  model: string | null;
  year: number | null;
  vehicle_type: string | null;
  engine_cc: number | null;
}

interface PolicyLite {
  id: string;
  insurer_name: string;
  policy_number: string;
  end_date?: string;
  vehicle_id?: string | null;
  data_source?: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmitted: () => void;
  vehicles: VehicleLite[];
  policies: PolicyLite[];
  defaults?: { vehicle_id?: string; driver_age?: number };
}

// 標準保障項目清單（業務員可能會用到的全部項目）
const ITEM_PRESETS: { name: string; limits?: number[]; group: string }[] = [
  { name: '強制汽車責任險',                              group: '強制險' },
  { name: '第三人責任險（體傷單一）',  limits: [1000000, 2000000, 5000000, 10000000], group: '第三人責任' },
  { name: '第三人財損責任險',          limits: [500000, 1000000, 3000000],            group: '第三人責任' },
  { name: '超額責任險',                limits: [3000000, 5000000, 10000000, 20000000], group: '第三人責任' },
  { name: '刑事訴訟補償費用',                            group: '附加' },
  { name: '駕駛人傷害險',              limits: [1000000, 2000000, 5000000],            group: '人身' },
  { name: '乘客傷害險',                limits: [1000000, 2000000, 5000000],            group: '人身' },
  { name: '車體損失險（甲式）',                           group: '車體' },
  { name: '車體損失險（乙式）',                           group: '車體' },
  { name: '車體損失險（丙式）',                           group: '車體' },
  { name: '竊盜險',                                       group: '車體' },
  { name: '道路救援',                                     group: '附加' },
  { name: '零配件折舊免計',                               group: '附加' },
];

export default function QuoteRequestModal({
  open, onClose, onSubmitted, vehicles, policies, defaults,
}: Props) {
  const [vehicleId, setVehicleId] = useState('');
  const [useExisting, setUseExisting] = useState(false);
  const [sourcePolicyId, setSourcePolicyId] = useState('');
  // map: name → {checked, limit?}
  const [items, setItems] = useState<Record<string, { checked: boolean; limit?: number }>>({});
  const [customItem, setCustomItem] = useState('');
  const [driverAge, setDriverAge] = useState<string>('');
  const [claimsCount, setClaimsCount] = useState<string>('0');
  const [surchargePct, setSurchargePct] = useState<string>('');
  const [notes, setNotes] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!open) return;
    setErr(''); setDone(false);
    setVehicleId(defaults?.vehicle_id || '');
    setUseExisting(false);
    setSourcePolicyId('');
    setItems({ '強制汽車責任險': { checked: true } });
    setCustomItem('');
    setDriverAge(defaults?.driver_age != null ? String(defaults.driver_age) : '');
    setClaimsCount('0');
    setSurchargePct('');
    setNotes('');
  }, [open, defaults]);

  if (!open) return null;

  const toggleItem = (name: string) => {
    setItems((m) => ({ ...m, [name]: { checked: !m[name]?.checked, limit: m[name]?.limit } }));
  };
  const setItemLimit = (name: string, limit: number) => {
    setItems((m) => ({ ...m, [name]: { checked: true, limit } }));
  };

  const handleSubmit = async () => {
    setErr('');
    const desired = Object.entries(items)
      .filter(([, v]) => v.checked)
      .map(([name, v]) => ({ name, limit: v.limit }));
    if (customItem.trim()) {
      customItem.split(/[,，;；]+/).map((s) => s.trim()).filter(Boolean)
        .forEach((s) => desired.push({ name: s }));
    }
    if (!useExisting && desired.length === 0) {
      setErr('請至少勾選一項保障，或選「跟原保單一樣」');
      return;
    }
    if (useExisting && !sourcePolicyId) {
      setErr('請選擇要參照的原保單');
      return;
    }

    const body: Record<string, unknown> = {
      vehicle_id: vehicleId || null,
      use_existing_policy: useExisting,
      source_policy_id: useExisting ? sourcePolicyId : null,
      desired_items: desired,
      driver_age: driverAge ? parseInt(driverAge, 10) : null,
      claims_count_3y: claimsCount ? parseInt(claimsCount, 10) : null,
      surcharge_pct: surchargePct ? parseFloat(surchargePct) : null,
      notes: notes.trim() || null,
    };

    setBusy(true);
    try {
      await api.post('/api/v1/quote-requests', body);
      setDone(true);
      onSubmitted();
    } catch (e: unknown) {
      const errObj = e as { response?: { data?: { message?: string; detail?: string } } };
      setErr(errObj?.response?.data?.message || errObj?.response?.data?.detail || '送出失敗');
    } finally {
      setBusy(false);
    }
  };

  const labelClass = 'block text-xs font-medium text-gray-600 mb-1';
  const inputClass = 'w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:border-primary-500';
  // 依 group 排組
  const grouped: Record<string, typeof ITEM_PRESETS> = {};
  ITEM_PRESETS.forEach((it) => {
    grouped[it.group] = grouped[it.group] || [];
    grouped[it.group].push(it);
  });

  return (
    <div className="fixed inset-0 z-[9998] bg-black/55 flex items-start justify-center overflow-y-auto p-3 sm:p-6">
      <div className="bg-white rounded-2xl w-full max-w-2xl shadow-2xl my-4 relative">
        <button onClick={onClose} className="absolute top-2 right-3 text-gray-400 hover:text-gray-600 text-2xl leading-none p-1">×</button>
        <div className="p-5 sm:p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-1">📋 請業務員精確報價</h2>
          <p className="text-xs text-gray-500 mb-4">
            您送出後，業務員（或本平台管理員）會實際向各家產險公司詢價，<b>6–12 小時</b>內回報多家精確保費供您選擇。
          </p>

          {done ? (
            <div className="rounded-2xl bg-green-50 border border-green-200 p-6 text-center">
              <div className="text-5xl mb-2">✅</div>
              <h3 className="text-lg font-bold text-green-700 mb-2">詢價工單已送出</h3>
              <p className="text-sm text-green-900 leading-relaxed">
                您的詢價工單已送至服務人員，<b>6–12 小時</b>內會收到精確報價通知（站內、LINE、Email）。
                <br />可至「我的詢價」追蹤工單進度。
              </p>
              <button
                onClick={onClose}
                className="mt-4 rounded-lg bg-primary-500 hover:bg-primary-700 px-6 py-2.5 text-sm font-semibold text-white"
              >
                關閉
              </button>
            </div>
          ) : (
            <>
              <div className="space-y-3">
                <div>
                  <label className={labelClass}>承保車輛（選填，系統會幫您附帶車輛資料）</label>
                  <select className={inputClass} value={vehicleId} onChange={(e) => setVehicleId(e.target.value)}>
                    <option value="">— 請選擇 —</option>
                    {vehicles.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.plate_number}{v.brand || v.model ? ` — ${v.brand || ''} ${v.model || ''}`.trim() : ''}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useExisting}
                      onChange={(e) => setUseExisting(e.target.checked)}
                      className="h-4 w-4"
                    />
                    <span className="text-sm font-semibold text-blue-900">📑 跟原保單一樣（指定一張既有保單作為參照）</span>
                  </label>
                  {useExisting && (
                    <select className={inputClass + ' mt-2'} value={sourcePolicyId} onChange={(e) => setSourcePolicyId(e.target.value)}>
                      <option value="">— 請選擇要參照的保單 —</option>
                      {policies.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.insurer_name} · {p.policy_number}{p.end_date ? ` (~${p.end_date})` : ''}
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                {!useExisting && (
                  <div>
                    <label className={labelClass}>勾選您想保的項目（可多選）</label>
                    <div className="rounded-lg border border-gray-200 p-3 space-y-3 bg-gray-50">
                      {Object.entries(grouped).map(([gname, list]) => (
                        <div key={gname}>
                          <div className="text-[11px] font-bold text-gray-500 mb-1">{gname}</div>
                          <div className="space-y-1">
                            {list.map((it) => {
                              const cur = items[it.name] || { checked: false };
                              return (
                                <div key={it.name} className="bg-white rounded p-2 border border-gray-100">
                                  <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                      type="checkbox"
                                      checked={!!cur.checked}
                                      onChange={() => toggleItem(it.name)}
                                      className="h-4 w-4"
                                    />
                                    <span className="text-xs flex-1">{it.name}</span>
                                  </label>
                                  {cur.checked && it.limits && (
                                    <div className="flex flex-wrap gap-1 mt-1.5 ml-6">
                                      {it.limits.map((lim) => (
                                        <button
                                          key={lim}
                                          type="button"
                                          onClick={() => setItemLimit(it.name, lim)}
                                          className={`rounded px-2 py-0.5 text-[10px] font-semibold transition ${
                                            cur.limit === lim
                                              ? 'bg-primary-500 text-white'
                                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                          }`}
                                        >
                                          {(lim / 10000).toLocaleString()} 萬
                                        </button>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                    <input
                      className={inputClass + ' mt-2'}
                      placeholder="其他自定項目（多項用逗號分開）"
                      value={customItem}
                      onChange={(e) => setCustomItem(e.target.value)}
                    />
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={labelClass}>駕駛人年齡</label>
                    <input type="number" className={inputClass} value={driverAge} onChange={(e) => setDriverAge(e.target.value)} placeholder="35" />
                  </div>
                  <div>
                    <label className={labelClass}>過去 3 年出險次數</label>
                    <select className={inputClass} value={claimsCount} onChange={(e) => setClaimsCount(e.target.value)}>
                      <option value="0">0 次（從未出險）</option>
                      <option value="1">1 次</option>
                      <option value="2">2 次</option>
                      <option value="3">3 次以上</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className={labelClass}>已知加費費率（選填，例：+20）</label>
                  <input type="number" step="0.01" className={inputClass} value={surchargePct} onChange={(e) => setSurchargePct(e.target.value)} placeholder="0" />
                  <p className="text-[10px] text-gray-400 mt-1">如保險公司或業務員已告知您的個人加費比率，請填入；不知道可留空</p>
                </div>

                <div>
                  <label className={labelClass}>備註 / 特別需求</label>
                  <textarea className={inputClass} value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} placeholder="例：車庫停放、僅自用、傾向 XX 保險公司…" />
                </div>
              </div>

              <div className="rounded-lg bg-amber-50 p-3 mt-4 flex gap-2 text-xs text-amber-900">
                <Info className="h-4 w-4 shrink-0 mt-0.5" />
                <span>送出後不會自動產生報價 — 由真人服務員實際向產險公司詢價，並在 <b>6–12 小時</b>內回報。</span>
              </div>

              {err && <div className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-600">{err}</div>}

              <div className="mt-5 flex gap-2 border-t border-gray-100 pt-4">
                <button onClick={onClose} className="rounded-lg bg-gray-100 hover:bg-gray-200 px-5 py-2.5 text-sm font-semibold text-gray-700">取消</button>
                <button onClick={handleSubmit} disabled={busy} className="flex items-center gap-1.5 rounded-lg bg-primary-500 hover:bg-primary-700 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50 ml-auto">
                  {busy && <Loader2 className="h-4 w-4 animate-spin" />}
                  📤 送出詢價工單
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
