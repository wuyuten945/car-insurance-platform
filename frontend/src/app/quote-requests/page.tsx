'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ChevronLeft, FileText, Loader2, Star, Check, XCircle, Clock, MessageCircle, Plus, Calculator } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api-client';
import { useAuthGuard } from '@/lib/useAuthGuard';
import { useIdleLogout } from '@/lib/useIdleLogout';
import { useEligibility } from '@/lib/useEligibility';
import QuoteRequestModal from '@/components/QuoteRequestModal';

interface QuoteResponseRow {
  id: string;
  insurer_name: string;
  quoted_premium: number;
  coverage_details?: { name?: string; limit?: number; premium?: number }[] | null;
  valid_until?: string | null;
  notes?: string | null;
  is_recommended: boolean;
}

interface QuoteRequestRow {
  id: string;
  vehicle_plate?: string | null;
  use_existing_policy: boolean;
  desired_items?: { name: string; limit?: number; note?: string }[];
  driver_age?: number;
  claims_count_3y?: number;
  surcharge_pct?: number;
  notes?: string | null;
  assigned_admin_name?: string | null;
  status: string;
  submitted_at: string;
  quoted_at?: string | null;
  completed_at?: string | null;
  responses: QuoteResponseRow[];
}

const STATUS_LABEL: Record<string, { label: string; color: string; bg: string }> = {
  pending:     { label: '待處理',   color: 'text-amber-700',  bg: 'bg-amber-50 border-amber-200' },
  in_progress: { label: '處理中',   color: 'text-blue-700',   bg: 'bg-blue-50 border-blue-200' },
  quoted:      { label: '已回報',   color: 'text-green-700',  bg: 'bg-green-50 border-green-200' },
  completed:   { label: '已結案',   color: 'text-gray-600',   bg: 'bg-gray-100 border-gray-200' },
  cancelled:   { label: '已取消',   color: 'text-red-700',    bg: 'bg-red-50 border-red-200' },
};

export default function QuoteRequestsPage() {
  const { ready: __authReady } = useAuthGuard();
  useIdleLogout();
  const { eligibility } = useEligibility();
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);

  const { data: requests, isLoading } = useQuery({
    queryKey: ['my-quote-requests'],
    queryFn: async () => {
      const res = await api.get('/api/v1/quote-requests');
      return (res.data.data || []) as QuoteRequestRow[];
    },
    refetchOnWindowFocus: true,
  });

  // 載入車輛 + 保單給 modal 用
  const { data: vehicles } = useQuery({
    queryKey: ['my-vehicles'],
    queryFn: async () => {
      const res = await api.get('/api/v1/customers/vehicles');
      return res.data.data as Array<{ id: string; plate_number: string; brand: string | null; model: string | null; year: number | null; vehicle_type: string | null; engine_cc: number | null }>;
    },
  });
  const { data: policiesForModal } = useQuery({
    queryKey: ['my-policies-for-quote-req'],
    queryFn: async () => {
      const res = await api.get('/api/v1/policies');
      return (res.data.data || []) as Array<{
        id: string; insurer_name: string; policy_number: string;
        end_date?: string; vehicle_id?: string | null; data_source?: string;
      }>;
    },
  });

  const cancelMut = useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/api/v1/quote-requests/${id}/cancel`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['my-quote-requests'] }),
  });

  if (!__authReady) return null;

  return (
    <div className="px-4 py-5 space-y-4 pb-24">
      <div className="flex items-center gap-3">
        <Link href="/profile" className="p-1"><ChevronLeft className="h-5 w-5 text-gray-600" /></Link>
        <div className="flex-1">
          <h1 className="text-lg font-bold text-gray-900">我的車險續期保費詢價</h1>
          <p className="text-xs text-gray-500">追蹤每張詢價單的處理狀態與服務人員回報的報價</p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center gap-1 rounded-lg bg-primary-500 hover:bg-primary-700 px-3 py-2 text-xs font-semibold text-white"
        >
          <Plus className="h-4 w-4" /> 新增詢價
        </button>
      </div>

      <Link href="/quote" className="flex items-center justify-center gap-1 rounded-lg bg-gray-50 hover:bg-gray-100 border border-gray-200 px-3 py-2 text-xs text-gray-600">
        <Calculator className="h-4 w-4" /> 想先自助試算保費？前往「保費簡易試算（參考）」
      </Link>

      {isLoading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-primary-500" /></div>
      ) : !requests?.length ? (
        <div className="rounded-2xl bg-gray-50 p-8 text-center">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-3" />
          <p className="text-sm text-gray-500">尚無詢價工單</p>
          <button
            onClick={() => setModalOpen(true)}
            className="mt-3 inline-flex items-center gap-1 rounded-lg bg-primary-500 hover:bg-primary-700 px-4 py-2 text-sm font-semibold text-white"
          >
            <Plus className="h-4 w-4" /> 送出第一張詢價
          </button>
        </div>
      ) : (
        requests.map((qr) => {
          const stat = STATUS_LABEL[qr.status] || STATUS_LABEL.pending;
          return (
            <div key={qr.id} className="rounded-2xl bg-white p-4 shadow-sm border border-gray-100 space-y-2">
              <div className="flex items-start justify-between gap-2 flex-wrap">
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold ${stat.color} ${stat.bg}`}>
                      {stat.label}
                    </span>
                    {qr.vehicle_plate && (
                      <span className="text-sm font-bold text-gray-900">{qr.vehicle_plate}</span>
                    )}
                    {qr.use_existing_policy && (
                      <span className="rounded-full bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 text-[10px]">與原保單相同</span>
                    )}
                  </div>
                  <p className="text-[11px] text-gray-500 mt-1">
                    送出：{new Date(qr.submitted_at).toLocaleString('zh-TW')}
                    {qr.quoted_at && <> · 回報：{new Date(qr.quoted_at).toLocaleString('zh-TW')}</>}
                  </p>
                  {qr.assigned_admin_name && (
                    <p className="text-[11px] text-gray-500">處理人：{qr.assigned_admin_name}</p>
                  )}
                </div>
                {(qr.status === 'pending' || qr.status === 'in_progress') && (
                  <button
                    onClick={() => { if (confirm('確定取消此詢價？')) cancelMut.mutate(qr.id); }}
                    className="rounded-lg bg-red-50 hover:bg-red-100 text-red-600 text-xs px-3 py-1.5 font-semibold"
                  >
                    取消詢價
                  </button>
                )}
              </div>

              {/* 詢價內容摘要 */}
              {!qr.use_existing_policy && qr.desired_items && qr.desired_items.length > 0 && (
                <div className="text-xs text-gray-600 bg-gray-50 rounded-lg p-2">
                  <span className="text-gray-500">勾選項目：</span>
                  {qr.desired_items.map((it, i) => (
                    <span key={i} className="inline-block bg-white rounded px-2 py-0.5 mx-0.5 my-0.5 border border-gray-200">
                      {it.name}{it.limit ? ` ${(it.limit / 10000).toLocaleString()}萬` : ''}
                    </span>
                  ))}
                </div>
              )}
              {qr.notes && (
                <div className="text-xs text-gray-600 bg-gray-50 rounded-lg p-2">
                  <span className="text-gray-500">備註：</span>{qr.notes}
                </div>
              )}

              {/* 報價回報區 */}
              {qr.responses && qr.responses.length > 0 ? (
                <div className="space-y-2 mt-2 pt-2 border-t border-gray-100">
                  <p className="text-xs font-bold text-gray-700">服務人員回報的報價（{qr.responses.length} 家）：</p>
                  {qr.responses.map((r) => (
                    <div key={r.id} className={`rounded-xl p-3 border-2 ${r.is_recommended ? 'border-orange-300 bg-orange-50' : 'border-gray-100 bg-white'}`}>
                      {r.is_recommended && (
                        <div className="flex items-center gap-1 text-[10px] font-bold text-orange-700 mb-1">
                          <Star className="h-3 w-3 fill-orange-500 text-orange-500" /> 推薦方案
                        </div>
                      )}
                      <div className="flex items-start justify-between">
                        <p className="font-bold text-sm text-gray-900">{r.insurer_name}</p>
                        <p className="text-xl font-bold text-primary-600">${r.quoted_premium.toLocaleString()}</p>
                      </div>
                      {r.coverage_details && r.coverage_details.length > 0 && (
                        <ul className="space-y-0.5 mt-2">
                          {r.coverage_details.map((cd, i) => (
                            <li key={i} className="text-xs text-gray-600 flex items-start gap-1">
                              <Check className="h-3 w-3 text-green-500 mt-0.5 shrink-0" />
                              {cd.name}
                              {cd.limit ? ` · ${(cd.limit / 10000).toLocaleString()}萬` : ''}
                              {cd.premium ? ` · $${cd.premium.toLocaleString()}` : ''}
                            </li>
                          ))}
                        </ul>
                      )}
                      {r.notes && <p className="text-[11px] text-gray-500 mt-2 italic">📝 {r.notes}</p>}
                      {r.valid_until && <p className="text-[10px] text-gray-400 mt-1">報價有效期至 {r.valid_until}</p>}
                    </div>
                  ))}
                  {qr.status === 'quoted' && eligibility.line_oa_url && (
                    <a href={eligibility.line_oa_url} target="_blank" rel="noopener noreferrer"
                       className="mt-2 flex items-center justify-center gap-1 rounded-lg bg-green-500 hover:bg-green-600 text-white text-xs font-semibold px-3 py-2.5">
                      <MessageCircle className="h-4 w-4" /> 我要這方案 — LINE 聯繫業務員
                    </a>
                  )}
                </div>
              ) : qr.status === 'pending' ? (
                <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 rounded-lg p-2">
                  <Clock className="h-4 w-4" /> 服務人員已收到您的詢價，6–12 小時內會回報報價
                </div>
              ) : qr.status === 'in_progress' ? (
                <div className="flex items-center gap-2 text-xs text-blue-700 bg-blue-50 rounded-lg p-2">
                  <Clock className="h-4 w-4" /> 服務人員處理中（已開始向保險公司詢價）
                </div>
              ) : qr.status === 'cancelled' ? (
                <div className="flex items-center gap-2 text-xs text-red-700 bg-red-50 rounded-lg p-2">
                  <XCircle className="h-4 w-4" /> 此工單已取消
                </div>
              ) : null}
            </div>
          );
        })
      )}

      <QuoteRequestModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmitted={() => queryClient.invalidateQueries({ queryKey: ['my-quote-requests'] })}
        vehicles={vehicles ?? []}
        policies={policiesForModal ?? []}
      />
    </div>
  );
}
