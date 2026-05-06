'use client';

import { useState, useRef, useEffect } from 'react';
import { Calendar, ChevronDown } from 'lucide-react';

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

/** 產生 .ics 檔內容（Apple Calendar / Outlook / Yahoo 都吃） */
function buildIcsBlob(title: string, date: string, description: string, reminderDays: number[]): Blob {
  const dtStart = toICalDate(date);
  const next = new Date(date + 'T00:00:00');
  next.setDate(next.getDate() + 1);
  const dtEnd = `${next.getFullYear()}${String(next.getMonth() + 1).padStart(2, '0')}${String(next.getDate()).padStart(2, '0')}`;
  const uid = `bopinan-${Date.now()}@bopinan.ego-intl.com`;
  const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');

  // 多個 VALARM（每個提醒天數一個）— 提前 N*1440 分鐘 (= N 天)
  const alarms = reminderDays.map((d) => [
    'BEGIN:VALARM',
    'ACTION:DISPLAY',
    `DESCRIPTION:${title} 倒數 ${d} 天`,
    `TRIGGER:-PT${d * 1440}M`,
    'END:VALARM',
  ].join('\r\n')).join('\r\n');

  const ics = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//BOPINAN//Reminder//ZH',
    'CALSCALE:GREGORIAN',
    'BEGIN:VEVENT',
    `UID:${uid}`,
    `DTSTAMP:${stamp}`,
    `DTSTART;VALUE=DATE:${dtStart}`,
    `DTEND;VALUE=DATE:${dtEnd}`,
    `SUMMARY:${title}`,
    `DESCRIPTION:${description.replace(/\n/g, '\\n')}`,
    alarms,
    'END:VEVENT',
    'END:VCALENDAR',
  ].filter(Boolean).join('\r\n');

  return new Blob([ics], { type: 'text/calendar;charset=utf-8' });
}

export default function AddToCalendar({
  title,
  date,
  description = '',
  reminderDays = [30, 14, 7, 1],
  size = 'sm',
}: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    if (open) document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  if (!date) return null;

  const handleApple = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const blob = buildIcsBlob(title, date, description, reminderDays);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title}.ics`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setOpen(false);
  };

  const btnPad = size === 'sm' ? 'px-2 py-1 text-[11px]' : 'px-3 py-1.5 text-xs';

  return (
    <div ref={ref} className="relative inline-block" onClick={(e) => e.stopPropagation()}>
      <button
        type="button"
        onClick={(e) => { e.preventDefault(); setOpen(!open); }}
        className={`inline-flex items-center gap-1 rounded-lg bg-primary-50 hover:bg-primary-100 ${btnPad} font-semibold text-primary-700 border border-primary-200`}
        title="加入行事曆"
      >
        <Calendar className="h-3 w-3" />
        加入行事曆
        <ChevronDown className="h-3 w-3" />
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 z-30 min-w-[180px] rounded-lg bg-white shadow-lg border border-gray-200 overflow-hidden">
          <a
            href={googleCalendarUrl(title, date, description)}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => setOpen(false)}
            className="block px-3 py-2 text-xs hover:bg-gray-50 border-b border-gray-100"
          >
            📅 Google 日曆
          </a>
          <button
            type="button"
            onClick={handleApple}
            className="w-full text-left block px-3 py-2 text-xs hover:bg-gray-50"
          >
            🍎 Apple / Outlook（.ics）
          </button>
        </div>
      )}
    </div>
  );
}
