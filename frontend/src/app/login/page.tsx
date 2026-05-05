'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { KeyRound, ArrowRight, Loader2, Mail, Languages, AlertTriangle, Copy, Check, ShieldCheck } from 'lucide-react';
import Image from 'next/image';
import { useAuthStore } from '@/stores/auth-store';
import api from '@/lib/api-client';
import { useT } from '@/lib/i18n/LanguageProvider';

export default function LoginPage() {
  const router = useRouter();
  const { sendOTP, verifyOTP } = useAuthStore();
  const { t, lang, toggleLang } = useT();

  const [step, setStep] = useState<'input' | 'otp'>('input');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [inAppBrowser, setInAppBrowser] = useState<{ isInApp: boolean; appName: string }>({ isInApp: false, appName: '' });
  const [urlCopied, setUrlCopied] = useState(false);

  // 偵測 LINE/FB/IG 等內建瀏覽器（Google OAuth 拒絕在 embedded webview 登入）
  useEffect(() => {
    const ua = navigator.userAgent || '';
    let appName = '';
    if (/Line\//i.test(ua)) appName = 'LINE';
    else if (/FBAN|FBAV/i.test(ua)) appName = 'Facebook';
    else if (/Instagram/i.test(ua)) appName = 'Instagram';
    else if (/MicroMessenger/i.test(ua)) appName = '微信';
    else if (/Bytedance|TikTok/i.test(ua)) appName = 'TikTok';
    else if (/; wv\)/i.test(ua)) appName = 'App 內建瀏覽器';
    setInAppBrowser({ isInApp: !!appName, appName });
  }, []);

  const handleCopyUrl = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setUrlCopied(true);
      setTimeout(() => setUrlCopied(false), 2000);
    } catch {
      // ignore (older browsers)
    }
  };

  const startCountdown = (seconds: number) => {
    setCountdown(seconds);
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) { clearInterval(timer); return 0; }
        return prev - 1;
      });
    }, 1000);
  };

  const handleSendOTP = async () => {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError(t('login.invalidEmail'));
      return;
    }
    setError('');
    setLoading(true);
    setDevOtp(null);  // 清掉前次殘留
    try {
      const result = await sendOTP(email);
      // 只有 dev mode 且明確帶 otp 時才顯示；正式環境後端不回 otp
      if (result.otp && process.env.NODE_ENV !== 'production') {
        setDevOtp(result.otp);
      }
      setStep('otp');
      startCountdown(60);
    } catch {
      setError(t('login.sendFailed'));
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (otp.length < 4) { setError(t('login.codeIncomplete')); return; }
    setError('');
    setLoading(true);
    try {
      await verifyOTP(email, otp);
      // 檢查是否需要補資料引導
      try {
        const res = await api.get('/api/v1/customers/profile');
        const u = res.data.data;
        router.replace(u?.is_profile_complete ? '/' : '/onboarding');
      } catch {
        router.replace('/');
      }
    } catch {
      setError('驗證碼錯誤或已過期');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (countdown > 0) return;
    setError('');
    setLoading(true);
    try {
      const result = await sendOTP(email);
      if (result.otp) setDevOtp(result.otp);
      startCountdown(60);
    } catch {
      setError(t('login.resendFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen flex-col bg-gradient-to-b from-primary-500 to-primary-700">
      {/* Top-right controls: 管理員入口 + 語言切換 */}
      <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
        <button
          type="button"
          onClick={() => {
            const apiBase = process.env.NEXT_PUBLIC_API_URL || '';
            window.location.href = `${apiBase}/admin`;
          }}
          aria-label="管理員入口"
          title={lang === 'zh' ? '管理員後台' : 'Admin'}
          className="flex items-center gap-1 rounded-full bg-white/20 backdrop-blur-sm px-3 py-1.5 text-xs font-bold text-white hover:bg-white/30 transition cursor-pointer"
        >
          <ShieldCheck className="h-3.5 w-3.5" />
          {lang === 'zh' ? '管理員' : 'Admin'}
        </button>
        <button
          type="button"
          onClick={toggleLang}
          aria-label="Toggle language"
          className="flex items-center gap-1 rounded-full bg-white/20 backdrop-blur-sm px-3 py-1.5 text-xs font-bold text-white hover:bg-white/30 transition cursor-pointer"
        >
          <Languages className="h-3.5 w-3.5" />
          {lang === 'zh' ? 'EN' : '中'}
        </button>
      </div>

      {/* Top section */}
      <div className="flex flex-1 flex-col items-center justify-center px-6 pt-12 pb-8 text-white">
        <div className="flex h-24 w-24 items-center justify-center rounded-3xl bg-white/20 backdrop-blur-sm mb-6 overflow-hidden">
          <Image src="/logo.png" alt="BOPINAN" width={96} height={96} className="h-full w-full object-contain" priority />
        </div>
        <h1 className="text-2xl font-bold">{t('login.appTitle')}</h1>
        <p className="mt-2 text-sm text-white/70">{t('login.appSubtitle')}</p>
      </div>

      {/* Form card */}
      <div className="rounded-t-3xl bg-white px-6 pt-8 pb-10 shadow-2xl">
        <h2 className="text-lg font-bold text-gray-900 mb-1">
          {step === 'input' ? t('login.signIn') : t('login.enterCode')}
        </h2>
        <p className="text-sm text-gray-500 mb-6">
          {step === 'input'
            ? t('login.enterEmailHint')
            : t('login.codeSentTo', { email })}
        </p>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</div>
        )}

        {devOtp && step === 'otp' && (
          <div className="mb-4 rounded-lg bg-yellow-50 border border-yellow-200 p-3 text-sm text-yellow-700">
            <span className="font-medium">{t('login.devOtp')}</span> <span className="font-bold">{devOtp}</span>
          </div>
        )}

        {step === 'input' ? (
          <div className="space-y-4">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="email" placeholder={t('login.emailPlaceholder')}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendOTP()}
                className="w-full rounded-xl border border-gray-200 bg-gray-50 py-3.5 pl-11 pr-4 text-base outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
              />
            </div>

            <button
              onClick={handleSendOTP}
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary-500 py-3.5 text-base font-semibold text-white transition hover:bg-primary-700 disabled:opacity-50 cursor-pointer"
            >
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <ArrowRight className="h-5 w-5" />}
              {t('login.getCode')}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="relative">
              <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text" inputMode="numeric" placeholder={t('login.codePlaceholder')} maxLength={6}
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                className="w-full rounded-xl border border-gray-200 bg-gray-50 py-3.5 pl-11 pr-4 text-base tracking-[0.5em] text-center outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
                autoFocus
              />
            </div>
            <button
              onClick={handleVerifyOTP}
              disabled={loading || otp.length < 4}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary-500 py-3.5 text-base font-semibold text-white transition hover:bg-primary-700 disabled:opacity-50"
            >
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : null}
              {t('login.verifyLogin')}
            </button>
            <div className="flex items-center justify-between">
              <button
                onClick={() => { setStep('input'); setOtp(''); setError(''); setDevOtp(null); }}
                className="text-sm text-gray-500"
              >
                {t('login.changeEmail')}
              </button>
              <button
                onClick={handleResend}
                disabled={countdown > 0 || loading}
                className="text-sm text-primary-500 disabled:text-gray-400"
              >
                {countdown > 0 ? t('login.resendIn', { s: countdown }) : t('login.resend')}
              </button>
            </div>
          </div>
        )}

        {/* Social Login */}
        {step === 'input' && (
          <div className="mt-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex-1 border-t border-gray-200" />
              <span className="text-xs text-gray-400">或使用社交帳號登入</span>
              <div className="flex-1 border-t border-gray-200" />
            </div>

            {inAppBrowser.isInApp && (
              <div className="mb-4 rounded-lg bg-amber-50 border border-amber-200 p-3 text-sm text-amber-800">
                <div className="flex gap-2">
                  <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 space-y-2">
                    <p>
                      偵測到您正使用 <b>{inAppBrowser.appName}</b> 內建瀏覽器，
                      <b className="text-amber-900">Google 登入會被拒絕</b>。
                    </p>
                    <p>請改用 Safari 或 Chrome 開啟本頁面：</p>
                    <ol className="list-decimal list-inside text-xs space-y-0.5 pl-1">
                      <li>點右上角「<b>···</b>」或「<b>分享</b>」</li>
                      <li>選「<b>用其他瀏覽器開啟</b>」或「<b>在 Safari/Chrome 中開啟</b>」</li>
                    </ol>
                    <button
                      onClick={handleCopyUrl}
                      className="inline-flex items-center gap-1 mt-1 rounded bg-amber-100 hover:bg-amber-200 px-2 py-1 text-xs font-medium text-amber-900 transition"
                    >
                      {urlCopied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                      {urlCopied ? '已複製，去瀏覽器貼上' : '複製本頁網址'}
                    </button>
                    <p className="text-xs text-amber-700 pt-1">
                      或改用 <b>Email 驗證碼</b>/<b>LINE 登入</b>，這兩種在內建瀏覽器都可正常使用。
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-2.5">
              <button
                onClick={() => {
                  const apiBase = process.env.NEXT_PUBLIC_API_URL || '';
                  window.location.href = `${apiBase}/api/v1/oauth/google/login`;
                }}
                className="flex w-full items-center justify-center gap-3 rounded-xl border border-gray-200 bg-white py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
                Google 登入
              </button>
              <button
                onClick={() => {
                  const apiBase = process.env.NEXT_PUBLIC_API_URL || '';
                  window.location.href = `${apiBase}/api/v1/oauth/line/login`;
                }}
                className="flex w-full items-center justify-center gap-3 rounded-xl border border-transparent bg-[#06C755] py-3 text-sm font-medium text-white hover:bg-[#05B14C] transition"
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M19.365 9.863c.349 0 .63.285.631.631 0 .345-.281.63-.631.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.282.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg>
                LINE 登入
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
