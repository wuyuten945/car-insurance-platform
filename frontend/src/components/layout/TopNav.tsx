'use client';

import { Home, FileText, AlertTriangle, ClipboardList, Menu } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useT } from '@/lib/i18n/LanguageProvider';

// 主導覽列：放在 Header 下方、一起固定在頂端（原本是底部導覽列）
export default function TopNav() {
  const pathname = usePathname();
  const { t } = useT();

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
              className={`flex flex-1 flex-col items-center gap-0.5 border-b-2 pt-2 pb-1.5 ${color} ${
                isActive ? (item.isEmergency ? 'border-emergency-red' : 'border-primary-500') : 'border-transparent'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span className={`text-[11px] ${item.isEmergency || isActive ? 'font-bold' : 'font-medium'}`}>
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
