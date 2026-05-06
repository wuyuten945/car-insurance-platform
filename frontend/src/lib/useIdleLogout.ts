'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';

const IDLE_TIMEOUT_MS = 10 * 60 * 1000; // 10 分鐘
const ACTIVITY_EVENTS = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart', 'click'];

/**
 * 前台閒置自動登出 hook：
 * - 10 分鐘無使用者動作 → 自動 logout 並 redirect 到 /login?reason=idle
 * - /login 頁讀 ?reason=idle 顯示「您已因閒置 10 分鐘自動登出」橫幅
 * - 使用者只要動滑鼠 / 鍵盤 / 點按 / 滑動 / 觸控 都會重置計時
 *
 * 用法：在 layout 或受保護頁面 useIdleLogout()
 */
export function useIdleLogout() {
  const router = useRouter();
  const logoutFn = useAuthStore((s) => s.logout);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const triggered = useRef(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (!localStorage.getItem('access_token')) return;  // 沒登入不啟動

    const onIdle = async () => {
      if (triggered.current) return;
      triggered.current = true;
      try { await logoutFn(); } catch {}
      router.replace('/login?reason=idle');
    };

    const reset = () => {
      if (triggered.current) return;
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(onIdle, IDLE_TIMEOUT_MS);
    };

    ACTIVITY_EVENTS.forEach((ev) => window.addEventListener(ev, reset, { passive: true }));
    reset();

    return () => {
      if (timer.current) clearTimeout(timer.current);
      ACTIVITY_EVENTS.forEach((ev) => window.removeEventListener(ev, reset));
    };
  }, [router, logoutFn]);
}

/**
 * 同伴 hook：如果 URL 帶 ?reason=idle，回傳 true，並在使用者第一次互動或 10 秒後自動清掉 query
 */
export function useIdleLogoutBanner() {
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    if (params.get('reason') === 'idle') {
      setShowBanner(true);
      // 10 秒後自動清 query 避免重整還在
      const t = setTimeout(() => {
        const url = new URL(window.location.href);
        url.searchParams.delete('reason');
        window.history.replaceState({}, '', url.toString());
        setShowBanner(false);
      }, 10000);
      return () => clearTimeout(t);
    }
  }, []);

  return showBanner;
}
