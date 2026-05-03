// 翻譯字典：所有 UI 字串集中管理
// 使用：t('key') 或 t('key', { name: 'foo' }) 帶變數
// 變數語法：'Hello {name}' → t(key, {name: 'World'}) → 'Hello World'

export type Lang = 'zh' | 'en';

type Dict = Record<string, string>;

const zh: Dict = {
  // ===== Header / Layout =====
  'header.title': '車險智能平台',
  'header.notifications': '通知',
  'header.langToggle': 'EN',

  // ===== Bottom Nav =====
  'nav.home': '首頁',
  'nav.policies': '保單',
  'nav.claims': '理賠',
  'nav.profile': '我的',

  // ===== Login =====
  'login.appTitle': '車險智能服務平台',
  'login.appSubtitle': '保單管理、理賠追蹤、緊急救援',
  'login.signIn': '登入',
  'login.enterCode': '輸入驗證碼',
  'login.enterEmailHint': '請輸入 Email 取得驗證碼',
  'login.codeSentTo': '驗證碼已發送至 {email}',
  'login.emailPlaceholder': 'your@email.com',
  'login.codePlaceholder': '請輸入驗證碼',
  'login.getCode': '取得驗證碼',
  'login.verifyLogin': '驗證登入',
  'login.changeEmail': '更換 Email',
  'login.resend': '重新傳送',
  'login.resendIn': '重新傳送 ({s}s)',
  'login.invalidEmail': '請輸入正確的 Email',
  'login.codeIncomplete': '請輸入完整的驗證碼',
  'login.sendFailed': '傳送驗證碼失敗，請稍後再試',
  'login.resendFailed': '重新傳送失敗',
  'login.devOtp': '開發模式：驗證碼為',
  'login.orContinueWith': '或使用以下方式登入',

  // ===== Dashboard =====
  'dash.greetingNamed': '{name}，您好！',
  'dash.greetingAnon': '您好！',
  'dash.welcome': '歡迎使用車險智能服務平台',
  'dash.quickAction.emergency': '緊急救援',
  'dash.quickAction.policies': '我的保單',
  'dash.quickAction.claims': '理賠服務',
  'dash.quickAction.chatbot': '智能客服',
  'dash.quickAction.inspection': '驗車查詢',
  'dash.section.policies': '保單',
  'dash.section.inspection': '驗車',
  'dash.viewAll': '查看全部',
  'dash.findStation': '查詢驗車廠',
  'dash.noPolicy': '尚無保單資料',
  'dash.noVehicle': '尚無車輛資料',
  'dash.compulsoryHas': '強制險 ✓ 剩 {days} 天到期',
  'dash.compulsoryNone': '強制險 ✕ 未投保',
  'dash.voluntaryHas': '任意險 ✓ 剩 {days} 天到期',
  'dash.voluntaryNone': '任意險 ✕ 未投保',
  'dash.inspectOverdue': '逾期 {days} 天',
  'dash.inspectToday': '今日到期',
  'dash.inspectCountdown': '倒數 {days} 天',
  'dash.inspectWindow': '可檢驗 {start} ~ {end}',
  'dash.inspectNoDate': '未設定驗車日期',
  'dash.compulsoryShort': '強制險：{status}',
  'dash.statusYes': '有',
  'dash.statusNo': '無',

  // ===== Common =====
  'common.loading': '載入中…',
  'common.cancel': '取消',
  'common.confirm': '確認',
  'common.save': '儲存',
  'common.delete': '刪除',
  'common.edit': '編輯',
  'common.back': '返回',
  'common.error': '發生錯誤',
};

const en: Dict = {
  // ===== Header / Layout =====
  'header.title': 'Car Insurance Platform',
  'header.notifications': 'Notifications',
  'header.langToggle': '中',

  // ===== Bottom Nav =====
  'nav.home': 'Home',
  'nav.policies': 'Policies',
  'nav.claims': 'Claims',
  'nav.profile': 'Profile',

  // ===== Login =====
  'login.appTitle': 'Car Insurance Platform',
  'login.appSubtitle': 'Policies · Claims · Emergency',
  'login.signIn': 'Sign In',
  'login.enterCode': 'Enter Code',
  'login.enterEmailHint': 'Enter your email to receive a verification code',
  'login.codeSentTo': 'Code sent to {email}',
  'login.emailPlaceholder': 'your@email.com',
  'login.codePlaceholder': 'Enter verification code',
  'login.getCode': 'Send Code',
  'login.verifyLogin': 'Verify & Sign In',
  'login.changeEmail': 'Change Email',
  'login.resend': 'Resend',
  'login.resendIn': 'Resend ({s}s)',
  'login.invalidEmail': 'Please enter a valid email',
  'login.codeIncomplete': 'Please enter the complete code',
  'login.sendFailed': 'Failed to send code. Please try again.',
  'login.resendFailed': 'Resend failed',
  'login.devOtp': 'Dev mode — code:',
  'login.orContinueWith': 'Or continue with',

  // ===== Dashboard =====
  'dash.greetingNamed': 'Hello, {name}!',
  'dash.greetingAnon': 'Hello!',
  'dash.welcome': 'Welcome to the Car Insurance Platform',
  'dash.quickAction.emergency': 'Emergency',
  'dash.quickAction.policies': 'Policies',
  'dash.quickAction.claims': 'Claims',
  'dash.quickAction.chatbot': 'Chatbot',
  'dash.quickAction.inspection': 'Inspection',
  'dash.section.policies': 'Policies',
  'dash.section.inspection': 'Inspection',
  'dash.viewAll': 'View All',
  'dash.findStation': 'Find Station',
  'dash.noPolicy': 'No policies yet',
  'dash.noVehicle': 'No vehicles yet',
  'dash.compulsoryHas': 'Compulsory ✓ {days}d left',
  'dash.compulsoryNone': 'Compulsory ✕ None',
  'dash.voluntaryHas': 'Voluntary ✓ {days}d left',
  'dash.voluntaryNone': 'Voluntary ✕ None',
  'dash.inspectOverdue': 'Overdue {days}d',
  'dash.inspectToday': 'Due today',
  'dash.inspectCountdown': '{days}d left',
  'dash.inspectWindow': 'Window {start} ~ {end}',
  'dash.inspectNoDate': 'No date set',
  'dash.compulsoryShort': 'Compulsory: {status}',
  'dash.statusYes': 'Yes',
  'dash.statusNo': 'No',

  // ===== Common =====
  'common.loading': 'Loading…',
  'common.cancel': 'Cancel',
  'common.confirm': 'Confirm',
  'common.save': 'Save',
  'common.delete': 'Delete',
  'common.edit': 'Edit',
  'common.back': 'Back',
  'common.error': 'An error occurred',
};

export const dictionaries: Record<Lang, Dict> = { zh, en };
