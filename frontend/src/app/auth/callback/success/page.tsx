'use client';

import { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { useAuthStore } from '@/stores/auth-store';
import api from '@/lib/api-client';

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { initAuth } = useAuthStore();

  useEffect(() => {
    const accessToken = searchParams.get('access_token');
    const refreshToken = searchParams.get('refresh_token');
    if (accessToken && refreshToken) {
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
      initAuth();
      // 檢查是否需要補資料引導（OAuth 通常缺生日/身份證）
      api.get('/api/v1/customers/profile')
        .then((res) => {
          const u = res.data.data;
          router.replace(u?.is_profile_complete ? '/' : '/onboarding');
        })
        .catch(() => router.replace('/onboarding'));
    } else {
      router.replace('/login?error=oauth_failed');
    }
  }, [searchParams, router, initAuth]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <Loader2 className="h-10 w-10 animate-spin text-primary-500 mx-auto mb-4" />
        <p className="text-gray-500">登入中...</p>
      </div>
    </div>
  );
}

export default function OAuthSuccessPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><p>載入中...</p></div>}>
      <CallbackHandler />
    </Suspense>
  );
}
