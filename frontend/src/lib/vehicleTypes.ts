/** 監理規定的車輛型式（與後台保持一致） */
export const VEHICLE_TYPE_GROUPS: Array<{ label: string; types: string[] }> = [
  {
    label: '自用車輛',
    types: [
      '自用小客車', '自用小貨車', '自用小客貨兩用車',
      '自用大客車', '自用大貨車', '自用特種車',
    ],
  },
  {
    label: '營業車輛',
    types: [
      '營業小客車（計程車）', '營業小貨車', '營業大客車',
      '營業大貨車', '營業遊覽車', '營業特種車',
    ],
  },
  {
    label: '機車',
    types: [
      '大型重型機車（550cc以上）', '普通重型機車（250cc以上）',
      '普通重型機車（50~250cc）', '普通輕型機車', '小型輕型機車（電動）',
    ],
  },
  {
    label: '其他',
    types: ['拖車', '曳引車', '電動汽車'],
  },
];

export const FUEL_TYPES = ['汽油', '柴油', '油電混合', '電動', 'LPG'] as const;

/** 西元 → 民國，回傳如「民國 115 年 (2026) 03 月 14 日」；空字串則回 '' */
export function rocLabel(value: string | null | undefined): string {
  if (!value) return '';
  const parts = String(value).split('-');
  if (parts.length < 2) return '';
  const y = parseInt(parts[0], 10);
  if (isNaN(y) || y < 1912) return '';
  const roc = y - 1911;
  const mm = (parts[1] || '').padStart(2, '0');
  let s = `民國 ${roc} 年 (${y}) ${mm} 月`;
  if (parts.length >= 3 && parts[2]) s += ` ${parts[2].padStart(2, '0')} 日`;
  return s;
}
