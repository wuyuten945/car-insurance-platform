'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useT } from '@/lib/i18n/LanguageProvider';

const COOKIE_KEY = 'cookie-consent-v1';

export default function CookieBanner() {
  const [show, setShow] = useState(false);
  const { t } = useT();

  useEffect(() => {
    try {
      if (!localStorage.getItem(COOKIE_KEY)) setShow(true);
    } catch { /* ignore */ }
  }, []);

  const accept = () => {
    try {
      localStorage.setItem(COOKIE_KEY, 'accepted-' + Date.now());
    } catch { /* ignore */ }
    setShow(false);
  };

  if (!show) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[60] bg-gray-900 text-white shadow-2xl">
      <div className="max-w-3xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm leading-relaxed flex-1 min-w-[200px]">
          {t('cookie.banner.text')}
          <Link href="/legal/cookie" className="underline ml-1">
            {t('cookie.banner.more')}
          </Link>
        </p>
        <button
          onClick={accept}
          className="bg-white text-gray-900 px-5 py-2 rounded-lg text-sm font-bold hover:bg-gray-100 whitespace-nowrap"
        >
          {t('cookie.banner.accept')}
        </button>
      </div>
    </div>
  );
}
