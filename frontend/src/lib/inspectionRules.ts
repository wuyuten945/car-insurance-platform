/**
 * 驗車到期日推算規則（與後台 admin.py 同步）
 * 給定車型 + 出廠年月 + 原發照日期 → 自動算出下一次驗車到期日
 */

type FreqFn = (ageInYears: number) => number;  // 回傳幾個月驗一次；0 = 免驗

const INSPECTION_FREQ_FN: Record<string, FreqFn> = {
  '自用小客車':           (a) => a < 5 ? 0 : a < 10 ? 12 : 6,
  '自用小貨車':           (a) => a < 5 ? 0 : a < 10 ? 12 : 6,
  '自用小客貨兩用車':     (a) => a < 5 ? 0 : a < 10 ? 12 : 6,
  '自用大客車':           (a) => a < 10 ? 12 : 6,
  '自用大貨車':           (a) => a < 10 ? 12 : 6,
  '自用特種車':           () => 12,
  '營業小客車（計程車）': (a) => a < 5 ? 12 : 6,
  '營業小貨車':           (a) => a < 5 ? 12 : 6,
  '營業大客車':           () => 4,
  '營業大貨車':           () => 6,
  '營業遊覽車':           () => 4,
  '營業特種車':           () => 12,
  '大型重型機車（550cc以上）': (a) => a < 5 ? 0 : 12,
  '普通重型機車（250cc以上）': (a) => a < 5 ? 0 : 12,
  '普通重型機車（50~250cc）':  (a) => a < 5 ? 0 : 12,
  '普通輕型機車':         (a) => a < 5 ? 0 : 12,
  '小型輕型機車（電動）': (a) => a < 5 ? 0 : 12,
  '拖車':                 () => 12,
  '曳引車':               () => 12,
  '電動汽車':             (a) => a < 5 ? 0 : a < 10 ? 12 : 6,
};

function addMonths(d: Date, months: number): Date {
  const nd = new Date(d.getTime());
  nd.setMonth(nd.getMonth() + months);
  return nd;
}

function fmtDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${dd}`;
}

/**
 * 推算下一個驗車到期日（YYYY-MM-DD）；推不出來回 null
 */
export function nextInspectionDue(
  vehicleType: string | null | undefined,
  year: number | null | undefined,
  month: number | null | undefined,
  regDateStr: string | null | undefined,
): string | null {
  if (!vehicleType || !year || !regDateStr) return null;
  const ruleFn = INSPECTION_FREQ_FN[vehicleType];
  if (!ruleFn) return null;

  const manuf = new Date(year, (month || 1) - 1, 1);
  const regD = new Date(regDateStr + 'T00:00:00');
  if (isNaN(manuf.getTime()) || isNaN(regD.getTime())) return null;
  const today = new Date(); today.setHours(0, 0, 0, 0);

  let cursor = new Date(regD.getTime());
  for (let i = 0; i < 600; i++) {
    const ageMs = cursor.getTime() - manuf.getTime();
    const ageYr = ageMs / (365.25 * 24 * 3600 * 1000);
    const freq = ruleFn(ageYr);
    if (freq === 0) {
      cursor = addMonths(cursor, 12);
      continue;
    }
    const nextDue = addMonths(cursor, freq);
    if (nextDue > today) return fmtDate(nextDue);
    cursor = nextDue;
  }
  return null;
}

/** 給定到期日，回傳「驗車期間」起迄（到期前 30 天 ~ 後 30 天） */
export function inspectionWindow(expiry: string | null | undefined): { start: string; end: string } | null {
  if (!expiry) return null;
  const d = new Date(expiry + 'T00:00:00');
  if (isNaN(d.getTime())) return null;
  const s = new Date(d.getTime()); s.setDate(s.getDate() - 30);
  const e = new Date(d.getTime()); e.setDate(e.getDate() + 30);
  return { start: fmtDate(s), end: fmtDate(e) };
}

/** 計算今天到 expiry 還剩幾天（負數 = 已逾期） */
export function daysUntil(expiry: string | null | undefined): number | null {
  if (!expiry) return null;
  const d = new Date(expiry + 'T00:00:00');
  if (isNaN(d.getTime())) return null;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return Math.round((d.getTime() - today.getTime()) / (24 * 3600 * 1000));
}
