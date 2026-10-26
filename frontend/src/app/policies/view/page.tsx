'use client';

import { Suspense, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Shield, DollarSign, AlertCircle, Loader2, Printer, Car, RefreshCw } from 'lucide-react';
import { AppTile, TileSection, TilePanel } from '@/components/AppTile';
import { useSearchParams } from 'next/navigation';
import api from '@/lib/api-client';

interface PolicyItem {
  id: string;
  item_name: string;
  coverage_limit: number | null;
  deductible: number | null;
  premium: number | null;
  is_active: boolean;
  description: string | null;
}

interface PolicyDetail {
  id: string;
  policy_number: string;
  insurer_name: string;
  status: string;
  start_date: string;
  end_date: string;
  total_premium: number | null;
  days_remaining: number | null;
  vehicle_plate: string | null;
  vehicle_brand: string | null;
  vehicle_model: string | null;
  document_url: string | null;
  items: PolicyItem[];
}

interface Exclusion {
  item_name: string;
  category: string;
  description: string;
  scenario: string;
}

function exportPolicyPdf(policy: PolicyDetail, exclusions?: Exclusion[]) {
  const itemsHtml = policy.items.map((it) => `
    <tr>
      <td style="padding:8px;border-bottom:1px solid #eee">${it.item_name}</td>
      <td style="padding:8px;border-bottom:1px solid #eee;text-align:right">${it.coverage_limit ? '$' + Number(it.coverage_limit).toLocaleString() : '-'}</td>
      <td style="padding:8px;border-bottom:1px solid #eee;text-align:right">${it.deductible && Number(it.deductible) > 0 ? '$' + Number(it.deductible).toLocaleString() : '-'}</td>
      <td style="padding:8px;border-bottom:1px solid #eee;text-align:right">${it.premium ? '$' + Number(it.premium).toLocaleString() : '-'}</td>
    </tr>
  `).join('');

  const excHtml = (exclusions && exclusions.length > 0) ? `
    <h2 style="margin-top:24px;font-size:16px;color:#333">不保事項</h2>
    <table style="width:100%;border-collapse:collapse;margin-top:8px;font-size:13px">
      <thead><tr style="background:#f5f5f5">
        <th style="padding:8px;text-align:left">項目</th>
        <th style="padding:8px;text-align:left">類別</th>
        <th style="padding:8px;text-align:left">說明</th>
      </tr></thead>
      <tbody>${exclusions.map((ex) => `
        <tr>
          <td style="padding:6px 8px;border-bottom:1px solid #eee">${ex.item_name}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee">${ex.category}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee">${ex.description}${ex.scenario ? '<br><span style="color:#999">情境：' + ex.scenario + '</span>' : ''}</td>
        </tr>
      `).join('')}</tbody>
    </table>
  ` : '';

  const html = `<!DOCTYPE html><html><head>
    <meta charset="utf-8">
    <title>${policy.insurer_name} - ${policy.policy_number}</title>
    <style>
      body { font-family: 'Microsoft JhengHei', Arial, sans-serif; margin: 30px; color: #333; }
      h1 { font-size: 20px; color: #1565C0; margin-bottom: 4px; }
      .subtitle { color: #666; font-size: 13px; margin-bottom: 20px; }
      .info-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 20px; }
      .info-box { background: #f8f9fa; border-radius: 8px; padding: 10px; }
      .info-box .label { font-size: 11px; color: #888; }
      .info-box .value { font-size: 14px; font-weight: bold; margin-top: 2px; }
      table { width: 100%; border-collapse: collapse; }
      th { background: #1565C0; color: white; padding: 8px; text-align: left; font-size: 13px; }
      td { font-size: 13px; }
      .footer { margin-top: 30px; padding-top: 12px; border-top: 1px solid #ddd; font-size: 11px; color: #999; }
      @media print { body { margin: 15px; } }
    </style>
  </head><body>
    <h1>${policy.insurer_name}</h1>
    <div class="subtitle">保單號碼：${policy.policy_number}${policy.vehicle_plate ? ' | 車號：' + policy.vehicle_plate : ''}</div>
    <div class="info-grid">
      <div class="info-box"><div class="label">起保日</div><div class="value">${policy.start_date}</div></div>
      <div class="info-box"><div class="label">到期日</div><div class="value">${policy.end_date}</div></div>
      <div class="info-box"><div class="label">總保費</div><div class="value">${policy.total_premium ? '$' + Number(policy.total_premium).toLocaleString() : '--'}</div></div>
    </div>
    ${policy.vehicle_plate ? `<div style="margin-bottom:16px;font-size:13px;color:#666">承保車輛：${policy.vehicle_plate} ${policy.vehicle_brand || ''} ${policy.vehicle_model || ''}</div>` : ''}
    <h2 style="font-size:16px;color:#333">保障項目</h2>
    <table style="margin-top:8px">
      <thead><tr><th>項目名稱</th><th style="text-align:right">保額</th><th style="text-align:right">自負額</th><th style="text-align:right">保費</th></tr></thead>
      <tbody>${itemsHtml}</tbody>
    </table>
    ${excHtml}
    <div class="footer">BOPINAN | 列印日期：${new Date().toLocaleDateString('zh-TW')}</div>
    <script>window.onload=function(){window.print();}</script>
  </body></html>`;

  const w = window.open('', '_blank');
  if (w) {
    w.document.write(html);
    w.document.close();
  }
}

function PolicyDetailContent() {
  const id = useSearchParams().get('id') ?? '';

  const { data: policy, isLoading } = useQuery({
    queryKey: ['policy', id],
    queryFn: async () => {
      const res = await api.get(`/api/v1/policies/${id}`);
      return res.data.data as PolicyDetail;
    },
    enabled: !!id,
  });

  // 方塊點開的區塊（一次一個，再點收起）；必須在下面的 early return 之前宣告
  const [openSec, setOpenSec] = useState<'' | 'items' | 'exclusions' | 'vehicle'>('');
  const toggleSec = (k: typeof openSec) => setOpenSec((cur) => (cur === k ? '' : k));

  const { data: exclusions } = useQuery({
    queryKey: ['policy-exclusions', id],
    queryFn: async () => {
      const res = await api.get(`/api/v1/policies/${id}/exclusions`);
      return res.data.data.exclusions as Exclusion[];
    },
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
      </div>
    );
  }

  if (!policy) {
    return (
      <div className="px-4 py-10 text-center">
        <p className="text-gray-500">找不到保單資料</p>
      </div>
    );
  }

  const daysLeft = policy.days_remaining ?? Math.ceil(
    (new Date(policy.end_date).getTime() - Date.now()) / 86400000
  );

  return (
    <div className="mx-auto max-w-[552px] px-4 py-5 space-y-4">
      {/* Back */}

      {/* Header Card */}
      <div className="rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 p-5 text-white">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-white/70">{policy.policy_number}</p>
            <h1 className="text-xl font-bold mt-1">{policy.insurer_name}</h1>
          </div>
          <Shield className="h-8 w-8 text-white/40" />
        </div>
        <div className="mt-4 grid grid-cols-3 gap-3">
          <div>
            <p className="text-[11px] text-white/60">保費</p>
            <p className="text-base font-bold">
              {policy.total_premium ? `$${Number(policy.total_premium).toLocaleString()}` : '--'}
            </p>
          </div>
          <div>
            <p className="text-[11px] text-white/60">到期日</p>
            <p className="text-sm font-semibold">{policy.end_date}</p>
          </div>
          <div>
            <p className="text-[11px] text-white/60">剩餘天數</p>
            <p className={`text-base font-bold ${daysLeft <= 30 ? 'text-yellow-300' : ''}`}>
              {daysLeft > 0 ? `${daysLeft} 天` : '已到期'}
            </p>
          </div>
        </div>
      </div>

      <TileSection>
        <AppTile onClick={() => toggleSec('items')} active={openSec === 'items'} icon={DollarSign} label={`保障項目\n（${policy.items?.length ?? 0}）`} color="#1565c0" />
        <AppTile onClick={() => toggleSec('exclusions')} active={openSec === 'exclusions'} icon={AlertCircle} label={`不保事項\n（${exclusions?.length ?? 0}）`} color="#ef6c00" />
        {policy.vehicle_plate && (
          <AppTile onClick={() => toggleSec('vehicle')} active={openSec === 'vehicle'} icon={Car} label="承保車輛" color="#455a64" />
        )}
        {policy.items?.length > 0 && (
          <AppTile onClick={() => exportPolicyPdf(policy, exclusions)} icon={Printer} label="匯出 PDF" color="#6d4c41" />
        )}
        {daysLeft > 0 && daysLeft <= 60 && (
          <AppTile href={`/renewal?policy_id=${id}`} icon={RefreshCw} label="續保比價" color="#2e7d32" />
        )}
      </TileSection>

      {/* Vehicle Info */}
      {openSec === 'vehicle' && policy.vehicle_plate && (
        <TilePanel title="承保車輛">
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div>
              <p className="text-gray-400 text-xs">車牌號碼</p>
              <p className="font-medium">{policy.vehicle_plate}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs">品牌</p>
              <p className="font-medium">{policy.vehicle_brand || '--'}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs">車型</p>
              <p className="font-medium">{policy.vehicle_model || '--'}</p>
            </div>
          </div>
        </TilePanel>
      )}

      {/* Coverage Items */}
      {openSec === 'items' && (
      <TilePanel title="保障項目">
        {policy.items?.length > 0 ? (
          <div className="space-y-3">
            {policy.items.map((item) => (
              <div key={item.id} className="flex items-center justify-between border-b border-gray-50 pb-2 last:border-0">
                <p className="text-sm text-gray-700">{item.item_name}</p>
                <div className="text-right">
                  {!!item.coverage_limit && (
                    <p className="text-sm font-semibold text-gray-900">
                      ${Number(item.coverage_limit).toLocaleString()}
                    </p>
                  )}
                  {Number(item.deductible) > 0 && (
                    <p className="text-[11px] text-gray-400">
                      自負額 ${Number(item.deductible).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">無保障項目資料</p>
        )}
      </TilePanel>
      )}

      {/* Exclusions */}
      {openSec === 'exclusions' && (
      <TilePanel title="不保事項">
        {exclusions && exclusions.length > 0 ? (
          <ul className="space-y-2">
            {exclusions.map((ex, i) => (
              <li key={i} className="text-sm text-gray-600">
                <span className="font-medium text-gray-800">{ex.item_name} - {ex.category}</span>
                <p className="text-xs text-gray-500 mt-0.5">{ex.description}</p>
                {ex.scenario && (
                  <p className="text-xs text-gray-400 mt-0.5">情境：{ex.scenario}</p>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-gray-400">無不保事項資料</p>
        )}
      </TilePanel>
      )}
    </div>
  );
}

export default function PolicyDetailPage() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      }
    >
      <PolicyDetailContent />
    </Suspense>
  );
}
