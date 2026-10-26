import Link from 'next/link';
import type { LucideIcon } from 'lucide-react';
import type { CSSProperties, ReactNode } from 'react';

// 方塊式入口（樣式沿用校園管理系統的 iPhone APP 風格；CSS 在 globals.css 的 .apptile 區）

export function TileSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="home-section">
      <h2 className="section-title">{title}</h2>
      <div className="appgrid">{children}</div>
    </section>
  );
}

export function AppTile({
  href, icon: Icon, label, color, badge,
}: {
  href: string;
  icon: LucideIcon;
  label: string;
  color: string;
  badge?: number;
}) {
  return (
    <Link href={href} className="apptile">
      <span className="app-icon" style={{ '--c': color } as CSSProperties}>
        <Icon />
        {badge != null && badge > 0 && <span className="app-badge">{badge > 99 ? '99+' : badge}</span>}
      </span>
      <span className="app-label">{label}</span>
    </Link>
  );
}
