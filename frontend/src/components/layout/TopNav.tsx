'use client';

import { useEffect, useState } from 'react';
import { Home, FileText, AlertTriangle, ClipboardList, Menu, ChevronLeft, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useT } from '@/lib/i18n/LanguageProvider';

// 主導覽列：放在 Header 下方、一起固定在頂端（原本是底部導覽列）
export default function TopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { t } = useT();

  // 上一頁 / 下一頁：能不能走用 Navigation API 判斷（Chrome/Edge 有）；
  // 不支援的瀏覽器（Safari、舊 iPad）一律可按，走不了瀏覽器自己不會動
  const [canBack, setCanBack] = useState(true);
  const [canFwd, setCanFwd] = useState(true);
  useEffect(() => {
    const nav = (window as unknown as { navigation?: { canGoBack: boolean; canGoForward: boolean } }).navigation;
    if (nav) {
      setCanBack(nav.canGoBack);
      setCanFwd(nav.canGoForward);
    } else {
      setCanBack(window.history.length > 1);
    }
  }, [pathname]);
  const stepBtn = 'flex w-10 shrink-0 items-center justify-center text-gray-700 disabled:text-gray-300';

  const NAV_ITEMS = [
    { href: '/', icon: Home, label: t('nav.home') },
    { href: '/policies', icon: FileText, label: t('nav.policies') },
    { href: '/emergency', icon: AlertTriangle, label: t('dash.quickAction.emergency'), isEmergency: true },
    { href: '/claims', icon: ClipboardList, label: t('nav.claims') },
    { href: '/profile', icon: Menu, label: t('nav.profile') },
  ];

  return (
    <nav className="border-b border-gray-200 bg-white shadow-sm">
      <div className="mx-auto flex max-w-2xl items-stretch justify-around px-1">
        <button type="button" onClick={() => router.back()} disabled={!canBack} aria-label="上一頁" className={stepBtn}>
          <ChevronLeft className="h-6 w-6" />
        </button>
        {NAV_ITEMS.map((item) => {
          const isActive = item.href === '/'
            ? pathname === '/'
            : pathname.startsWith(item.href);
          const Icon = item.icon;
          const color = item.isEmergency
            ? 'text-emergency-red'
            : isActive ? 'text-primary-500' : 'text-gray-500';

          return (
            <Link
              key={item.href}
              href={item.href}
              aria-label={item.label}
              className={`flex flex-1 flex-col items-center gap-0.5 border-b-2 pt-2 pb-1.5 ${item.href === '/' ? 'justify-center' : ''} ${color} ${
                isActive ? (item.isEmergency ? 'border-emergency-red' : 'border-primary-500') : 'border-transparent'
              }`}
            >
              {/* 首頁只留圖示，不顯示文字 */}
              <Icon className={item.href === '/' ? 'h-6 w-6' : 'h-5 w-5'} />
              {item.href !== '/' && (
                <span className={`text-[11px] ${item.isEmergency || isActive ? 'font-bold' : 'font-medium'}`}>
                  {item.label}
                </span>
              )}
            </Link>
          );
        })}
        <button type="button" onClick={() => router.forward()} disabled={!canFwd} aria-label="下一頁" className={stepBtn}>
          <ChevronRight className="h-6 w-6" />
        </button>
      </div>
    </nav>
  );
}
