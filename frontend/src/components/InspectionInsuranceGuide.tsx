'use client';

import { AlertTriangle, MessageCircle, Phone, ShieldCheck } from 'lucide-react';
import { daysUntil, inspectionWindow } from '@/lib/inspectionRules';

interface PolicyLite {
  id: string;
  status: string;
  compulsory_end_date?: string | null;
  end_date?: string;  // 任意險到期
  vehicle_id?: string | null;
  data_source?: string;
}

interface Props {
  vehicleId: string;
  vehiclePlate: string;
  registrationExpiry: string | null;
  policies: PolicyLite[];   // 此客戶名下所有保單（會自動 filter 此車輛 + active）
  hasAgentPolicy: boolean;  // eligibility.has_agent_policy
  lineOaUrl: string;
}

/**
 * 驗車 + 強制險 引導卡片：
 * - 驗車期間（到期前 30 天起）→ 開始檢查強制險
 * - 強制險距驗車到期日 < 30 天 → 必須先補強制險
 * - 完全沒強制險 → 同上
 *
 * UI 分流：
 * - has_agent_policy = true（已是業務員的客戶）→ 提示「請聯繫您的業務員處理」
 * - has_agent_policy = false（無業務員的自填客戶）→ 兩個 CTA：
 *     A) 撥打既有業務員（如果有）/ 自行聯繫
 *     B) 直接從 BOPINAN 投保（LINE OA）
 */
export default function InspectionInsuranceGuide({
  vehiclePlate,
  registrationExpiry,
  policies,
  hasAgentPolicy,
  lineOaUrl,
}: Props) {
  if (!registrationExpiry) return null;
  const daysToInspect = daysUntil(registrationExpiry);
  if (daysToInspect == null) return null;

  // 只在「驗車期間」前後關注：到期前 60 天 ~ 後 30 天（早提醒、好預備）
  if (daysToInspect > 60) return null;
  if (daysToInspect < -30) return null;

  const window = inspectionWindow(registrationExpiry);

  // 找出強制險最晚的到期日
  const compulsoryEnds = policies
    .filter((p) => p.compulsory_end_date)
    .map((p) => p.compulsory_end_date as string);
  const latestCompulsory = compulsoryEnds.length
    ? compulsoryEnds.sort().reverse()[0]
    : null;
  const compulsoryDays = latestCompulsory ? daysUntil(latestCompulsory) : null;

  // 驗車當下強制險必須剩 ≥ 30 天，否則無法通過驗車
  const needCompulsory =
    !latestCompulsory || (compulsoryDays != null && compulsoryDays < 30);

  if (!needCompulsory) {
    // 只在進入驗車期間前 14 天才提示「驗車快到了」
    if (daysToInspect > 14) return null;
    return (
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 mt-3">
        <div className="flex gap-2 items-start">
          <ShieldCheck className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
          <div className="text-xs text-blue-900 leading-relaxed">
            <b>{vehiclePlate} 驗車期間：</b>{window?.start} ~ {window?.end}
            <br />強制險到期日：{latestCompulsory}（剩 {compulsoryDays} 天，足夠驗車 ✓）
          </div>
        </div>
      </div>
    );
  }

  // 強制險不夠 → 顯示 CTA
  if (hasAgentPolicy) {
    // 已是業務員客戶 → 引導回業務員（不搶客）
    return (
      <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 mt-3">
        <div className="flex gap-2 items-start">
          <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="flex-1 text-xs text-amber-900 leading-relaxed">
            <b>需要補強制險才能驗車</b>
            <br />
            {vehiclePlate} 驗車期間：<b>{window?.start} ~ {window?.end}</b>
            <br />
            目前強制險{latestCompulsory ? `將於 ${latestCompulsory}（剩 ${compulsoryDays} 天）到期` : '尚未登錄'}，<br />驗車要求強制險剩餘 <b>≥ 30 天</b>。
            <div className="mt-2 rounded-md bg-white p-2 border border-amber-200">
              💡 您是 BOPINAN 已服務客戶 — 請<b>直接聯繫您專屬的業務員</b>協助續保 / 投保強制險。我們不搶您與業務員之間的關係。
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 自填客戶 → 兩個 CTA（聯繫熟識業務員 / 透過我們投保）
  return (
    <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 mt-3">
      <div className="flex gap-2 items-start mb-2">
        <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="flex-1 text-xs text-amber-900 leading-relaxed">
          <b>需要補強制險才能驗車</b>
          <br />
          {vehiclePlate} 驗車期間：<b>{window?.start} ~ {window?.end}</b>
          <br />
          {latestCompulsory
            ? <>強制險將於 <b>{latestCompulsory}</b> 到期（剩 {compulsoryDays} 天）</>
            : <>目前無強制險紀錄</>
          }，驗車要求強制險剩餘 <b>≥ 30 天</b>。
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
        <a
          href="tel:"
          onClick={(e) => { e.preventDefault(); alert('請撥打您原有業務員的電話辦理強制險續保。'); }}
          className="flex items-center justify-center gap-1.5 rounded-lg bg-white border border-amber-300 px-3 py-2.5 text-xs font-semibold text-amber-900 hover:bg-amber-100"
        >
          <Phone className="h-4 w-4" />
          1️⃣ 聯繫熟識業務員
        </a>
        <a
          href={lineOaUrl || '#'}
          target="_blank"
          rel="noopener noreferrer"
          className={`flex items-center justify-center gap-1.5 rounded-lg px-3 py-2.5 text-xs font-semibold ${lineOaUrl ? 'bg-green-500 text-white hover:bg-green-600' : 'bg-gray-200 text-gray-400 cursor-not-allowed'}`}
        >
          <MessageCircle className="h-4 w-4" />
          2️⃣ 從本平台投保（LINE）
        </a>
      </div>
    </div>
  );
}
