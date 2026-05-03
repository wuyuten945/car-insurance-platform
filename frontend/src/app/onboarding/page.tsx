'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, ArrowRight, Loader2, User, Calendar, IdCard, Phone, AlertCircle, CheckCircle2 } from 'lucide-react';
import api from '@/lib/api-client';

interface MatchResult {
  matched: boolean;
  masked_phone?: string;
  name_hint?: string | null;
  message?: string;
  reason?: string;
}

export default function OnboardingPage() {
  const router = useRouter();

  const [name, setName] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [idNumber, setIdNumber] = useState('');
  const [phone, setPhone] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [match, setMatch] = useState<MatchResult | null>(null);
  const [done, setDone] = useState(false);
  const [claiming, setClaiming] = useState(false);
  const [claimResult, setClaimResult] = useState<{ vehicles: number; policies: number } | null>(null);

  // 若已經完整 onboard，直接跳首頁
  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/api/v1/customers/profile');
        const u = res.data.data;
        if (u?.is_profile_complete) {
          router.replace('/');
        } else if (u) {
          // 預填既有資料
          if (u.name) setName(u.name);
          if (u.birth_date) setBirthDate(u.birth_date.substring(0, 10));
          if (u.phone) setPhone(u.phone);
        }
      } catch {
        router.replace('/login');
      }
    })();
  }, [router]);

  const handleSubmit = async () => {
    setError('');
    if (!name.trim()) { setError('請輸入姓名'); return; }
    if (!birthDate) { setError('請選擇出生日期'); return; }
    if (!/^[A-Z][0-9]{9}$/i.test(idNumber.trim())) {
      setError('身份證字號格式不正確（1 個英文字母 + 9 個數字）');
      return;
    }
    if (phone && !/^09\d{8}$/.test(phone.replace(/[\s-]/g, ''))) {
      setError('手機格式不正確（09 開頭，10 碼）');
      return;
    }

    setLoading(true);
    try {
      await api.patch('/api/v1/customers/profile', {
        name: name.trim(),
        birth_date: new Date(birthDate).toISOString(),
        id_number: idNumber.trim().toUpperCase(),
        ...(phone ? { phone: phone.replace(/[\s-]/g, '') } : {}),
      });

      // 查詢是否有業務員預先建立的同一身份證帳號
      const res = await api.get('/api/v1/customers/profile/match-existing');
      const m = res.data.data as MatchResult;
      setMatch(m);
      setDone(true);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { message?: string; detail?: string } } };
      setError(e.response?.data?.message || e.response?.data?.detail || '儲存失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  const goHome = () => router.replace('/');

  const handleClaim = async () => {
    setError('');
    setClaiming(true);
    try {
      const res = await api.post('/api/v1/customers/profile/claim-existing');
      const moved = res.data?.data?.moved as { vehicles?: number; policies?: number } | undefined;
      setClaimResult({ vehicles: moved?.vehicles || 0, policies: moved?.policies || 0 });
    } catch (err: unknown) {
      const e = err as { response?: { data?: { message?: string; detail?: string } } };
      setError(e.response?.data?.message || e.response?.data?.detail || '合併失敗，請聯繫客服');
    } finally {
      setClaiming(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-primary-500 to-primary-700">
      <div className="flex flex-1 flex-col items-center justify-center px-6 pt-12 pb-8 text-white">
        <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-white/20 backdrop-blur-sm mb-6">
          <Shield className="h-10 w-10 text-white" />
        </div>
        <h1 className="text-2xl font-bold">完成基本資料</h1>
        <p className="mt-2 text-sm text-white/70 text-center">為了服務您的車險權益，請補齊以下資料</p>
      </div>

      <div className="rounded-t-3xl bg-white px-6 pt-8 pb-10 shadow-2xl">
        {!done ? (
          <>
            <h2 className="text-lg font-bold text-gray-900 mb-1">基本資料</h2>
            <p className="text-sm text-gray-500 mb-6">這些資訊將用於保單作業與身份核對</p>

            {error && (
              <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">姓名 <span className="text-red-500">*</span></label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text" placeholder="王小明"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 py-3 pl-11 pr-4 text-base outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-gray-500 mb-1 block">出生年月日 <span className="text-red-500">*</span></label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="date"
                    value={birthDate}
                    onChange={(e) => setBirthDate(e.target.value)}
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 py-3 pl-11 pr-4 text-base outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-gray-500 mb-1 block">身份證字號 <span className="text-red-500">*</span></label>
                <div className="relative">
                  <IdCard className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text" placeholder="A123456789"
                    maxLength={10}
                    value={idNumber}
                    onChange={(e) => setIdNumber(e.target.value.toUpperCase())}
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 py-3 pl-11 pr-4 text-base outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1">系統會以雜湊方式加密儲存，不保留明文</p>
              </div>

              <div>
                <label className="text-xs text-gray-500 mb-1 block">手機號碼（選填）</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="tel" placeholder="0912-345-678"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full rounded-xl border border-gray-200 bg-gray-50 py-3 pl-11 pr-4 text-base outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
                  />
                </div>
              </div>

              <button
                onClick={handleSubmit}
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary-500 py-3.5 text-base font-semibold text-white transition hover:bg-primary-700 disabled:opacity-50 mt-4"
              >
                {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <ArrowRight className="h-5 w-5" />}
                送出
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 className="h-6 w-6 text-green-500" />
              <h2 className="text-lg font-bold text-gray-900">資料已儲存</h2>
            </div>

            {error && (
              <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-600 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {claimResult ? (
              <div className="mb-4 rounded-lg bg-green-50 border border-green-200 p-4 text-sm text-green-800">
                <p className="font-semibold mb-1">合併完成！</p>
                <p>已將車輛 {claimResult.vehicles} 筆、保單 {claimResult.policies} 筆連動到您的帳號。</p>
              </div>
            ) : match?.matched ? (
              <div className="mb-4 rounded-lg bg-amber-50 border border-amber-200 p-4">
                <p className="text-sm font-semibold text-amber-900 mb-2">系統發現可能屬於您的既有資料</p>
                <p className="text-xs text-amber-800 mb-3">
                  業務員已為您預先建立了車險紀錄：
                </p>
                <div className="bg-white rounded p-3 mb-3 text-sm">
                  {match.name_hint && <div className="text-gray-700">姓名：<span className="font-mono">{match.name_hint}</span></div>}
                  {match.masked_phone && <div className="text-gray-700">電話：<span className="font-mono">{match.masked_phone}</span></div>}
                </div>
                <p className="text-xs text-amber-800 mb-3">
                  比對身份證字號相符。可一鍵合併到您目前登入的帳號，之後就能在 App 中看到既有保單與車輛。
                </p>
                <button
                  onClick={handleClaim}
                  disabled={claiming}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-amber-500 py-3 text-sm font-semibold text-white transition hover:bg-amber-600 disabled:opacity-50"
                >
                  {claiming ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                  合併資料到我的帳號
                </button>
              </div>
            ) : (
              <div className="mb-4 rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-700">
                未找到既有預設資料。您可以開始使用平台功能，新增車輛與保單。
              </div>
            )}

            <button
              onClick={goHome}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary-500 py-3.5 text-base font-semibold text-white transition hover:bg-primary-700"
            >
              <ArrowRight className="h-5 w-5" />
              進入車險服務平台
            </button>
          </>
        )}
      </div>
    </div>
  );
}
