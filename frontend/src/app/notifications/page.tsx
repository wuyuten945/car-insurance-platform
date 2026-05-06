'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell, Loader2, CheckCheck, Car, Shield, Calendar, CircleCheck, CircleX, Clock, AlertTriangle } from 'lucide-react';
import api from '@/lib/api-client';
import { useAuthGuard } from '@/lib/useAuthGuard';
import { useIdleLogout } from '@/lib/useIdleLogout';

interface PinnedItem {
  id: string;
  title: string;
  body: string;
  urgency: string;
  days_left: number;
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
    source: string;
  };
  zone_can_inspect: {
    in_window: boolean;
    can_inspect: boolean;
    window_status: string;
    reasons: string[];
  };
}

interface Notification {
  id: string;
  title: string;
  body: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
}

export default function NotificationsPage() {
  const { ready: __authReady } = useAuthGuard();
  useIdleLogout();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => {
      const res = await api.get('/api/v1/notifications');
      return res.data.data as { pinned: PinnedItem[]; items: Notification[]; unread_count: number };
    },
  });

  const markRead = useMutation({
    mutationFn: async (id: string) => { await api.patch(`/api/v1/notifications/${id}/read`); },
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['notifications'] }); },
  });

  const pinned = data?.pinned ?? [];
  const notifications = data?.items ?? [];

  const formatTime = (dateStr: string) => {
    const d = new Date(dateStr);
    const ms = Date.now() - d.getTime();
    const m = Math.floor(ms / 60000);
    if (m < 1) return '剛剛';
    if (m < 60) return `${m} 分鐘前`;
    const h = Math.floor(ms / 3600000);
    if (h < 24) return `${h} 小時前`;
    const dd = Math.floor(ms / 86400000);
    if (dd < 7) return `${dd} 天前`;
    return d.toLocaleDateString('zh-TW');
  };

  if (!__authReady) return null;

  return (
    <div className="px-4 py-5">
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-xl font-bold text-gray-900">通知中心</h1>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
        </div>
      ) : (
        <div className="space-y-4">
          {/* Pinned: per-vehicle cards with 3 zones */}
          {pinned.map((p) => <VehicleCard key={p.id} data={p} />)}

          {/* Separator */}
          {pinned.length > 0 && notifications.length > 0 && (
            <div className="flex items-center gap-2 py-1">
              <div className="flex-1 border-t border-gray-200" />
              <span className="text-[10px] text-gray-400">一般通知</span>
              <div className="flex-1 border-t border-gray-200" />
            </div>
          )}

          {/* Regular notifications */}
          {notifications.map((n) => (
            <div
              key={n.id}
              onClick={() => { if (!n.is_read) markRead.mutate(n.id); }}
              className={`rounded-xl p-3.5 border cursor-pointer transition ${
                n.is_read ? 'bg-white border-gray-100' : 'bg-primary-50 border-primary-200'
              }`}
            >
              <div className="flex items-start gap-3">
                <span className="text-base mt-0.5">
                  {n.notification_type === 'renewal_reminder' ? '🔄' :
                   n.notification_type === 'inspection_reminder' ? '🚗' :
                   n.notification_type === 'system' ? '🔔' : '📄'}
                </span>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-semibold ${n.is_read ? 'text-gray-600' : 'text-gray-900'}`}>{n.title}</p>
                  <p className="text-xs text-gray-500 mt-1 line-clamp-2">{n.body}</p>
                  <p className="text-[10px] text-gray-400 mt-1">{formatTime(n.created_at)}</p>
                </div>
                {n.is_read && <CheckCheck className="h-3.5 w-3.5 text-gray-300 shrink-0 mt-1" />}
              </div>
            </div>
          ))}

          {pinned.length === 0 && notifications.length === 0 && (
            <div className="flex flex-col items-center py-20">
              <Bell className="h-16 w-16 text-gray-200 mb-3" />
              <p className="text-sm text-gray-400">暫無通知</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function VehicleCard({ data }: { data: PinnedItem }) {
  const p = data;
  const veh = p.vehicle;
  const pol = p.zone_policy;
  const insp = p.zone_inspection;
  const canInsp = p.zone_can_inspect;
  const comp = pol.compulsory;

  const isOverdue = p.urgency === 'overdue';
  const isUrgent = p.urgency === 'urgent';
  const headerBg = isOverdue ? 'bg-red-600' : isUrgent ? 'bg-orange-500' : 'bg-primary-500';
  const headerBadge = isOverdue ? '逾期' : isUrgent ? '緊急' : '正常';

  return (
    <div className="rounded-xl overflow-hidden border border-gray-200 shadow-sm">
      {/* Header: plate + car info */}
      <div className={`${headerBg} text-white px-4 py-2.5 flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <Car className="h-5 w-5" />
          <span className="font-bold text-base">{veh.plate}</span>
          <span className="text-xs text-white/70">{veh.desc}</span>
          {veh.car_age != null && <span className="text-xs text-white/70">車齡 {veh.car_age} 年</span>}
        </div>
        <span className="rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-bold">{headerBadge}</span>
      </div>

      {/* Zone 1: 保單有效期間 */}
      <div className="px-4 py-3 border-b border-gray-100">
        <div className="flex items-center gap-1.5 mb-2">
          <Shield className="h-4 w-4 text-primary-500" />
          <span className="text-xs font-bold text-primary-700">保單有效期間</span>
        </div>
        <div className="space-y-1.5">
          {pol.policies.map((line, i) => (
            <p key={i} className="text-xs text-gray-700 leading-relaxed">{line}</p>
          ))}
        </div>
        <div className="mt-2 flex gap-3">
          <div className={`flex-1 rounded-lg p-2 text-center text-xs ${comp.ok_for_inspect ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <p className="text-[10px] text-gray-500">強制險</p>
            <p className={`font-bold ${comp.ok_for_inspect ? 'text-green-700' : 'text-red-600'}`}>
              {comp.has ? `${comp.days} 天` : '未投保'}
            </p>
          </div>
          <div className={`flex-1 rounded-lg p-2 text-center text-xs ${pol.voluntary?.has ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50 border border-gray-200'}`}>
            <p className="text-[10px] text-gray-500">任意險</p>
            <p className={`font-bold ${pol.voluntary?.has ? 'text-blue-700' : 'text-gray-400'}`}>
              {pol.voluntary?.has ? `${pol.voluntary.days} 天` : '未投保'}
            </p>
          </div>
        </div>
      </div>

      {/* Zone 2: 驗車期間 */}
      <div className="px-4 py-3 border-b border-gray-100">
        <div className="flex items-center gap-1.5 mb-2">
          <Calendar className="h-4 w-4 text-orange-500" />
          <span className="text-xs font-bold text-orange-700">驗車到期</span>
        </div>
        {insp.expiry ? (
          <div>
            <div className="flex items-center justify-between">
              <p className="text-sm font-bold text-gray-900">{insp.expiry}</p>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${
                insp.days_left != null && insp.days_left < 0 ? 'bg-red-100 text-red-700' :
                insp.days_left != null && insp.days_left <= 30 ? 'bg-orange-100 text-orange-700' :
                'bg-gray-100 text-gray-600'
              }`}>
                {insp.days_left != null && insp.days_left < 0 ? `逾期 ${Math.abs(insp.days_left)} 天` :
                 insp.days_left === 0 ? '今日到期' :
                 `倒數 ${insp.days_left} 天`}
              </span>
            </div>
            <p className="text-[11px] text-gray-500 mt-1">
              可驗車區間：{insp.window_start} ~ {insp.window_end}
            </p>
            {insp.source && <p className="text-[10px] text-gray-400 mt-0.5">{insp.source}</p>}
          </div>
        ) : (
          <p className="text-xs text-gray-400">未設定驗車日期</p>
        )}
      </div>

      {/* Zone 3: 是否可驗車 */}
      <div className="px-4 py-3">
        <div className="flex items-center gap-1.5 mb-2">
          {canInsp.can_inspect ? (
            <CircleCheck className="h-4 w-4 text-green-600" />
          ) : (
            <CircleX className="h-4 w-4 text-red-500" />
          )}
          <span className={`text-xs font-bold ${canInsp.can_inspect ? 'text-green-700' : 'text-red-600'}`}>
            {canInsp.can_inspect ? '可辦理驗車' : '目前無法驗車'}
          </span>
        </div>
        <div className={`rounded-lg p-2.5 ${canInsp.can_inspect ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <p className={`text-xs font-medium ${canInsp.can_inspect ? 'text-green-700' : 'text-red-600'}`}>
            {canInsp.window_status}
          </p>
          {canInsp.reasons.length > 0 && (
            <ul className="mt-1.5 space-y-0.5">
              {canInsp.reasons.map((r, i) => (
                <li key={i} className="flex items-center gap-1 text-[11px] text-red-500">
                  <AlertTriangle className="h-3 w-3 shrink-0" />{r}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
