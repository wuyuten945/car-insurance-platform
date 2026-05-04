'use client';

import { Bell, Languages, LogOut } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import api from '@/lib/api-client';
import { useT } from '@/lib/i18n/LanguageProvider';
import { useAuthStore } from '@/stores/auth-store';

export default function Header() {
  const [unreadCount, setUnreadCount] = useState(0);
  const { t, toggleLang, lang } = useT();
  const { logout, isAuthenticated } = useAuthStore();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.replace('/login');
  };

  useEffect(() => {
    const fetchNotifications = async () => {
      if (!localStorage.getItem('access_token')) return;
      try {
        const res = await api.get('/api/v1/notifications');
        setUnreadCount(res.data.data?.unread_count ?? 0);
      } catch {
        // ignore
      }
    };
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-primary-500 text-white shadow-md">
      <div className="flex items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <Image src="/logo.png" alt="BOPINAN" width={32} height={32} className="h-8 w-8 object-contain" priority />
          <span className="text-lg font-bold tracking-tight">{t('header.title')}</span>
        </Link>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={toggleLang}
            aria-label="Toggle language"
            className="flex items-center gap-1 rounded-full px-2.5 py-1.5 text-xs font-bold bg-white/15 hover:bg-white/25 transition"
          >
            <Languages className="h-3.5 w-3.5" />
            {lang === 'zh' ? 'EN' : '中'}
          </button>
          <Link href="/notifications" className="relative p-2" aria-label={t('header.notifications')}>
            <Bell className="h-6 w-6" />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-accent-500 text-[10px] font-bold">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </Link>
          {isAuthenticated && (
            <button
              type="button"
              onClick={handleLogout}
              aria-label={t('header.logout')}
              className="p-2 hover:bg-white/10 rounded-full transition"
            >
              <LogOut className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
