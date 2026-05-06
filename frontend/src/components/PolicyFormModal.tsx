'use client';

import { useEffect, useState } from 'react';
import { Loader2, Plus, Trash2 } from 'lucide-react';
import api from '@/lib/api-client';
import { TAIWAN_INSURERS, POLICY_STATUS_OPTIONS } from '@/lib/insurers';
import { rocLabel } from '@/lib/vehicleTypes';

interface ItemRow {
  item_name: string;
  coverage_limit?: number | null;
  deductible?: number | null;
  premium?: number | null;
}

export interface PolicyPayload {
  id?: string;
  vehicle_id?: string | null;
  insurer_name: string;
  policy_number: string;
  status?: string;
  start_date?: string | null;
  end_date?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  total_premium?: number | null;
  // 強制險
  compulsory_insurer_name?: string | null;
  compulsory_policy_number?: string | null;
  compulsory_premium?: number | null;
  compulsory_start_date?: string | null;
  compulsory_end_date?: string | null;
  compulsory_start_time?: string | null;
  compulsory_end_time?: string | null;
  items?: ItemRow[];
  data_source?: string;
}

interface VehicleOpt { id: string; plate_number: string; brand?: string | null; model?: string | null }

interface Props {
  open: boolean;
  initial?: PolicyPayload | null;
  vehicles: VehicleOpt[];
  onClose: () => void;
  onSaved: () => void;
}

function InsurerSelect({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const isOther = value && !TAIWAN_INSURERS.includes(value);
  const [otherVal, setOtherVal] = useState(isOther ? value : '');
  const [mode, setMode] = useState<'list' | 'other'>(isOther ? 'other' : 'list');
  useEffect(() => {
    setMode(value && !TAIWAN_INSURERS.includes(value) ? 'other' : 'list');
    setOtherVal(value && !TAIWAN_INSURERS.includes(value) ? value : '');
  }, [value]);

  return (
    <div>
      <select
        className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm"
        value={mode === 'other' ? '__other__' : value}
        onChange={(e) => {
          if (e.target.value === '__other__') { setMode('other'); onChange(otherVal); }
          else { setMode('list'); onChange(e.target.value); }
        }}
      >
        <option value="">— 請選擇 —</option>
        {TAIWAN_INSURERS.map((n) => <option key={n} value={n}>{n}</option>)}
        <option value="__other__">其他（手動輸入）</option>
      </select>
      {mode === 'other' && (
        <input
          className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm mt-2"
          placeholder="保險公司名稱"
          value={otherVal}
          onChange={(e) => { setOtherVal(e.target.value); onChange(e.target.value); }}
        />
      )}
    </div>
  );
}

export default function PolicyFormModal({ open, initial, vehicles, onClose, onSaved }: Props) {
  const isEdit = !!initial?.id;
  const [form, setForm] = useState<PolicyPayload>({ insurer_name: '', policy_number: '' });
  const [items, setItems] = useState<ItemRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    if (!open) return;
    setErr('');
    if (initial) {
      setForm({ ...initial, status: initial.status ?? 'active' });
      setItems(initial.items ?? []);
    } else {
      setForm({ insurer_name: '', policy_number: '', status: 'active' });
      setItems([]);
    }
  }, [open, initial]);

  if (!open) return null;

  const upd = <K extends keyof PolicyPayload>(k: K, v: PolicyPayload[K]) => {
    setForm((f) => ({ ...f, [k]: v }));
  };

  // 起保日變動 → 自動帶到期日 +1 年（任意險）
  const onStartChange = (val: string) => {
    upd('start_date', val);
    if (!form.end_date && val) {
      const d = new Date(val + 'T00:00:00');
      d.setFullYear(d.getFullYear() + 1);
      const y = d.getFullYear(); const m = String(d.getMonth() + 1).padStart(2, '0'); const dd = String(d.getDate()).padStart(2, '0');
      setForm((f) => ({ ...f, start_date: val, end_date: `${y}-${m}-${dd}` }));
    }
  };
  // 強制險同邏輯
  const onCStartChange = (val: string) => {
    upd('compulsory_start_date', val);
    if (!form.compulsory_end_date && val) {
      const d = new Date(val + 'T00:00:00');
      d.setFullYear(d.getFullYear() + 1);
      const y = d.getFullYear(); const m = String(d.getMonth() + 1).padStart(2, '0'); const dd = String(d.getDate()).padStart(2, '0');
      setForm((f) => ({ ...f, compulsory_start_date: val, compulsory_end_date: `${y}-${m}-${dd}` }));
    }
  };

  const addItem = () => setItems((arr) => [...arr, { item_name: '' }]);
  const updItem = (idx: number, k: keyof ItemRow, v: string) => {
    setItems((arr) => arr.map((it, i) => {
      if (i !== idx) return it;
      if (k === 'item_name') return { ...it, item_name: v };
      const num = v === '' ? null : Number(v.replace(/,/g, ''));
      return { ...it, [k]: isNaN(num as number) ? null : num };
    }));
  };
  const delItem = (idx: number) => setItems((arr) => arr.filter((_, i) => i !== idx));

  const handleSave = async () => {
    setErr('');
    if (!form.insurer_name?.trim() || !form.policy_number?.trim()) {
      setErr('請至少填寫保險公司與保單號碼');
      return;
    }
    const body: Record<string, unknown> = {
      vehicle_id: form.vehicle_id || null,
      insurer_name: form.insurer_name.trim(),
      policy_number: form.policy_number.trim(),
      status: form.status || 'active',
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      start_time: form.start_time || null,
      end_time: form.end_time || null,
      total_premium: form.total_premium ?? null,
      compulsory_insurer_name: form.compulsory_insurer_name?.trim() || null,
      compulsory_policy_number: form.compulsory_policy_number?.trim() || null,
      compulsory_premium: form.compulsory_premium ?? null,
      compulsory_start_date: form.compulsory_start_date || null,
      compulsory_end_date: form.compulsory_end_date || null,
      compulsory_start_time: form.compulsory_start_time || null,
      compulsory_end_time: form.compulsory_end_time || null,
      items: items.filter((it) => it.item_name.trim()),
    };
    setBusy(true);
    try {
      if (isEdit) {
        await api.put(`/api/v1/policies/${initial!.id}`, body);
      } else {
        await api.post('/api/v1/policies', body);
      }
      onSaved();
      onClose();
    } catch (e: unknown) {
      const errObj = e as { response?: { data?: { message?: string; detail?: string } } };
      setErr(errObj?.response?.data?.message || errObj?.response?.data?.detail || '儲存失敗');
    } finally {
      setBusy(false);
    }
  };

  const labelClass = 'block text-xs font-medium text-gray-600 mb-1';
  const inputClass = 'w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:border-primary-500';
  const sectionClass = 'mt-4 rounded-lg border-l-4 p-3';

  return (
    <div className="fixed inset-0 z-[9998] bg-black/55 flex items-start justify-center overflow-y-auto p-3 sm:p-6">
      <div className="bg-white rounded-2xl w-full max-w-xl shadow-2xl my-4 relative">
        <button onClick={onClose} className="absolute top-2 right-3 text-gray-400 hover:text-gray-600 text-2xl leading-none p-1">×</button>
        <div className="p-5 sm:p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-1">{isEdit ? '編輯保單' : '新增保單'}</h2>
          <p className="text-xs text-gray-500 mb-4">記錄您的保單資料以接收到期提醒。理賠流程仍需業務員協助。</p>

          {/* 基本欄位 */}
          <div className="space-y-3">
            <div>
              <label className={labelClass}>保險公司 <span className="text-red-500">*</span></label>
              <InsurerSelect value={form.insurer_name} onChange={(v) => upd('insurer_name', v)} />
            </div>
            <div>
              <label className={labelClass}>保單號碼 <span className="text-red-500">*</span></label>
              <input className={inputClass} value={form.policy_number} onChange={(e) => upd('policy_number', e.target.value)} placeholder="例：FBN-2026-001234" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>承保車輛</label>
                <select className={inputClass} value={form.vehicle_id ?? ''} onChange={(e) => upd('vehicle_id', e.target.value)}>
                  <option value="">不指定</option>
                  {vehicles.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.plate_number}{(v.brand || v.model) ? ` — ${v.brand || ''} ${v.model || ''}`.trim() : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelClass}>狀態</label>
                <select className={inputClass} value={form.status ?? 'active'} onChange={(e) => upd('status', e.target.value)}>
                  {POLICY_STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className={labelClass}>總保費</label>
              <input type="number" className={inputClass} value={form.total_premium ?? ''} onChange={(e) => upd('total_premium', e.target.value === '' ? null : Number(e.target.value))} placeholder="18500" />
            </div>
          </div>

          {/* 任意險期間 */}
          <div className={`${sectionClass} bg-blue-50 border-blue-500`}>
            <div className="text-xs font-bold text-blue-800 mb-2">任意險 期間</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>起保日</label>
                <div className="flex gap-2">
                  <input type="date" className={inputClass + ' flex-1'} value={form.start_date ?? ''} onChange={(e) => onStartChange(e.target.value)} />
                  <input type="time" lang="en-GB" step={60} className={inputClass + ' w-24'} value={form.start_time ?? ''} onChange={(e) => upd('start_time', e.target.value)} />
                </div>
                {form.start_date && <div className="text-[11px] text-blue-700 font-semibold mt-1">{rocLabel(form.start_date)}{form.start_time ? ` ${form.start_time}` : ''}</div>}
              </div>
              <div>
                <label className={labelClass}>到期日 <span className="text-[10px] text-gray-400">（自動 +1 年）</span></label>
                <div className="flex gap-2">
                  <input type="date" className={inputClass + ' flex-1'} value={form.end_date ?? ''} onChange={(e) => upd('end_date', e.target.value)} />
                  <input type="time" lang="en-GB" step={60} className={inputClass + ' w-24'} value={form.end_time ?? ''} onChange={(e) => upd('end_time', e.target.value)} />
                </div>
                {form.end_date && <div className="text-[11px] text-blue-700 font-semibold mt-1">{rocLabel(form.end_date)}{form.end_time ? ` ${form.end_time}` : ''}</div>}
              </div>
            </div>
          </div>

          {/* 強制險（可能不同家） */}
          <div className={`${sectionClass} bg-amber-50 border-amber-600`}>
            <div className="text-xs font-bold text-amber-800 mb-2">強制險（可能與任意險不同家、不同期間）</div>
            <div className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className={labelClass}>強制險 保險公司</label>
                  <InsurerSelect value={form.compulsory_insurer_name ?? ''} onChange={(v) => upd('compulsory_insurer_name', v || null)} />
                </div>
                <div>
                  <label className={labelClass}>強制險 保單號</label>
                  <input className={inputClass} value={form.compulsory_policy_number ?? ''} onChange={(e) => upd('compulsory_policy_number', e.target.value)} />
                </div>
              </div>
              <div>
                <label className={labelClass}>強制險 保費</label>
                <input type="number" className={inputClass} value={form.compulsory_premium ?? ''} onChange={(e) => upd('compulsory_premium', e.target.value === '' ? null : Number(e.target.value))} />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className={labelClass}>強制險 起保日</label>
                  <div className="flex gap-2">
                    <input type="date" className={inputClass + ' flex-1'} value={form.compulsory_start_date ?? ''} onChange={(e) => onCStartChange(e.target.value)} />
                    <input type="time" lang="en-GB" step={60} className={inputClass + ' w-24'} value={form.compulsory_start_time ?? ''} onChange={(e) => upd('compulsory_start_time', e.target.value)} />
                  </div>
                  {form.compulsory_start_date && <div className="text-[11px] text-amber-800 font-semibold mt-1">{rocLabel(form.compulsory_start_date)}{form.compulsory_start_time ? ` ${form.compulsory_start_time}` : ''}</div>}
                </div>
                <div>
                  <label className={labelClass}>強制險 到期日</label>
                  <div className="flex gap-2">
                    <input type="date" className={inputClass + ' flex-1'} value={form.compulsory_end_date ?? ''} onChange={(e) => upd('compulsory_end_date', e.target.value)} />
                    <input type="time" lang="en-GB" step={60} className={inputClass + ' w-24'} value={form.compulsory_end_time ?? ''} onChange={(e) => upd('compulsory_end_time', e.target.value)} />
                  </div>
                  {form.compulsory_end_date && <div className="text-[11px] text-amber-800 font-semibold mt-1">{rocLabel(form.compulsory_end_date)}{form.compulsory_end_time ? ` ${form.compulsory_end_time}` : ''}</div>}
                </div>
              </div>
            </div>
          </div>

          {/* 保障項目 */}
          <div className={`${sectionClass} bg-green-50 border-green-600`}>
            <div className="text-xs font-bold text-green-800 mb-2">保障項目</div>
            <div className="space-y-2">
              {items.map((it, idx) => (
                <div key={idx} className="flex flex-wrap gap-2 items-center bg-white rounded-md p-2 border border-gray-200">
                  <input className="flex-1 min-w-[120px] rounded border border-gray-200 px-2 py-1 text-xs" placeholder="項目名稱" value={it.item_name} onChange={(e) => updItem(idx, 'item_name', e.target.value)} />
                  <input type="number" className="w-24 rounded border border-gray-200 px-2 py-1 text-xs" placeholder="保額" value={it.coverage_limit ?? ''} onChange={(e) => updItem(idx, 'coverage_limit', e.target.value)} />
                  <input type="number" className="w-20 rounded border border-gray-200 px-2 py-1 text-xs" placeholder="自付額" value={it.deductible ?? ''} onChange={(e) => updItem(idx, 'deductible', e.target.value)} />
                  <input type="number" className="w-20 rounded border border-gray-200 px-2 py-1 text-xs" placeholder="保費" value={it.premium ?? ''} onChange={(e) => updItem(idx, 'premium', e.target.value)} />
                  <button type="button" onClick={() => delItem(idx)} className="rounded bg-red-50 hover:bg-red-100 p-1.5">
                    <Trash2 className="h-3.5 w-3.5 text-red-500" />
                  </button>
                </div>
              ))}
              <button type="button" onClick={addItem} className="flex items-center gap-1 text-xs text-green-700 font-semibold hover:bg-green-100 rounded px-2 py-1">
                <Plus className="h-3.5 w-3.5" /> 新增項目
              </button>
            </div>
          </div>

          {err && <div className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-600">{err}</div>}

          <div className="mt-5 flex flex-wrap gap-2 border-t border-gray-100 pt-4">
            <button onClick={handleSave} disabled={busy} className="flex items-center gap-1.5 rounded-lg bg-primary-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-primary-700 disabled:opacity-50">
              {busy && <Loader2 className="h-4 w-4 animate-spin" />}
              {isEdit ? '儲存變更' : '建立保單'}
            </button>
            <button onClick={onClose} className="rounded-lg bg-gray-100 px-5 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-200 ml-auto">關閉</button>
          </div>
        </div>
      </div>
    </div>
  );
}
