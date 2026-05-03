'use client';

import Link from 'next/link';
import { useT } from '@/lib/i18n/LanguageProvider';

export default function Footer() {
  const { t } = useT();

  const links: Array<{ slug: string; label: string }> = [
    { slug: 'personal-data', label: t('footer.personalData') },
    { slug: 'privacy', label: t('footer.privacy') },
    { slug: 'cookie', label: t('footer.cookie') },
    { slug: 'minor', label: t('footer.minor') },
    { slug: 'disclaimer', label: t('footer.disclaimer') },
  ];

  return (
    <footer className="mt-8 px-4 py-5 border-t border-gray-200 bg-white/60 backdrop-blur-sm">
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 mb-3">
        {links.map((l) => (
          <Link
            key={l.slug}
            href={`/legal/${l.slug}`}
            className="text-xs text-gray-500 hover:text-gray-800 transition"
          >
            {l.label}
          </Link>
        ))}
      </div>
      <p className="text-center text-[11px] text-gray-400 leading-relaxed">
        {t('footer.copyright')}
      </p>
    </footer>
  );
}
