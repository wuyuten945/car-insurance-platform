'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, ChevronRight, Loader2, Phone, Truck } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api-client';

interface PolicyItem {
  item_name: string;
}

interface Policy {
  id: string;
  policy_number: string;
  insurer_name: string;
  status: string;
  start_date: string;
  end_date: string;
  total_premium: number | null;
  vehicle_plate: string | null;
  items: PolicyItem[];
}

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  active: { label: '有效', color: 'bg-green-100 text-green-700' },
  expired: { label: '已到期', color: 'bg-gray-100 text-gray-500' },
  cancelled: { label: '已取消', color: 'bg-red-100 text-red-600' },
  pending: { label: '待生效', color: 'bg-yellow-100 text-yellow-700' },
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

const TABS = [
  { key: 'all', label: '全部' },
  { key: 'active', label: '有效' },
  { key: 'expired', label: '已到期' },
];

export default function PoliciesPage() {
  const [activeTab, setActiveTab] = useState('all');

  const { data: policies, isLoading } = useQuery({
    queryKey: ['policies'],
    queryFn: async () => {
      const res = await api.get('/api/v1/policies');
      return res.data.data as Policy[];
    },
  });

  const filtered = policies?.filter((p) =>
    activeTab === 'all' ? true : p.status === activeTab
  ) ?? [];

  return (
    <div className="px-4 py-5">
      <h1 className="text-xl font-bold text-gray-900 mb-4">我的保單</h1>

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
          <p className="text-sm text-gray-400">尚無保單資料</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((policy) => {
            const statusInfo = STATUS_MAP[policy.status] ?? { label: policy.status, color: 'bg-gray-100 text-gray-600' };
            return (
              <Link
                key={policy.id}
                href={`/policies/${policy.id}`}
                className="block rounded-xl bg-white p-4 shadow-sm border border-gray-100 active:bg-gray-50"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-gray-900">{policy.vehicle_plate ? `[${policy.vehicle_plate}] ` : ''}{policy.insurer_name}</p>
                      <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${statusInfo.color}`}>
                        {statusInfo.label}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">{policy.policy_number}</p>
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      <span className="text-xs text-gray-500">
                        {policy.start_date} ~ {policy.end_date}
                      </span>
                      {hasTowInsurance(policy.items || []) ? (
                        <span className="inline-flex items-center gap-0.5 rounded-full bg-green-50 px-1.5 py-0.5 text-[10px] font-medium text-green-600">
                          <Truck className="h-3 w-3" /> 含拖吊
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-0.5 rounded-full bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-400">
                          <Truck className="h-3 w-3" /> 無拖吊
                        </span>
                      )}
                    </div>
                    {getInsurerPhone(policy.insurer_name) && (
                      <span
                         onClick={(e) => { e.preventDefault(); e.stopPropagation(); window.location.href = `tel:${getInsurerPhone(policy.insurer_name)}`; }}
                         className="inline-flex items-center gap-1 mt-1.5 text-[11px] text-primary-500 cursor-pointer">
                        <Phone className="h-3 w-3" /> 客服 {getInsurerPhone(policy.insurer_name)}
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
            );
          })}
        </div>
      )}
    </div>
  );
}
