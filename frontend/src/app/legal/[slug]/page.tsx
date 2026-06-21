import LegalView from './LegalView';

const VALID = ['personal-data', 'privacy', 'cookie', 'minor', 'disclaimer'] as const;

// static export：列舉所有合法 slug，build 時各產一頁
export function generateStaticParams() {
  return VALID.map((slug) => ({ slug }));
}

export const dynamicParams = false;

export default async function LegalPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <LegalView slug={slug} />;
}
