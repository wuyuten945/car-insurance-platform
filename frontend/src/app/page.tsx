'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle, FileText, ClipboardList, MessageCircle,
  ChevronRight, MapPin, Shield, Car, Calendar,
  CircleCheck, CircleX, Sparkles,
} from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import { useT } from '@/lib/i18n/LanguageProvider';

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
  };
}

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, user, loadUser } = useAuthStore();
  const { t } = useT();

  const QUICK_ACTIONS = [
    { href: '/emergency', icon: AlertTriangle, label: t('dash.quickAction.emergency'), color: 'bg-emergency-red', textColor: 'text-white' },
    { href: '/policies', icon: FileText, label: t('dash.quickAction.policies'), color: 'bg-primary-500', textColor: 'text-white' },
    { href: '/claims', icon: ClipboardList, label: t('dash.quickAction.claims'), color: 'bg-accent-500', textColor: 'text-white' },
    { href: '/chatbot', icon: MessageCircle, label: t('dash.quickAction.chatbot'), color: 'bg-primary-700', textColor: 'text-white' },
    { href: '/inspection', icon: MapPin, label: t('dash.quickAction.inspection'), color: 'bg-teal-500', textColor: 'text-white' },
  ];

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    if (!user) loadUser();
  }, [isAuthenticated, user, loadUser, router]);

  const { data: vehicleStatus } = useQuery({
    queryKey: ['vehicles-status'],
    queryFn: async () => {
      const res = await api.get('/api/v1/notifications/vehicles-status');
      return res.data.data as PinnedVehicle[];
    },
    enabled: isAuthenticated,
  });

  if (!isAuthenticated) return null;

  const pinned = vehicleStatus ?? [];

  return (
    <div className="px-4 py-5 space-y-6">
      {/* Greeting */}
      <div>
        <h1 className="text-xl font-bold text-gray-900">
          {user?.name ? t('dash.greetingNamed', { name: user.name }) : t('dash.greetingAnon')}
        </h1>
        <p className="text-sm text-gray-500 mt-1">{t('dash.welcome')}</p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-5 gap-3">
        {QUICK_ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <Link key={action.href} href={action.href} className="flex flex-col items-center gap-2">
              <div className={`flex h-14 w-14 items-center justify-center rounded-2xl ${action.color} ${action.textColor} shadow-sm`}>
                <Icon className="h-6 w-6" />
              </div>
              <span className="text-xs font-medium text-gray-700">{action.label}</span>
            </Link>
          );
        })}
      </div>

      {/* 數字易經 — 跨系統入口 */}
      <Link
        href="/numerology"
        className="block rounded-2xl bg-gradient-to-r from-purple-500 via-pink-500 to-orange-400 p-4 shadow-md hover:shadow-lg transition active:scale-[0.98]"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/25 backdrop-blur-sm">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <div className="flex-1 text-white">
            <p className="text-base font-bold">🃏 幫人生拿副好牌</p>
            <p className="text-xs opacity-90 mt-0.5">數字易經分析 · 用生日數字找出你的人生節奏</p>
          </div>
          <ChevronRight className="h-5 w-5 text-white opacity-80" />
        </div>
      </Link>

      {/* 保單 */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-bold text-gray-900 flex items-center gap-1.5">
            <Shield className="h-4 w-4 text-primary-500" /> {t('dash.section.policies')}
          </h2>
          <Link href="/policies" className="text-sm text-primary-500 flex items-center gap-0.5">
            {t('dash.viewAll')} <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
        {pinned.length === 0 ? (
          <div className="rounded-xl bg-white p-6 text-center shadow-sm border border-gray-100">
            <FileText className="h-10 w-10 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-400">{t('dash.noPolicy')}</p>
          </div>
        ) : (
          <div className="space-y-2">
            {pinned.map((p) => {
              const comp = p.zone_policy.compulsory;
              const vol = p.zone_policy.voluntary;
              const hasPolicy = p.zone_policy.policies.length > 0 && p.zone_policy.policies[0] !== '無有效保單';
              return (
                <div key={`pol_${p.id}`} className="rounded-xl bg-white p-3.5 shadow-sm border border-gray-100">
                  <div className="flex items-center gap-2 mb-2">
                    <Car className="h-4 w-4 text-primary-500" />
                    <span className="font-bold text-gray-900 text-sm">{p.vehicle.plate}</span>
                    <span className="text-xs text-gray-400">{p.vehicle.desc}</span>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {comp.has ? (
                      <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold ${
                        comp.days <= 30 ? 'bg-red-50 text-red-600' : comp.days <= 60 ? 'bg-orange-50 text-orange-600' : 'bg-green-50 text-green-600'
                      }`}>
                        {t('dash.compulsoryHas', { days: comp.days })}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-bold text-red-600">
                        {t('dash.compulsoryNone')}
                      </span>
                    )}
                    {vol.has ? (
                      <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold ${
                        vol.days <= 30 ? 'bg-red-50 text-red-600' : vol.days <= 60 ? 'bg-orange-50 text-orange-600' : 'bg-blue-50 text-blue-600'
                      }`}>
                        {t('dash.voluntaryHas', { days: vol.days })}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-bold text-gray-500">
                        {t('dash.voluntaryNone')}
                      </span>
                    )}
                  </div>
                  {hasPolicy && (
                    <div className="mt-2 space-y-0.5">
                      {p.zone_policy.policies.map((line, i) => (
                        <p key={i} className="text-[11px] text-gray-500 leading-relaxed truncate">{line}</p>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* 驗車 */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-bold text-gray-900 flex items-center gap-1.5">
            <Calendar className="h-4 w-4 text-orange-500" /> {t('dash.section.inspection')}
          </h2>
          <Link href="/inspection" className="text-sm text-primary-500 flex items-center gap-0.5">
            {t('dash.findStation')} <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
        {pinned.length === 0 ? (
          <div className="rounded-xl bg-white p-6 text-center shadow-sm border border-gray-100">
            <Car className="h-10 w-10 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-400">{t('dash.noVehicle')}</p>
          </div>
        ) : (
          <div className="space-y-2">
            {pinned.map((p) => {
              const insp = p.zone_inspection;
              const comp = p.zone_policy.compulsory;
              const canInsp = p.zone_can_inspect;
              return (
                <div key={`insp_${p.id}`} className="rounded-xl bg-white p-3.5 shadow-sm border border-gray-100">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Car className="h-4 w-4 text-orange-500" />
                      <span className="font-bold text-gray-900 text-sm">{p.vehicle.plate}</span>
                      {insp.days_left != null && (
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                          insp.days_left < 0 ? 'bg-red-100 text-red-700' :
                          insp.days_left <= 30 ? 'bg-orange-100 text-orange-700' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {insp.days_left < 0 ? t('dash.inspectOverdue', { days: Math.abs(insp.days_left) }) :
                           insp.days_left === 0 ? t('dash.inspectToday') :
                           t('dash.inspectCountdown', { days: insp.days_left })}
                        </span>
                      )}
                    </div>
                    {canInsp.can_inspect ? (
                      <CircleCheck className="h-4 w-4 text-green-500" />
                    ) : (
                      <CircleX className="h-4 w-4 text-red-400" />
                    )}
                  </div>
                  <div className="mt-2 flex items-center justify-between text-[11px]">
                    <span className="text-gray-500">
                      {insp.window_start && insp.window_end
                        ? t('dash.inspectWindow', { start: insp.window_start, end: insp.window_end })
                        : t('dash.inspectNoDate')}
                    </span>
                    <span className={`font-medium ${comp.has ? 'text-green-600' : 'text-red-500'}`}>
                      {t('dash.compulsoryShort', { status: comp.has ? t('dash.statusYes') : t('dash.statusNo') })}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

    </div>
  );
}
