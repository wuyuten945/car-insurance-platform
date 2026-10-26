'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect, type ReactNode } from 'react';
import Header from '@/components/layout/Header';
import TopNav from '@/components/layout/TopNav';
import Footer from '@/components/legal/Footer';
import CookieBanner from '@/components/legal/CookieBanner';
import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';
import { LanguageProvider } from '@/lib/i18n/LanguageProvider';

export default function Providers({ children }: { children: ReactNode }) {
  // 客戶端初始化認證狀態（避免 hydration mismatch）
  const initAuth = useAuthStore((s) => s.initAuth);
  useEffect(() => { initAuth(); }, [initAuth]);

  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 1,
          },
        },
      })
  );

  const pathname = usePathname();
  const isLoginPage = pathname === '/login';
  const hasOwnHeader = pathname === '/inspection';
  const showGlobalChrome = !isLoginPage;

  return (
    <LanguageProvider>
      <QueryClientProvider client={queryClient}>
        {showGlobalChrome && (
          <div className="sticky top-0 z-50">
            {!hasOwnHeader && <Header />}
            <TopNav />
          </div>
        )}
        <main className="flex-1">
          {children}
        </main>
        <Footer />
        <CookieBanner />
      </QueryClientProvider>
    </LanguageProvider>
  );
}
