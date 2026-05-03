'use client';

import { Home, FileText, AlertTriangle, ClipboardList, Menu } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useT } from '@/lib/i18n/LanguageProvider';

export default function BottomNav() {
  const pathname = usePathname();
  const { t } = useT();

  const NAV_ITEMS = [
    { href: '/', icon: Home, label: t('nav.home') },
    { href: '/policies', icon: FileText, label: t('nav.policies') },
    { href: '/emergency', icon: AlertTriangle, label: t('dash.quickAction.emergency'), isCenter: true },
    { href: '/claims', icon: ClipboardList, label: t('nav.claims') },
    { href: '/profile', icon: Menu, label: t('nav.profile') },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-200 bg-white pb-[env(safe-area-inset-bottom)]">
      <div className="flex items-end justify-around px-1 pt-1 pb-2">
        {NAV_ITEMS.map((item) => {
          const isActive = item.href === '/'
            ? pathname === '/'
            : pathname.startsWith(item.href);
          const Icon = item.icon;

          if (item.isCenter) {
            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex flex-col items-center -mt-5"
              >
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emergency-red text-white shadow-lg">
                  <Icon className="h-7 w-7" />
                </div>
                <span className="mt-0.5 text-[10px] font-semibold text-emergency-red">
                  {item.label}
                </span>
              </Link>
            );
          }

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center gap-0.5 px-2 py-1 ${
                isActive ? 'text-primary-500' : 'text-gray-400'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px] font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
