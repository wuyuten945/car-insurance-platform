'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, Loader2, Upload, CheckCircle } from 'lucide-react';
import api from '@/lib/api-client';
import { ACCIDENT_TYPES, MY_SITUATIONS } from '@/lib/constants';

const claimSchema = z.object({
  policy_id: z.string().min(1, '請選擇保單'),
  claim_type: z.string().min(1, '請選擇理賠類型'),
  accident_type: z.string().min(1, '請選擇事故類型'),
  my_situation: z.string().min(1, '請選擇行車狀態'),
  occurred_at: z.string().min(1, '請填寫事故時間'),
  location: z.string().min(1, '請填寫事故地點'),
  description: z.string().min(10, '請詳細描述事故情況（至少10字）'),
  amount_claimed: z.number().min(1, '請填寫預估損失金額'),
});

type ClaimForm = z.infer<typeof claimSchema>;

interface Policy {
  id: string;
  policy_number: string;
  insurer_name: string;
  vehicle_plate: string | null;
  status: string;
}

const CLAIM_TYPES = [
  { value: 'collision', label: '碰撞理賠' },
  { value: 'theft', label: '竊盜理賠' },
  { value: 'liability', label: '責任險理賠' },
  { value: 'comprehensive', label: '綜合理賠' },
  { value: 'other', label: '其他' },
];

export default function NewClaimPage() {
  const router = useRouter();
  const [submitted, setSubmitted] = useState(false);

  const { data: policies } = useQuery({
    queryKey: ['policies-active'],
    queryFn: async () => {
      const res = await api.get('/api/v1/policies');
      return (res.data.data as Policy[]).filter((p) => p.status === 'active');
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ClaimForm>({
    resolver: zodResolver(claimSchema),
  });

  const mutation = useMutation({
    mutationFn: async (data: ClaimForm) => {
      const res = await api.post('/api/v1/claims', data);
      return res.data.data;
    },
    onSuccess: () => setSubmitted(true),
  });

  if (submitted) {
    return (
      <div className="flex flex-col items-center justify-center px-4 py-20">
        <CheckCircle className="h-20 w-20 text-green-500 mb-4" />
        <h1 className="text-xl font-bold text-gray-900">理賠申請已送出</h1>
        <p className="text-sm text-gray-500 mt-2 text-center">
          我們將盡快為您處理，您可以在理賠紀錄中查看進度
        </p>
        <button
          onClick={() => router.push('/claims')}
          className="mt-6 rounded-xl bg-primary-500 px-8 py-3 text-sm font-semibold text-white"
        >
          查看理賠紀錄
        </button>
      </div>
    );
  }

  const inputClass = 'w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100';
  const labelClass = 'block text-sm font-medium text-gray-700 mb-1.5';
  const errorClass = 'text-xs text-red-500 mt-1';

  return (
    <div className="px-4 py-5">
      <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-primary-500 mb-4">
        <ArrowLeft className="h-4 w-4" /> 返回
      </button>

      <h1 className="text-xl font-bold text-gray-900 mb-1">申請理賠</h1>
      <p className="text-sm text-gray-500 mb-6">請填寫事故及理賠資訊</p>

      {mutation.isError && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">
          提交失敗，請稍後再試
        </div>
      )}

      <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-5">
        {/* Policy Selection */}
        <div>
          <label className={labelClass}>選擇保單</label>
          <select {...register('policy_id')} className={inputClass}>
            <option value="">請選擇保單</option>
            {policies?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.vehicle_plate ? `[${p.vehicle_plate}] ` : ''}{p.insurer_name} ({p.policy_number})
              </option>
            ))}
          </select>
          {errors.policy_id && <p className={errorClass}>{errors.policy_id.message}</p>}
        </div>

        {/* Claim Type */}
        <div>
          <label className={labelClass}>理賠類型</label>
          <select {...register('claim_type')} className={inputClass}>
            <option value="">請選擇類型</option>
            {CLAIM_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          {errors.claim_type && <p className={errorClass}>{errors.claim_type.message}</p>}
        </div>

        {/* Accident Type */}
        <div>
          <label className={labelClass}>事故類型</label>
          <select {...register('accident_type')} className={inputClass}>
            <option value="">請選擇事故類型</option>
            {ACCIDENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          {errors.accident_type && <p className={errorClass}>{errors.accident_type.message}</p>}
        </div>

        {/* My Situation */}
        <div>
          <label className={labelClass}>行車狀態</label>
          <select {...register('my_situation')} className={inputClass}>
            <option value="">請選擇您的行車狀態</option>
            {MY_SITUATIONS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
          {errors.my_situation && <p className={errorClass}>{errors.my_situation.message}</p>}
        </div>

        {/* Date */}
        <div>
          <label className={labelClass}>事故時間</label>
          <input type="datetime-local" {...register('occurred_at')} className={inputClass} />
          {errors.occurred_at && <p className={errorClass}>{errors.occurred_at.message}</p>}
        </div>

        {/* Location */}
        <div>
          <label className={labelClass}>事故地點</label>
          <input
            type="text"
            placeholder="例：台北市信義區信義路五段7號前"
            {...register('location')}
            className={inputClass}
          />
          {errors.location && <p className={errorClass}>{errors.location.message}</p>}
        </div>

        {/* Description */}
        <div>
          <label className={labelClass}>事故描述</label>
          <textarea
            rows={4}
            placeholder="請詳細描述事故經過..."
            {...register('description')}
            className={inputClass + ' resize-none'}
          />
          {errors.description && <p className={errorClass}>{errors.description.message}</p>}
        </div>

        {/* Amount */}
        <div>
          <label className={labelClass}>預估損失金額 (NTD)</label>
          <input
            type="number"
            placeholder="0"
            {...register('amount_claimed', { valueAsNumber: true })}
            className={inputClass}
          />
          {errors.amount_claimed && <p className={errorClass}>{errors.amount_claimed.message}</p>}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={mutation.isPending}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary-500 py-3.5 text-base font-semibold text-white transition hover:bg-primary-700 disabled:opacity-50"
        >
          {mutation.isPending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Upload className="h-5 w-5" />}
          送出理賠申請
        </button>
      </form>
    </div>
  );
}
