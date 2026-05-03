'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, KeyRound, ArrowRight, Loader2, Mail } from 'lucide-react';
import { useAuthStore } from '@/stores/auth-store';
import api from '@/lib/api-client';

export default function LoginPage() {
  const router = useRouter();
  const { sendOTP, verifyOTP } = useAuthStore();

  const [step, setStep] = useState<'input' | 'otp'>('input');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [countdown, setCountdown] = useState(0);

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
      setError('請輸入正確的 Email');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const result = await sendOTP(email);
      if (result.otp) setDevOtp(result.otp);
      setStep('otp');
      startCountdown(60);
    } catch {
      setError('傳送驗證碼失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (otp.length < 4) { setError('請輸入完整的驗證碼'); return; }
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
      setError('重新傳送失敗');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-primary-500 to-primary-700">
      {/* Top section */}
      <div className="flex flex-1 flex-col items-center justify-center px-6 pt-12 pb-8 text-white">
        <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-white/20 backdrop-blur-sm mb-6">
          <Shield className="h-10 w-10 text-white" />
        </div>
        <h1 className="text-2xl font-bold">車險智能服務平台</h1>
        <p className="mt-2 text-sm text-white/70">保單管理、理賠追蹤、緊急救援</p>
      </div>

      {/* Form card */}
      <div className="rounded-t-3xl bg-white px-6 pt-8 pb-10 shadow-2xl">
        <h2 className="text-lg font-bold text-gray-900 mb-1">
          {step === 'input' ? '登入' : '輸入驗證碼'}
        </h2>
        <p className="text-sm text-gray-500 mb-6">
          {step === 'input'
            ? '請輸入 Email 取得驗證碼'
            : `驗證碼已發送至 ${email}`}
        </p>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</div>
        )}

        {devOtp && step === 'otp' && (
          <div className="mb-4 rounded-lg bg-yellow-50 border border-yellow-200 p-3 text-sm text-yellow-700">
            <span className="font-medium">開發模式：</span>驗證碼為 <span className="font-bold">{devOtp}</span>
          </div>
        )}

        {step === 'input' ? (
          <div className="space-y-4">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="email" placeholder="your@email.com"
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
              取得驗證碼
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="relative">
              <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text" inputMode="numeric" placeholder="請輸入驗證碼" maxLength={6}
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
              驗證登入
            </button>
            <div className="flex items-center justify-between">
              <button
                onClick={() => { setStep('input'); setOtp(''); setError(''); setDevOtp(null); }}
                className="text-sm text-gray-500"
              >
                更換 Email
              </button>
              <button
                onClick={handleResend}
                disabled={countdown > 0 || loading}
                className="text-sm text-primary-500 disabled:text-gray-400"
              >
                {countdown > 0 ? `重新傳送 (${countdown}s)` : '重新傳送'}
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
            <div className="space-y-2.5">
              <button
                onClick={() => { window.location.href = '/api/v1/oauth/google/login'; }}
                className="flex w-full items-center justify-center gap-3 rounded-xl border border-gray-200 bg-white py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
                Google 登入
              </button>
              <button
                onClick={() => { window.location.href = '/api/v1/oauth/apple/login'; }}
                className="flex w-full items-center justify-center gap-3 rounded-xl border border-gray-200 bg-black py-3 text-sm font-medium text-white hover:bg-gray-900 transition"
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/></svg>
                Apple 登入
              </button>
              <button
                onClick={() => { window.location.href = '/api/v1/oauth/facebook/login'; }}
                className="flex w-full items-center justify-center gap-3 rounded-xl border border-gray-200 bg-[#1877F2] py-3 text-sm font-medium text-white hover:bg-[#166FE5] transition"
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
                Facebook 登入
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
