'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm, type SubmitErrorHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Loader2, Send, CheckCircle, CarFront, KeyRound, Users, ShieldCheck, Ellipsis,
  ChevronsRight, ArrowRightLeft, ArrowDownUp, Scissors, SquareParking, Car,
  ArrowUp, CornerUpLeft, CornerUpRight, ArrowDown, CirclePause, Gauge,
  type LucideIcon,
} from 'lucide-react';
import api from '@/lib/api-client';
import { ACCIDENT_TYPES, MY_SITUATIONS } from '@/lib/constants';
import { useT } from '@/lib/i18n/LanguageProvider';
import { useEligibility } from '@/lib/useEligibility';
import LockedFeatureNotice from '@/components/LockedFeatureNotice';
import { useAuthGuard } from '@/lib/useAuthGuard';
import { useIdleLogout } from '@/lib/useIdleLogout';
import { AppTile, TileSection } from '@/components/AppTile';

// 事故類型 / 行車狀態方塊的圖示與底色（選項本身定義在 lib/constants）
const ACCIDENT_ICONS: Record<string, LucideIcon> = {
  rear_end: ChevronsRight, side: ArrowRightLeft, head_on: ArrowDownUp,
  scrape: Scissors, parking: SquareParking, single: Car, other: Ellipsis,
};
const ACCIDENT_COLORS: Record<string, string> = {
  rear_end: '#d32f2f', side: '#ef6c00', head_on: '#b71c1c',
  scrape: '#f9a825', parking: '#1565c0', single: '#455a64', other: '#6d4c41',
};
const SITUATION_ICONS: Record<string, LucideIcon> = {
  straight: ArrowUp, turning_left: CornerUpLeft, turning_right: CornerUpRight,
  reversing: ArrowDown, parked: CirclePause, accelerating: Gauge, other: Ellipsis,
};
const SITUATION_COLORS: Record<string, string> = {
  straight: '#1565c0', turning_left: '#00897b', turning_right: '#2e7d32',
  reversing: '#6a1b9a', parked: '#455a64', accelerating: '#ef6c00', other: '#6d4c41',
};

const makeClaimSchema = (t: (k: string) => string) => z.object({
  policy_id: z.string().min(1, t('claimForm.err.policyRequired')),
  claim_type: z.string().min(1, t('claimForm.err.typeRequired')),
  accident_type: z.string().min(1, t('claimForm.err.accidentRequired')),
  my_situation: z.string().min(1, t('claimForm.err.situationRequired')),
  occurred_at: z.string().min(1, t('claimForm.err.occurredRequired')),
  location: z.string().min(1, t('claimForm.err.locationRequired')),
  description: z.string().min(10, t('claimForm.err.descRequired')),
  amount_claimed: z.number().min(1, t('claimForm.err.amountRequired')),
});

type ClaimForm = z.infer<ReturnType<typeof makeClaimSchema>>;

interface Policy {
  id: string;
  policy_number: string;
  insurer_name: string;
  vehicle_plate: string | null;
  status: string;
}

export default function NewClaimPage() {
  const router = useRouter();
  const { t } = useT();
  const claimSchema = makeClaimSchema(t);
  const CLAIM_TYPES = [
    { value: 'collision', label: t('claims.type.collision'), icon: CarFront, color: '#ef6c00' },
    { value: 'theft', label: t('claims.type.theft'), icon: KeyRound, color: '#6a1b9a' },
    { value: 'liability', label: t('claims.type.liability'), icon: Users, color: '#1565c0' },
    { value: 'comprehensive', label: t('claims.type.comprehensive'), icon: ShieldCheck, color: '#00897b' },
    { value: 'other', label: t('claims.type.other'), icon: Ellipsis, color: '#455a64' },
  ];
  const [submitted, setSubmitted] = useState(false);
  const { ready: authReady } = useAuthGuard();
  const { eligibility, isLoading: eligLoading } = useEligibility();

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
    setValue,
    watch,
    formState: { errors },
  } = useForm<ClaimForm>({
    resolver: zodResolver(claimSchema),
  });
  const claimType = watch('claim_type');
  const accidentType = watch('accident_type');
  const mySituation = watch('my_situation');

  const mutation = useMutation({
    mutationFn: async (data: ClaimForm) => {
      const res = await api.post('/api/v1/claims', data);
      return res.data.data;
    },
    onSuccess: () => setSubmitted(true),
  });

  // 送出成功 → 自動把畫面捲到頂部，讓使用者看到「✓ 已送出」確認頁
  // 6 秒後自動跳到「理賠紀錄」頁，避免使用者沒按按鈕被卡在這頁（包含登出後又重整的尷尬狀況）
  useEffect(() => {
    if (!submitted) return;
    window.scrollTo({ top: 0, behavior: 'smooth' });
    const timer = setTimeout(() => router.push('/claims'), 6000);
    return () => clearTimeout(timer);
  }, [submitted, router]);

  // 送出失敗 → 把錯誤訊息捲到視野中央
  useEffect(() => {
    if (mutation.isError) window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [mutation.isError]);

  // 驗證失敗 → 自動捲到第一個有錯誤的欄位
  const onInvalid: SubmitErrorHandler<ClaimForm> = (errs) => {
    const first = Object.keys(errs)[0];
    if (!first) return;
    const el = (document.querySelector(`[data-field="${first}"]`) || document.querySelector(`[name="${first}"]`)) as HTMLElement | null;
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      try { el.focus(); } catch {}
    }
  };

  // 等 auth guard 確認登入再 render（沒登入會被導去 /login）
  if (!authReady) return null;

  // 自填客戶 → 鎖定整頁，顯示「請聯繫 LINE」CTA
  if (!eligLoading && !eligibility.can_file_claim) {
    return (
      <div className="px-4 py-5">
        <h1 className="text-xl font-bold text-gray-900 mb-1">{t('claimForm.title')}</h1>
        <LockedFeatureNotice fullPage lineOaUrl={eligibility.line_oa_url} />
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="flex flex-col items-center justify-center px-4 py-20">
        <CheckCircle className="h-20 w-20 text-green-500 mb-4" />
        <h1 className="text-xl font-bold text-gray-900">{t('claimForm.submitted.title')}</h1>
        <p className="text-sm text-gray-500 mt-2 text-center">
          {t('claimForm.submitted.subtitle')}
        </p>
        <button
          onClick={() => router.push('/claims')}
          className="mt-6 rounded-xl bg-primary-500 px-8 py-3 text-sm font-semibold text-white"
        >
          {t('claimForm.submitted.btn')}
        </button>
      </div>
    );
  }

  const inputClass = 'w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100';
  const labelClass = 'block text-sm font-medium text-gray-700 mb-1.5';
  const errorClass = 'text-xs text-red-500 mt-1';

  return (
    <div className="px-4 py-5">

      <h1 className="text-xl font-bold text-gray-900 mb-1">{t('claimForm.title')}</h1>
      <p className="text-sm text-gray-500 mb-6">{t('claimForm.subtitle')}</p>

      {mutation.isError && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">
          {t('claimForm.submitFailed')}
        </div>
      )}

      <form onSubmit={handleSubmit((data) => mutation.mutate(data), onInvalid)} className="space-y-5">
        <div>
          <label className={labelClass}>{t('claimForm.lbl.policy')}</label>
          <select {...register('policy_id')} className={inputClass}>
            <option value="">{t('claimForm.opt.policyChoose')}</option>
            {policies?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.vehicle_plate ? `[${p.vehicle_plate}] ` : ''}{p.insurer_name} ({p.policy_number})
              </option>
            ))}
          </select>
          {errors.policy_id && <p className={errorClass}>{errors.policy_id.message}</p>}
        </div>

        <div>
          {/* 理賠類型改方塊；值仍走 react-hook-form（隱藏欄位），驗證失敗時捲到這塊 */}
          <div data-field="claim_type">
            <input type="hidden" {...register('claim_type')} />
            <TileSection title={t('claimForm.lbl.claimType')}>
              {CLAIM_TYPES.map((ct) => (
                <AppTile
                  key={ct.value}
                  onClick={() => setValue('claim_type', ct.value, { shouldValidate: true })}
                  active={claimType === ct.value}
                  icon={ct.icon}
                  label={ct.label}
                  color={ct.color}
                />
              ))}
            </TileSection>
          </div>
          {errors.claim_type && <p className={errorClass}>{errors.claim_type.message}</p>}
        </div>

        <div>
          <div data-field="accident_type">
            <input type="hidden" {...register('accident_type')} />
            <TileSection title={t('claimForm.lbl.accidentType')}>
              {ACCIDENT_TYPES.map((ac) => (
                <AppTile
                  key={ac.value}
                  onClick={() => setValue('accident_type', ac.value, { shouldValidate: true })}
                  active={accidentType === ac.value}
                  icon={ACCIDENT_ICONS[ac.value] ?? Ellipsis}
                  label={ac.label}
                  color={ACCIDENT_COLORS[ac.value] ?? '#455a64'}
                />
              ))}
            </TileSection>
          </div>
          {errors.accident_type && <p className={errorClass}>{errors.accident_type.message}</p>}
        </div>

        <div>
          <div data-field="my_situation">
            <input type="hidden" {...register('my_situation')} />
            <TileSection title={t('claimForm.lbl.situation')}>
              {MY_SITUATIONS.map((st) => (
                <AppTile
                  key={st.value}
                  onClick={() => setValue('my_situation', st.value, { shouldValidate: true })}
                  active={mySituation === st.value}
                  icon={SITUATION_ICONS[st.value] ?? Ellipsis}
                  label={st.label}
                  color={SITUATION_COLORS[st.value] ?? '#455a64'}
                />
              ))}
            </TileSection>
          </div>
          {errors.my_situation && <p className={errorClass}>{errors.my_situation.message}</p>}
        </div>

        <div>
          <label className={labelClass}>{t('claimForm.lbl.occurredAt')}</label>
          <input type="datetime-local" {...register('occurred_at')} className={inputClass} />
          {errors.occurred_at && <p className={errorClass}>{errors.occurred_at.message}</p>}
        </div>

        <div>
          <label className={labelClass}>{t('claimForm.lbl.location')}</label>
          <input
            type="text"
            placeholder={t('claimForm.ph.location')}
            {...register('location')}
            className={inputClass}
          />
          {errors.location && <p className={errorClass}>{errors.location.message}</p>}
        </div>

        <div>
          <label className={labelClass}>{t('claimForm.lbl.description')}</label>
          <textarea
            rows={4}
            placeholder={t('claimForm.ph.description')}
            {...register('description')}
            className={inputClass + ' resize-none'}
          />
          {errors.description && <p className={errorClass}>{errors.description.message}</p>}
        </div>

        <div>
          <label className={labelClass}>{t('claimForm.lbl.amount')}</label>
          <input
            type="number"
            placeholder="0"
            {...register('amount_claimed', { valueAsNumber: true })}
            className={inputClass}
          />
          {errors.amount_claimed && <p className={errorClass}>{errors.amount_claimed.message}</p>}
        </div>

        <button
          type="submit"
          disabled={mutation.isPending}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary-500 py-3.5 text-base font-semibold text-white transition hover:bg-primary-700 disabled:opacity-50"
        >
          {mutation.isPending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
          {mutation.isPending ? t('claimForm.btn.submitting') : t('claimForm.btn.submit')}
        </button>
      </form>
    </div>
  );
}
