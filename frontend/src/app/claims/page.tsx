'use client';

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { ClipboardList, ChevronRight, Loader2, FilePlus, Hourglass, CircleCheck } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api-client';
import { CLAIM_STAGES } from '@/lib/constants';
import { useT } from '@/lib/i18n/LanguageProvider';
import { useAuthGuard } from '@/lib/useAuthGuard';
import { useIdleLogout } from '@/lib/useIdleLogout';
import { AppTile, TileSection } from '@/components/AppTile';

interface Claim {
  id: string;
  claim_number: string;
  claim_type: string;
  status: string;
  created_at: string;
  amount_claimed: number;
  amount_approved: number | null;
}

const STATUS_COLOR: Record<string, string> = {
  submitted: 'bg-blue-100 text-blue-700',
  reviewing: 'bg-yellow-100 text-yellow-700',
  investigating: 'bg-purple-100 text-purple-700',
  negotiating: 'bg-orange-100 text-orange-700',
  approved: 'bg-green-100 text-green-700',
  paying: 'bg-emerald-100 text-emerald-700',
  closed: 'bg-gray-100 text-gray-600',
  rejected: 'bg-red-100 text-red-600',
};

export default function ClaimsPage() {
  const { ready: __authReady } = useAuthGuard();
  useIdleLogout();
  const { t, lang } = useT();
  const CLAIM_TYPE_MAP: Record<string, string> = {
    collision: t('claims.type.collision'),
    theft: t('claims.type.theft'),
    liability: t('claims.type.liability'),
    comprehensive: t('claims.type.comprehensive'),
    other: t('claims.type.other'),
  };
  const { data: claims, isLoading } = useQuery({
    queryKey: ['claims'],
    queryFn: async () => {
      const res = await api.get('/api/v1/claims');
      return res.data.data as Claim[];
    },
  });

  // 篩選方塊：已結案＝closed/rejected，其餘都算處理中
  const [filter, setFilter] = useState<'all' | 'open' | 'done'>('all');
  const isDone = (c: Claim) => c.status === 'closed' || c.status === 'rejected';
  const FILTERS = [
    { key: 'all' as const, label: t('claims.filter.all'), icon: ClipboardList, color: '#1565c0', match: () => true },
    { key: 'open' as const, label: t('claims.filter.open'), icon: Hourglass, color: '#f9a825', match: (c: Claim) => !isDone(c) },
    { key: 'done' as const, label: t('claims.filter.done'), icon: CircleCheck, color: '#757575', match: (c: Claim) => isDone(c) },
  ];
  const shown = (claims ?? []).filter(FILTERS.find((f) => f.key === filter)!.match);

  const getStageLabel = (status: string) => {
    const stage = CLAIM_STAGES.find((s) => s.key === status);
    return stage?.label ?? status;
  };

  const getStageIcon = (status: string) => {
    const stage = CLAIM_STAGES.find((s) => s.key === status);
    return stage?.icon ?? '';
  };

  if (!__authReady) return null;

  return (
    <div className="mx-auto max-w-lg px-4 py-5 space-y-5">
      <h1 className="text-xl font-bold text-gray-900">{t('claims.title')}</h1>

      <TileSection>
        <AppTile href="/claims/new" icon={FilePlus} label={t('claims.btnApply')} color="#ef6c00" />
        {FILTERS.map((f) => (
          <AppTile
            key={f.key}
            onClick={() => setFilter(f.key)}
            active={filter === f.key}
            icon={f.icon}
            label={`${f.label}（${(claims ?? []).filter(f.match).length}）`}
            color={f.color}
          />
        ))}
      </TileSection>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      ) : shown.length === 0 ? (
        <div className="flex flex-col items-center py-20">
          <ClipboardList className="h-16 w-16 text-gray-200 mb-3" />
          <p className="text-sm text-gray-400">{t('claims.empty')}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {shown.map((claim) => {
            const stageIndex = CLAIM_STAGES.findIndex((s) => s.key === claim.status);
            return (
              <Link
                key={claim.id}
                href={`/claims/view?id=${claim.id}`}
                className="block rounded-xl bg-white p-4 shadow-sm border border-gray-100 active:bg-gray-50"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-gray-900">
                        {CLAIM_TYPE_MAP[claim.claim_type] ?? claim.claim_type}
                      </p>
                      <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${STATUS_COLOR[claim.status] ?? 'bg-gray-100 text-gray-600'}`}>
                        {getStageIcon(claim.status)} {getStageLabel(claim.status)}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">{claim.claim_number}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {t('claims.appliedAt')}{new Date(claim.created_at).toLocaleDateString(lang === 'zh' ? 'zh-TW' : 'en-US')}
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="text-right">
                      <p className="text-sm font-semibold text-gray-900">
                        ${claim.amount_claimed?.toLocaleString()}
                      </p>
                      {claim.amount_approved !== null && claim.amount_approved !== undefined && (
                        <p className="text-[11px] text-green-600">
                          {t('claims.approvedLabel')}${claim.amount_approved.toLocaleString()}
                        </p>
                      )}
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  </div>
                </div>

                {/* Mini Timeline */}
                <div className="mt-3 flex items-center gap-0.5">
                  {CLAIM_STAGES.map((stage, i) => (
                    <div
                      key={stage.key}
                      className={`h-1.5 flex-1 rounded-full ${
                        i <= stageIndex ? 'bg-primary-500' : 'bg-gray-200'
                      }`}
                    />
                  ))}
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
