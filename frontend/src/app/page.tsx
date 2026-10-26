'use client';

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle, FileText, ClipboardList, MessageCircle, MapPin,
  Car, Calculator, Bell, Sparkles, User, Send,
} from 'lucide-react';
import Link from 'next/link';
import type { CSSProperties } from 'react';
import api from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import { useT } from '@/lib/i18n/LanguageProvider';
import { AppTile, TileSection } from '@/components/AppTile';
import { useAuthGuard } from '@/lib/useAuthGuard';

interface PinnedVehicle {
  id: string;
  urgency: string;
  vehicle: { plate: string; desc: string; car_age: number | null };
  zone_policy: {
    policies: string[];
    compulsory: { has: boolean; expiry: string | null; days: number; ok_for_inspect: boolean };
    voluntary: { has: boolean; expiry: string | null; days: number };
  };
  zone_inspection: {
    expiry: string | null;
    days_left: number | null;
    window_start: string | null;
    window_end: string | null;
  };
  zone_can_inspect: {
    in_window: boolean;
    can_inspect: boolean;
    window_status?: string;
    reasons?: string[];
  };
}

// 車輛方塊底色：紅＝已逾期/未投保/30 天內到期，橘＝60 天內，綠＝正常
function carColor(p: PinnedVehicle): string {
  const comp = p.zone_policy.compulsory;
  const insp = p.zone_inspection.days_left;
  if (!comp.has || comp.days <= 30 || (insp != null && insp < 0)) return '#d32f2f';
  if (comp.days <= 60 || (insp != null && insp <= 30)) return '#ef6c00';
  return '#2e7d32';
}

export default function DashboardPage() {
  // 用 localStorage 同步判定登入（initAuth 在 Providers 的 effect 裡，比本頁晚跑，直接看 isAuthenticated 會誤踢回登入頁）
  const { ready } = useAuthGuard();
  const { user, loadUser } = useAuthStore();
  const { t } = useT();

  useEffect(() => {
    if (ready && !user) loadUser();
  }, [ready, user, loadUser]);

  const { data: vehicleStatus } = useQuery({
    queryKey: ['vehicles-status'],
    queryFn: async () => {
      const res = await api.get('/api/v1/notifications/vehicles-status');
      return res.data.data as PinnedVehicle[];
    },
    enabled: ready,
  });

  const { data: unread } = useQuery({
    queryKey: ['notifications-unread'],
    queryFn: async () => {
      const res = await api.get('/api/v1/notifications');
      return (res.data.data?.unread_count ?? 0) as number;
    },
    enabled: ready,
  });

  if (!ready) return null;

  const pinned = vehicleStatus ?? [];

  const inspectStatus = (p: PinnedVehicle) => {
    if (p.zone_can_inspect.can_inspect) return t('tile.canInspect');
    const d = p.zone_inspection.days_left;
    if (d == null) return t('dash.inspectNoDate');
    const status = d < 0 ? t('dash.inspectOverdue', { days: Math.abs(d) })
      : d === 0 ? t('dash.inspectToday')
      : t('dash.inspectCountdown', { days: d });
    return t('tile.inspect', { status });
  };

  return (
    <div className="mx-auto max-w-lg px-4 py-5 space-y-4">
      <h1 className="text-xl font-bold text-gray-900">
        {user?.name ? t('dash.greetingNamed', { name: user.name }) : t('dash.greetingAnon')}
      </h1>

      <TileSection title={t('tile.section.service')}>
        <AppTile href="/emergency" icon={AlertTriangle} label={t('dash.quickAction.emergency')} color="#d32f2f" />
        <AppTile href="/chatbot" icon={MessageCircle} label={t('dash.quickAction.chatbot')} color="#3949ab" />
        <AppTile href="/notifications" icon={Bell} label={t('tile.notifications')} color="#f9a825" badge={unread} />
      </TileSection>

      <TileSection title={t('tile.section.policy')}>
        <AppTile href="/policies" icon={FileText} label={t('dash.quickAction.policies')} color="#1565c0" />
        <AppTile href="/claims" icon={ClipboardList} label={t('dash.quickAction.claims')} color="#ef6c00" />
        <AppTile href="/vehicles" icon={Car} label={t('tile.vehicles')} color="#455a64" />
        <AppTile href="/inspection" icon={MapPin} label={t('dash.quickAction.inspection')} color="#00897b" />
        <AppTile href="/quote-requests" icon={Send} label={t('tile.quoteRequests')} color="#00838f" />
        <AppTile href="/quote" icon={Calculator} label={t('tile.quote')} color="#6d4c41" />
      </TileSection>

      <TileSection title={t('tile.section.mine')}>
        <AppTile href="/profile" icon={User} label={t('tile.profile')} color="#5c6bc0" />
        <AppTile href="/numerology" icon={Sparkles} label={t('tile.numerology')} color="#8e24aa" />
      </TileSection>

      <section className="home-section">
        <h2 className="section-title">{t('tile.section.vehicles')}</h2>
        {pinned.length === 0 ? (
          <p className="home-empty">{t('dash.noVehicle')}</p>
        ) : (
          <div className="cargrid">
            {pinned.map((p) => (
              <Link
                key={p.id}
                href="/vehicles"
                className="cartile"
                style={{ '--c': carColor(p) } as CSSProperties}
                title={p.zone_can_inspect.reasons?.join('、') || p.zone_can_inspect.window_status || ''}
              >
                <span className="cartile-plate">{p.vehicle.plate}</span>
                <span className="cartile-sub">
                  {p.zone_policy.compulsory.has
                    ? t('tile.compulsory', { days: p.zone_policy.compulsory.days })
                    : t('tile.compulsoryNone')}
                </span>
                <span className="cartile-sub">{inspectStatus(p)}</span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
