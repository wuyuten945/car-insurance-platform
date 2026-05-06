'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  User, LogOut, Loader2, Save, Car, Bell, MessageCircle, MapPin,
  Mail, Phone, Calendar, IdCard, Home, FileText, Heart, Lock, ShieldCheck,
} from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import { useT } from '@/lib/i18n/LanguageProvider';
import { useAuthGuard } from '@/lib/useAuthGuard';

type ProfileForm = {
  name: string;
  email: string;
  phone: string;
  birth_date: string;          // yyyy-mm-dd
  id_number: string;           // 1 letter + 9 digits
  address: string;             // 居住地
  registered_address: string;  // 戶籍地
  license_number: string;
  license_expiry: string;      // yyyy-mm-dd
  emergency_contact_name: string;
  emergency_contact_phone: string;
  emergency_contact_relation: string;
};

// Schema 用的錯誤訊息會在元件內透過 t() 動態產出 — 這裡先用 zh 為預設
const makeProfileSchema = (t: (k: string) => string) => z.object({
  name: z.string().min(1, t('profile.errors.nameRequired')),
  email: z.string().email(t('profile.errors.invalidEmail')).or(z.literal('')),
  phone: z.string().regex(/^09\d{8}$/, t('profile.errors.invalidPhone')).or(z.literal('')),
  birth_date: z.string().or(z.literal('')),
  id_number: z.string().regex(/^[A-Z][0-9]{9}$/i, t('profile.errors.invalidIdNumber')).or(z.literal('')),
  address: z.string().or(z.literal('')),
  registered_address: z.string().or(z.literal('')),
  license_number: z.string().or(z.literal('')),
  license_expiry: z.string().or(z.literal('')),
  emergency_contact_name: z.string().or(z.literal('')),
  emergency_contact_phone: z.string().or(z.literal('')),
  emergency_contact_relation: z.string().or(z.literal('')),
});

export default function ProfilePage() {
  const { ready: __authReady } = useAuthGuard();
  const router = useRouter();
  const { user, loadUser, logout, isAuthenticated } = useAuthStore();
  const { t } = useT();

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

  const profileSchema = makeProfileSchema(t);
  const { register, handleSubmit, reset, formState: { errors, isDirty } } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: '', email: '', phone: '', birth_date: '', id_number: '',
      address: '', registered_address: '',
      license_number: '', license_expiry: '',
      emergency_contact_name: '', emergency_contact_phone: '', emergency_contact_relation: '',
    },
  });

  useEffect(() => {
    if (user) {
      reset({
        name: user.name ?? '',
        email: user.email ?? '',
        phone: user.phone ?? '',
        birth_date: user.birth_date ? user.birth_date.substring(0, 10) : '',
        id_number: '',  // 不回填（後端只存 hash）
        address: user.address ?? '',
        registered_address: user.registered_address ?? '',
        license_number: user.license_number ?? '',
        license_expiry: user.license_expiry ? user.license_expiry.substring(0, 10) : '',
        emergency_contact_name: user.emergency_contact_name ?? '',
        emergency_contact_phone: user.emergency_contact_phone ?? '',
        emergency_contact_relation: user.emergency_contact_relation ?? '',
      });
    }
  }, [user, reset]);

  const mutation = useMutation({
    mutationFn: async (data: ProfileForm) => {
      // 空字串 → 不送（避免覆蓋 hash 過的身分證或必填欄位驗證掛掉）
      const payload: Record<string, string | undefined> = {};
      Object.entries(data).forEach(([k, v]) => {
        const trimmed = (v ?? '').trim();
        if (trimmed) payload[k] = trimmed;
      });
      // 日期欄位轉 ISO（後端 schema 是 datetime）
      if (data.birth_date) payload.birth_date = new Date(data.birth_date).toISOString();
      if (data.license_expiry) payload.license_expiry = new Date(data.license_expiry).toISOString();
      // id_number 大寫
      if (payload.id_number) payload.id_number = payload.id_number.toUpperCase();

      await api.patch('/api/v1/customers/profile', payload);
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

  const inputClass = 'w-full rounded-xl border border-gray-200 bg-gray-50 py-3 pl-10 pr-4 text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100';
  const inputClassNoIcon = 'w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100';
  const labelClass = 'block text-sm font-medium text-gray-700 mb-1.5';
  const sectionTitle = 'text-sm font-bold text-gray-800 mb-3 mt-2 first:mt-0';

  if (!__authReady) return null;

  return (
    <div className="px-4 py-5 space-y-6">
      {/* User Avatar + Name */}
      <div className="flex items-center gap-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary-100">
          <User className="h-8 w-8 text-primary-500" />
        </div>
        <div>
          <p className="text-lg font-bold text-gray-900">{user?.name ?? t('profile.notSetName')}</p>
          <p className="text-sm text-gray-500">{user?.phone || user?.email}</p>
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

      {/* 進階保護密碼 */}
      <AdvancedPasswordSection />

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
            {(() => {
              const e = mutation.error as { response?: { data?: { message?: string; detail?: string } } };
              return e?.response?.data?.message || e?.response?.data?.detail || t('profile.saveFailed');
            })()}
          </div>
        )}

        <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-5">
          {/* —— 基本資料 —— */}
          <div>
            <h3 className={sectionTitle}>{t('profile.section.basic')}</h3>
            <div className="space-y-3">
              <div>
                <label className={labelClass}>{t('profile.field.name')} <span className="text-red-500">*</span></label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input type="text" {...register('name')} className={inputClass} placeholder={t('profile.field.namePlaceholder')} />
                </div>
                {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name.message}</p>}
              </div>

              <div>
                <label className={labelClass}>Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input type="email" {...register('email')} className={inputClass} placeholder="example@email.com" />
                </div>
                {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
              </div>

              <div>
                <label className={labelClass}>{t('profile.field.phone')}</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input type="tel" inputMode="numeric" {...register('phone')} className={inputClass} placeholder="0912345678" />
                </div>
                {errors.phone && <p className="text-xs text-red-500 mt-1">{errors.phone.message}</p>}
              </div>

              <div>
                <label className={labelClass}>{t('profile.field.birthDate')}</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input type="date" {...register('birth_date')} className={inputClass} />
                </div>
              </div>

              <div>
                <label className={labelClass}>
                  {t('profile.field.idNumber')}
                  {user?.has_id_number && (
                    <span className="ml-2 text-xs text-green-600 font-normal">{t('profile.field.idNumberFilled')}</span>
                  )}
                </label>
                <div className="relative">
                  <IdCard className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    maxLength={10}
                    {...register('id_number')}
                    className={inputClass}
                    placeholder={user?.has_id_number ? t('profile.field.idNumberPlaceholderSaved') : t('profile.field.idNumberPlaceholder')}
                    style={{ textTransform: 'uppercase' }}
                  />
                </div>
                {errors.id_number && <p className="text-xs text-red-500 mt-1">{errors.id_number.message}</p>}
                <p className="text-xs text-gray-400 mt-1">{t('profile.field.idNumberHint')}</p>
              </div>
            </div>
          </div>

          {/* —— 地址 —— */}
          <div>
            <h3 className={sectionTitle}>{t('profile.section.address')}</h3>
            <div className="space-y-3">
              <div>
                <label className={labelClass}>{t('profile.field.address')}</label>
                <div className="relative">
                  <Home className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input type="text" {...register('address')} className={inputClass} placeholder={t('profile.field.addressPlaceholder')} />
                </div>
              </div>
              <div>
                <label className={labelClass}>{t('profile.field.registeredAddress')}</label>
                <div className="relative">
                  <Home className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input type="text" {...register('registered_address')} className={inputClass} placeholder={t('profile.field.registeredAddressPlaceholder')} />
                </div>
              </div>
            </div>
          </div>

          {/* —— 駕照資訊 —— */}
          <div>
            <h3 className={sectionTitle}>{t('profile.section.license')}</h3>
            <div className="space-y-3">
              <div>
                <label className={labelClass}>{t('profile.field.licenseNumber')}</label>
                <div className="relative">
                  <FileText className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input type="text" {...register('license_number')} className={inputClass} />
                </div>
              </div>
              <div>
                <label className={labelClass}>{t('profile.field.licenseExpiry')}</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input type="date" {...register('license_expiry')} className={inputClass} />
                </div>
              </div>
            </div>
          </div>

          {/* —— 緊急聯絡人 —— */}
          <div>
            <h3 className={sectionTitle}>{t('profile.section.emergency')}</h3>
            <div className="space-y-3">
              <div>
                <label className={labelClass}>{t('profile.field.name')}</label>
                <div className="relative">
                  <Heart className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input type="text" {...register('emergency_contact_name')} className={inputClass} />
                </div>
              </div>
              <div>
                <label className={labelClass}>{t('profile.field.relation')}</label>
                <select {...register('emergency_contact_relation')} className={inputClassNoIcon}>
                  <option value="">{t('profile.relation.choose')}</option>
                  <option value="配偶">{t('profile.relation.spouse')}</option>
                  <option value="父母">{t('profile.relation.parent')}</option>
                  <option value="子女">{t('profile.relation.child')}</option>
                  <option value="兄弟姊妹">{t('profile.relation.sibling')}</option>
                  <option value="親戚">{t('profile.relation.relative')}</option>
                  <option value="朋友">{t('profile.relation.friend')}</option>
                  <option value="同事">{t('profile.relation.colleague')}</option>
                  <option value="其他">{t('profile.relation.other')}</option>
                </select>
              </div>
              <div>
                <label className={labelClass}>{t('profile.field.contactPhone')}</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input type="tel" inputMode="numeric" {...register('emergency_contact_phone')} className={inputClass} />
                </div>
              </div>
            </div>
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

function AdvancedPasswordSection() {
  const { t } = useT();
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [modal, setModal] = useState<'' | 'enable' | 'change'>('');
  const [cur, setCur] = useState('');
  const [nw, setNw] = useState('');
  const [cf, setCf] = useState('');
  const [err, setErr] = useState('');
  const [ok, setOk] = useState('');
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    try {
      const r = await api.get('/api/v1/auth/password/status');
      setEnabled(!!r.data.data?.enabled);
    } catch { /* ignore */ }
  };
  useEffect(() => { refresh(); }, []);

  const reset = () => { setCur(''); setNw(''); setCf(''); setErr(''); setOk(''); };

  const submit = async () => {
    setErr(''); setOk('');
    if (modal === 'change' && !cur) { setErr(t('pw.errRequired')); return; }
    if (!nw || !cf) { setErr(t('pw.errRequired')); return; }
    if (nw.length < 8) { setErr(t('pw.errShort')); return; }
    if (nw !== cf) { setErr(t('pw.errMismatch')); return; }
    if (modal === 'change' && nw === cur) { setErr(t('pw.errSame')); return; }
    setBusy(true);
    try {
      await api.post('/api/v1/auth/password/set', {
        new_password: nw,
        ...(modal === 'change' ? { current_password: cur } : {}),
      });
      setOk(modal === 'enable' ? t('pw.successEnabled') : t('pw.successChanged'));
      setEnabled(true);
      setTimeout(() => { setModal(''); reset(); }, 1500);
    } catch (e: unknown) {
      const er = e as { response?: { data?: { message?: string; detail?: string } } };
      setErr(er.response?.data?.message || er.response?.data?.detail || 'Error');
    } finally { setBusy(false); }
  };

  const removeProtection = async () => {
    if (!confirm(t('pw.confirmRemove'))) return;
    const pw = prompt(t('pw.fieldCurrent'));
    if (!pw) return;
    try {
      await api.post('/api/v1/auth/password/remove', { current_password: pw });
      alert(t('pw.successRemoved'));
      setEnabled(false);
    } catch (e: unknown) {
      const er = e as { response?: { data?: { message?: string; detail?: string } } };
      alert(er.response?.data?.message || er.response?.data?.detail || 'Error');
    }
  };

  if (enabled === null) return null;

  return (
    <section className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
      <h2 className="text-base font-bold text-gray-900 mb-1 flex items-center gap-2">
        <ShieldCheck className="h-4 w-4 text-primary-500" />
        {t('pw.section')}
      </h2>
      <p className="text-xs text-gray-500 mb-3">{t('pw.subtitle')}</p>
      <div className="flex items-center justify-between mb-3 text-sm">
        <span className={enabled ? 'text-green-600 font-semibold' : 'text-gray-400'}>
          {enabled ? t('pw.statusEnabled') : t('pw.statusDisabled')}
        </span>
      </div>
      {enabled ? (
        <p className="text-xs text-gray-500 mb-3">{t('pw.benefit')}</p>
      ) : (
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-2 mb-3">{t('pw.benefit')}</p>
      )}
      <div className="flex gap-2 flex-wrap">
        {enabled ? (
          <>
            <button
              onClick={() => { reset(); setModal('change'); }}
              className="flex-1 rounded-lg bg-primary-500 text-white py-2 text-sm font-semibold"
            >
              {t('pw.btnChange')}
            </button>
            <button
              onClick={removeProtection}
              className="rounded-lg border border-red-200 text-red-500 py-2 px-4 text-sm font-semibold"
            >
              {t('pw.btnRemove')}
            </button>
          </>
        ) : (
          <button
            onClick={() => { reset(); setModal('enable'); }}
            className="w-full rounded-lg bg-primary-500 text-white py-2.5 text-sm font-semibold flex items-center justify-center gap-2"
          >
            <Lock className="h-4 w-4" /> {t('pw.btnEnable')}
          </button>
        )}
      </div>

      {/* Modal */}
      {modal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center px-4" onClick={() => !busy && setModal('')}>
          <div className="bg-white rounded-xl p-5 max-w-sm w-full" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-base font-bold mb-3">
              {modal === 'enable' ? t('pw.modalEnable') : t('pw.modalChange')}
            </h3>
            {err && <div className="mb-3 rounded-lg bg-red-50 p-2 text-xs text-red-600">{err}</div>}
            {ok && <div className="mb-3 rounded-lg bg-green-50 p-2 text-xs text-green-600">{ok}</div>}
            {modal === 'change' && (
              <div className="mb-3">
                <label className="block text-xs text-gray-600 mb-1">{t('pw.fieldCurrent')}</label>
                <input type="password" value={cur} onChange={(e) => setCur(e.target.value)}
                  className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm" />
              </div>
            )}
            <div className="mb-3">
              <label className="block text-xs text-gray-600 mb-1">{t('pw.fieldNew')}</label>
              <input type="password" value={nw} onChange={(e) => setNw(e.target.value)}
                className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm" />
            </div>
            <div className="mb-4">
              <label className="block text-xs text-gray-600 mb-1">{t('pw.fieldConfirm')}</label>
              <input type="password" value={cf} onChange={(e) => setCf(e.target.value)}
                className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm" />
            </div>
            <div className="flex gap-2">
              <button onClick={() => setModal('')} disabled={busy}
                className="flex-1 rounded-lg border border-gray-200 py-2 text-sm font-semibold text-gray-600">
                {t('pw.btnCancel')}
              </button>
              <button onClick={submit} disabled={busy}
                className="flex-1 rounded-lg bg-primary-500 text-white py-2 text-sm font-semibold disabled:opacity-50">
                {busy ? <Loader2 className="h-4 w-4 animate-spin mx-auto" /> : t('pw.btnSubmit')}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function LineBindingSection() {
  const { t } = useT();
  const [status, setStatus] = useState<{ bound: boolean; notify_enabled: boolean; is_friend?: boolean; official_id: string } | null>(null);
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

      {status.bound && (
        <div className="flex items-center justify-between mb-3 text-sm">
          <span className="text-gray-700">{t('profile.line.friendStatus')}</span>
          <span className={status.is_friend ? 'text-green-600 font-semibold' : 'text-amber-600'}>
            {status.is_friend ? t('profile.line.isFriend') : t('profile.line.notFriend')}
          </span>
        </div>
      )}

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
          {status.official_id && !status.is_friend && (
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-2 mb-3">
              {t('profile.line.addFriendFull', { id: status.official_id })}
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
