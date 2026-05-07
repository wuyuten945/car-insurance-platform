/**
 * 數字易經（Number I-Ching）核心演算法
 *
 * 八宅遊星表：兩位數 → 八星之一
 * 4 吉星：生氣、延年、天醫、伏位
 * 4 凶星：絕命、五鬼、六煞、禍害
 *
 * 數字 → 後天八卦：
 *  1=坎(水) 2=坤(地) 3=震(雷) 4=巽(風)
 *  6=乾(天) 7=兌(澤) 8=艮(山) 9=離(火)
 *  0/5 視為「空白」分隔（遇到時跳過）
 */

const DIGIT_GUA: Record<string, number> = {
  '1': 1, '2': 2, '3': 3, '4': 4,
  '6': 6, '7': 7, '8': 8, '9': 9,
};

export type EnergyName = '生氣' | '延年' | '天醫' | '伏位' | '絕命' | '五鬼' | '六煞' | '禍害';

// 八宅遊星表（兩卦關係）
const TABLE: Record<number, Record<number, EnergyName>> = {
  1: { 1: '伏位', 2: '絕命', 3: '天醫', 4: '生氣', 6: '六煞', 7: '禍害', 8: '五鬼', 9: '延年' },
  2: { 1: '絕命', 2: '伏位', 3: '禍害', 4: '五鬼', 6: '延年', 7: '天醫', 8: '生氣', 9: '六煞' },
  3: { 1: '天醫', 2: '禍害', 3: '伏位', 4: '延年', 6: '五鬼', 7: '絕命', 8: '六煞', 9: '生氣' },
  4: { 1: '生氣', 2: '五鬼', 3: '延年', 4: '伏位', 6: '禍害', 7: '六煞', 8: '絕命', 9: '天醫' },
  6: { 1: '六煞', 2: '延年', 3: '五鬼', 4: '禍害', 6: '伏位', 7: '生氣', 8: '天醫', 9: '絕命' },
  7: { 1: '禍害', 2: '天醫', 3: '絕命', 4: '六煞', 6: '生氣', 7: '伏位', 8: '延年', 9: '五鬼' },
  8: { 1: '五鬼', 2: '生氣', 3: '六煞', 4: '絕命', 6: '天醫', 7: '延年', 8: '伏位', 9: '禍害' },
  9: { 1: '延年', 2: '六煞', 3: '生氣', 4: '天醫', 6: '絕命', 7: '五鬼', 8: '禍害', 9: '伏位' },
};

export interface EnergyMeta {
  type: 'auspicious' | 'inauspicious' | 'neutral';
  emoji: string;
  short: string;
  desc: string;
  score: number;
  color: string;
}

export const ENERGY_INFO: Record<EnergyName, EnergyMeta> = {
  生氣: { type: 'auspicious',   emoji: '🌟', short: '大吉', desc: '貴人相助、活力旺盛、事業突破', score:  3, color: '#2E7D32' },
  延年: { type: 'auspicious',   emoji: '💚', short: '吉',   desc: '健康長壽、感情和諧、家業穩定', score:  2, color: '#388E3C' },
  天醫: { type: 'auspicious',   emoji: '💛', short: '吉',   desc: '財運興旺、化解病災、貴人提拔', score:  2, color: '#F9A825' },
  伏位: { type: 'neutral',      emoji: '⚪', short: '平',   desc: '守成穩定、無大起無大落',         score:  0, color: '#757575' },
  禍害: { type: 'inauspicious', emoji: '⚠️', short: '小凶', desc: '病痛煩惱、健康警訊、易損財',     score: -1.5, color: '#E65100' },
  六煞: { type: 'inauspicious', emoji: '🌀', short: '凶',   desc: '感情糾葛、官非訴訟、煩惱多',     score: -2, color: '#D84315' },
  五鬼: { type: 'inauspicious', emoji: '👻', short: '凶',   desc: '口舌是非、小人糾纏、莫名破財',   score: -2, color: '#C62828' },
  絕命: { type: 'inauspicious', emoji: '🔴', short: '大凶', desc: '損失重大、感情破裂、意外傷害',   score: -3, color: '#B71C1C' },
};

export const ALL_ENERGIES: EnergyName[] = ['生氣', '延年', '天醫', '伏位', '禍害', '六煞', '五鬼', '絕命'];

/** 移除非數字字元 */
export function digitsOnly(s: string): string {
  return (s || '').replace(/\D+/g, '');
}

export interface NumerologyAnalysis {
  digits: string;                        // 抽出後的純數字
  pairs: { a: string; b: string; energy: EnergyName }[];
  energyCounts: Partial<Record<EnergyName, number>>;
  auspiciousCount: number;               // 吉星總數
  inauspiciousCount: number;             // 凶星總數
  totalScore: number;                    // 加權分數
  rating: 'excellent' | 'good' | 'neutral' | 'bad';   // 整體評等
  ratingLabel: string;
  ratingColor: string;
}

/** 分析一組數字 */
export function analyzeNumber(input: string): NumerologyAnalysis {
  const digits = digitsOnly(input);
  const pairs: { a: string; b: string; energy: EnergyName }[] = [];
  for (let i = 0; i < digits.length - 1; i++) {
    const a = digits[i], b = digits[i + 1];
    const ag = DIGIT_GUA[a], bg = DIGIT_GUA[b];
    if (!ag || !bg) continue;  // 0 / 5 視為空白分隔
    pairs.push({ a, b, energy: TABLE[ag][bg] });
  }
  const energyCounts: Partial<Record<EnergyName, number>> = {};
  let totalScore = 0;
  let auspiciousCount = 0;
  let inauspiciousCount = 0;
  for (const p of pairs) {
    energyCounts[p.energy] = (energyCounts[p.energy] || 0) + 1;
    const meta = ENERGY_INFO[p.energy];
    totalScore += meta.score;
    if (meta.type === 'auspicious') auspiciousCount++;
    else if (meta.type === 'inauspicious') inauspiciousCount++;
  }

  let rating: 'excellent' | 'good' | 'neutral' | 'bad';
  let ratingLabel: string;
  let ratingColor: string;
  if (totalScore >= 5)      { rating = 'excellent'; ratingLabel = '★★★ 大吉'; ratingColor = '#2E7D32'; }
  else if (totalScore >= 1) { rating = 'good';      ratingLabel = '★★ 吉';     ratingColor = '#558B2F'; }
  else if (totalScore >= -2){ rating = 'neutral';   ratingLabel = '★ 平';      ratingColor = '#757575'; }
  else                      { rating = 'bad';       ratingLabel = '凶 — 建議更換'; ratingColor = '#C62828'; }

  return {
    digits, pairs, energyCounts,
    auspiciousCount, inauspiciousCount, totalScore,
    rating, ratingLabel, ratingColor,
  };
}

export interface RecommendOpts {
  length: number;                            // 號碼總長度（含 prefix）
  count: number;                             // 想要幾組推薦
  prefix?: string;                           // 開頭固定（手機 '09'、車牌字母...）
  minScore?: number;                         // 最低分數門檻（預設 2）
  preferredEnergies?: EnergyName[];          // 加分能量（出現越多分越高）
  forbiddenEnergies?: EnergyName[];          // 黑名單（出現就排除）
  alphaPositions?: { pos: number; chars: string }[]; // 指定位置用字母（車牌用）
}

/**
 * 推薦吉祥號碼。
 * - 隨機產生 → 過濾掉低於門檻的 → 排序 → 取前 N 組
 * - 同一個 number 不重複
 */
export function recommendNumbers(opts: RecommendOpts): {
  number: string;
  analysis: NumerologyAnalysis;
  bonus: number;
}[] {
  const out: { number: string; analysis: NumerologyAnalysis; bonus: number }[] = [];
  const seen = new Set<string>();
  const minScore = opts.minScore ?? 2;
  const maxAttempts = Math.max(50000, opts.count * 800);
  let attempts = 0;

  const alphaMap: Record<number, string> = {};
  if (opts.alphaPositions) {
    opts.alphaPositions.forEach((ap) => { alphaMap[ap.pos] = ap.chars; });
  }

  while (out.length < opts.count && attempts < maxAttempts) {
    attempts++;
    let num = opts.prefix || '';
    while (num.length < opts.length) {
      const pos = num.length;
      if (alphaMap[pos]) {
        const ch = alphaMap[pos];
        num += ch[Math.floor(Math.random() * ch.length)];
      } else {
        num += String(Math.floor(Math.random() * 10));
      }
    }
    if (seen.has(num)) continue;
    seen.add(num);
    const a = analyzeNumber(num);
    if (a.totalScore < minScore) continue;
    if (opts.forbiddenEnergies && opts.forbiddenEnergies.some((e) => a.energyCounts[e])) continue;

    let bonus = 0;
    if (opts.preferredEnergies) {
      for (const e of opts.preferredEnergies) {
        bonus += (a.energyCounts[e] || 0) * 1.5;
      }
    }
    out.push({ number: num, analysis: a, bonus });
  }

  out.sort((x, y) => (y.analysis.totalScore + y.bonus) - (x.analysis.totalScore + x.bonus));
  return out;
}

/** 從生日推算「主命卦」— 取生日數字加總取個位 */
export function birthMingGua(birthYmd: string): { gua: number | null; energy: EnergyName | null; meta: EnergyMeta | null } {
  const d = digitsOnly(birthYmd);
  if (!d) return { gua: null, energy: null, meta: null };
  let sum = 0;
  for (const ch of d) sum += parseInt(ch, 10);
  // 反覆取個位，直到 1-9
  while (sum > 9) {
    let s = 0;
    for (const ch of String(sum)) s += parseInt(ch, 10);
    sum = s;
  }
  if (sum === 0 || sum === 5) {
    return { gua: sum, energy: '伏位', meta: ENERGY_INFO['伏位'] };  // 5 / 0 = 中宮 → 視為平
  }
  // 「主命卦」對自己來說是 伏位（自身對自身）
  return { gua: sum, energy: '伏位', meta: ENERGY_INFO['伏位'] };
}
