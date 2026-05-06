'use client';

import { useState, useRef, useEffect } from 'react';
import { Calendar, ChevronDown, X } from 'lucide-react';

interface Props {
  /** 行事曆事件標題（如：「保單到期 — 富邦 ABC-1234」） */
  title: string;
  /** 事件日期 YYYY-MM-DD */
  date: string;
  /** 詳細說明（保單號、車牌等） */
  description?: string;
  /** 預設提醒天數（在事件當天前 N 天彈通知；0 = 當天）。預設 [30, 14, 7, 1] */
  reminderDays?: number[];
  /** 按鈕大小 */
  size?: 'sm' | 'md';
  /** 唯一識別 — 給「取消加入」用同一個 UID，匯入 .ics CANCEL 時行事曆會找到原事件並移除 */
  uid?: string;
}

/** 把 YYYY-MM-DD 轉成 iCal 格式 YYYYMMDD（全天事件） */
function toICalDate(d: string): string {
  return d.replace(/-/g, '');
}

/** Google Calendar URL — 用「全天事件」格式（dates=YYYYMMDD/YYYYMMDD+1） */
function googleCalendarUrl(title: string, date: string, description: string): string {
  const start = toICalDate(date);
  const next = new Date(date + 'T00:00:00');
  next.setDate(next.getDate() + 1);
  const end = `${next.getFullYear()}${String(next.getMonth() + 1).padStart(2, '0')}${String(next.getDate()).padStart(2, '0')}`;
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: title,
    dates: `${start}/${end}`,
    details: description,
  });
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

/** 產生 .ics 檔（Apple Calendar / Outlook / Yahoo 都吃）。method = 'REQUEST' 加入；'CANCEL' 取消同 UID 事件 */
function buildIcsBlob(
  method: 'REQUEST' | 'CANCEL',
  title: string,
  date: string,
  description: string,
  reminderDays: number[],
  uid: string,
): Blob {
  const dtStart = toICalDate(date);
  const next = new Date(date + 'T00:00:00');
  next.setDate(next.getDate() + 1);
  const dtEnd = `${next.getFullYear()}${String(next.getMonth() + 1).padStart(2, '0')}${String(next.getDate()).padStart(2, '0')}`;
  const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
  const safeDesc = description.replace(/\\/g, '\\\\').replace(/\n/g, '\\n').replace(/,/g, '\\,');

  const lines: string[] = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//BOPINAN//Reminder//ZH',
    'CALSCALE:GREGORIAN',
    `METHOD:${method}`,
    'BEGIN:VEVENT',
    `UID:${uid}`,
    `DTSTAMP:${stamp}`,
    `DTSTART;VALUE=DATE:${dtStart}`,
    `DTEND;VALUE=DATE:${dtEnd}`,
    `SUMMARY:${method === 'CANCEL' ? '[已取消] ' : ''}${title}`,
    `DESCRIPTION:${safeDesc}`,
    `STATUS:${method === 'CANCEL' ? 'CANCELLED' : 'CONFIRMED'}`,
    `SEQUENCE:${method === 'CANCEL' ? '1' : '0'}`,
  ];
  if (method !== 'CANCEL') {
    reminderDays.forEach((d) => {
      lines.push('BEGIN:VALARM', 'ACTION:DISPLAY', `DESCRIPTION:${title} 倒數 ${d} 天`, `TRIGGER:-PT${d * 1440}M`, 'END:VALARM');
    });
  }
  lines.push('END:VEVENT', 'END:VCALENDAR');
  return new Blob([lines.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
}

export default function AddToCalendar({
  title,
  date,
  description = '',
  reminderDays = [30, 14, 7, 1],
  size = 'sm',
  uid,
}: Props) {
  const [openAdd, setOpenAdd] = useState(false);
  const [openCancel, setOpenCancel] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpenAdd(false); setOpenCancel(false);
      }
    };
    if (openAdd || openCancel) document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [openAdd, openCancel]);

  if (!date) return null;

  // 加入 / 取消用同一個 UID，這樣行事曆 app 看到 CANCEL 才能找到原事件移除
  const eventUid = uid || `bopinan-${title.replace(/\s+/g, '-')}-${date}@bopinan.ego-intl.com`;

  const downloadIcs = (method: 'REQUEST' | 'CANCEL', e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const blob = buildIcsBlob(method, title, date, description, reminderDays, eventUid);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${method === 'CANCEL' ? 'CANCEL_' : ''}${title}.ics`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setOpenAdd(false); setOpenCancel(false);
  };

  const btnPad = size === 'sm' ? 'px-2 py-1 text-[11px]' : 'px-3 py-1.5 text-xs';

  return (
    <div ref={ref} className="relative inline-flex gap-1" onClick={(e) => e.stopPropagation()}>
      <div className="relative">
        <button
          type="button"
          onClick={(e) => { e.preventDefault(); setOpenAdd(!openAdd); setOpenCancel(false); }}
          className={`inline-flex items-center gap-1 rounded-lg bg-primary-50 hover:bg-primary-100 ${btnPad} font-semibold text-primary-700 border border-primary-200`}
          title="加入行事曆"
        >
          <Calendar className="h-3 w-3" />
          加入行事曆
          <ChevronDown className="h-3 w-3" />
        </button>
        {openAdd && (
          <div className="absolute right-0 top-full mt-1 z-30 min-w-[200px] rounded-lg bg-white shadow-lg border border-gray-200 overflow-hidden">
            <a
              href={googleCalendarUrl(title, date, description)}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setOpenAdd(false)}
              className="block px-3 py-2 text-xs hover:bg-gray-50 border-b border-gray-100"
            >
              📅 Google 日曆
            </a>
            <button
              type="button"
              onClick={(e) => downloadIcs('REQUEST', e)}
              className="w-full text-left block px-3 py-2 text-xs hover:bg-gray-50"
            >
              🍎 Apple / Outlook（.ics）
            </button>
          </div>
        )}
      </div>

      <div className="relative">
        <button
          type="button"
          onClick={(e) => { e.preventDefault(); setOpenCancel(!openCancel); setOpenAdd(false); }}
          className={`inline-flex items-center gap-1 rounded-lg bg-red-50 hover:bg-red-100 ${btnPad} font-semibold text-red-700 border border-red-200`}
          title="取消加入行事曆"
        >
          <X className="h-3 w-3" />
          取消
        </button>
        {openCancel && (
          <div className="absolute right-0 top-full mt-1 z-30 min-w-[220px] rounded-lg bg-white shadow-lg border border-gray-200 overflow-hidden">
            <div className="px-3 py-2 text-[10px] text-amber-700 bg-amber-50 border-b border-amber-200 leading-snug">
              下載取消通知並匯入到行事曆 → 行事曆 app 會自動移除原事件
            </div>
            <button
              type="button"
              onClick={(e) => downloadIcs('CANCEL', e)}
              className="w-full text-left block px-3 py-2 text-xs hover:bg-gray-50 border-b border-gray-100"
            >
              🍎 下載取消通知（.ics）
            </button>
            <a
              href={googleCalendarUrl('[已取消] ' + title, date, '⚠️ 此事件已取消\n\n' + description)}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setOpenCancel(false)}
              className="block px-3 py-2 text-xs hover:bg-gray-50 text-gray-500"
            >
              📅 開啟 Google 日曆（請手動刪除）
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
