'use client';

import { use } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Loader2, User, FileText, Phone } from 'lucide-react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api-client';
import { CLAIM_STAGES } from '@/lib/constants';

interface ProgressEntry {
  stage: string;
  note: string;
  timestamp: string;
}

interface ClaimDetail {
  id: string;
  claim_number: string;
  claim_type: string;
  status: string;
  created_at: string;
  amount_claimed: number;
  amount_approved: number | null;
  description: string;
  location: string;
  occurred_at: string;
  progress_history: ProgressEntry[];
  adjuster: {
    name: string;
    phone: string;
    email: string;
  } | null;
  documents: Array<{
    id: string;
    name: string;
    type: string;
    uploaded_at: string;
  }>;
}

const CLAIM_TYPE_MAP: Record<string, string> = {
  collision: '碰撞理賠',
  theft: '竊盜理賠',
  liability: '責任險理賠',
  comprehensive: '綜合理賠',
  other: '其他',
};

export default function ClaimDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();

  const { data: claim, isLoading } = useQuery({
    queryKey: ['claim', id],
    queryFn: async () => {
      const res = await api.get(`/api/v1/claims/${id}`);
      return res.data.data as ClaimDetail;
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="px-4 py-10 text-center">
        <p className="text-gray-500">找不到理賠紀錄</p>
      </div>
    );
  }

  const currentStageIndex = CLAIM_STAGES.findIndex((s) => s.key === claim.status);

  return (
    <div className="px-4 py-5 space-y-5">
      <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-primary-500">
        <ArrowLeft className="h-4 w-4" /> 返回
      </button>

      {/* Header */}
      <div className="rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 p-5 text-white">
        <p className="text-sm text-white/70">{claim.claim_number}</p>
        <h1 className="text-xl font-bold mt-1">
          {CLAIM_TYPE_MAP[claim.claim_type] ?? claim.claim_type}
        </h1>
        <div className="mt-3 flex gap-6">
          <div>
            <p className="text-[11px] text-white/60">申請金額</p>
            <p className="text-base font-bold">${claim.amount_claimed?.toLocaleString()}</p>
          </div>
          {claim.amount_approved !== null && claim.amount_approved !== undefined && (
            <div>
              <p className="text-[11px] text-white/60">核準金額</p>
              <p className="text-base font-bold text-green-300">${claim.amount_approved.toLocaleString()}</p>
            </div>
          )}
        </div>
      </div>

      {/* 7-Stage Progress Timeline */}
      <section className="rounded-xl bg-white p-4 shadow-sm border border-gray-100">
        <h2 className="text-sm font-bold text-gray-900 mb-4">理賠進度</h2>
        <div className="space-y-0">
          {CLAIM_STAGES.map((stage, i) => {
            const isCompleted = i < currentStageIndex;
            const isCurrent = i === currentStageIndex;
            const isPending = i > currentStageIndex;
            const historyEntry = claim.progress_history?.find((h) => h.stage === stage.key);

            return (
              <div key={stage.key} className="flex gap-3">
                {/* Timeline Line */}
                <div className="flex flex-col items-center">
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm ${
                      isCompleted
                        ? 'bg-green-500 text-white'
                        : isCurrent
                        ? 'bg-primary-500 text-white ring-4 ring-primary-100'
                        : 'bg-gray-200 text-gray-400'
                    }`}
                  >
                    {stage.icon}
                  </div>
                  {i < CLAIM_STAGES.length - 1 && (
                    <div
                      className={`w-0.5 h-10 ${
                        isCompleted ? 'bg-green-500' : 'bg-gray-200'
                      }`}
                    />
                  )}
                </div>

                {/* Content */}
                <div className="pb-6">
                  <p
                    className={`text-sm font-semibold ${
                      isPending ? 'text-gray-400' : 'text-gray-900'
                    }`}
                  >
                    {stage.label}
                    {isCurrent && (
                      <span className="ml-2 inline-flex rounded-full bg-primary-50 px-2 py-0.5 text-[10px] font-medium text-primary-500">
                        進行中
                      </span>
                    )}
                  </p>
                  {historyEntry && (
                    <>
                      <p className="text-xs text-gray-500 mt-0.5">{historyEntry.note}</p>
                      <p className="text-[11px] text-gray-400 mt-0.5">
                        {new Date(historyEntry.timestamp).toLocaleString('zh-TW')}
                      </p>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Adjuster Info */}
      {claim.adjuster && (
        <section className="rounded-xl bg-white p-4 shadow-sm border border-gray-100">
          <h2 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-1.5">
            <User className="h-4 w-4 text-primary-500" /> 理賠專員
          </h2>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">{claim.adjuster.name}</p>
              <p className="text-xs text-gray-500">{claim.adjuster.email}</p>
            </div>
            <a
              href={`tel:${claim.adjuster.phone}`}
              className="flex items-center gap-1 rounded-full bg-primary-500 px-3 py-1.5 text-xs font-medium text-white"
            >
              <Phone className="h-3.5 w-3.5" /> 聯繫
            </a>
          </div>
        </section>
      )}

      {/* Documents */}
      {claim.documents && claim.documents.length > 0 && (
        <section className="rounded-xl bg-white p-4 shadow-sm border border-gray-100">
          <h2 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-1.5">
            <FileText className="h-4 w-4 text-primary-500" /> 相關文件
          </h2>
          <div className="space-y-2">
            {claim.documents.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                <div>
                  <p className="text-sm text-gray-700">{doc.name}</p>
                  <p className="text-[11px] text-gray-400">
                    {new Date(doc.uploaded_at).toLocaleDateString('zh-TW')}
                  </p>
                </div>
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] text-gray-500">
                  {doc.type}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Claim Details */}
      <section className="rounded-xl bg-white p-4 shadow-sm border border-gray-100">
        <h2 className="text-sm font-bold text-gray-900 mb-3">事故資訊</h2>
        <div className="space-y-3 text-sm">
          <div>
            <p className="text-gray-400 text-xs">事故時間</p>
            <p className="text-gray-700">{new Date(claim.occurred_at).toLocaleString('zh-TW')}</p>
          </div>
          <div>
            <p className="text-gray-400 text-xs">事故地點</p>
            <p className="text-gray-700">{claim.location}</p>
          </div>
          <div>
            <p className="text-gray-400 text-xs">事故描述</p>
            <p className="text-gray-700 leading-relaxed">{claim.description}</p>
          </div>
        </div>
      </section>
    </div>
  );
}
