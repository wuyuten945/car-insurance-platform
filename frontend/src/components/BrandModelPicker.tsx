'use client';

import { useState } from 'react';
import { Search, Pencil } from 'lucide-react';
import { brandsFor, findBrand } from '@/lib/carCatalog';

// 新增/編輯車輛彈窗用：廠牌 → 車型 兩段點選方塊；清單外的走「其他」手動輸入
export default function BrandModelPicker({
  vehicleType, brand, model, onChange,
}: {
  vehicleType: string | null | undefined;
  brand: string | null | undefined;
  model: string | null | undefined;
  onChange: (brand: string, model: string) => void;
}) {
  const list = brandsFor(vehicleType);
  const matched = findBrand(list, brand);
  // 有值但不在清單 → 視為手動輸入
  const [customBrand, setCustomBrand] = useState(!!brand && !matched);
  const [customModel, setCustomModel] = useState(!!model && !!matched && !matched.models.includes(model));
  // 已選廠牌時收起廠牌方塊，只顯示選到的那個；點它可再展開
  const [pickingBrand, setPickingBrand] = useState(!brand);
  const [q, setQ] = useState('');

  const kw = q.trim().toLowerCase();
  const shown = kw ? list.filter((b) => b.value.toLowerCase().includes(kw) || b.zh.includes(q.trim())) : list;

  const chooseBrand = (value: string) => {
    setCustomBrand(false);
    setCustomModel(false);
    setPickingBrand(false);
    setQ('');
    onChange(value, '');
  };

  const labelClass = 'block text-xs font-medium text-gray-600 mb-1';
  const inputClass = 'w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:border-primary-500';

  return (
    <div className="space-y-3">
      <div>
        <label className={labelClass}>廠牌</label>
        {!pickingBrand && (brand || customBrand) ? (
          <div className="pickgrid">
            <button type="button" className="picktile is-active" onClick={() => setPickingBrand(true)}>
              {matched ? <><b>{matched.zh}</b><span>{matched.value}</span></> : <b>{brand || '其他'}</b>}
              <Pencil className="picktile-edit" />
            </button>
          </div>
        ) : (
          <>
            <div className="relative mb-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input className={inputClass + ' pl-9'} value={q} onChange={(e) => setQ(e.target.value)} placeholder="搜尋廠牌" />
            </div>
            <div className="pickgrid">
              {shown.map((b) => (
                <button
                  key={b.value}
                  type="button"
                  className={`picktile${matched?.value === b.value ? ' is-active' : ''}`}
                  onClick={() => chooseBrand(b.value)}
                >
                  <b>{b.zh}</b>
                  {b.zh !== b.value && <span>{b.value}</span>}
                </button>
              ))}
              <button
                type="button"
                className={`picktile${customBrand ? ' is-active' : ''}`}
                onClick={() => { setCustomBrand(true); setCustomModel(true); setPickingBrand(false); setQ(''); onChange('', ''); }}
              >
                <b>其他</b><span>自行輸入</span>
              </button>
            </div>
          </>
        )}
        {customBrand && !pickingBrand && (
          <input className={inputClass + ' mt-2'} value={brand ?? ''} onChange={(e) => onChange(e.target.value, model ?? '')} placeholder="輸入廠牌" autoFocus />
        )}
      </div>

      {(matched || customBrand) && !pickingBrand && (
        <div>
          <label className={labelClass}>車型</label>
          {matched && (
            <div className="pickgrid">
              {matched.models.map((m) => (
                <button
                  key={m}
                  type="button"
                  className={`picktile${!customModel && model === m ? ' is-active' : ''}`}
                  onClick={() => { setCustomModel(false); onChange(matched.value, m); }}
                >
                  <b>{m}</b>
                </button>
              ))}
              <button
                type="button"
                className={`picktile${customModel ? ' is-active' : ''}`}
                onClick={() => { setCustomModel(true); onChange(matched.value, ''); }}
              >
                <b>其他</b><span>自行輸入</span>
              </button>
            </div>
          )}
          {customModel && (
            <input className={inputClass + (matched ? ' mt-2' : '')} value={model ?? ''} onChange={(e) => onChange(brand ?? '', e.target.value)} placeholder="輸入車型" />
          )}
        </div>
      )}
    </div>
  );
}
