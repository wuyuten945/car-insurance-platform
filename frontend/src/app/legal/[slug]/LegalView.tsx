'use client';

import Link from 'next/link';
import { useT } from '@/lib/i18n/LanguageProvider';
import { LEGAL_DOCS, type LegalKey } from '@/components/legal/legal-content';

const VALID: LegalKey[] = ['personal-data', 'privacy', 'cookie', 'minor', 'disclaimer'];

export default function LegalView({ slug }: { slug: string }) {
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
    <div className="px-4 py-5 max-w-[552px] mx-auto">
      {/* 正式文件版面：雙線外框（深藍外框＋金色內線）＋品牌抬頭 */}
      <div className="legal-doc">
        <header className="legal-doc-head">
          <div className="legal-doc-brand">
            <img src="/logo.png" alt="" width={28} height={28} />
            <span>BOPINAN</span>
          </div>
          <h1>{title}</h1>
        </header>
        <article
          className="legal-prose"
          dangerouslySetInnerHTML={{ __html: body }}
        />
      </div>
    </div>
  );
}
