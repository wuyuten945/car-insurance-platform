'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { User, LogOut, Loader2, Save, Car, Bell, MessageCircle, MapPin } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import { useT } from '@/lib/i18n/LanguageProvider';

type ProfileForm = {
  name: string;
  email: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
};

export default function ProfilePage() {
  const router = useRouter();
  const { user, loadUser, logout, isAuthenticated } = useAuthStore();
  const { t } = useT();

  const profileSchema = z.object({
    name: z.string().min(1, t('profile.errors.nameRequired')),
    email: z.string().email(t('profile.errors.invalidEmail')).or(z.literal('')),
    emergency_contact_name: z.string().optional(),
    emergency_contact_phone: z.string().optional(),
  });

  const MENU_ITEMS = [
    { href: '/vehicles', icon: Car, label: t('profile.menu.vehicles') },
    { href: '/notifications', icon: Bell, label: t('profile.menu.notifications') },
    { href: '/chatbot', icon: MessageCircle, label: t('profile.menu.chatbot') },
    { href: '/inspection', icon: MapPin, label: t('profile.menu.inspection') },
  ];

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    if (!user) loadUser();
  }, [isAuthenticated, user, loadUser, router]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: '',
      email: '',
      emergency_contact_name: '',
      emergency_contact_phone: '',
    },
  });

  useEffect(() => {
    if (user) {
      reset({
        name: user.name ?? '',
        email: user.email ?? '',
        emergency_contact_name: user.emergency_contact_name ?? '',
        emergency_contact_phone: user.emergency_contact_phone ?? '',
      });
    }
  }, [user, reset]);

  const mutation = useMutation({
    mutationFn: async (data: ProfileForm) => {
      await api.patch('/api/v1/customers/profile', data);
    },
    onSuccess: () => {
      loadUser();
    },
  });

  const handleLogout = async () => {
    await logout();
    router.replace('/login');
  };

  if (!isAuthenticated) return null;

  const inputClass = 'w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100';
  const labelClass = 'block text-sm font-medium text-gray-700 mb-1.5';

  return (
    <div className="px-4 py-5 space-y-6">
      {/* User Avatar + Name */}
      <div className="flex items-center gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary-100">
          <User className="h-8 w-8 text-primary-500" />
        </div>
        <div>
          <p className="text-lg font-bold text-gray-900">{user?.name ?? t('profile.notSetName')}</p>
          <p className="text-sm text-gray-500">{user?.phone}</p>
        </div>
      </div>

      {/* Quick Menu */}
      <div className="rounded-xl bg-white shadow-sm border border-gray-100 divide-y divide-gray-50">
        {MENU_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 px-4 py-3.5"
            >
              <Icon className="h-5 w-5 text-primary-500" />
              <span className="text-sm font-medium text-gray-700">{item.label}</span>
            </Link>
          );
        })}
      </div>

      {/* LINE binding section */}
      <LineBindingSection />

      {/* Profile Edit Form */}
      <section className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
        <h2 className="text-base font-bold text-gray-900 mb-4">{t('profile.section.title')}</h2>

        {mutation.isSuccess && (
          <div className="mb-4 rounded-lg bg-green-50 p-3 text-sm text-green-600">
            {t('profile.savedSuccess')}
          </div>
        )}

        {mutation.isError && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">
            {t('profile.saveFailed')}
          </div>
        )}

        <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
          <div>
            <label className={labelClass}>{t('profile.field.name')}</label>
            <input type="text" {...register('name')} className={inputClass} />
            {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name.message}</p>}
          </div>

          <div>
            <label className={labelClass}>{t('profile.field.email')}</label>
            <input type="email" placeholder="example@email.com" {...register('email')} className={inputClass} />
            {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
          </div>

          <div>
            <label className={labelClass}>{t('profile.field.emergencyName')}</label>
            <input type="text" {...register('emergency_contact_name')} className={inputClass} />
          </div>

          <div>
            <label className={labelClass}>{t('profile.field.emergencyPhone')}</label>
            <input type="tel" inputMode="numeric" {...register('emergency_contact_phone')} className={inputClass} />
          </div>

          <button
            type="submit"
            disabled={mutation.isPending || !isDirty}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary-500 py-3 text-sm font-semibold text-white transition hover:bg-primary-700 disabled:opacity-50"
          >
            {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            {t('profile.saveChanges')}
          </button>
        </form>
      </section>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="flex w-full items-center justify-center gap-2 rounded-xl border border-red-200 py-3 text-sm font-semibold text-red-500 hover:bg-red-50 transition"
      >
        <LogOut className="h-4 w-4" /> {t('profile.logout')}
      </button>
    </div>
  );
}

function LineBindingSection() {
  const { t } = useT();
  const [status, setStatus] = useState<{ bound: boolean; notify_enabled: boolean; official_id: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/v1/customers/line/status')
      .then(r => setStatus(r.data.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const toggleNotify = async (enabled: boolean) => {
    try {
      await api.patch(`/api/v1/customers/line/notify?enabled=${enabled}`);
      setStatus(prev => prev ? { ...prev, notify_enabled: enabled } : prev);
    } catch { /* ignore */ }
  };

  const unbind = async () => {
    if (!confirm(`${t('profile.line.unbind')}?`)) return;
    try {
      await api.delete('/api/v1/customers/line/unbind');
      setStatus(prev => prev ? { ...prev, bound: false } : prev);
    } catch { /* ignore */ }
  };

  const bind = () => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || '';
    window.location.href = `${apiBase}/api/v1/oauth/line/login`;
  };

  if (loading || !status) return null;

  return (
    <section className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
      <h2 className="text-base font-bold text-gray-900 mb-3 flex items-center gap-2">
        <span className="inline-flex items-center justify-center w-6 h-6 rounded-md bg-[#06C755] text-white text-xs font-bold">L</span>
        {t('profile.line.section')}
      </h2>
      <div className="flex items-center justify-between mb-3 text-sm">
        <span className="text-gray-700">{t('profile.line.bound')}：</span>
        <span className={status.bound ? 'text-green-600 font-semibold' : 'text-gray-400'}>
          {status.bound ? `✓ ${t('profile.line.bound')}` : t('profile.line.notBound')}
        </span>
      </div>

      {status.bound ? (
        <>
          <label className="flex items-center justify-between mb-3 text-sm">
            <span className="text-gray-700">{t('profile.line.notify')}：</span>
            <button
              onClick={() => toggleNotify(!status.notify_enabled)}
              className={`relative w-11 h-6 rounded-full transition ${status.notify_enabled ? 'bg-[#06C755]' : 'bg-gray-300'}`}
            >
              <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition ${status.notify_enabled ? 'left-5' : 'left-0.5'}`} />
            </button>
          </label>
          {status.official_id && (
            <p className="text-xs text-gray-500 mb-3">
              {t('profile.line.addFriend')} <strong className="text-gray-700">{status.official_id}</strong>
            </p>
          )}
          <button
            onClick={unbind}
            className="w-full text-sm font-semibold text-red-500 border border-red-200 rounded-lg py-2 hover:bg-red-50 transition"
          >
            {t('profile.line.unbind')}
          </button>
        </>
      ) : (
        <button
          onClick={bind}
          className="w-full bg-[#06C755] hover:bg-[#05B14C] text-white font-semibold rounded-lg py-2.5 text-sm transition"
        >
          {t('profile.line.bind')}
        </button>
      )}
    </section>
  );
}
