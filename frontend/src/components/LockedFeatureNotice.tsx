'use client';

import { Lock, MessageCircle } from 'lucide-react';

interface Props {
  /** 標題（預設：此功能限投保客戶使用） */
  title?: string;
  /** 副標 / 說明 */
  description?: string;
  /** LINE OA 連結（從 useEligibility 拿） */
  lineOaUrl?: string;
  /** 是否做成 inline 卡片版（預設）；false = 整頁置中版（用於 /claims/new） */
  fullPage?: boolean;
}

export default function LockedFeatureNotice({
  title = '此功能限投保客戶使用',
  description = '您目前的車輛 / 保單為自行建檔，理賠 / 事故照片上傳等流程需要由業務員或平台為您建立正式保單後才能啟動。如想透過本平台正式投保，歡迎透過 LINE 與我們聯繫。',
  lineOaUrl = '',
  fullPage = false,
}: Props) {
  const wrapClass = fullPage
    ? 'mx-auto max-w-md mt-10 rounded-2xl border border-amber-200 bg-amber-50 p-6 shadow-sm'
    : 'rounded-xl border border-amber-200 bg-amber-50 p-4';

  return (
    <div className={wrapClass}>
      <div className="flex items-start gap-3">
        <div className="rounded-full bg-amber-100 p-2 shrink-0">
          <Lock className="h-5 w-5 text-amber-700" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-bold text-amber-900">{title}</h3>
          <p className="mt-1.5 text-sm leading-relaxed text-amber-800">
            {description}
          </p>
          {lineOaUrl && (
            <a
              href={lineOaUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-green-500 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-green-600 transition"
            >
              <MessageCircle className="h-4 w-4" />
              透過 LINE 與我們聯繫
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
