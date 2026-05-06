'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, ChevronRight, Loader2, Phone, Truck, Plus, Pencil, Trash2 } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api-client';
import { useT } from '@/lib/i18n/LanguageProvider';
import { useAuthGuard } from '@/lib/useAuthGuard';
import PolicyFormModal, { type PolicyPayload } from '@/components/PolicyFormModal';
import AddToCalendar from '@/components/AddToCalendar';

interface PolicyItem {
  item_name: string;
  coverage_limit?: number | null;
  deductible?: number | null;
  premium?: number | null;
}

interface Policy {
  id: string;
  policy_number: string;
  insurer_name: string;
  status: string;
  start_date: string;
  end_date: string;
  start_time?: string | null;
  end_time?: string | null;
  total_premium: number | null;
  vehicle_id?: string | null;
  vehicle_plate: string | null;
  items: PolicyItem[];
  data_source?: string;
  compulsory_insurer_name?: string | null;
  compulsory_policy_number?: string | null;
  compulsory_premium?: number | null;
  compulsory_start_date?: string | null;
  compulsory_end_date?: string | null;
  compulsory_start_time?: string | null;
  compulsory_end_time?: string | null;
}

interface VehicleLite { id: string; plate_number: string; brand?: string | null; model?: string | null }

const STATUS_COLOR: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  expired: 'bg-gray-100 text-gray-500',
  cancelled: 'bg-red-100 text-red-600',
  pending: 'bg-yellow-100 text-yellow-700',
};

const INSURER_PHONES: Record<string, string> = {
  '富邦': '0800-009-888',       // 富邦產物保險
  '國泰': '0800-036-599',       // 國泰世紀產險
  '新光': '0800-789-999',       // 新光產物保險
  '明台': '0800-099-080',       // 明台產物保險（三井住友）
  '南山': '0800-020-060',       // 南山產物保險
  '泰安': '0800-012-080',       // 泰安產物保險
  '旺旺友聯': '0800-024-024',   // 旺旺友聯產險
  '華南': '0800-010-850',       // 華南產物保險
  '兆豐': '0800-053-588',       // 兆豐產物保險
  '第一': '0800-288-168',       // 第一產物保險
  '新安東京': '0800-050-119',   // 新安東京海上產險
  '和泰': '0800-880-550',       // 和泰產險
  '台灣產物': '0800-053-888',   // 台灣產物保險
  '中國信託': '0800-024-168',   // 中國信託產險
  '台壽保': '0800-099-850',     // 台灣人壽保產險
  '安達': '02-2175-0803',       // 安達產險
  '蘇黎世': '02-2655-7890',     // 蘇黎世產險
  'Chubb': '02-2175-0803',      // 安達 Chubb
  'Zurich': '02-2655-7890',     // 蘇黎世 Zurich
  'Taiwan Fire': '0800-009-888', // 測試用（對應 seed data）
  'Test': '',                    // 測試保單不顯示電話
};

function getInsurerPhone(name: string): string | null {
  for (const [k, v] of Object.entries(INSURER_PHONES)) {
    if (name.includes(k) && v) return v;
  }
  return null;
}

function hasTowInsurance(items: PolicyItem[]): boolean {
  return items.some((it) =>
    it.item_name.includes('拖吊') || it.item_name.includes('道路救援') ||
    it.item_name.includes('路邊服務') || it.item_name.includes('拖車')
  );
}

export default function PoliciesPage() {
  const { ready: __authReady } = useAuthGuard();
  const [activeTab, setActiveTab] = useState('all');
  const { t } = useT();

  const TABS = [
    { key: 'all', label: t('policies.filter.all') },
    { key: 'active', label: t('policies.filter.active') },
    { key: 'expired', label: t('policies.filter.expired') },
  ];

  const STATUS_LABEL: Record<string, string> = {
    active: t('policies.status.active'),
    expired: t('policies.status.expired'),
    cancelled: t('policies.status.cancelled'),
    pending: t('policies.status.pending'),
  };

  const { data: policies, isLoading } = useQuery({
    queryKey: ['policies'],
    queryFn: async () => {
      const res = await api.get('/api/v1/policies');
      return res.data.data as Policy[];
    },
  });
  const { data: vehicles } = useQuery({
    queryKey: ['vehicles-for-policy'],
    queryFn: async () => {
      const res = await api.get('/api/v1/customers/vehicles');
      return res.data.data as VehicleLite[];
    },
  });

  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<PolicyPayload | null>(null);

  const handleAdd = () => { setEditing(null); setModalOpen(true); };
  const handleEdit = (p: Policy) => {
    setEditing({
      id: p.id, vehicle_id: p.vehicle_id ?? null,
      insurer_name: p.insurer_name, policy_number: p.policy_number,
      status: p.status,
      start_date: p.start_date, end_date: p.end_date,
      start_time: p.start_time ?? null, end_time: p.end_time ?? null,
      total_premium: p.total_premium,
      compulsory_insurer_name: p.compulsory_insurer_name ?? null,
      compulsory_policy_number: p.compulsory_policy_number ?? null,
      compulsory_premium: p.compulsory_premium ?? null,
      compulsory_start_date: p.compulsory_start_date ?? null,
      compulsory_end_date: p.compulsory_end_date ?? null,
      compulsory_start_time: p.compulsory_start_time ?? null,
      compulsory_end_time: p.compulsory_end_time ?? null,
      items: p.items ?? [],
    });
    setModalOpen(true);
  };
  const handleSaved = () => {
    queryClient.invalidateQueries({ queryKey: ['policies'] });
    queryClient.invalidateQueries({ queryKey: ['eligibility'] });
  };
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => { await api.delete(`/api/v1/policies/${id}`); },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['policies'] }),
  });

  const filtered = policies?.filter((p) =>
    activeTab === 'all' ? true : p.status === activeTab
  ) ?? [];

  if (!__authReady) return null;

  return (
    <div className="px-4 py-5">
      <div className="flex items-center mb-4">
        <h1 className="text-xl font-bold text-gray-900 flex-1">{t('policies.title')}</h1>
        <button onClick={handleAdd} className="flex items-center gap-1 rounded-lg bg-primary-500 px-3 py-2 text-xs font-semibold text-white hover:bg-primary-700">
          <Plus className="h-4 w-4" /> 新增保單
        </button>
      </div>

      {/* Tab Filters */}
      <div className="flex gap-2 mb-5">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
              activeTab === tab.key
                ? 'bg-primary-500 text-white'
                : 'bg-white text-gray-600 border border-gray-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center py-20">
          <FileText className="h-16 w-16 text-gray-200 mb-3" />
          <p className="text-sm text-gray-400">{t('policies.empty')}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((policy) => {
            const statusColor = STATUS_COLOR[policy.status] ?? 'bg-gray-100 text-gray-600';
            const statusLabel = STATUS_LABEL[policy.status] ?? policy.status;
            const isSelf = (policy.data_source || 'agent') === 'self';
            return (
              <div key={policy.id} className="rounded-xl bg-white p-4 shadow-sm border border-gray-100">
                <Link href={`/policies/${policy.id}`} className="block active:bg-gray-50 -m-4 p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-semibold text-gray-900">{policy.vehicle_plate ? `[${policy.vehicle_plate}] ` : ''}{policy.insurer_name}</p>
                      <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${statusColor}`}>
                        {statusLabel}
                      </span>
                      {isSelf ? (
                        <span className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-700">👤 自填</span>
                      ) : (
                        <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700">🛡 業務員建檔</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 mt-1">{policy.policy_number}</p>
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      <span className="text-xs text-gray-500">
                        任意險：{policy.start_date} ~ {policy.end_date}
                      </span>
                      {policy.end_date && (
                        <AddToCalendar
                          title={`保單到期 — ${policy.insurer_name} ${policy.policy_number}`}
                          date={policy.end_date}
                          description={`保單號：${policy.policy_number}\n保險公司：${policy.insurer_name}\n承保車輛：${policy.vehicle_plate || '-'}\n本次提醒由 BOPINAN 平台建立`}
                        />
                      )}
                    </div>
                    {policy.compulsory_end_date && (
                      <div className="flex items-center gap-2 mt-2 flex-wrap">
                        <span className="text-xs text-amber-700">
                          強制險：{policy.compulsory_start_date} ~ {policy.compulsory_end_date}
                        </span>
                        <AddToCalendar
                          title={`強制險到期 — ${policy.compulsory_insurer_name || policy.insurer_name}`}
                          date={policy.compulsory_end_date}
                          description={`強制險保單號：${policy.compulsory_policy_number || ''}\n保險公司：${policy.compulsory_insurer_name || ''}\n承保車輛：${policy.vehicle_plate || '-'}`}
                        />
                      </div>
                    )}
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      {hasTowInsurance(policy.items || []) ? (
                        <span className="inline-flex items-center gap-0.5 rounded-full bg-green-50 px-1.5 py-0.5 text-[10px] font-medium text-green-600">
                          <Truck className="h-3 w-3" /> {t('policies.hasTowing')}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-0.5 rounded-full bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-400">
                          <Truck className="h-3 w-3" /> {t('policies.noTowing')}
                        </span>
                      )}
                    </div>
                    {getInsurerPhone(policy.insurer_name) && (
                      <span
                         onClick={(e) => { e.preventDefault(); e.stopPropagation(); window.location.href = `tel:${getInsurerPhone(policy.insurer_name)}`; }}
                         className="inline-flex items-center gap-1 mt-1.5 text-[11px] text-primary-500 cursor-pointer">
                        <Phone className="h-3 w-3" /> {t('policies.customerService')} {getInsurerPhone(policy.insurer_name)}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 text-gray-400">
                    <span className="text-sm font-semibold text-primary-500">
                      ${policy.total_premium ? Number(policy.total_premium).toLocaleString() : '--'}
                    </span>
                    <ChevronRight className="h-4 w-4" />
                  </div>
                </div>
                </Link>
                {isSelf && (
                  <div className="flex gap-2 pt-3 border-t border-gray-100 mt-3">
                    <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleEdit(policy); }} className="flex-1 flex items-center justify-center gap-1 rounded-lg bg-gray-100 hover:bg-gray-200 px-3 py-2 text-xs font-semibold text-gray-700">
                      <Pencil className="h-3.5 w-3.5" /> 編輯
                    </button>
                    <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); if (confirm(`確定刪除保單「${policy.policy_number}」？`)) deleteMutation.mutate(policy.id); }} className="flex items-center justify-center gap-1 rounded-lg bg-red-50 hover:bg-red-100 px-3 py-2 text-xs font-semibold text-red-600">
                      <Trash2 className="h-3.5 w-3.5" /> 刪除
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <PolicyFormModal
        open={modalOpen}
        initial={editing}
        vehicles={vehicles ?? []}
        onClose={() => setModalOpen(false)}
        onSaved={handleSaved}
      />
    </div>
  );
}
