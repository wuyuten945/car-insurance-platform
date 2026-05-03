'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Check, Star, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api-client';

interface RenewalQuote {
  id: string;
  insurer_name: string;
  product_name: string;
  annual_premium: number;
  coverage_items: Array<{
    name: string;
    coverage_amount: number;
    deductible: number;
  }>;
  rating: number;
  is_recommended: boolean;
  features: string[];
}

export default function RenewalPage() {
  return (
    <Suspense fallback={<div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-primary-500" /></div>}>
      <RenewalContent />
    </Suspense>
  );
}

function RenewalContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const policyId = searchParams.get('policy_id') ?? '';

  const { data: quotes, isLoading } = useQuery({
    queryKey: ['renewal-quotes', policyId],
    queryFn: async () => {
      const res = await api.get(`/api/v1/renewal/quotes?policy_id=${policyId}`);
      return res.data.data as RenewalQuote[];
    },
    enabled: !!policyId,
  });

  return (
    <div className="px-4 py-5 space-y-5">
      <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-primary-500">
        <ArrowLeft className="h-4 w-4" /> 返回
      </button>

      <div>
        <h1 className="text-xl font-bold text-gray-900">續保比價</h1>
        <p className="text-sm text-gray-500 mt-1">為您推薦最佳續保方案</p>
      </div>

      {!policyId && (
        <div className="rounded-xl bg-yellow-50 p-4 text-sm text-yellow-700">
          請從保單詳情頁面進入續保比價
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      ) : quotes && quotes.length > 0 ? (
        <div className="space-y-4">
          {quotes.map((quote) => (
            <div
              key={quote.id}
              className={`relative rounded-2xl bg-white p-5 shadow-sm border-2 ${
                quote.is_recommended ? 'border-accent-500' : 'border-gray-100'
              }`}
            >
              {quote.is_recommended && (
                <div className="absolute -top-3 left-4 flex items-center gap-1 rounded-full bg-accent-500 px-3 py-0.5 text-xs font-bold text-white">
                  <Star className="h-3 w-3" /> 推薦方案
                </div>
              )}
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-bold text-gray-900">{quote.insurer_name}</p>
                  <p className="text-sm text-gray-500 mt-0.5">{quote.product_name}</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-primary-500">
                    ${quote.annual_premium?.toLocaleString()}
                  </p>
                  <p className="text-[11px] text-gray-400">/年</p>
                </div>
              </div>

              {/* Rating */}
              {quote.rating > 0 && (
                <div className="flex items-center gap-1 mt-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star
                      key={i}
                      className={`h-3.5 w-3.5 ${
                        i < quote.rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-200'
                      }`}
                    />
                  ))}
                  <span className="text-xs text-gray-500 ml-1">{quote.rating}</span>
                </div>
              )}

              {/* Coverage Items */}
              <div className="mt-4 space-y-2">
                {quote.coverage_items?.map((item, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span className="text-gray-600">{item.name}</span>
                    <span className="font-medium text-gray-900">${item.coverage_amount?.toLocaleString()}</span>
                  </div>
                ))}
              </div>

              {/* Features */}
              {quote.features?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {quote.features.map((feat, i) => (
                    <span key={i} className="inline-flex items-center gap-0.5 rounded-full bg-green-50 px-2 py-0.5 text-[11px] text-green-700">
                      <Check className="h-3 w-3" /> {feat}
                    </span>
                  ))}
                </div>
              )}

              <button className="mt-4 w-full rounded-xl bg-primary-500 py-2.5 text-sm font-semibold text-white hover:bg-primary-700 transition">
                選擇此方案
              </button>
            </div>
          ))}
        </div>
      ) : policyId ? (
        <div className="text-center py-20">
          <p className="text-gray-400">暫無可用的續保方案</p>
        </div>
      ) : null}
    </div>
  );
}
