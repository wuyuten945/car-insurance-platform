'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api-client';

export interface Eligibility {
  has_agent_policy: boolean;
  can_file_claim: boolean;
  can_upload_accident_photo: boolean;
  can_self_register_vehicle: boolean;
  can_self_register_policy: boolean;
  can_use_reminders: boolean;
  line_oa_id: string;
  line_oa_url: string;
}

const FALLBACK: Eligibility = {
  has_agent_policy: false,
  can_file_claim: false,
  can_upload_accident_photo: false,
  can_self_register_vehicle: true,
  can_self_register_policy: true,
  can_use_reminders: true,
  line_oa_id: '',
  line_oa_url: '',
};

/**
 * 抓取目前登入使用者的功能權限旗標。
 * - has_agent_policy = true → 完整功能（理賠申請、事故照片上傳）
 * - has_agent_policy = false → 自填客戶，理賠 / 事故照片功能會被鎖定
 */
export function useEligibility() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['eligibility'],
    queryFn: async (): Promise<Eligibility> => {
      const res = await api.get('/api/v1/customers/eligibility');
      return res.data?.data ?? FALLBACK;
    },
    staleTime: 60_000, // 1 分鐘
  });
  return {
    eligibility: data ?? FALLBACK,
    isLoading,
    isError,
  };
}
