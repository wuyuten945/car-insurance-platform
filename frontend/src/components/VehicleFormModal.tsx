'use client';

import { useEffect, useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import api from '@/lib/api-client';
import { VEHICLE_TYPE_GROUPS, FUEL_TYPES, rocLabel } from '@/lib/vehicleTypes';
import { nextInspectionDue } from '@/lib/inspectionRules';

export interface VehiclePayload {
  id?: string;
  plate_number: string;
  brand?: string | null;
  model?: string | null;
  year?: number | null;
  manufacture_month?: number | null;
  color?: string | null;
  vin?: string | null;
  engine_cc?: number | null;
  vehicle_type?: string | null;
  fuel_type?: string | null;
  registration_date?: string | null;
  reissue_date?: string | null;
  registration_expiry?: string | null;
  data_source?: string;
}

interface Props {
  open: boolean;
  initial?: VehiclePayload | null;  // null/undefined = 新增；有值 = 編輯
  onClose: () => void;
  onSaved: () => void;
}

export default function VehicleFormModal({ open, initial, onClose, onSaved }: Props) {
  const isEdit = !!initial?.id;
  const [form, setForm] = useState<VehiclePayload>({
    plate_number: '',
  });
  const [yearMonth, setYearMonth] = useState('');  // 'YYYY-MM'
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    if (!open) return;
    setErr('');
    if (initial) {
      setForm({ ...initial });
      const ym = initial.year
        ? `${initial.year}-${String(initial.manufacture_month || 1).padStart(2, '0')}`
        : '';
      setYearMonth(ym);
    } else {
      setForm({ plate_number: '' });
      setYearMonth('');
    }
  }, [open, initial]);

  if (!open) return null;

  const update = <K extends keyof VehiclePayload>(k: K, v: VehiclePayload[K]) => {
    setForm((f) => ({ ...f, [k]: v }));
  };

  // 任何「車型 / 出廠年月 / 原發照日期」變動 → 自動推算驗車到期日（除非使用者已手動覆寫）
  const autoExpiry = (typeOverride?: string | null, ymOverride?: string, regOverride?: string) => {
    const vt = typeOverride !== undefined ? typeOverride : form.vehicle_type;
    const ym = ymOverride !== undefined ? ymOverride : yearMonth;
    const rd = regOverride !== undefined ? regOverride : (form.registration_date ?? '');
    if (!vt || !ym || !rd || !/^\d{4}-\d{2}$/.test(ym)) return;
    const [y, m] = ym.split('-');
    const due = nextInspectionDue(vt, parseInt(y, 10), parseInt(m, 10), rd);
    if (due) setForm((f) => ({ ...f, registration_expiry: due }));
  };

  const handleSave = async () => {
    setErr('');
    if (!form.plate_number.trim()) {
      setErr('請至少輸入車牌號碼');
      return;
    }
    // 把 form 各字串欄位的空字串轉 null（後端 schema 用 None），數字欄位保留原值
    const s = (v: string | null | undefined): string | null =>
      v && String(v).trim() ? String(v).trim() : null;
    let bodyYear: number | null = null;
    let bodyMonth: number | null = null;
    if (yearMonth && /^\d{4}-\d{2}$/.test(yearMonth)) {
      const [yy, mm] = yearMonth.split('-');
      bodyYear = parseInt(yy, 10);
      bodyMonth = parseInt(mm, 10);
    }
    const body: VehiclePayload = {
      plate_number: form.plate_number.trim(),
      brand: s(form.brand),
      model: s(form.model),
      year: bodyYear,
      manufacture_month: bodyMonth,
      color: s(form.color),
      vin: s(form.vin),
      engine_cc: form.engine_cc ?? null,
      vehicle_type: s(form.vehicle_type),
      fuel_type: s(form.fuel_type),
      registration_date: s(form.registration_date),
      reissue_date: s(form.reissue_date),
      registration_expiry: s(form.registration_expiry),
    };
    setBusy(true);
    try {
      if (isEdit) {
        await api.patch(`/api/v1/customers/vehicles/${initial!.id}`, body);
      } else {
        await api.post('/api/v1/customers/vehicles', body);
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
  const rocClass = 'block text-[11px] text-primary-600 font-semibold mt-1';

  return (
    <div className="fixed inset-0 z-[9998] bg-black/55 flex items-start justify-center overflow-y-auto p-3 sm:p-6">
      <div className="bg-white rounded-2xl w-full max-w-xl shadow-2xl my-4 relative">
        <button onClick={onClose} className="absolute top-2 right-3 text-gray-400 hover:text-gray-600 text-2xl leading-none p-1">×</button>
        <div className="p-5 sm:p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-1">
            {isEdit ? '編輯車輛' : '新增車輛'}
          </h2>
          <p className="text-xs text-gray-500 mb-4">至少填入車牌號碼，其他欄位有助於到期提醒與保單管理。</p>

          <div className="space-y-3">
            <div>
              <label className={labelClass}>車牌號碼 <span className="text-red-500">*</span></label>
              <input className={inputClass} value={form.plate_number} onChange={(e) => update('plate_number', e.target.value)} placeholder="例：ABC-1234" />
            </div>

            <div>
              <label className={labelClass}>車輛型式（監理分類）</label>
              <select className={inputClass} value={form.vehicle_type ?? ''} onChange={(e) => { update('vehicle_type', e.target.value); autoExpiry(e.target.value); }}>
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
                <label className={labelClass}>廠牌</label>
                <input className={inputClass} value={form.brand ?? ''} onChange={(e) => update('brand', e.target.value)} placeholder="例：Toyota" />
              </div>
              <div>
                <label className={labelClass}>車型</label>
                <input className={inputClass} value={form.model ?? ''} onChange={(e) => update('model', e.target.value)} placeholder="例：Altis" />
              </div>
            </div>

            <div>
              <label className={labelClass}>出廠年月</label>
              <input type="month" className={inputClass} value={yearMonth} onChange={(e) => { setYearMonth(e.target.value); autoExpiry(undefined, e.target.value); }} />
              {yearMonth && <span className={rocClass}>{rocLabel(yearMonth)}</span>}
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className={labelClass}>顏色</label>
                <input className={inputClass} value={form.color ?? ''} onChange={(e) => update('color', e.target.value)} />
              </div>
              <div>
                <label className={labelClass}>排氣量 cc</label>
                <input type="number" className={inputClass} value={form.engine_cc ?? ''} onChange={(e) => update('engine_cc', e.target.value ? parseInt(e.target.value, 10) : null)} />
              </div>
              <div>
                <label className={labelClass}>燃料</label>
                <select className={inputClass} value={form.fuel_type ?? ''} onChange={(e) => update('fuel_type', e.target.value)}>
                  <option value="">--</option>
                  {FUEL_TYPES.map((f) => <option key={f} value={f}>{f}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label className={labelClass}>車身號碼 (VIN)</label>
              <input className={inputClass} value={form.vin ?? ''} onChange={(e) => update('vin', e.target.value)} />
            </div>

            <div className="grid grid-cols-1 gap-3">
              <div>
                <label className={labelClass}>原發照日期</label>
                <input type="date" className={inputClass} value={form.registration_date ?? ''} onChange={(e) => { update('registration_date', e.target.value); autoExpiry(undefined, undefined, e.target.value); }} />
                {form.registration_date && <span className={rocClass}>{rocLabel(form.registration_date)}</span>}
              </div>
              <div>
                <label className={labelClass}>換補照日期</label>
                <input type="date" className={inputClass} value={form.reissue_date ?? ''} onChange={(e) => update('reissue_date', e.target.value)} />
                {form.reissue_date && <span className={rocClass}>{rocLabel(form.reissue_date)}</span>}
              </div>
              <div>
                <label className={labelClass}>驗車到期日</label>
                <input type="date" className={inputClass} value={form.registration_expiry ?? ''} onChange={(e) => update('registration_expiry', e.target.value)} />
                {form.registration_expiry && <span className={rocClass}>{rocLabel(form.registration_expiry)}</span>}
              </div>
            </div>
          </div>

          {err && <div className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-600">{err}</div>}

          <div className="mt-5 flex flex-wrap gap-2 border-t border-gray-100 pt-4">
            <button onClick={handleSave} disabled={busy} className="flex items-center gap-1.5 rounded-lg bg-primary-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-primary-700 disabled:opacity-50">
              {busy && <Loader2 className="h-4 w-4 animate-spin" />}
              {isEdit ? '儲存變更' : '建立車輛'}
            </button>
            <button onClick={onClose} className="rounded-lg bg-gray-100 px-5 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-200 ml-auto">關閉</button>
          </div>
        </div>
      </div>
    </div>
  );
}
