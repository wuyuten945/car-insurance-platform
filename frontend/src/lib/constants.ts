// Design system constants matching SPEC
export const COLORS = {
  primary: {
    50: '#E3F2FD',
    100: '#BBDEFB',
    200: '#90CAF9',
    300: '#64B5F6',
    400: '#42A5F5',
    500: '#1565C0',  // Main primary
    600: '#1565C0',
    700: '#0D47A1',
    800: '#0A3A8A',
    900: '#072D6F',
  },
  accent: {
    500: '#FF6F00',  // Main accent/CTA
    600: '#E65100',
  },
  emergency: {
    red: '#D32F2F',
    bg: '#FFFFFF',
  },
};

// Claim stages
export const CLAIM_STAGES = [
  { key: 'submitted', label: '立案確認', icon: '📋' },
  { key: 'reviewing', label: '文件審核', icon: '📄' },
  { key: 'investigating', label: '現場勘查', icon: '🔍' },
  { key: 'negotiating', label: '責任認定', icon: '⚖️' },
  { key: 'approved', label: '理賠確認', icon: '✅' },
  { key: 'paying', label: '撥款作業', icon: '💰' },
  { key: 'closed', label: '案件結案', icon: '📁' },
];

export const ACCIDENT_TYPES = [
  { value: 'rear_end', label: '追撞' },
  { value: 'side', label: '側撞' },
  { value: 'head_on', label: '對撞' },
  { value: 'scrape', label: '刮撞' },
  { value: 'parking', label: '停車場事故' },
  { value: 'single', label: '單車事故' },
  { value: 'other', label: '其他' },
];

export const MY_SITUATIONS = [
  { value: 'straight', label: '直行中' },
  { value: 'turning_left', label: '左轉中' },
  { value: 'turning_right', label: '右轉中' },
  { value: 'reversing', label: '倒車中' },
  { value: 'parked', label: '靜止停車中' },
  { value: 'accelerating', label: '加速中' },
  { value: 'other', label: '其他' },
];
