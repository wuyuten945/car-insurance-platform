'use client';

import Link from 'next/link';
import type { LucideIcon } from 'lucide-react';
import { useEffect, useRef, type CSSProperties, type ReactNode } from 'react';

// 方塊式入口（樣式沿用校園管理系統的 iPhone APP 風格；CSS 在 globals.css 的 .apptile 區）

export function TileSection({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <section className="home-section">
      {title && <h2 className="section-title">{title}</h2>}
      <div className="appgrid">{children}</div>
    </section>
  );
}

type TileProps = {
  icon: LucideIcon;
  label: string;
  color: string;
  badge?: number;
  active?: boolean;
} & (
  | { href: string; onClick?: never }   // 站內連結；tel: / http 開頭走原生 <a>
  | { href?: never; onClick: () => void }
);

export function AppTile({ href, onClick, icon: Icon, label, color, badge, active }: TileProps) {
  const cls = `apptile${active ? ' is-active' : ''}`;
  const inner = (
    <>
      <span className="app-icon" style={{ '--c': color } as CSSProperties}>
        <Icon />
        {badge != null && badge > 0 && <span className="app-badge">{badge > 99 ? '99+' : badge}</span>}
      </span>
      <span className="app-label">{label}</span>
    </>
  );
  if (onClick) {
    return <button type="button" className={cls} onClick={onClick} aria-pressed={active}>{inner}</button>;
  }
  if (href && /^(tel:|https?:)/.test(href)) {
    return <a href={href} className={cls} {...(href.startsWith('http') ? { target: '_blank', rel: 'noopener noreferrer' } : {})}>{inner}</a>;
  }
  return <Link href={href!} className={cls}>{inner}</Link>;
}

// 方塊點開後的內容面板（淺底深字），放在方塊區下方
// 只在打開/切換面板時捲動到它（不能放在 ref callback：每次重繪都會被拉回來，打字時很煩）
// bare：內容自己已經是卡片（例如既有的設定區塊），就不再外包一層卡片與標題
export function TilePanel({ title, children, bare }: { title: string; children: ReactNode; bare?: boolean }) {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [title]);
  if (bare) return <section ref={ref} className="scroll-mt-32">{children}</section>;
  return (
    <section ref={ref} className="rounded-2xl bg-white p-4 shadow-sm border border-gray-200 text-gray-900 scroll-mt-32">
      <h2 className="text-base font-bold text-gray-900 mb-3">{title}</h2>
      {children}
    </section>
  );
}
