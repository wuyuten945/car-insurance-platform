'use client';

import { use } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Shield, Calendar, DollarSign, AlertCircle, Loader2, ChevronRight, Printer } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
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
    <div class="footer">車險智能服務平台 | 列印日期：${new Date().toLocaleDateString('zh-TW')}</div>
    <script>window.onload=function(){window.print();}</script>
  </body></html>`;

  const w = window.open('', '_blank');
  if (w) {
    w.document.write(html);
    w.document.close();
  }
}

export default function PolicyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();

  const { data: policy, isLoading } = useQuery({
    queryKey: ['policy', id],
    queryFn: async () => {
      const res = await api.get(`/api/v1/policies/${id}`);
      return res.data.data as PolicyDetail;
    },
  });

  const { data: exclusions } = useQuery({
    queryKey: ['policy-exclusions', id],
    queryFn: async () => {
      const res = await api.get(`/api/v1/policies/${id}/exclusions`);
      return res.data.data.exclusions as Exclusion[];
    },
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
    <div className="px-4 py-5 space-y-5">
      {/* Back */}
      <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-primary-500">
        <ArrowLeft className="h-4 w-4" /> 返回
      </button>

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

      {/* Renewal CTA */}
      {daysLeft > 0 && daysLeft <= 60 && (
        <Link
          href={`/renewal?policy_id=${id}`}
          className="flex items-center justify-between rounded-xl bg-accent-500 px-4 py-3 text-white shadow-sm"
        >
          <span className="font-semibold">續保比價方案</span>
          <ChevronRight className="h-5 w-5" />
        </Link>
      )}

      {/* Vehicle Info */}
      {policy.vehicle_plate && (
        <section className="rounded-xl bg-white p-4 shadow-sm border border-gray-100">
          <h2 className="text-sm font-bold text-gray-900 mb-3">承保車輛</h2>
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
        </section>
      )}

      {/* Coverage Items */}
      <section className="rounded-xl bg-white p-4 shadow-sm border border-gray-100">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-gray-900 flex items-center gap-1.5">
            <DollarSign className="h-4 w-4 text-primary-500" /> 保障項目
          </h2>
          {policy.items?.length > 0 && (
            <button
              onClick={() => exportPolicyPdf(policy, exclusions)}
              className="flex items-center gap-1 rounded-lg bg-primary-50 border border-primary-200 px-2.5 py-1 text-[11px] font-medium text-primary-600 hover:bg-primary-100 transition"
            >
              <Printer className="h-3 w-3" /> 匯出 PDF
            </button>
          )}
        </div>
        {policy.items?.length > 0 ? (
          <div className="space-y-3">
            {policy.items.map((item) => (
              <div key={item.id} className="flex items-center justify-between border-b border-gray-50 pb-2 last:border-0">
                <p className="text-sm text-gray-700">{item.item_name}</p>
                <div className="text-right">
                  {item.coverage_limit && (
                    <p className="text-sm font-semibold text-gray-900">
                      ${Number(item.coverage_limit).toLocaleString()}
                    </p>
                  )}
                  {item.deductible && Number(item.deductible) > 0 && (
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
      </section>

      {/* Exclusions */}
      <section className="rounded-xl bg-white p-4 shadow-sm border border-gray-100">
        <h2 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-1.5">
          <AlertCircle className="h-4 w-4 text-accent-500" /> 不保事項
        </h2>
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
      </section>
    </div>
  );
}
