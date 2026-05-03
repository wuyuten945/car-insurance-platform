'use client';

import { Bell, Shield } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import api from '@/lib/api-client';

export default function Header() {
  const [unreadCount, setUnreadCount] = useState(0);

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
          <Shield className="h-7 w-7" />
          <span className="text-lg font-bold tracking-tight">車險智能平台</span>
        </Link>
        <Link href="/notifications" className="relative p-2">
          <Bell className="h-6 w-6" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-accent-500 text-[10px] font-bold">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Link>
      </div>
    </header>
  );
}
