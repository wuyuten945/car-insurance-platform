'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

/**
 * 受登入保護的頁面用：沒 access_token 直接 router.replace('/login')。
 * 回傳 { ready: boolean } — ready=true 時表示已驗過 token，可放心 render 受保護內容。
 *
 * 為什麼不用 useAuthStore.isAuthenticated：
 *   loadUser 是 async，初始 isAuthenticated 為 false 但 token 還在 localStorage 跑驗證中，
 *   直接判斷會誤踢已登入使用者。改 read localStorage 即可同步判定。
 */
export function useAuthGuard() {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.replace('/login');
      return;
    }
    setReady(true);
  }, [router]);

  return { ready };
}
