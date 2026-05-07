// 5 大法遵內容（繁體中文 + 英文）

export type LegalKey = 'personal-data' | 'privacy' | 'cookie' | 'minor' | 'disclaimer';

interface LegalDoc {
  title: { zh: string; en: string };
  body: { zh: string; en: string };
}

export const LEGAL_DOCS: Record<LegalKey, LegalDoc> = {
  'personal-data': {
    title: { zh: '個人資料蒐集告知', en: 'Personal Data Collection Notice' },
    body: {
      zh: `
<p>依據《個人資料保護法》第 8 條，本平台於使用者於註冊或使用服務時蒐集下列個人資料：</p>
<ul>
  <li><strong>身分驗證資料</strong>：Email、姓名、緊急聯絡人。</li>
  <li><strong>車輛資料</strong>：車牌號碼、行照、品牌型號。</li>
  <li><strong>保單資料</strong>：保單號碼、承保項目、保期。</li>
  <li><strong>理賠事故資料</strong>：事故時間地點、車損照片、事故描述。</li>
</ul>
<p><strong>蒐集目的</strong>：保單管理、理賠服務、驗車提醒、緊急救援等車險相關業務。</p>
<p><strong>利用期間</strong>：自您建立帳號至刪除帳號後 5 年（依法令保存期限）。</p>
<p><strong>利用對象</strong>：本平台與合作之保險公司、修車廠、救援拖吊業者（依您觸發之服務需求）。</p>
<p><strong>權利行使</strong>：您得隨時：</p>
<ul>
  <li>查詢、複本、更正您的個資</li>
  <li>停止蒐集、處理及利用</li>
  <li>請求刪除帳號與所有相關資料</li>
</ul>
<p><strong>不提供之影響</strong>：未提供必要資料將無法享有部分服務（如理賠申請）。</p>
`,
      en: `
<p>Pursuant to Article 8 of Taiwan's Personal Data Protection Act, this platform collects the following personal data when you register or use our services:</p>
<ul>
  <li><strong>Identity</strong>: Email, name, emergency contact.</li>
  <li><strong>Vehicle data</strong>: License plate, registration, brand and model.</li>
  <li><strong>Policy data</strong>: Policy number, coverage items, validity period.</li>
  <li><strong>Claims data</strong>: Incident time/place, damage photos, descriptions.</li>
</ul>
<p><strong>Purpose</strong>: Policy management, claims processing, inspection reminders, emergency assistance.</p>
<p><strong>Retention</strong>: From account creation through 5 years after account deletion (per legal retention requirements).</p>
<p><strong>Recipients</strong>: This platform and partner insurers, repair shops, towing companies (based on services you trigger).</p>
<p><strong>Your rights</strong>: You may at any time:</p>
<ul>
  <li>Request access, copy, or correction of your data</li>
  <li>Stop collection, processing, and use</li>
  <li>Request deletion of your account and all related data</li>
</ul>
<p><strong>Consequences of non-provision</strong>: Without required data, certain services (e.g., claims) cannot be provided.</p>
`,
    },
  },

  privacy: {
    title: { zh: '隱私權政策', en: 'Privacy Policy' },
    body: {
      zh: `
<h3>1. 適用範圍</h3>
<p>本政策適用於您使用本平台網站及服務時所提供的所有個人資料。</p>

<h3>2. 資訊蒐集</h3>
<p>我們在您註冊、登入、上傳行照、申請理賠時蒐集您主動提供的資料。系統不會在您不知情的情況下蒐集任何資料。</p>

<h3>3. 自動蒐集</h3>
<p>為維護服務運作，伺服器會記錄訪問時間、瀏覽器類型、設備類型與來源 IP（用於偵測異常登入）。</p>

<h3>4. 資料安全</h3>
<p>我們採取下列措施保護您的資料：</p>
<ul>
  <li>HTTPS 全站加密傳輸</li>
  <li>密碼使用單向雜湊存儲（無法還原）</li>
  <li>OTP 驗證碼僅暫存 5 分鐘</li>
  <li>定期備份與安全稽核</li>
</ul>

<h3>5. 資料分享</h3>
<p>我們<strong>不會出售</strong>您的個人資料。僅在下列情形分享：</p>
<ul>
  <li>您主動觸發合作服務（理賠、拖吊、修車）</li>
  <li>法令要求（如司法調查命令）</li>
  <li>取得您事前同意</li>
</ul>

<h3>6. 您的權利（個資法第 3 條）</h3>
<ol>
  <li>查詢與閱覽您的個資</li>
  <li>請求製給複本</li>
  <li>請求補充或更正</li>
  <li>請求停止蒐集、處理或利用</li>
  <li>請求刪除</li>
</ol>
<p>欲行使上述權利，請使用「個人資料」頁面操作或聯絡平台客服。</p>

<h3>7. Cookie</h3>
<p>詳見「Cookie 政策」。</p>

<h3>8. 政策變更</h3>
<p>本政策如有重大變更，將於您下次登入時主動告知並請求重新同意。</p>

<p class="legal-meta">最後更新：2026-05-04</p>
`,
      en: `
<h3>1. Scope</h3>
<p>This policy applies to all personal data you provide while using this platform.</p>

<h3>2. Information Collection</h3>
<p>We collect data you actively provide during registration, login, document upload, and claims submission. Nothing is collected without your knowledge.</p>

<h3>3. Automatic Collection</h3>
<p>To maintain service, servers log access time, browser type, device type, and source IP (for detecting abnormal logins).</p>

<h3>4. Data Security</h3>
<p>We protect your data with:</p>
<ul>
  <li>Site-wide HTTPS encryption</li>
  <li>One-way password hashing</li>
  <li>OTP codes valid for 5 minutes only</li>
  <li>Regular backups and security audits</li>
</ul>

<h3>5. Data Sharing</h3>
<p>We do <strong>not sell</strong> your personal data. Sharing only occurs when:</p>
<ul>
  <li>You actively trigger partner services (claims, towing, repair)</li>
  <li>Required by law (e.g., judicial orders)</li>
  <li>You give prior consent</li>
</ul>

<h3>6. Your Rights</h3>
<ol>
  <li>Access and review your data</li>
  <li>Request copies</li>
  <li>Request supplementation or correction</li>
  <li>Stop collection, processing, or use</li>
  <li>Request deletion</li>
</ol>

<h3>7. Cookies</h3>
<p>See the Cookie Policy.</p>

<h3>8. Policy Changes</h3>
<p>Significant changes will be communicated at your next login with a re-consent request.</p>

<p class="legal-meta">Last updated: 2026-05-04</p>
`,
    },
  },

  cookie: {
    title: { zh: 'Cookie 政策', en: 'Cookie Policy' },
    body: {
      zh: `
<h3>什麼是 Cookie</h3>
<p>Cookie 是儲存在您裝置上的小型文字檔，用於記住您的偏好設定、登入狀態等。</p>

<h3>本平台使用的 Cookie 類型</h3>
<table class="legal-table">
  <tr><th>類型</th><th>用途</th><th>保存期限</th></tr>
  <tr><td>必要 Cookie</td><td>維持登入狀態（access_token / refresh_token）</td><td>登入有效期間</td></tr>
  <tr><td>偏好 Cookie</td><td>記住您的語言選擇（中文/英文）、Cookie 同意狀態</td><td>1 年</td></tr>
  <tr><td>功能 Cookie</td><td>記住您上次查看過的車輛、保單篩選條件</td><td>30 天</td></tr>
</table>

<h3>本平台<strong>不</strong>使用</h3>
<ul>
  <li>追蹤分析 Cookie</li>
  <li>廣告 Cookie</li>
  <li>跨站追蹤 Cookie</li>
</ul>

<h3>如何拒絕 Cookie</h3>
<p>您可於瀏覽器設定中關閉 Cookie，但部分功能（如保持登入）將無法運作。</p>

<p class="legal-meta">最後更新：2026-05-04</p>
`,
      en: `
<h3>What are Cookies</h3>
<p>Cookies are small text files stored on your device to remember preferences, login state, etc.</p>

<h3>Cookies used on this platform</h3>
<table class="legal-table">
  <tr><th>Type</th><th>Purpose</th><th>Retention</th></tr>
  <tr><td>Essential</td><td>Maintain login state (access_token / refresh_token)</td><td>Session duration</td></tr>
  <tr><td>Preference</td><td>Remember language choice, cookie consent status</td><td>1 year</td></tr>
  <tr><td>Functional</td><td>Remember last viewed vehicles, policy filters</td><td>30 days</td></tr>
</table>

<h3>We do <strong>NOT</strong> use</h3>
<ul>
  <li>Tracking / analytics cookies</li>
  <li>Advertising cookies</li>
  <li>Cross-site tracking cookies</li>
</ul>

<h3>How to refuse</h3>
<p>You can disable cookies in browser settings, but some features (e.g., persistent login) will not work.</p>

<p class="legal-meta">Last updated: 2026-05-04</p>
`,
    },
  },

  minor: {
    title: { zh: '未成年保護政策', en: 'Minor Protection Policy' },
    body: {
      zh: `
<h3>適用對象</h3>
<p>本平台依《兒童及少年福利與權益保障法》制定本政策。</p>

<h3>使用年齡</h3>
<ul>
  <li>本平台主要服務對象為 <strong>18 歲以上</strong> 之車輛持有人。</li>
  <li>未滿 18 歲之未成年人，原則上不應自行申辦車險、駕駛車輛或使用本平台之保單管理功能。</li>
  <li>如為法定代理人代為操作，請依法授權並負監護責任。</li>
</ul>

<h3>家長 / 監護人責任</h3>
<p>未成年人之家長或法定代理人：</p>
<ul>
  <li>應對未成年人使用網路服務負監護責任。</li>
  <li>如發現未成年人未經同意註冊本平台，請通知客服協助刪除帳號。</li>
</ul>

<h3>資料保護加強措施</h3>
<p>對於識別為未成年人之帳號，本平台：</p>
<ul>
  <li>不主動發送行銷訊息</li>
  <li>限制其敏感資料之處理範圍</li>
  <li>提供更便捷之資料刪除流程</li>
</ul>

<p class="legal-meta">最後更新：2026-05-04</p>
`,
      en: `
<h3>Scope</h3>
<p>This policy is governed by Taiwan's Child and Youth Welfare Act.</p>

<h3>Age Requirements</h3>
<ul>
  <li>This platform primarily serves vehicle owners aged <strong>18 and above</strong>.</li>
  <li>Minors under 18 should not apply for car insurance, drive, or use platform features independently.</li>
  <li>Legal guardians acting on behalf of minors must be properly authorized.</li>
</ul>

<h3>Parent / Guardian Responsibility</h3>
<ul>
  <li>Parents/guardians are responsible for supervising minors' use of online services.</li>
  <li>If a minor has registered without consent, contact customer service for account deletion.</li>
</ul>

<h3>Enhanced Data Protection</h3>
<p>For accounts identified as minors:</p>
<ul>
  <li>No marketing messages sent</li>
  <li>Restricted processing of sensitive data</li>
  <li>Streamlined data deletion process</li>
</ul>

<p class="legal-meta">Last updated: 2026-05-04</p>
`,
    },
  },

  disclaimer: {
    title: { zh: '使用警語', en: 'Disclaimer' },
    body: {
      zh: `
<div class="legal-warning">
  <p><strong>⚠️ 重要聲明</strong></p>
  <p>本平台提供之資訊與功能僅為輔助工具，<strong>不取代專業諮詢、法律意見或保險業務員之建議</strong>。</p>
</div>

<h3>使用須知</h3>
<ol>
  <li><strong>保單到期提醒</strong>：本平台依您提供的資料推算到期日，<strong>實際到期日請以保險公司書面通知為準</strong>。</li>
  <li><strong>驗車日期計算</strong>：依監理單位公告規則計算，特殊情形（如過戶、變更）請以監理站官方答覆為準。</li>
  <li><strong>理賠申請</strong>：本平台僅協助蒐集與整理事故資料，<strong>實際理賠審核權在保險公司</strong>。</li>
  <li><strong>緊急救援</strong>：實際拖吊、救援服務由合作業者提供，本平台不對其服務品質負最終責任。</li>
  <li><strong>服務導引</strong>：系統回覆為固定格式之操作指引，僅協助找到對應功能位置；重要事項請聯絡保險公司客服或法務專員。</li>
</ol>

<h3>免責聲明</h3>
<p>使用者依本平台資訊所做之任何決策、行為或衍生後果，包括但不限於：</p>
<ul>
  <li>因依平台提醒誤判到期日造成之保障空窗</li>
  <li>因平台資訊錯誤導致之罰款或處分</li>
  <li>第三方合作業者之服務品質爭議</li>
</ul>
<p>本平台<strong>僅於故意或重大過失範圍內負責</strong>，並以您所支付之服務費（如有）為損害賠償上限。</p>

<h3>系統可用性</h3>
<p>本平台採盡力服務（best-effort）方式運作，<strong>不保證 24 小時不中斷</strong>。維護、升級或不可抗力因素可能造成短暫無法使用。</p>

<p class="legal-meta">最後更新：2026-05-04</p>
`,
      en: `
<div class="legal-warning">
  <p><strong>⚠️ Important Notice</strong></p>
  <p>Information and features provided by this platform are auxiliary tools and <strong>do not replace professional consulting, legal advice, or insurance agent recommendations</strong>.</p>
</div>

<h3>Usage Notes</h3>
<ol>
  <li><strong>Policy expiration reminders</strong>: Calculated from your provided data. <strong>Actual expiration is per the insurer's written notice</strong>.</li>
  <li><strong>Inspection date calculation</strong>: Based on transportation authority rules. For special cases (transfer, changes), refer to official station response.</li>
  <li><strong>Claims application</strong>: Platform assists in collecting incident data only. <strong>Actual claim approval rests with the insurer</strong>.</li>
  <li><strong>Emergency assistance</strong>: Towing/rescue is performed by partner providers. Platform is not ultimately responsible for their service quality.</li>
  <li><strong>Chatbot</strong>: Bot responses are for reference only. For important matters, contact insurer's customer service or legal staff.</li>
</ol>

<h3>Limitation of Liability</h3>
<p>For any decisions, actions, or consequences based on platform information, including but not limited to:</p>
<ul>
  <li>Coverage gaps from misjudging expiration dates</li>
  <li>Fines or penalties from platform information errors</li>
  <li>Service quality disputes with third-party partners</li>
</ul>
<p>The platform is responsible <strong>only within the scope of intentional or gross negligence</strong>, with damages capped at the service fee you paid (if any).</p>

<h3>System Availability</h3>
<p>Platform operates on a best-effort basis. <strong>24/7 uninterrupted availability is not guaranteed</strong>. Maintenance, upgrades, or force majeure may cause temporary unavailability.</p>

<p class="legal-meta">Last updated: 2026-05-04</p>
`,
    },
  },
};
