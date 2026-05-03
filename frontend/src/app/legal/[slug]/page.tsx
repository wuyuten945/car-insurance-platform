'use client';

import { use } from 'react';
import { ChevronLeft } from 'lucide-react';
import Link from 'next/link';
import { useT } from '@/lib/i18n/LanguageProvider';
import { LEGAL_DOCS, type LegalKey } from '@/components/legal/legal-content';

const VALID: LegalKey[] = ['personal-data', 'privacy', 'cookie', 'minor', 'disclaimer'];

export default function LegalPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const { lang } = useT();

  if (!VALID.includes(slug as LegalKey)) {
    return (
      <div className="px-4 py-12 text-center">
        <p className="text-gray-500">Document not found</p>
        <Link href="/" className="text-primary-500 mt-3 inline-block">回首頁</Link>
      </div>
    );
  }

  const doc = LEGAL_DOCS[slug as LegalKey];
  const title = doc.title[lang];
  const body = doc.body[lang];

  return (
    <div className="px-4 py-5 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-4">
        <Link href="/" className="p-1">
          <ChevronLeft className="h-5 w-5 text-gray-600" />
        </Link>
        <h1 className="text-xl font-bold text-gray-900">{title}</h1>
      </div>
      <article
        className="legal-prose"
        dangerouslySetInnerHTML={{ __html: body }}
      />
    </div>
  );
}
