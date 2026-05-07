"""
後台管理頁面 — 行照上傳 / 保單輸入 / 資料檢視
不依賴外部 CDN，純內嵌 HTML。
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db

router = APIRouter()

ADMIN_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BOPINAN - 管理控制台</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Microsoft JhengHei', Arial, sans-serif; background: #f5f7fa; color: #333; }
.header { background: #1565C0; color: #fff; padding: 16px 24px; }
.header h1 { font-size: 20px; }
.header small { color: rgba(255,255,255,.7); }
.container { max-width: 960px; margin: 0 auto; padding: 20px; }
.card { background: #fff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.08); padding: 20px; margin-bottom: 20px; }
.card h2 { font-size: 16px; color: #1565C0; margin-bottom: 14px; border-bottom: 2px solid #E3F2FD; padding-bottom: 8px; }
.tabs { display: flex; gap: 4px; margin-bottom: 20px; }
.tab { padding: 10px 20px; background: #e0e0e0; border: none; border-radius: 8px 8px 0 0; cursor: pointer; font-size: 14px; font-weight: bold; }
.tab.active { background: #1565C0; color: #fff; }
.tab-content { display: none; }
.tab-content.active { display: block; }
label { display: block; font-size: 13px; color: #666; margin-bottom: 4px; margin-top: 12px; }
input, select, textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
input:focus, select:focus, textarea:focus { outline: none; border-color: #1565C0; box-shadow: 0 0 0 2px #E3F2FD; }
textarea { resize: vertical; min-height: 60px; }
.row { display: flex; gap: 12px; }
.row > div { flex: 1; }
.btn { display: inline-block; padding: 10px 24px; background: #1565C0; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: bold; cursor: pointer; margin-top: 16px; }
.btn:hover { background: #0D47A1; }
.btn.danger { background: #D32F2F; }
.btn.success { background: #2E7D32; }
.msg { padding: 10px; border-radius: 8px; margin-top: 12px; font-size: 13px; display: none; }
.msg.ok { display: block; background: #E8F5E9; color: #2E7D32; border: 1px solid #A5D6A7; }
.msg.err { display: block; background: #FFEBEE; color: #C62828; border: 1px solid #EF9A9A; }
table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 12px; }
th { background: #F5F5F5; text-align: left; padding: 8px; border-bottom: 2px solid #ddd; }
td { padding: 8px; border-bottom: 1px solid #eee; }
tr:hover { background: #FAFAFA; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; }
.badge.active { background: #E8F5E9; color: #2E7D32; }
.badge.expired { background: #FFEBEE; color: #C62828; }
.badge.expiring { background: #FFF3E0; color: #E65100; }
img.preview { max-width: 200px; max-height: 120px; border-radius: 8px; margin-top: 8px; border: 1px solid #ddd; }
.item-row { display: flex; gap: 8px; align-items: end; margin-top: 8px; padding: 8px; background: #FAFAFA; border-radius: 8px; }
.item-row input { flex: 1; }
.item-row .btn { margin-top: 0; padding: 8px 12px; font-size: 12px; }
#login-section { text-align: center; padding: 60px 20px; }
#login-section input { max-width: 300px; margin: 0 auto 12px; display: block; }
#login-section .btn { margin: 8px; }
.pw-wrap{position:relative}
.pw-wrap input{padding-right:36px}
.pw-toggle{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:#888;font-size:16px;padding:4px}
.pw-toggle:hover{color:#333}
@keyframes spin { to { transform: rotate(360deg); } }

/* ═════════ 手機 / 平板響應式（≤ 768px） ═════════ */
@media (max-width: 768px) {
  body { font-size: 14px; }

  /* Header */
  .header { padding: 10px 12px; display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
  .header h1 { font-size: 16px; flex: 1 1 100%; }
  .header > * { font-size: 12px; }
  .header button { font-size: 11px !important; padding: 5px 10px !important; margin-left: 0 !important; }

  /* Container */
  .container { padding: 10px; max-width: 100%; }

  /* Card */
  .card { padding: 14px; border-radius: 10px; margin-bottom: 12px; }
  .card h2 { font-size: 15px; padding-bottom: 6px; margin-bottom: 10px; }

  /* Tabs：橫向捲動 */
  .tabs { overflow-x: auto; flex-wrap: nowrap; -webkit-overflow-scrolling: touch; padding-bottom: 4px; gap: 4px; }
  .tab { padding: 8px 12px; font-size: 12px; white-space: nowrap; flex-shrink: 0; border-radius: 6px 6px 0 0; }

  /* Row stack（左右並排的表單欄改成上下） */
  .row { flex-direction: column; gap: 8px; }

  /* 按鈕 */
  .btn { padding: 9px 16px; font-size: 13px; margin-top: 10px; }

  /* 表格：橫向捲動避免擠壓 */
  table { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; white-space: nowrap; }
  th, td { padding: 6px 8px; font-size: 12px; }

  /* Modal 外層 padding 縮小、內層 card 改全寬 */
  #v-upload-modal, #v-edit-form, #create-customer-modal, #change-pw-modal,
  #p-upload-modal, #p-form-modal, #p-edit-modal, #csv-import-modal, #quote-respond-modal {
    padding: 10px !important;
  }
  #v-upload-modal > div, #v-edit-form > div, #create-customer-modal > div, #change-pw-modal > div,
  #p-upload-modal > div, #p-form-modal > div, #p-edit-modal > div, #csv-import-modal > div, #quote-respond-modal > div {
    padding: 16px 14px !important;
    width: 100% !important;
    max-width: 100% !important;
    border-radius: 12px !important;
  }
  #v-edit-form table, #v-upload-modal table { font-size: 12px; }
  #v-edit-form input, #v-edit-form select, #v-upload-modal input, #v-upload-modal select { font-size: 13px; }

  /* 操作客戶 bar 改直向堆疊 */
  #customer-bar { display: flex; flex-direction: column; align-items: stretch !important; gap: 6px; padding: 8px !important; }
  #customer-bar > * { margin-left: 0 !important; }
  #cur-customer { min-width: 0 !important; width: 100% !important; }

  /* 全域快速搜尋 */
  #quick-search-bar > div:first-child { flex-wrap: wrap; gap: 6px; }
  #quick-search-bar input { min-width: 0; flex: 1 1 100%; }

  /* Login 畫面 */
  #login-section { padding: 30px 14px; }
  #login-section input { max-width: 100%; }

  /* 圖片預覽縮小 */
  img.preview { max-width: 140px; max-height: 100px; }

  /* item-row（理賠/條款項目編輯）改直向 */
  .item-row { flex-direction: column; align-items: stretch; }
  .item-row .btn { margin-top: 6px; }

  /* 編輯表單按鈕列在小螢幕也能換行 */
  #v-edit-form button { margin-left: 0 !important; }
}

/* 非常小的手機（≤ 380px）：再壓縮一點 */
@media (max-width: 380px) {
  .header h1 { font-size: 15px; }
  .card h2 { font-size: 14px; }
  .tab { padding: 7px 10px; font-size: 11px; }
  .btn { padding: 8px 12px; font-size: 12px; }
  th, td { font-size: 11px; padding: 5px 6px; }
  .container { padding: 8px; }
}
</style>
</head>
<body>
<div class="header">
  <h1 data-i18n="header_title">BOPINAN — 管理控制台</h1>
  <small id="user-info"></small>
  <button type="button" onclick="openNumerologyModal()" title="幫自己和客戶拿副好牌"
     style="display:inline-block;background:linear-gradient(90deg,#9C27B0,#E91E63,#FF9800);color:#fff;border:0;border-radius:14px;padding:4px 12px;font-size:12px;font-weight:600;margin-left:10px;cursor:pointer">
    <span data-i18n="btn_iching">✨ 幫自己和客戶拿副好牌</span>
  </button>
  <button id="lang-toggle-btn" type="button" onclick="toggleAdminLang()" title="Toggle Language" style="background:rgba(255,255,255,0.2);color:#fff;border:0;border-radius:14px;padding:4px 12px;font-size:12px;font-weight:600;margin-left:10px;cursor:pointer">EN</button>
  <button id="change-pw-btn" type="button" onclick="openChangePwModal()" style="display:none;background:rgba(255,255,255,0.2);color:#fff;border:0;border-radius:14px;padding:4px 12px;font-size:12px;font-weight:600;margin-left:10px;cursor:pointer" data-i18n="btn_change_password">變更密碼</button>
  <button class="btn danger" id="logout-btn" style="display:none;padding:4px 12px;font-size:12px;margin-left:10px" onclick="doLogout()" data-i18n="btn_logout">登出</button>
  <div id="customer-bar" style="display:none;margin-top:10px;padding:10px;background:rgba(255,255,255,0.15);border-radius:6px;font-size:13px">
    <span style="margin-right:8px" data-i18n="cur_customer_label">操作客戶（新增車輛/保單時套用）：</span>
    <select id="cur-customer" style="background:#fff;color:#000;padding:4px 8px;border-radius:4px;border:0;min-width:280px"></select>
    <button class="btn success" style="padding:4px 12px;font-size:11px;margin-left:8px" onclick="openCreateCustomerModal()" data-i18n="btn_new_customer">+ 新增客戶</button>
    <button class="btn" style="padding:4px 10px;font-size:11px;margin-left:6px;background:#0288D1" onclick="loadCustomerList()" data-i18n="btn_refresh_customers">重新整理客戶清單</button>
    <span id="customer-bar-msg" style="margin-left:10px;color:#FFD54F;font-size:11px"></span>
  </div>
</div>

<!-- 選擇 / 新增客戶 Modal（整合兩種流程，避免紅色警告打斷）-->
<div id="create-customer-modal" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:9999;align-items:center;justify-content:center">
  <div style="background:#fff;padding:24px;border-radius:12px;max-width:460px;width:92%">
    <h3 id="cc-modal-title" style="color:#1565C0;margin-bottom:8px" data-i18n="cc_title">選擇 / 新增客戶</h3>
    <p style="font-size:12px;color:#888;margin-bottom:14px" data-i18n="cc_hint">先選一位現有客戶，或為轉介紹的新客戶建立稱呼（如「王大哥」「陳小姐」）。電話與 Email 之後再補。</p>

    <!-- A. 選現有客戶 -->
    <div style="background:#F5F7FA;border-radius:8px;padding:12px;margin-bottom:14px">
      <label style="display:block;font-size:12px;color:#1565C0;font-weight:bold;margin-bottom:6px" data-i18n="cc_pick_existing">A. 選擇現有客戶</label>
      <div style="display:flex;gap:6px;align-items:center">
        <select id="cc-pick" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:4px"></select>
        <button class="btn success" style="padding:6px 14px;font-size:12px;white-space:nowrap" onclick="doPickExistingCustomer()" data-i18n="cc_pick_btn">選此客戶</button>
      </div>
    </div>

    <!-- B. 新增客戶 -->
    <div style="background:#FFF8E1;border-radius:8px;padding:12px">
      <label style="display:block;font-size:12px;color:#E65100;font-weight:bold;margin-bottom:6px" data-i18n="cc_create_new_section">B. 或新增客戶</label>
      <div style="margin-bottom:8px">
        <label style="display:block;font-size:12px;color:#666;margin-bottom:4px" data-i18n="cc_name">客戶姓名 / 稱呼 <span style="color:#d32f2f">*</span></label>
        <input type="text" id="cc-name" placeholder="例：王大哥 / 陳小姐 / 林美玲" data-i18n-placeholder="ph_cc_name" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px">
      </div>
      <div style="margin-bottom:8px">
        <label style="display:block;font-size:12px;color:#666;margin-bottom:4px" data-i18n="cc_phone">電話（選填）</label>
        <input type="tel" id="cc-phone" placeholder="0912-345-678" data-i18n-placeholder="ph_cc_phone" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px">
      </div>
      <div style="margin-bottom:8px">
        <label style="display:block;font-size:12px;color:#666;margin-bottom:4px" data-i18n="cc_email">Email（選填）</label>
        <input type="email" id="cc-email" placeholder="customer@example.com" data-i18n-placeholder="ph_cc_email" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px" onkeydown="if(event.key==='Enter')doCreateCustomer()">
      </div>
      <div style="text-align:right">
        <button class="btn success" onclick="doCreateCustomer()" data-i18n="cc_submit">建立並選取</button>
      </div>
    </div>

    <div id="cc-msg" class="msg" style="margin-top:10px"></div>
    <div style="text-align:right;margin-top:6px">
      <button class="btn" style="background:#999;color:#fff" onclick="closeCreateCustomerModal()" data-i18n="btn_cancel">取消</button>
    </div>
  </div>
</div>

<!-- 變更密碼彈窗 -->
<div id="change-pw-modal" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:9999;align-items:center;justify-content:center">
  <div style="background:#fff;padding:24px;border-radius:12px;max-width:400px;width:90%">
    <h3 style="color:#1565C0;margin-bottom:14px" data-i18n="cp_title">變更密碼</h3>
    <p style="font-size:12px;color:#888;margin-bottom:14px" data-i18n="cp_hint">請先輸入當前密碼確認本人，再設定新密碼。</p>
    <div style="margin-bottom:10px">
      <label style="display:block;font-size:12px;color:#666;margin-bottom:4px" data-i18n="cp_current">當前密碼</label>
      <div class="pw-wrap"><input type="password" id="cp-current" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"><button type="button" class="pw-toggle" onclick="togglePw('cp-current',this)">👁</button></div>
    </div>
    <div style="margin-bottom:10px">
      <label style="display:block;font-size:12px;color:#666;margin-bottom:4px" data-i18n="cp_new">新密碼（至少 8 字元）</label>
      <div class="pw-wrap"><input type="password" id="cp-new" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"><button type="button" class="pw-toggle" onclick="togglePw('cp-new',this)">👁</button></div>
    </div>
    <div style="margin-bottom:14px">
      <label style="display:block;font-size:12px;color:#666;margin-bottom:4px" data-i18n="cp_confirm">確認新密碼</label>
      <div class="pw-wrap"><input type="password" id="cp-confirm" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px" onkeydown="if(event.key==='Enter')doChangePassword()"><button type="button" class="pw-toggle" onclick="togglePw('cp-confirm',this)">👁</button></div>
    </div>
    <div id="cp-msg" class="msg"></div>
    <div style="text-align:right">
      <button class="btn" style="background:#999;color:#fff" onclick="closeChangePwModal()" data-i18n="btn_cancel">取消</button>
      <button class="btn success" onclick="doChangePassword()" data-i18n="cp_submit">變更</button>
    </div>
  </div>
</div>

<!-- Login (Admin Account) -->
<div id="login-section" class="container">
  <div class="card">
    <h2 data-i18n="login_title">管理員登入</h2>
    <p style="color:#666;margin-bottom:16px" data-i18n="login_hint">使用管理員帳號密碼登入</p>
    <label data-i18n="lbl_username">帳號</label>
    <input type="text" id="login-user" placeholder="admin" data-i18n-placeholder="ph_username">
    <label data-i18n="lbl_password">密碼</label>
    <div class="pw-wrap">
      <input type="password" id="login-pass" placeholder="密碼" data-i18n-placeholder="ph_password" onkeydown="if(event.key==='Enter')doAdminLogin()">
      <button type="button" class="pw-toggle" onclick="togglePw('login-pass',this)">👁</button>
    </div>
    <button class="btn" onclick="doAdminLogin()" style="width:100%;margin-top:14px" data-i18n="btn_login">登入</button>
    <p style="font-size:11px;color:#999;margin-top:14px;text-align:center" data-i18n="forgot_pw_hint">忘記密碼？請聯繫管理員（super_admin）為您重設。本系統不支援自助式 Email 重設以保護帳號安全。</p>
    <div id="login-msg" class="msg"></div>
  </div>
</div>

<!-- Admin Panel (hidden until login) -->
<div id="admin-panel" class="container" style="display:none">

  <!-- ★ 全域快速搜尋 -->
  <div id="quick-search-bar" style="background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:12px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.04)">
    <div style="display:flex;gap:8px;align-items:center">
      <span style="font-size:18px">🔍</span>
      <input type="text" id="qs-input" placeholder="搜尋：客戶姓名 / 電話 / Email / 車牌 / 保單號 / 理賠號"
             data-i18n-placeholder="ph_search"
             style="flex:1;border:1px solid #ddd;border-radius:6px;padding:8px 12px;font-size:14px"
             onkeydown="if(event.key==='Enter')doQuickSearch()">
      <button onclick="doQuickSearch()" style="background:#1976d2;color:#fff;border:0;border-radius:6px;padding:8px 18px;font-weight:600;cursor:pointer" data-i18n="btn_search">搜尋</button>
      <button onclick="clearQuickSearch()" style="background:#f5f5f5;color:#666;border:1px solid #ddd;border-radius:6px;padding:8px 12px;cursor:pointer" data-i18n="btn_clear">清除</button>
    </div>
    <div id="qs-results" style="margin-top:10px"></div>
  </div>

  <!-- 整合 CSV 匯入 / 匯出 -->
  <div id="csv-bar" style="background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:12px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.04)">
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <span style="font-size:18px">📊</span>
      <span style="font-size:13px;font-weight:600;color:#1565C0" data-i18n="csv_title">資料匯入 / 匯出（客戶+車輛+保單一張表）</span>
      <button onclick="downloadUnifiedCsv()" style="background:#2E7D32;color:#fff;border:0;border-radius:6px;padding:6px 14px;font-size:12px;font-weight:600;cursor:pointer;margin-left:auto" data-i18n="btn_csv_export">⬇ 下載完整資料</button>
      <button onclick="downloadCsvTemplate()" style="background:#0288D1;color:#fff;border:0;border-radius:6px;padding:6px 14px;font-size:12px;font-weight:600;cursor:pointer" data-i18n="btn_csv_template">📥 下載空白範本</button>
      <input type="file" id="csv-import-file" accept=".csv,text/csv" style="display:none" onchange="onCsvFileChosen(this)">
      <button onclick="onCsvImportClick()" style="background:#E65100;color:#fff;border:0;border-radius:6px;padding:6px 14px;font-size:12px;font-weight:600;cursor:pointer" data-i18n="btn_csv_import">⬆ 上傳大量匯入</button>
    </div>
    <div id="csv-msg" class="msg" style="margin-top:8px"></div>
    <div id="csv-result" style="margin-top:8px;font-size:12px"></div>
  </div>

  <!-- 業務員待辦提醒中心 -->
  <div id="todo-bar" style="background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:12px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.04)">
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <span style="font-size:18px">🔔</span>
      <span style="font-size:13px;font-weight:600;color:#1565C0" data-i18n="todo_title">待辦提醒中心（保單 / 驗車到期）</span>
      <span id="todo-summary" style="font-size:11px;color:#666;margin-left:8px"></span>
      <button onclick="loadAgentTasks()" style="margin-left:auto;background:#0288D1;color:#fff;border:0;border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer" data-i18n="btn_todo_refresh">🔄 重新整理</button>
    </div>
    <div id="todo-tabs" style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;font-size:12px">
      <button class="todo-tab" data-bucket="overdue"  onclick="switchTodoBucket('overdue')"  style="padding:6px 12px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer">🚨 已逾期 <span class="todo-cnt"></span></button>
      <button class="todo-tab" data-bucket="today"    onclick="switchTodoBucket('today')"    style="padding:6px 12px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer">📍 當天 <span class="todo-cnt"></span></button>
      <button class="todo-tab" data-bucket="next_3d"  onclick="switchTodoBucket('next_3d')"  style="padding:6px 12px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer">⚡ 近 3 日 <span class="todo-cnt"></span></button>
      <button class="todo-tab" data-bucket="next_7d"  onclick="switchTodoBucket('next_7d')"  style="padding:6px 12px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer">📅 近 7 日 <span class="todo-cnt"></span></button>
      <button class="todo-tab" data-bucket="next_30d" onclick="switchTodoBucket('next_30d')" style="padding:6px 12px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer">📆 近 30 日 <span class="todo-cnt"></span></button>
    </div>
    <div id="todo-list" style="margin-top:10px"></div>
  </div>

  <!-- 上傳大量匯入 — 說明 modal -->
  <!-- 數字易經 modal 已搬至 admin-panel 外層（避免登出時 display:none 影響清空邏輯） -->

  <div id="csv-import-modal" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.55);z-index:9998;align-items:flex-start;justify-content:center;overflow-y:auto;padding:30px 12px">
    <div style="background:#fff;padding:22px 26px;border-radius:14px;max-width:600px;width:100%;position:relative;box-shadow:0 8px 32px rgba(0,0,0,.25)">
      <button type="button" onclick="closeCsvImportModal()" style="position:absolute;top:8px;right:12px;background:none;border:0;font-size:26px;cursor:pointer;color:#888;line-height:1">×</button>
      <h3 style="margin-top:0;margin-bottom:8px;color:#E65100" data-i18n="csv_import_title">⚠️ 上傳 CSV 大量匯入 — 上傳前必讀</h3>
      <ol style="margin:8px 0 12px 20px;padding:0;font-size:13px;line-height:1.8;color:#333">
        <li data-i18n="csv_step_1">必須使用本平台 CSV 範本格式（中文表頭）。如尚未下載，請點下方「📥 下載空白範本」按鈕。</li>
        <li data-i18n="csv_step_2">表頭欄位請保持不動；範本第 2 列為示範資料，填新資料時可整列刪除。</li>
        <li data-i18n="csv_step_3">
          配對規則（idempotent，可重複上傳同檔案不會重複建立）：
          <ul style="margin:4px 0 0 16px;padding:0;font-size:12px;color:#666">
            <li>客戶：依「客戶ID」→「客戶電話」→「客戶Email」依序配對；都查無 → 新建</li>
            <li>車輛：依「車牌號碼」於該客戶名下配對</li>
            <li>保單：依「任意險保單號碼」（全平台唯一）配對</li>
            <li>已存在欄位若提供新值會更新，空值不會覆蓋</li>
          </ul>
        </li>
        <li data-i18n="csv_step_4">建議第一次先選「試跑（dry-run）」確認解析無誤再正式匯入；任一列失敗整批會自動 rollback。</li>
        <li data-i18n="csv_step_5">業務員只能匯入自己負責的客戶；嘗試匯入到他人客戶會被拒絕並列為錯誤。</li>
      </ol>

      <div style="background:#FFF8E1;border-left:3px solid #FF9800;padding:10px 12px;border-radius:4px;margin-bottom:14px">
        <button type="button" onclick="downloadCsvTemplate()" style="background:#0288D1;color:#fff;border:0;border-radius:6px;padding:6px 14px;font-size:12px;font-weight:600;cursor:pointer" data-i18n="btn_csv_template">📥 下載空白範本</button>
        <span style="margin-left:8px;font-size:11px;color:#5D4037" data-i18n="csv_modal_dl_hint">點此下載最新格式範本</span>
      </div>

      <label style="display:flex;align-items:center;gap:8px;padding:10px;background:#F5F5F5;border-radius:6px;cursor:pointer;margin-bottom:12px">
        <input type="checkbox" id="csv-confirm-cb" style="width:16px;height:16px;cursor:pointer" onchange="onCsvConfirmToggle()">
        <span style="font-size:13px;font-weight:600;color:#333" data-i18n="csv_understood">我已了解上述說明，並確認使用本平台範本格式的 CSV 檔</span>
      </label>

      <div style="display:flex;gap:8px;justify-content:flex-end;border-top:1px solid #eee;padding-top:12px">
        <button type="button" onclick="closeCsvImportModal()" style="background:#999;color:#fff;border:0;border-radius:6px;padding:8px 16px;font-size:13px;cursor:pointer" data-i18n="btn_cancel">取消</button>
        <button type="button" id="csv-pick-file-btn" onclick="document.getElementById('csv-import-file').click()" disabled
                style="background:#E65100;color:#fff;border:0;border-radius:6px;padding:8px 16px;font-size:13px;font-weight:600;cursor:not-allowed;opacity:0.5" data-i18n="btn_csv_pick_file">⬆ 選擇 CSV 檔案上傳</button>
      </div>
    </div>
  </div>

  <div class="tabs">
    <button class="tab active" id="tab-btn-vehicles" onclick="switchTab('vehicles')" data-i18n="tab_vehicles">車輛 / 行照</button>
    <button class="tab" id="tab-btn-policies" onclick="switchTab('policies')" data-i18n="tab_policies">保單管理</button>
    <button class="tab" id="tab-btn-claims" onclick="switchTab('claims')" data-i18n="tab_claims">理賠申請</button>
    <button class="tab" id="tab-btn-accidents" onclick="switchTab('accidents')" data-i18n="tab_accidents">事故照片</button>
    <button class="tab" id="tab-btn-overview" onclick="switchTab('overview')" data-i18n="tab_overview">資料總覽</button>
    <button class="tab" id="tab-btn-quotes" onclick="switchTab('quotes')" data-i18n="tab_quotes">詢價工單</button>
    <button class="tab" id="tab-btn-agents" onclick="switchTab('agents')" style="display:none" data-i18n="tab_agents">業務員管理</button>
    <button class="tab" id="tab-btn-assign" onclick="switchTab('assign')" style="display:none" data-i18n="tab_assign">客戶分配</button>
    <button class="tab" id="tab-btn-logs" onclick="switchTab('logs')" style="display:none" data-i18n="tab_logs">操作日誌</button>
  </div>

  <!-- Tab: Vehicles -->
  <div id="tab-vehicles" class="tab-content active">

  <!-- ★★ 上傳行照 modal（按下「+新增車輛(上傳行照)」開啟） ★★ -->
  <div id="v-upload-modal" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.55);z-index:9997;align-items:flex-start;justify-content:center;overflow-y:auto;padding:30px 12px">
    <div style="background:#fff;padding:22px 26px;border-radius:14px;max-width:680px;width:100%;position:relative;box-shadow:0 8px 32px rgba(0,0,0,.25)">
      <button type="button" onclick="closeVehicleUploadModal()" style="position:absolute;top:8px;right:12px;background:none;border:0;font-size:26px;cursor:pointer;color:#888;line-height:1">×</button>
      <h2 style="margin-top:0;margin-bottom:6px" data-i18n="h_upload_reg">新增車輛（上傳行照 AI 辨識）</h2>
      <p style="color:#666;font-size:13px;margin-bottom:14px" data-i18n="upload_reg_hint">操作客戶：<b id="v-upload-modal-customer" style="color:#1565C0">—</b><br>選擇車輛型式並上傳行照後，系統會自動建立車輛並 AI 辨識內容。</p>

      <div class="row">
        <div>
          <label data-i18n="lbl_vehicle_type">車輛型式（監理分類）</label>
          <select id="v-type" onchange="onTypeChange()">
            <optgroup label="自用車輛" data-i18n-label="vt_group_private">
              <option value="自用小客車" data-i18n="vt_private_sedan">自用小客車</option>
              <option value="自用小貨車" data-i18n="vt_private_light_truck">自用小貨車</option>
              <option value="自用小客貨兩用車" data-i18n="vt_private_combo">自用小客貨兩用車</option>
              <option value="自用大客車" data-i18n="vt_private_bus">自用大客車</option>
              <option value="自用大貨車" data-i18n="vt_private_heavy_truck">自用大貨車</option>
              <option value="自用特種車" data-i18n="vt_private_special">自用特種車</option>
            </optgroup>
            <optgroup label="營業車輛" data-i18n-label="vt_group_commercial">
              <option value="營業小客車（計程車）" data-i18n="vt_taxi">營業小客車（計程車）</option>
              <option value="營業小貨車" data-i18n="vt_commercial_light_truck">營業小貨車</option>
              <option value="營業大客車" data-i18n="vt_commercial_bus">營業大客車</option>
              <option value="營業大貨車" data-i18n="vt_commercial_heavy_truck">營業大貨車</option>
              <option value="營業遊覽車" data-i18n="vt_tour_bus">營業遊覽車</option>
              <option value="營業特種車" data-i18n="vt_commercial_special">營業特種車</option>
            </optgroup>
            <optgroup label="機車" data-i18n-label="vt_group_moto">
              <option value="大型重型機車（550cc以上）" data-i18n="vt_moto_550">大型重型機車（550cc以上）</option>
              <option value="普通重型機車（250cc以上）" data-i18n="vt_moto_250">普通重型機車（250cc以上）</option>
              <option value="普通重型機車（50~250cc）" data-i18n="vt_moto_50_250">普通重型機車（50~250cc）</option>
              <option value="普通輕型機車" data-i18n="vt_moto_light">普通輕型機車</option>
              <option value="小型輕型機車（電動）" data-i18n="vt_moto_electric">小型輕型機車（電動）</option>
            </optgroup>
            <optgroup label="其他" data-i18n-label="vt_group_other">
              <option value="拖車" data-i18n="vt_trailer">拖車</option>
              <option value="曳引車" data-i18n="vt_tractor">曳引車</option>
              <option value="電動汽車" data-i18n="vt_ev">電動汽車</option>
            </optgroup>
          </select>
        </div>
        <!-- v-select 隱藏：原本「現有車輛 / 新車」造成誤會。新增車輛改用下方按鈕；
             更新既有車輛的行照請從「現有車輛」table 內每筆的「上傳/更換」按鈕。 -->
        <select id="v-select" onchange="onVSelectChange()" style="display:none">
          <option value="__new__">+ 新增車輛</option>
        </select>
      </div>

      <div id="v-inspection-rule" style="margin-top:10px;padding:10px;background:#E3F2FD;border-radius:8px;font-size:12px;color:#1565C0;display:none"></div>

      <label style="margin-top:14px" data-i18n="lbl_reg_image">行照圖片 (JPG/PNG)</label>
      <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
        <input type="file" id="v-file" accept="image/jpeg,image/png,image/webp,application/pdf,.pdf" onchange="onFileChange()" style="display:none">
        <button type="button" class="btn" style="padding:6px 16px;font-size:12px;background:#0288D1" onclick="document.getElementById('v-file').click()" data-i18n="btn_choose_file">選擇檔案</button>
        <span id="v-file-name" style="font-size:12px;color:#666" data-i18n="msg_no_file">未選擇任何檔案</span>
      </div>
      <img id="v-preview" class="preview" style="display:none">
      <button class="btn" id="v-upload-btn" onclick="uploadRegistration()" data-i18n="btn_upload_reg">上傳行照</button>
      <button class="btn success" id="v-ocr-btn" style="display:none" onclick="runOcr()" data-i18n="btn_ocr_reg">AI 辨識行照</button>
      <div id="v-loading" style="display:none;margin-top:12px;color:#1565C0;font-size:14px">
        <span style="display:inline-block;animation:spin 1s linear infinite;margin-right:8px">&#9696;</span>
        <span id="v-loading-text" data-i18n="msg_uploading">上傳中...</span>
      </div>
      <div id="v-msg" class="msg"></div>
    </div>
  </div>
  <!-- ★★ 上傳行照 modal 結束 ★★ -->

  <!-- ★★ 車輛編輯/新增表單 modal（OCR result & 手動新增 & 編輯既有都用這個） ★★ -->
  <div id="v-edit-form" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.55);z-index:9998;align-items:flex-start;justify-content:center;overflow-y:auto;padding:30px 12px">
    <div style="background:#fff;padding:20px 26px;border-radius:14px;max-width:760px;width:100%;position:relative;box-shadow:0 8px 32px rgba(0,0,0,.25)">
      <button type="button" onclick="closeVehicleFormModal()" style="position:absolute;top:8px;right:12px;background:none;border:0;font-size:26px;cursor:pointer;color:#888;line-height:1">×</button>
      <h3 id="v-edit-title" style="font-size:16px;color:#2E7D32;margin-top:0;margin-bottom:10px" data-i18n="h_ocr_result">AI 辨識結果</h3>
      <p style="font-size:11px;color:#888;margin-bottom:10px" data-i18n="ocr_hint_edit">點擊各欄位值可直接編輯修正</p>
        <table style="font-size:13px;width:100%"><tbody>
          <tr><td style="width:130px;color:#666;padding:6px"><b data-i18n="lbl_customer_name">客戶姓名</b></td><td><input type="text" id="ve-customer-name" placeholder="此車輛所屬客戶（修改會更新客戶資料）" data-i18n-placeholder="ph_customer_name" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%;background:#fffbea"></td></tr>
          <tr><td style="color:#666;padding:6px"><b data-i18n="lbl_customer_email">客戶 Email</b></td><td><input type="email" id="ve-customer-email" placeholder="設定後客戶可用此 Email 登入並看到自己的車輛保單" data-i18n-placeholder="ph_customer_email" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%;background:#e8f5e9"></td></tr>
          <tr><td style="color:#666;padding:6px"><b data-i18n="lbl_plate">車牌號碼</b></td><td><input type="text" id="ve-plate" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b data-i18n="lbl_brand">廠牌</b></td><td><input type="text" id="ve-brand" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b data-i18n="lbl_model">車型</b></td><td><input type="text" id="ve-model" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b data-i18n="lbl_year_month">出廠年月</b></td><td><input type="month" id="ve-year-month" oninput="autoComputeExpiry()" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b data-i18n="lbl_color">顏色</b></td><td><input type="text" id="ve-color" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b data-i18n="lbl_cc">排氣量 (cc)</b></td><td><input type="number" id="ve-cc" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b data-i18n="lbl_vin">車身號碼</b></td><td><input type="text" id="ve-vin" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b data-i18n="lbl_orig_reg_date">原發照日期</b></td><td><input type="date" id="ve-reg-date" oninput="autoComputeExpiry()" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b data-i18n="lbl_reissue_date">換補照日期</b></td><td><input type="date" id="ve-reissue-date" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b data-i18n="lbl_expiry_date">驗車到期日</b></td><td><input type="date" id="ve-expiry" oninput="updateInspectionWindow()" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b data-i18n="lbl_inspection_window">驗車期間</b><br><span style="font-size:10px;color:#999;font-weight:normal" data-i18n="hint_inspection_window">到期日前 30 天 ~ 後 30 天</span></td><td>
            <div style="display:flex;align-items:center;gap:6px">
              <input type="date" id="ve-window-start" readonly style="background:#f5f5f5;border:1px solid #ddd;border-radius:4px;padding:4px 8px;flex:1;color:#666">
              <span style="color:#999">~</span>
              <input type="date" id="ve-window-end" readonly style="background:#f5f5f5;border:1px solid #ddd;border-radius:4px;padding:4px 8px;flex:1;color:#666">
            </div>
          </td></tr>
          <tr><td style="color:#666;padding:6px"><b data-i18n="lbl_fuel">燃料種類</b></td><td>
            <select id="ve-fuel" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%">
              <option value="">--</option><option value="汽油">汽油</option><option value="柴油">柴油</option>
              <option value="油電混合">油電混合</option><option value="電動">電動</option><option value="LPG">LPG</option>
            </select>
          </td></tr>
        </tbody></table>

        <!-- 行照圖片直接上傳 -->
        <div style="margin-top:14px;padding:12px;background:#f5f7fa;border-radius:8px;border:1px solid #ddd">
          <div style="font-size:13px;color:#1565C0;font-weight:bold;margin-bottom:8px" data-i18n="reg_upload_direct_title">行照圖片（直接上傳到此車輛）</div>
          <img id="ve-current-image" class="preview" style="display:none;max-width:200px;max-height:140px;margin-bottom:8px;border-radius:6px;border:1px solid #ccc">
          <div style="display:flex;align-items:center;gap:8px">
            <input type="file" id="ve-file" accept="image/jpeg,image/png,image/webp,application/pdf,.pdf" onchange="onEditFileChange()" style="display:none">
            <button type="button" class="btn" style="padding:5px 12px;font-size:11px;background:#0288D1" onclick="document.getElementById('ve-file').click()" data-i18n="btn_choose_file">選擇檔案</button>
            <span id="ve-file-name" style="font-size:11px;color:#666" data-i18n="msg_no_file">未選擇任何檔案</span>
          </div>
          <img id="ve-file-preview" class="preview" style="display:none;max-width:200px;max-height:140px;margin:6px 0;border-radius:6px;border:1px solid #ccc">
          <div style="margin-top:6px">
            <button class="btn" style="padding:6px 14px;font-size:12px;background:#1565C0;color:#fff" onclick="uploadRegistrationDirect()" data-i18n="btn_upload_reg">上傳行照</button>
            <button class="btn success" style="padding:6px 14px;font-size:12px;display:none" id="ve-ocr-btn" onclick="ocrRegistrationDirect()" data-i18n="btn_ocr_autofill">AI 辨識自動填入</button>
          </div>
          <div id="ve-upload-loading" style="display:none;margin-top:6px;color:#1565C0;font-size:12px">
            <span style="display:inline-block;animation:spin 1s linear infinite;margin-right:6px">&#9696;</span>
            <span id="ve-upload-text" data-i18n="msg_processing">處理中...</span>
          </div>
        </div>

        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;border-top:1px solid #eee;padding-top:14px">
          <button class="btn success" onclick="saveEditedVehicle()" data-i18n="btn_save_vehicle">儲存車輛資料</button>
          <button class="btn" style="background:#0288D1" onclick="addAnotherVehicleSameCustomer()" data-i18n="btn_add_another_vehicle">+ 新增此客戶另一輛車</button>
          <button class="btn" style="background:#777;margin-left:auto" onclick="closeVehicleFormModal()" data-i18n="btn_done_close">完成 / 關閉</button>
        </div>
        <div id="ve-msg" class="msg"></div>
      </div>
    </div>
    <div class="card">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;flex-wrap:wrap;gap:6px">
        <h2 data-i18n="h_existing_vehicles" style="margin:0">現有車輛</h2>
        <div style="display:flex;gap:6px">
          <button class="btn success" onclick="openManualVehicleForm()" style="padding:8px 16px;font-size:14px" data-i18n="btn_add_new_vehicle_manual">+ 新增車輛（手動）</button>
          <button class="btn" onclick="scrollToAddVehicle()" style="padding:8px 16px;font-size:14px;background:#0288D1" data-i18n="btn_add_new_vehicle_ocr">+ 新增車輛（上傳行照）</button>
        </div>
      </div>
      <!-- 隱藏的 file input：給 row 內「上傳/更換」按鈕共用 -->
      <input type="file" id="row-upload-file" accept="image/jpeg,image/png,image/webp,application/pdf,.pdf" style="display:none" onchange="onRowFileSelected()">
      <table><thead><tr><th data-i18n="th_customer">客戶</th><th data-i18n="th_plate">車牌</th><th data-i18n="th_type">型式</th><th data-i18n="th_brand">品牌</th><th data-i18n="th_model">車型</th><th data-i18n="th_year">年份</th><th data-i18n="th_color">顏色</th><th data-i18n="th_cc">排氣量</th><th data-i18n="th_reg_expiry">行照到期</th><th data-i18n="th_inspection_window">驗車期間</th><th data-i18n="th_reg_image">行照</th><th data-i18n="th_action">操作</th></tr></thead>
      <tbody id="v-table"></tbody></table>
    </div>
  </div>

  <!-- Tab: Policies -->
  <div id="tab-policies" class="tab-content">

    <!-- ★★ 上傳保單 modal ★★ -->
    <div id="p-upload-modal" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.55);z-index:9997;align-items:flex-start;justify-content:center;overflow-y:auto;padding:30px 12px">
      <div style="background:#fff;padding:22px 26px;border-radius:14px;max-width:680px;width:100%;position:relative;box-shadow:0 8px 32px rgba(0,0,0,.25)">
        <button type="button" onclick="closePolicyUploadModal()" style="position:absolute;top:8px;right:12px;background:none;border:0;font-size:26px;cursor:pointer;color:#888;line-height:1">×</button>
        <h2 style="margin-top:0;margin-bottom:6px" data-i18n="h_upload_policy">新增保單（上傳 AI 辨識）</h2>
        <p style="color:#666;font-size:13px;margin-bottom:14px" data-i18n="upload_policy_hint">操作客戶：<b id="p-upload-modal-customer" style="color:#1565C0">—</b><br>上傳保單圖片/PDF，系統會自動辨識保險公司、保單號碼、起迄日、保障項目等並一鍵建立保單。</p>
        <label data-i18n="lbl_policy_image">保單圖片 (JPG/PNG/PDF)</label>
        <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
          <input type="file" id="p-file" accept="image/jpeg,image/png,image/webp,application/pdf,.pdf" onchange="onPolicyFileChange()" style="display:none">
          <button type="button" class="btn" style="padding:6px 16px;font-size:12px;background:#0288D1" onclick="document.getElementById('p-file').click()" data-i18n="btn_choose_file">選擇檔案</button>
          <span id="p-file-name" style="font-size:12px;color:#666" data-i18n="msg_no_file">未選擇任何檔案</span>
        </div>
        <img id="p-preview" class="preview" style="display:none">
        <button class="btn" id="p-upload-btn" onclick="uploadPolicy()" data-i18n="btn_upload_policy">上傳保單</button>
        <button class="btn success" id="p-ocr-btn" style="display:none" onclick="runPolicyOcr()" data-i18n="btn_ocr_policy">AI 辨識保單</button>
        <div id="p-upload-loading" style="display:none;margin-top:12px;color:#1565C0;font-size:14px">
          <span style="display:inline-block;animation:spin 1s linear infinite;margin-right:8px">&#9696;</span>
          <span id="p-loading-text" data-i18n="msg_uploading">上傳中...</span>
        </div>
        <div id="p-upload-msg" class="msg"></div>
        <!-- OCR result for policy -->
        <div id="p-ocr-result" style="display:none;margin-top:16px">
          <h3 style="font-size:14px;color:#2E7D32;margin-bottom:8px" data-i18n="h_ocr_result_short">辨識結果</h3>
          <table id="p-ocr-table" style="font-size:13px"><tbody></tbody></table>
        </div>
      </div>
    </div>

    <!-- ★★ 手動新增保單 modal ★★ -->
    <div id="p-form-modal" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.55);z-index:9998;align-items:flex-start;justify-content:center;overflow-y:auto;padding:30px 12px">
      <div style="background:#fff;padding:22px 26px;border-radius:14px;max-width:760px;width:100%;position:relative;box-shadow:0 8px 32px rgba(0,0,0,.25)">
        <button type="button" onclick="closePolicyFormModal()" style="position:absolute;top:8px;right:12px;background:none;border:0;font-size:26px;cursor:pointer;color:#888;line-height:1">×</button>
        <h2 style="margin-top:0;margin-bottom:6px" data-i18n="h_manual_policy">手動新增保單</h2>
        <p style="color:#666;font-size:13px;margin-bottom:12px">操作客戶：<b id="p-form-modal-customer" style="color:#1565C0">—</b></p>
        <div class="row">
          <div>
            <label data-i18n="lbl_insurer">保險公司</label>
            <select id="p-insurer" onchange="onInsurerChange('p-insurer','p-insurer-other')"></select>
            <input type="text" id="p-insurer-other" placeholder="保險公司名稱" data-i18n-placeholder="ph_insurer_other" style="display:none;margin-top:6px">
          </div>
          <div>
            <label data-i18n="lbl_policy_number">保單號碼</label>
            <input type="text" id="p-number" placeholder="例：FBN-2026-001234" data-i18n-placeholder="ph_policy_number">
          </div>
        </div>
        <div class="row">
          <div>
            <label data-i18n="lbl_covered_vehicle">承保車輛</label>
            <select id="p-vehicle"><option value="" data-i18n="opt_unspecified">不指定</option></select>
          </div>
          <div>
            <label data-i18n="lbl_status">狀態</label>
            <select id="p-status">
              <option value="active" data-i18n="opt_active">有效</option>
              <option value="expiring" data-i18n="opt_expiring">即將到期</option>
              <option value="expired" data-i18n="opt_expired">已到期</option>
            </select>
          </div>
        </div>
        <div class="row">
          <div><label data-i18n="lbl_premium">總保費</label><input type="text" inputmode="decimal" id="p-premium" placeholder="18,500" oninput="formatThousand(this)"></div>
        </div>

        <!-- 任意險 期間 -->
        <div style="margin-top:14px;padding:12px;background:#E3F2FD;border-radius:8px;border-left:4px solid #1565C0">
          <div style="font-size:13px;color:#1565C0;font-weight:bold;margin-bottom:8px" data-i18n="sec_voluntary_period">任意險 期間（綜合險 / 第三人責任 / 車體損失 等）</div>
          <div class="row">
            <div>
              <label data-i18n="lbl_start_date">起保日</label>
              <div style="display:flex;gap:6px">
                <input type="date" id="p-start" style="flex:1" oninput="autoComputePolicyEnd()">
                <input type="time" id="p-start-time" lang="en-GB" step="60" placeholder="HH:MM" style="width:96px" oninput="autoComputePolicyEnd()">
              </div>
            </div>
            <div>
              <label data-i18n="lbl_end_date">到期日 <span style="font-size:10px;color:#999">（自動 = 起保 +1 年；可手動修正）</span></label>
              <div style="display:flex;gap:6px">
                <input type="date" id="p-end" style="flex:1" oninput="markPolicyEndManual()">
                <input type="time" id="p-end-time" lang="en-GB" step="60" placeholder="HH:MM" style="width:96px" oninput="markPolicyEndManual()">
              </div>
            </div>
          </div>
        </div>

        <!-- 強制險 全套（如果跟任意險不同保險公司 / 保單號 / 期間） -->
        <div style="margin-top:14px;padding:12px;background:#FFF3E0;border-radius:8px;border-left:4px solid #E65100">
          <div style="font-size:13px;color:#E65100;font-weight:bold;margin-bottom:8px" data-i18n="sec_compulsory_period">強制險（汽車強制責任險，可能跟任意險不同家、不同保單號、不同期間）</div>
          <div class="row">
            <div>
              <label data-i18n="lbl_compulsory_insurer">強制險 保險公司</label>
              <select id="p-cinsurer" onchange="onInsurerChange('p-cinsurer','p-cinsurer-other')"></select>
              <input type="text" id="p-cinsurer-other" placeholder="保險公司名稱" data-i18n-placeholder="ph_insurer_other" style="display:none;margin-top:6px">
            </div>
            <div>
              <label data-i18n="lbl_compulsory_policy_no">強制險 保單號碼</label>
              <input type="text" id="p-cnumber" placeholder="例：CALI-2026-001234">
            </div>
          </div>
          <div class="row">
            <div>
              <label data-i18n="lbl_compulsory_premium">強制險 保費</label>
              <input type="text" inputmode="decimal" id="p-cpremium" placeholder="1,500" oninput="formatThousand(this)">
            </div>
            <div></div>
          </div>
          <div class="row">
            <div>
              <label data-i18n="lbl_compulsory_start">強制險 起保日</label>
              <div style="display:flex;gap:6px">
                <input type="date" id="p-cstart" style="flex:1" oninput="autoComputeCompulsoryEnd()">
                <input type="time" id="p-cstart-time" lang="en-GB" step="60" placeholder="HH:MM" style="width:96px" oninput="autoComputeCompulsoryEnd()">
              </div>
            </div>
            <div>
              <label data-i18n="lbl_compulsory_end">強制險 到期日 <span style="font-size:10px;color:#999">（自動 = 起保 +1 年；可手動修正）</span></label>
              <div style="display:flex;gap:6px">
                <input type="date" id="p-cend" style="flex:1" oninput="markCompulsoryEndManual()">
                <input type="time" id="p-cend-time" lang="en-GB" step="60" placeholder="HH:MM" style="width:96px" oninput="markCompulsoryEndManual()">
              </div>
            </div>
          </div>
        </div>

        <!-- 要保人（policyholder） -->
        <div style="margin-top:14px;padding:12px;background:#E1F5FE;border-radius:8px;border-left:4px solid #0288D1">
          <div style="font-size:13px;color:#01579B;font-weight:bold;margin-bottom:8px" data-i18n="sec_policyholder">要保人（可與客戶為不同人）</div>
          <div class="row">
            <div><label data-i18n="lbl_ph_name">姓名</label><input type="text" id="p-ph-name" placeholder="留空則沿用客戶姓名"></div>
            <div><label data-i18n="lbl_ph_id">身分證字號</label><input type="text" id="p-ph-id" placeholder="A123456789" maxlength="10" style="text-transform:uppercase"></div>
          </div>
          <div class="row">
            <div><label data-i18n="lbl_ph_birth">生日</label><input type="date" id="p-ph-birth"></div>
            <div><label data-i18n="lbl_ph_gender">性別</label>
              <select id="p-ph-gender">
                <option value="">--</option><option value="男">男</option><option value="女">女</option><option value="其他">其他</option>
              </select>
            </div>
            <div><label data-i18n="lbl_ph_phone">電話</label><input type="tel" id="p-ph-phone" placeholder="0912-345-678"></div>
          </div>
          <div class="row">
            <div style="flex:1;min-width:0">
              <label data-i18n="lbl_ph_relation">與車主(=被保險人)的關係</label>
              <input type="text" id="p-ph-relation" placeholder="如：本人 / 父 / 母 / 配偶 / 子女 / 員工 / 朋友" maxlength="50" autocomplete="off">
            </div>
          </div>
        </div>

        <!-- 被保人（insured） -->
        <div style="margin-top:14px;padding:12px;background:#E8F5E9;border-radius:8px;border-left:4px solid #2E7D32">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap">
            <span style="font-size:13px;color:#1B5E20;font-weight:bold" data-i18n="sec_insured">被保人（受益對象，應為車主）</span>
            <span id="p-in-status" style="font-size:11px;color:#999"></span>
            <button type="button" onclick="_alignInsured('p')" style="margin-left:auto;padding:4px 10px;font-size:11px;background:#2E7D32;color:#fff;border:0;border-radius:4px;cursor:pointer" data-i18n="btn_align_insured">📋 對齊車主</button>
          </div>
          <div class="row">
            <div><label data-i18n="lbl_in_name">姓名</label><input type="text" id="p-in-name" placeholder="留空則沿用要保人姓名" oninput="_recheckInsuredAlignment('p')"></div>
            <div><label data-i18n="lbl_in_id">身分證字號</label><input type="text" id="p-in-id" placeholder="A123456789" maxlength="10" style="text-transform:uppercase"></div>
          </div>
          <div class="row">
            <div><label data-i18n="lbl_in_birth">生日</label><input type="date" id="p-in-birth"></div>
            <div><label data-i18n="lbl_in_gender">性別</label>
              <select id="p-in-gender">
                <option value="">--</option><option value="男">男</option><option value="女">女</option><option value="其他">其他</option>
              </select>
            </div>
            <div><label data-i18n="lbl_in_phone">電話</label><input type="tel" id="p-in-phone" placeholder="0912-345-678"></div>
          </div>
        </div>

        <div style="margin-top:16px">
          <h3 style="font-size:14px;color:#666" data-i18n="h_coverage_items">保障項目</h3>
          <div id="p-items"></div>
          <button class="btn" style="background:#666;margin-top:8px" onclick="addItemRow()" data-i18n="btn_add_item">+ 新增項目</button>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;border-top:1px solid #eee;padding-top:14px">
          <button class="btn success" onclick="createPolicy()" data-i18n="btn_create_policy">建立保單</button>
          <button class="btn" style="background:#0288D1" onclick="addAnotherPolicySameCustomer()" data-i18n="btn_add_another_policy">+ 新增此客戶另一張保單</button>
          <button class="btn" style="background:#777;margin-left:auto" onclick="closePolicyFormModal()" data-i18n="btn_done_close">完成 / 關閉</button>
        </div>
        <div id="p-msg" class="msg"></div>
      </div>
    </div>

    <!-- 現有保單（唯一 inline card，按鈕在 header） -->
    <div class="card">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;flex-wrap:wrap;gap:6px">
        <h2 data-i18n="h_existing_policies" style="margin:0">現有保單</h2>
        <div style="display:flex;gap:6px">
          <button class="btn success" onclick="openManualPolicyForm()" style="padding:8px 16px;font-size:14px" data-i18n="btn_add_new_policy_manual">+ 新增保單（手動）</button>
          <button class="btn" onclick="openPolicyUploadModal()" style="padding:8px 16px;font-size:14px;background:#0288D1" data-i18n="btn_add_new_policy_ocr">+ 新增保單（上傳辨識）</button>
        </div>
      </div>
      <p style="font-size:12px;color:#666;margin-bottom:8px" data-i18n="policy_list_hint">💡 點擊任一保單列可選取，<b>雙擊</b>查看承保項目明細</p>
      <!-- 隱藏 file input：給 row 上傳保單按鈕共用 -->
      <input type="file" id="row-policy-file" accept="image/jpeg,image/png,image/webp,application/pdf,.pdf" style="display:none" onchange="onPolicyFileSelectedRow()">
      <table><thead><tr>
        <th data-i18n="th_customer">客戶</th><th data-i18n="th_plate">車牌</th><th data-i18n="th_policy_number">保單號碼</th><th data-i18n="th_insurer">保險公司</th><th data-i18n="th_status">狀態</th>
        <th data-i18n="th_start">起保</th><th data-i18n="th_end">到期</th><th data-i18n="th_premium">保費</th><th data-i18n="th_items">項目</th><th data-i18n="th_action">操作</th>
      </tr></thead>
      <tbody id="p-table"></tbody></table>
    </div>

    <!-- 保單編輯彈窗（從 row 點編輯時用） -->
    <div id="p-edit-modal" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:9999;align-items:center;justify-content:center">
      <div style="background:#fff;padding:24px;border-radius:12px;max-width:500px;width:90%;max-height:90vh;overflow-y:auto;position:relative">
        <button type="button" onclick="closePolicyEdit()" style="position:absolute;top:8px;right:12px;background:none;border:0;font-size:26px;cursor:pointer;color:#888;line-height:1">×</button>
        <h3 style="color:#1565C0;margin-bottom:14px" data-i18n="h_edit_policy">編輯保單</h3>
        <table style="width:100%"><tbody>
          <tr><td style="width:90px;padding:6px;color:#666" data-i18n="lbl_policyholder">要保人姓名</td><td><input type="text" id="pe-customer-name" placeholder="此保單所屬客戶（修改會轉移保單）" data-i18n-placeholder="ph_policyholder" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px;background:#fffbea"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_customer_email">客戶 Email</td><td><input type="email" id="pe-customer-email" placeholder="設定後客戶可用此 Email 登入並看到此保單" data-i18n-placeholder="ph_customer_email_short" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px;background:#e8f5e9"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_policy_number">保單號碼</td><td><input type="text" id="pe-number" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_covered_vehicle">承保車牌</td><td>
            <div id="pe-vehicle-info" style="padding:6px 10px;background:#F5F5F5;border:1px solid #ddd;border-radius:4px;font-family:monospace;color:#333;font-weight:600">—</div>
            <small style="color:#999;font-size:10px" data-i18n="hint_plate_readonly">車牌與車輛主檔同步，請至「車輛 / 行照」分頁修改</small>
          </td></tr>

          <!-- 要保人 -->
          <tr><td colspan="2" style="padding:8px 6px 4px;color:#1565C0;font-weight:bold;font-size:13px;border-top:1px solid #eee" data-i18n="sec_policyholder">要保人（可與客戶為不同人）</td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_ph_name">要保人姓名</td><td><input type="text" id="pe-ph-name" placeholder="留空則沿用客戶姓名" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_ph_id">要保人身分證字號</td><td><input type="text" id="pe-ph-id" placeholder="A123456789" maxlength="10" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px;text-transform:uppercase"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_ph_birth">要保人生日</td><td><input type="date" id="pe-ph-birth" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_ph_gender">要保人性別</td><td>
            <select id="pe-ph-gender" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px">
              <option value="">--</option><option value="男">男</option><option value="女">女</option><option value="其他">其他</option>
            </select>
          </td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_ph_phone">要保人電話</td><td><input type="tel" id="pe-ph-phone" placeholder="0912-345-678" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_ph_relation">與車主(=被保險人)的關係</td><td><input type="text" id="pe-ph-relation" placeholder="如：本人 / 父 / 母 / 配偶 / 子女 / 員工 / 朋友" maxlength="50" autocomplete="off" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>

          <!-- 被保人 -->
          <tr><td colspan="2" style="padding:8px 6px 4px;color:#2E7D32;font-weight:bold;font-size:13px;border-top:1px solid #eee">
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <span data-i18n="sec_insured">被保人（受益對象，應為車主）</span>
              <span id="pe-in-status" style="font-size:11px;font-weight:normal;color:#999"></span>
              <button type="button" onclick="_alignInsured('pe')" style="margin-left:auto;padding:3px 10px;font-size:11px;background:#2E7D32;color:#fff;border:0;border-radius:4px;cursor:pointer" data-i18n="btn_align_insured">📋 對齊車主</button>
            </div>
          </td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_in_name">被保人姓名</td><td><input type="text" id="pe-in-name" placeholder="留空則沿用要保人姓名" oninput="_recheckInsuredAlignment('pe')" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_in_id">被保人身分證字號</td><td><input type="text" id="pe-in-id" placeholder="A123456789" maxlength="10" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px;text-transform:uppercase"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_in_birth">被保人生日</td><td><input type="date" id="pe-in-birth" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_in_gender">被保人性別</td><td>
            <select id="pe-in-gender" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px">
              <option value="">--</option><option value="男">男</option><option value="女">女</option><option value="其他">其他</option>
            </select>
          </td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_in_phone">被保人電話</td><td><input type="tel" id="pe-in-phone" placeholder="0912-345-678" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_insurer">保險公司</td><td>
            <select id="pe-insurer" onchange="onInsurerChange('pe-insurer','pe-insurer-other')" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></select>
            <input type="text" id="pe-insurer-other" placeholder="保險公司名稱" data-i18n-placeholder="ph_insurer_other" style="display:none;margin-top:6px;width:100%;padding:6px;border:1px solid #ddd;border-radius:4px">
          </td></tr>
          <tr><td colspan="2" style="padding:8px 6px 4px;color:#1565C0;font-weight:bold;font-size:13px;border-top:1px solid #eee" data-i18n="sec_voluntary_period">任意險 期間</td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_start_date">起保日</td><td>
            <div style="display:flex;gap:6px">
              <input type="date" id="pe-start" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:4px">
              <input type="time" id="pe-start-time" lang="en-GB" step="60" style="width:96px;padding:6px;border:1px solid #ddd;border-radius:4px">
            </div>
          </td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_end_date">到期日</td><td>
            <div style="display:flex;gap:6px">
              <input type="date" id="pe-end" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:4px">
              <input type="time" id="pe-end-time" lang="en-GB" step="60" style="width:96px;padding:6px;border:1px solid #ddd;border-radius:4px">
            </div>
          </td></tr>
          <tr><td colspan="2" style="padding:8px 6px 4px;color:#E65100;font-weight:bold;font-size:13px;border-top:1px solid #eee" data-i18n="sec_compulsory_period">強制險（可能跟任意險不同家）</td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_compulsory_insurer">強制險 保險公司</td><td>
            <select id="pe-cinsurer" onchange="onInsurerChange('pe-cinsurer','pe-cinsurer-other')" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></select>
            <input type="text" id="pe-cinsurer-other" placeholder="保險公司名稱" data-i18n-placeholder="ph_insurer_other" style="display:none;margin-top:6px;width:100%;padding:6px;border:1px solid #ddd;border-radius:4px">
          </td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_compulsory_policy_no">強制險 保單號碼</td><td><input type="text" id="pe-cnumber" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_compulsory_premium">強制險 保費</td><td><input type="text" inputmode="decimal" id="pe-cpremium" oninput="formatThousand(this)" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_compulsory_start">強制險起保日</td><td>
            <div style="display:flex;gap:6px">
              <input type="date" id="pe-cstart" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:4px">
              <input type="time" id="pe-cstart-time" lang="en-GB" step="60" style="width:96px;padding:6px;border:1px solid #ddd;border-radius:4px">
            </div>
          </td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_compulsory_end">強制險到期日</td><td>
            <div style="display:flex;gap:6px">
              <input type="date" id="pe-cend" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:4px">
              <input type="time" id="pe-cend-time" lang="en-GB" step="60" style="width:96px;padding:6px;border:1px solid #ddd;border-radius:4px">
            </div>
          </td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_premium">總保費</td><td><input type="text" inputmode="decimal" id="pe-premium" oninput="formatThousand(this)" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666" data-i18n="lbl_status">狀態</td><td>
            <select id="pe-status" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px">
              <option value="active">active</option>
              <option value="expiring">expiring</option>
              <option value="expired">expired</option>
              <option value="cancelled">cancelled</option>
            </select>
          </td></tr>
        </tbody></table>

        <!-- 保障項目（編輯版）-->
        <div style="margin-top:14px;padding:12px;background:#F1F8E9;border-radius:8px;border-left:4px solid #2E7D32">
          <div style="font-size:13px;color:#2E7D32;font-weight:bold;margin-bottom:8px" data-i18n="h_coverage_items">保障項目</div>
          <div id="pe-items"></div>
          <button class="btn" style="background:#666;margin-top:8px;padding:6px 14px;font-size:12px" onclick="addEditItemRow()" data-i18n="btn_add_item">+ 新增項目</button>
        </div>

        <div style="margin-top:14px;text-align:right">
          <button class="btn" style="background:#999;color:#fff" onclick="closePolicyEdit()" data-i18n="btn_cancel">取消</button>
          <button class="btn success" onclick="savePolicyEdit()" data-i18n="btn_save">儲存</button>
        </div>
        <div id="pe-msg" class="msg"></div>
      </div>
    </div>
  </div>

  <!-- Tab: Overview -->
  <!-- Tab: Claims -->
  <div id="tab-claims" class="tab-content">
    <div class="card">
      <h2 data-i18n="h_claims">理賠申請管理</h2>
      <p style="color:#666;font-size:13px;margin-bottom:12px" data-i18n="claims_hint">客戶送出的理賠申請</p>
      <button class="btn" onclick="loadClaims()" data-i18n="btn_load_claims">載入理賠列表</button>
      <div id="claims-list" style="margin-top:16px"></div>
    </div>
  </div>

  <!-- Tab: Accidents -->
  <div id="tab-accidents" class="tab-content">
    <div class="card">
      <h2 data-i18n="h_accidents">事故照片管理</h2>
      <p style="color:#666;font-size:13px;margin-bottom:12px" data-i18n="accidents_hint">客戶透過緊急救援上傳的事故現場照片</p>
      <button class="btn" onclick="loadAccidents()" data-i18n="btn_load_accidents">載入事故列表</button>
      <div id="acc-list" style="margin-top:16px"></div>
    </div>
  </div>

  <div id="tab-overview" class="tab-content">
    <div class="card">
      <h2 data-i18n="h_overview">系統資料總覽</h2>
      <div id="overview-content"></div>
    </div>
  </div>

  <!-- 詢價回報 modal -->
  <div id="quote-respond-modal" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.55);z-index:9998;align-items:flex-start;justify-content:center;overflow-y:auto;padding:30px 12px">
    <div style="background:#fff;padding:22px 26px;border-radius:14px;max-width:600px;width:100%;position:relative;box-shadow:0 8px 32px rgba(0,0,0,.25)">
      <button type="button" onclick="closeQuoteRespond()" style="position:absolute;top:8px;right:12px;background:none;border:0;font-size:26px;cursor:pointer;color:#888">×</button>
      <h3 style="margin-top:0">處理詢價工單 / 加入報價</h3>
      <p style="font-size:11px;color:#666">向保險公司詢得各家報價後，逐筆加進來；填完所有報價按「✓ 完成回報」會通知客戶。</p>

      <div class="row">
        <div>
          <label>保險公司</label>
          <input type="text" id="qrsp-insurer" placeholder="富邦產險">
        </div>
        <div>
          <label>保費 (NTD)</label>
          <input type="text" inputmode="decimal" id="qrsp-premium" placeholder="18,500" oninput="formatThousand(this)">
        </div>
      </div>
      <div>
        <label>報價有效期至</label>
        <input type="date" id="qrsp-valid-until">
      </div>
      <div>
        <label>保障明細（每行一項，格式：<code>項目名稱|保額(萬)|保費</code>）</label>
        <textarea id="qrsp-coverage" rows="6" placeholder="第三人責任險（體傷）|500|3500&#10;車體損失險甲式|200|18500&#10;道路救援||"></textarea>
      </div>
      <div>
        <label>備註（特別條款 / 折扣等）</label>
        <textarea id="qrsp-notes" rows="2"></textarea>
      </div>
      <label style="display:flex;align-items:center;gap:6px;margin-top:8px">
        <input type="checkbox" id="qrsp-recommend"> <span style="font-size:12px">標記為推薦方案</span>
      </label>

      <div id="qrsp-msg" class="msg" style="margin-top:8px"></div>

      <div style="display:flex;gap:8px;margin-top:14px;border-top:1px solid #eee;padding-top:14px;flex-wrap:wrap">
        <button class="btn success" onclick="submitQuoteResponse()" style="padding:8px 16px;font-size:13px">➕ 加入此筆報價</button>
        <button class="btn" onclick="markQuoteRequestStatus('in_progress')" style="background:#0288D1;padding:8px 16px;font-size:13px">處理中</button>
        <button class="btn" onclick="markQuoteRequestStatus('quoted')" style="background:#2E7D32;padding:8px 16px;font-size:13px">✓ 完成回報（通知客戶）</button>
        <button class="btn" onclick="markQuoteRequestStatus('completed')" style="background:#666;padding:8px 16px;font-size:13px">已結案</button>
        <button class="btn" style="background:#999;margin-left:auto" onclick="closeQuoteRespond()">關閉</button>
      </div>
    </div>
  </div>

  <!-- Tab: 詢價工單 -->
  <div id="tab-quotes" class="tab-content">
    <div class="card">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;flex-wrap:wrap;gap:6px">
        <h2 style="margin:0" data-i18n="h_quote_requests">詢價工單</h2>
        <div style="display:flex;gap:6px;font-size:11px">
          <button class="qr-filter" data-status="" onclick="loadQuoteRequests('')" style="padding:4px 10px;border:1px solid #ddd;border-radius:6px;background:#fff;cursor:pointer">全部</button>
          <button class="qr-filter" data-status="pending" onclick="loadQuoteRequests('pending')" style="padding:4px 10px;border:1px solid #ddd;border-radius:6px;background:#fff;cursor:pointer">待處理</button>
          <button class="qr-filter" data-status="in_progress" onclick="loadQuoteRequests('in_progress')" style="padding:4px 10px;border:1px solid #ddd;border-radius:6px;background:#fff;cursor:pointer">處理中</button>
          <button class="qr-filter" data-status="quoted" onclick="loadQuoteRequests('quoted')" style="padding:4px 10px;border:1px solid #ddd;border-radius:6px;background:#fff;cursor:pointer">已回報</button>
          <button class="qr-filter" data-status="completed" onclick="loadQuoteRequests('completed')" style="padding:4px 10px;border:1px solid #ddd;border-radius:6px;background:#fff;cursor:pointer">已結案</button>
        </div>
      </div>
      <p style="font-size:11px;color:#666;margin-bottom:8px">客戶送出的詢價工單。處理流程：實際向保險公司詢價 → 加入「報價」→ 標記「已回報」（通知客戶）。</p>
      <div id="quote-list"></div>
    </div>
  </div>

  <!-- Console: Agents -->
  <div id="tab-agents" class="tab-content">
    <div class="card">
      <h2 data-i18n="h_add_agent">新增業務員</h2>
      <div class="row"><div><label data-i18n="lbl_username">帳號</label><input id="ag-user" placeholder="agent01"></div><div><label data-i18n="lbl_password">密碼</label><div class="pw-wrap"><input id="ag-pass" type="password"><button type="button" class="pw-toggle" onclick="togglePw('ag-pass',this)">👁</button></div></div></div>
      <div class="row"><div><label data-i18n="lbl_display_name">顯示名稱</label><input id="ag-name"></div><div><label>Email</label><input id="ag-email"></div></div>
      <div class="row"><div><label data-i18n="lbl_phone">電話</label><input id="ag-phone"></div><div><label data-i18n="lbl_ip_whitelist">IP 白名單（逗號分隔，空=不限）</label><input id="ag-ip"></div></div>
      <button class="btn" onclick="createAgent()" data-i18n="btn_add_agent">新增業務員</button>
      <div id="ag-msg" class="msg"></div>
    </div>
    <div class="card">
      <h2 data-i18n="h_agent_list">業務員列表</h2>
      <table><thead><tr><th data-i18n="lbl_username">帳號</th><th data-i18n="th_name">名稱</th><th data-i18n="th_status">狀態</th><th data-i18n="th_customer_count">客戶數</th><th data-i18n="th_last_login">最後登入</th><th data-i18n="th_action">操作</th></tr></thead>
      <tbody id="agents-table"></tbody></table>
    </div>
  </div>

  <!-- Console: Assign -->
  <div id="tab-assign" class="tab-content">
    <div class="card">
      <h2 data-i18n="h_assign_customer">分配客戶給業務員</h2>
      <div class="row"><div><label data-i18n="lbl_choose_agent">選擇業務員</label><select id="assign-agent"></select></div><div><label data-i18n="lbl_choose_customer">選擇客戶</label><select id="assign-customer"></select></div></div>
      <button class="btn success" onclick="assignCustomer()" data-i18n="btn_assign">分配</button>
      <div id="assign-msg" class="msg"></div>
    </div>
  </div>

  <!-- Console: Logs -->
  <div id="tab-logs" class="tab-content">
    <div class="card">
      <h2 data-i18n="h_audit_logs">操作日誌</h2>
      <button class="btn" onclick="loadLogs()" style="margin-bottom:8px" data-i18n="btn_load_latest">載入最新</button>
      <table><thead><tr><th data-i18n="th_time">時間</th><th data-i18n="th_admin">管理員</th><th data-i18n="th_action_col">操作</th><th data-i18n="th_target">目標</th><th data-i18n="th_detail">說明</th><th data-i18n="th_ip">IP</th></tr></thead>
      <tbody id="logs-table"></tbody></table>
    </div>
  </div>
</div>

<!-- 數字易經 modal（搬出 admin-panel 避免 display:none 父層干擾值清空） -->
<div id="numerology-modal" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.6);z-index:9998;align-items:flex-start;justify-content:center;overflow-y:auto;padding:30px 12px">
  <div style="background:#fff;padding:22px 26px;border-radius:14px;max-width:760px;width:100%;position:relative;box-shadow:0 8px 32px rgba(0,0,0,.3)">
    <button type="button" onclick="closeNumerologyModal()" style="position:absolute;top:8px;right:12px;background:none;border:0;font-size:26px;cursor:pointer;color:#888;line-height:1">×</button>
    <h2 style="margin-top:0;background:linear-gradient(90deg,#9C27B0,#E91E63,#FF9800);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">✨ 數字易經 — 幫自己和客戶拿副好牌</h2>
    <p style="font-size:11px;color:#666;margin-bottom:12px">八宅遊星 · 4 吉星（生氣/延年/天醫/伏位）vs 4 凶星（絕命/五鬼/六煞/禍害）</p>

    <!-- Tabs -->
    <div style="display:flex;gap:4px;background:#F5F5F5;border-radius:8px;padding:4px;margin-bottom:12px">
      <button class="num-tab" data-tab="personal" onclick="numSwitchTab('personal')" style="flex:1;padding:8px;border:0;border-radius:6px;background:#fff;font-size:13px;font-weight:600;cursor:pointer;color:#9C27B0">個人分析</button>
      <button class="num-tab" data-tab="advanced" onclick="numSwitchTab('advanced')" style="flex:1;padding:8px;border:0;border-radius:6px;background:transparent;font-size:13px;font-weight:600;cursor:pointer;color:#666">進階分析</button>
      <button class="num-tab" data-tab="recommend" onclick="numSwitchTab('recommend')" style="flex:1;padding:8px;border:0;border-radius:6px;background:transparent;font-size:13px;font-weight:600;cursor:pointer;color:#666">智能建議 (30 組)</button>
    </div>

    <!-- 用 form 包起來,可以 form.reset() 一次清光所有欄位 -->
    <form id="num-form" autocomplete="off" onsubmit="return false" style="margin:0">
      <!-- Tab: 個人分析 -->
      <div id="num-tab-personal" class="num-pane">
        <div style="font-size:11px;color:#666;background:#F3E5F5;padding:8px;border-radius:6px;margin-bottom:8px">輸入客戶 / 自己的身分證、生日、電話、車牌（每項可填可不填,至少填一項）。同個人有兩支電話 / 兩台車可分別填入,會一起整合分析,結果會自動帶入智能建議避凶補吉。</div>
        <div class="row">
          <div><label>身分證字號</label><input type="text" id="num-id" placeholder="A123456789" maxlength="10" autocomplete="off" data-form-type="other" style="text-transform:uppercase"></div>
          <div><label>生日（西元）</label><input type="text" id="num-birthday" placeholder="1985/03/15" maxlength="10" autocomplete="off" data-form-type="other"></div>
        </div>
        <div class="row">
          <div><label>電話</label><input type="text" id="num-phone" placeholder="0912345678" autocomplete="off" data-form-type="other"></div>
          <div><label>電話 2（選填）</label><input type="text" id="num-phone2" placeholder="0987654321" autocomplete="off" data-form-type="other"></div>
        </div>
        <div class="row">
          <div><label>車牌（含英文字也可）</label><input type="text" id="num-license" placeholder="如 ABC-1234" maxlength="12" autocomplete="off" data-form-type="other" style="text-transform:uppercase"></div>
          <div><label>車牌 2（含英文字也可,選填）</label><input type="text" id="num-license2" placeholder="如 XYZ-5678" maxlength="12" autocomplete="off" data-form-type="other" style="text-transform:uppercase"></div>
        </div>
        <button type="button" onclick="numAutoSubmit()" style="margin-top:8px;width:100%;padding:10px;background:linear-gradient(90deg,#9C27B0,#E91E63);color:#fff;border:0;border-radius:8px;font-weight:600;cursor:pointer">🔍 分析</button>
        <div id="num-personal-results" style="margin-top:10px"></div>
      </div>

      <!-- Tab: 進階分析 -->
      <div id="num-tab-advanced" class="num-pane" style="display:none">
        <div style="font-size:11px;color:#666;background:#F3E5F5;padding:8px;border-radius:6px;margin-bottom:8px">1–3 組號碼任意分析,多組會合併計算交互作用（A1 天醫消絕命、A3 延年壓六煞、生氣消禍害等規則）。</div>
        <div><label>號碼 1</label><input type="text" id="num-m1" placeholder="如 13311331" autocomplete="off" data-form-type="other"></div>
        <div><label>號碼 2（選填）</label><input type="text" id="num-m2" placeholder="如 0912345678" autocomplete="off" data-form-type="other"></div>
        <div><label>號碼 3（選填）</label><input type="text" id="num-m3" placeholder="如 A1234" autocomplete="off" data-form-type="other"></div>
        <button type="button" onclick="numManualSubmit()" style="margin-top:8px;width:100%;padding:10px;background:linear-gradient(90deg,#9C27B0,#E91E63);color:#fff;border:0;border-radius:8px;font-weight:600;cursor:pointer">🔍 分析</button>
        <div id="num-manual-results" style="margin-top:10px"></div>
      </div>

      <!-- Tab: 智能建議 -->
      <div id="num-tab-recommend" class="num-pane" style="display:none">
        <div style="font-size:11px;color:#666;background:#F3E5F5;padding:8px;border-radius:6px;margin-bottom:8px">產生 30 組高分號碼,自動讀取「個人分析」結果避凶補吉。請先到個人分析跑一次以提供參照。</div>
        <div class="row">
          <div>
            <label>用途</label>
            <select id="num-rec-purpose" onchange="numUpdateRecommendLimits()">
              <option value="phone">📱 電話</option>
              <option value="license">🚗 車牌</option>
              <option value="pin">🔢 PIN / 密碼</option>
            </select>
          </div>
          <div><label>長度</label><input type="number" id="num-rec-length" value="10" min="2" max="12" autocomplete="off"></div>
          <div><label>開頭</label><input type="text" id="num-rec-prefix" value="09" placeholder="如 09 / ABC" autocomplete="off" data-form-type="other" style="text-transform:uppercase"></div>
        </div>
        <button type="button" onclick="numRecommendSubmit()" style="margin-top:8px;width:100%;padding:10px;background:linear-gradient(90deg,#9C27B0,#E91E63);color:#fff;border:0;border-radius:8px;font-weight:600;cursor:pointer">🎯 產生 30 組吉祥號碼</button>
        <div id="num-rec-results" style="margin-top:10px;max-height:75vh;overflow-y:auto;padding-right:4px"></div>
      </div>
    </form>

    <div style="margin-top:14px;text-align:right;border-top:1px solid #eee;padding-top:10px">
      <button onclick="closeNumerologyModal()" style="background:#999;color:#fff;border:0;border-radius:6px;padding:6px 14px;font-size:12px;cursor:pointer">關閉</button>
    </div>
  </div>
</div>

<!-- 數字易經：未登入引導對話框（必須放在 admin-panel 之外,否則登出時 display:none 會吃掉它） -->
<div id="numerology-login-required" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.6);z-index:99999;align-items:center;justify-content:center;padding:20px">
  <div style="background:#fff;padding:24px;border-radius:14px;max-width:380px;width:100%;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,.3)">
    <div style="font-size:48px;margin-bottom:6px">🔒</div>
    <h3 style="margin:0 0 10px;color:#333">請先登入</h3>
    <p style="font-size:13px;color:#666;margin:0 0 18px;line-height:1.7">
      「✨ 幫自己和客戶拿副好牌」是業務員專屬功能,<br>請先用您的管理員帳號密碼登入後再使用。
    </p>
    <button onclick="closeNumerologyLoginRequired(true)"
      style="width:100%;padding:10px;background:linear-gradient(90deg,#9C27B0,#E91E63);color:#fff;border:0;border-radius:8px;font-weight:600;cursor:pointer">
      前往登入 →
    </button>
    <button onclick="closeNumerologyLoginRequired(false)"
      style="margin-top:8px;width:100%;padding:8px;background:#f5f5f5;color:#666;border:0;border-radius:8px;font-size:12px;cursor:pointer">
      取消
    </button>
  </div>
</div>

<script>
var API = '';
var TOKEN = '';
var ADMIN_TOKEN = '';
var ADMIN_ROLE = '';
var CONSOLE_API = '/api/v1/admin-console';

// 台灣主要產險公司清單（含車險業務）— 後端會直接存字串，OCR 結果若不在此清單則自動切到「其他」手動輸入
var TAIWAN_INSURERS = [
  '富邦產險', '國泰世紀產險', '新光產險', '明台產險', '兆豐產險',
  '第一產險', '華南產險', '旺旺友聯產險', '新安東京海上產險',
  '泰安產險', '安達產險', '南山產險', '臺灣產險', '美亞產險',
  '法國巴黎產險', '蘇黎世產險', '三井住友海上產險'
];

function fillInsurerSelect(selectId, otherInputId, value) {
  var sel = document.getElementById(selectId);
  if (!sel) return;
  var html = '<option value="">' + (LANG==='en' ? '— Select Insurer —' : '— 請選擇保險公司 —') + '</option>';
  for (var i = 0; i < TAIWAN_INSURERS.length; i++) {
    html += '<option value="' + TAIWAN_INSURERS[i] + '">' + TAIWAN_INSURERS[i] + '</option>';
  }
  html += '<option value="__other__">' + (LANG==='en' ? 'Other (type in)' : '其他（手動輸入）') + '</option>';
  sel.innerHTML = html;
  var other = otherInputId ? document.getElementById(otherInputId) : null;
  if (value) {
    if (TAIWAN_INSURERS.indexOf(value) >= 0) {
      sel.value = value;
      if (other) { other.style.display = 'none'; other.value = ''; }
    } else {
      sel.value = '__other__';
      if (other) { other.style.display = 'block'; other.value = value; }
    }
  } else {
    sel.value = '';
    if (other) { other.style.display = 'none'; other.value = ''; }
  }
}

// === 千分位數字輸入 helpers ===
// 純數字（含小數點）字串加千分位逗號；非數字字元一律剝掉
function formatThousand(el) {
  if (!el) return;
  var v = (el.value || '').replace(/[^\\d.]/g, '');
  // 只保留第一個小數點
  var firstDot = v.indexOf('.');
  if (firstDot >= 0) v = v.slice(0, firstDot + 1) + v.slice(firstDot + 1).replace(/\\./g, '');
  if (!v) { el.value = ''; return; }
  var parts = v.split('.');
  parts[0] = parts[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',');
  el.value = parts.join('.');
}
// 帶逗號字串轉 number；空字串/非法 → null
function parseThousand(s) {
  if (s == null || s === '') return null;
  var raw = String(s).replace(/,/g, '').trim();
  if (!raw) return null;
  var n = parseFloat(raw);
  return isNaN(n) ? null : n;
}
// 把純數字寫到 input 並加千分位
function setNumberWithComma(id, val) {
  var el = document.getElementById(id);
  if (!el) return;
  if (val == null || val === '' || val === 0) { el.value = (val === 0) ? '0' : ''; return; }
  el.value = Number(val).toLocaleString('en-US', { maximumFractionDigits: 2 });
}

// === 加入 / 取消 行事曆 — 用 data-* 屬性傳值（避開 onclick 字串轉義雷）===
// uid 用「用途+物件 id」設定固定值 → 加入 vs 取消 用同一個 UID，匯入 .ics CANCEL 時行事曆會找到原事件移除
function _icalIcs(method, title, dateStr, desc, uid, days) {
  var dt = String(dateStr).replace(/-/g, '');
  var n = new Date(dateStr + 'T00:00:00');
  n.setDate(n.getDate() + 1);
  var end = n.getFullYear() + String(n.getMonth() + 1).padStart(2,'0') + String(n.getDate()).padStart(2,'0');
  var stamp = new Date().toISOString().replace(/[-:]/g,'').replace(/\\.\\d{3}/,'');
  var safeDesc = String(desc||'').replace(/\\\\/g,'\\\\\\\\').replace(/\\n/g,'\\\\n').replace(/,/g,'\\\\,');
  var lines = [
    'BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//BOPINAN//Admin//ZH','CALSCALE:GREGORIAN',
    'METHOD:' + method,
    'BEGIN:VEVENT',
    'UID:' + uid,
    'DTSTAMP:' + stamp,
    'DTSTART;VALUE=DATE:' + dt,
    'DTEND;VALUE=DATE:' + end,
    'SUMMARY:' + (method === 'CANCEL' ? '[已取消] ' : '') + title,
    'DESCRIPTION:' + safeDesc,
    'STATUS:' + (method === 'CANCEL' ? 'CANCELLED' : 'CONFIRMED'),
    'SEQUENCE:' + (method === 'CANCEL' ? '1' : '0'),
  ];
  if (method !== 'CANCEL') {
    (days || [30,14,7,1]).forEach(function(d){
      lines.push('BEGIN:VALARM');
      lines.push('ACTION:DISPLAY');
      lines.push('DESCRIPTION:' + title + ' 倒數 ' + d + ' 天');
      lines.push('TRIGGER:-PT' + (d*1440) + 'M');
      lines.push('END:VALARM');
    });
  }
  lines.push('END:VEVENT');
  lines.push('END:VCALENDAR');
  return lines.join('\\r\\n');
}
function _googleCalUrl(title, dateStr, desc) {
  if (!dateStr) return '#';
  var dt = String(dateStr).replace(/-/g, '');
  var n = new Date(dateStr + 'T00:00:00');
  n.setDate(n.getDate() + 1);
  var end = n.getFullYear() + String(n.getMonth() + 1).padStart(2,'0') + String(n.getDate()).padStart(2,'0');
  var p = new URLSearchParams({action:'TEMPLATE', text:title, dates:dt+'/'+end, details:desc||''});
  return 'https://calendar.google.com/calendar/render?' + p.toString();
}
function _downloadIcs(filename, ics) {
  var blob = new Blob([ics], {type:'text/calendar;charset=utf-8'});
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(function(){ URL.revokeObjectURL(url); }, 1000);
}

// 點到 .cal-btn 或 .cal-cancel-btn → 顯示對應 popover
document.addEventListener('click', function(e){
  var btn = e.target.closest('.cal-btn, .cal-cancel-btn');
  if (!btn) return;
  e.stopPropagation();
  var isCancel = btn.classList.contains('cal-cancel-btn');
  var title = btn.dataset.calTitle || '';
  var dateStr = btn.dataset.calDate || '';
  var desc = btn.dataset.calDesc || '';
  var uid = btn.dataset.calUid || ('bopinan-' + Date.now() + '@bopinan');
  if (!dateStr) return;

  var old = document.getElementById('_cal_pop'); if (old) old.remove();
  var pop = document.createElement('div');
  pop.id = '_cal_pop';
  pop.style.cssText = 'position:absolute;z-index:10001;background:#fff;border:1px solid #ddd;border-radius:6px;box-shadow:0 4px 12px rgba(0,0,0,.15);overflow:hidden;font-size:12px;min-width:200px';

  if (isCancel) {
    pop.innerHTML =
        '<div style="padding:6px 10px;background:#fff3e0;font-size:11px;color:#E65100;border-bottom:1px solid #eee">下載取消通知並匯入到行事曆</div>'
      + '<a href="#" data-act="ics-cancel" style="display:block;padding:6px 10px;text-decoration:none;color:#333">🍎 下載 .ics 取消通知</a>'
      + '<a href="' + _googleCalUrl('[已取消] ' + title, dateStr, '⚠️ 此事件已取消\\n\\n' + desc) + '" target="_blank" rel="noopener" style="display:block;padding:6px 10px;text-decoration:none;color:#333;border-top:1px solid #eee">📅 在 Google 日曆中刪除（手動）</a>';
  } else {
    pop.innerHTML =
        '<a href="' + _googleCalUrl(title, dateStr, desc) + '" target="_blank" rel="noopener" style="display:block;padding:6px 10px;text-decoration:none;color:#333;border-bottom:1px solid #eee">📅 Google 日曆</a>'
      + '<a href="#" data-act="ics-add" style="display:block;padding:6px 10px;text-decoration:none;color:#333">🍎 Apple / Outlook (.ics)</a>';
  }

  document.body.appendChild(pop);
  var r = btn.getBoundingClientRect();
  pop.style.left = (r.right + window.scrollX - pop.offsetWidth) + 'px';
  pop.style.top = (r.bottom + window.scrollY + 4) + 'px';
  setTimeout(function(){ pop.style.left = (r.right + window.scrollX - pop.offsetWidth) + 'px'; }, 0);

  pop.addEventListener('click', function(ev){
    var a = ev.target.closest('[data-act]');
    if (!a) return;
    ev.preventDefault();
    var act = a.getAttribute('data-act');
    if (act === 'ics-add') {
      _downloadIcs(title + '.ics', _icalIcs('REQUEST', title, dateStr, desc, uid));
    } else if (act === 'ics-cancel') {
      _downloadIcs('CANCEL_' + title + '.ics', _icalIcs('CANCEL', title, dateStr, desc, uid));
    }
    pop.remove();
  });

  setTimeout(function(){
    document.addEventListener('click', function _close(ev){
      if (!pop.contains(ev.target) && !btn.contains(ev.target)) {
        pop.remove(); document.removeEventListener('click', _close);
      }
    });
  }, 0);
});

// 用 data-* 屬性產生加入 + 取消兩顆按鈕；安全（不會被 desc 內的引號或換行 break）
function _attr(s) { return String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function _calBtnHtml(title, dateStr, desc, uid) {
  if (!dateStr) return '';
  var u = uid || ('bopinan-' + String(title).replace(/\\s+/g,'-') + '-' + dateStr + '@bopinan');
  var common = 'data-cal-title="' + _attr(title) + '" data-cal-date="' + _attr(dateStr) + '" data-cal-desc="' + _attr(desc) + '" data-cal-uid="' + _attr(u) + '"';
  return '<button class="cal-btn" ' + common + ' style="margin-left:4px;padding:2px 6px;font-size:10px;background:#E3F2FD;color:#1565C0;border:1px solid #BBDEFB;border-radius:4px;cursor:pointer;white-space:nowrap" title="加入行事曆">📅 加入</button>'
       + '<button class="cal-cancel-btn" ' + common + ' style="margin-left:2px;padding:2px 6px;font-size:10px;background:#FFEBEE;color:#C62828;border:1px solid #EF9A9A;border-radius:4px;cursor:pointer;white-space:nowrap" title="取消加入行事曆">✕</button>';
}

// === 被保人 ↔ 車主 對齊（防呆）===
// 在台灣車險，被保人 (insured) 通常應為車輛登記車主，否則理賠時可能出狀況。
// 取得目前 modal 對應的「客戶 / 車主」姓名（manual=p, edit=pe）
function _getCustomerNameForPolicy(prefix) {
  if (prefix === 'pe') {
    // 編輯既有保單 → 取編輯 modal 內的客戶姓名欄位（可能被改過）
    var el = document.getElementById('pe-customer-name');
    return (el && el.value || '').trim();
  } else {
    // 手動新增（p）→ 取當前操作客戶下拉
    var sel = document.getElementById('cur-customer');
    if (sel && sel.selectedIndex >= 0) {
      return (sel.options[sel.selectedIndex].text || '').split(' · ')[0].trim();
    }
    return '';
  }
}

// 即時檢查被保人姓名 vs 車主姓名，更新狀態列
function _recheckInsuredAlignment(prefix) {
  var insEl = document.getElementById(prefix + '-in-name');
  var statusEl = document.getElementById(prefix + '-in-status');
  if (!insEl || !statusEl) return;
  var insName = (insEl.value || '').trim();
  var custName = _getCustomerNameForPolicy(prefix);
  if (!insName) {
    statusEl.innerHTML = '<span style="color:#999;font-size:11px">未填（點「對齊車主」自動帶入）</span>';
    insEl.style.borderColor = '';
    return;
  }
  if (custName && insName === custName) {
    statusEl.innerHTML = '<span style="color:#2E7D32;font-size:11px;font-weight:600">✓ 與車主一致</span>';
    insEl.style.borderColor = '#A5D6A7';
  } else {
    statusEl.innerHTML = '<span style="color:#D32F2F;font-size:11px;font-weight:600">⚠️ 與車主「' + (custName || '?') + '」不符</span>';
    insEl.style.borderColor = '#EF9A9A';
  }
}

// 一鍵對齊：把車主姓名 copy 到被保人姓名（其他欄位若客戶有也帶過去）
function _alignInsured(prefix) {
  var custName = _getCustomerNameForPolicy(prefix);
  if (!custName) {
    alert(LANG==='en' ? 'No customer selected' : '尚未選定客戶 / 車主');
    return;
  }
  var nameEl = document.getElementById(prefix + '-in-name');
  if (nameEl) nameEl.value = custName;
  _recheckInsuredAlignment(prefix);
}

// ════════════════════════════════════════════════
// 數字易經（Number I-Ching）— 透過 BOPINAN 後端代理至 numerology-easing API
// ════════════════════════════════════════════════
var NUM_GOOD = ['天醫','生氣','延年','伏位'];
var NUM_BAD  = ['絕命','五鬼','六煞','禍害'];
var NUM_ALL = NUM_GOOD.concat(NUM_BAD);
var NUM_INFO = {
  '天醫': { kind:'吉', brief:'貴人財富', desc:'貴人相助、財運穩固、化險為夷', color:'#F9A825' },
  '生氣': { kind:'吉', brief:'機會人緣', desc:'正能量、機會多、人緣亨通',     color:'#2E7D32' },
  '延年': { kind:'吉', brief:'長久穩定', desc:'感情和諧、健康長壽、做事持久', color:'#388E3C' },
  '伏位': { kind:'吉', brief:'平穩守成', desc:'按部就班、安守本分、穩中求進', color:'#558B2F' },
  '絕命': { kind:'凶', brief:'破財損傷', desc:'破財、健康危機、意外損失',     color:'#B71C1C' },
  '五鬼': { kind:'凶', brief:'是非小人', desc:'口舌官司、小人作祟、心神不寧', color:'#C62828' },
  '六煞': { kind:'凶', brief:'感情糾葛', desc:'桃花是非、人際困擾、感情風波', color:'#D84315' },
  '禍害': { kind:'凶', brief:'爭執病災', desc:'病災、爭執糾紛、運勢起伏',     color:'#E65100' },
};
window._numPersonalSnapshot = null;  // 個人分析結果快取（給智能建議讀凶星）

// ────── UI helpers ──────
function _numClearAllInputs() {
  // 防個資殘留:每次開 / 關 / 登出都清空所有輸入和結果
  console.log('[numerology] _numClearAllInputs() called');
  var form = document.getElementById('num-form');
  if (form && typeof form.reset === 'function') {
    form.reset();   // ← 一次性還原所有受 form 管理的欄位（含 input value、select selectedIndex）
  }
  // 雙保險:再用 querySelectorAll 把所有 input 顯式設空,擊敗任何瀏覽器 autofill / 殘留
  var modal = document.getElementById('numerology-modal');
  if (modal) {
    modal.querySelectorAll('input').forEach(function(el){
      if (el.id === 'num-rec-length') el.value = '10';
      else if (el.id === 'num-rec-prefix') el.value = '09';
      else el.value = '';
    });
    var selPurpose = modal.querySelector('#num-rec-purpose');
    if (selPurpose) selPurpose.selectedIndex = 0;
  }
  ['num-personal-results','num-manual-results','num-rec-results'].forEach(function(id){
    var el = document.getElementById(id);
    if (el) el.innerHTML = '';
  });
  window._numPersonalSnapshot = null;
}

function openNumerologyModal() {
  // 未登入 → 跳警語引導去登入,而不是無聲打開空白 modal
  if (!ADMIN_TOKEN) {
    var dlg = document.getElementById('numerology-login-required');
    if (dlg) dlg.style.display = 'flex';
    return;
  }
  _numClearAllInputs();   // 開啟前清空,避免上次操作的個資殘留
  document.getElementById('numerology-modal').style.display = 'flex';
  numSwitchTab('personal');
  // 50ms 後再清一次,擊敗瀏覽器 autofill / autocomplete 還原
  setTimeout(_numClearAllInputs, 50);
}

function closeNumerologyLoginRequired(goLogin) {
  var dlg = document.getElementById('numerology-login-required');
  if (dlg) dlg.style.display = 'none';
  if (goLogin) {
    var sec = document.getElementById('login-section');
    if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
    var u = document.getElementById('login-user');
    if (u) setTimeout(function(){ u.focus(); }, 300);
  }
}

function closeNumerologyModal() {
  document.getElementById('numerology-modal').style.display = 'none';
  _numClearAllInputs();   // 關閉時也清,雙重保險
}

function numSwitchTab(tab) {
  document.querySelectorAll('.num-tab').forEach(function(b){
    if (b.dataset.tab === tab) {
      b.style.background = '#fff'; b.style.color = '#9C27B0';
    } else {
      b.style.background = 'transparent'; b.style.color = '#666';
    }
  });
  document.querySelectorAll('.num-pane').forEach(function(p){ p.style.display = 'none'; });
  document.getElementById('num-tab-' + tab).style.display = '';
}

// 智能建議：依用途動態調整長度上限 + 開頭預設值（與前台一致）
function numUpdateRecommendLimits() {
  var p = document.getElementById('num-rec-purpose');
  var lenEl = document.getElementById('num-rec-length');
  var prefixEl = document.getElementById('num-rec-prefix');
  if (!p || !lenEl || !prefixEl) return;
  var purpose = p.value;
  if (purpose === 'license') {
    lenEl.max = 7;
    if (parseInt(lenEl.value, 10) > 7) lenEl.value = 7;
    prefixEl.value = '';
    prefixEl.placeholder = '如 ABC、AAA（監理站發的英文字）';
  } else if (purpose === 'phone') {
    lenEl.max = 12;
    if (!prefixEl.value) prefixEl.value = '09';
    prefixEl.placeholder = '如 09';
  } else {
    lenEl.max = 12;
    prefixEl.placeholder = '（可留空）';
  }
}

// ─── 前台同款視覺元件（綜合儀表 + 年齡分區 + 磁場 bar chart）─────

// 8 磁場大長條圖（每張分析卡內用）
function _numMagnetBarChartHtml(counts) {
  var maxCount = 1;
  NUM_ALL.forEach(function(m){ if ((counts[m]||0) > maxCount) maxCount = counts[m]; });
  var html = '<div style="display:flex;align-items:flex-end;gap:3px;height:80px;padding:0 4px">';
  NUM_ALL.forEach(function(m){
    var info = NUM_INFO[m];
    var n = counts[m] || 0;
    var pct = (n / maxCount) * 100;
    html += '<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;height:100%;justify-content:flex-end">' +
      '<div style="font-size:10px;font-weight:bold;color:#4b5563;height:14px">' + (n > 0 ? n : '') + '</div>' +
      '<div style="width:100%;height:' + Math.max(2, pct) + '%;min-height:' + (n > 0 ? '4px' : '2px') + ';border-radius:3px 3px 0 0;background:' + (info.kind === '吉' ? '#059669' : '#dc2626') + ';opacity:' + (n > 0 ? 1 : 0.15) + '"></div>' +
      '<div style="font-size:9px;color:#6b7280;margin-top:2px">' + m + '</div>' +
    '</div>';
  });
  html += '</div>';
  return html;
}

// 綜合磁場儀表卡（所有欄位整合 + 半圓指針 + 環形圖 + 8 磁場音量條 + 重點摘要）
function _numSummaryCardHtml(data) {
  // 從 6 欄位整合磁場
  var total = {};
  ['id','birthday','phone','phone2','license','license2'].forEach(function(k){
    var c = (data[k] || {}).magnet_count || {};
    Object.keys(c).forEach(function(m){
      if (m === '中性') return;
      total[m] = (total[m] || 0) + c[m];
    });
  });
  var goodSum = 0, badSum = 0;
  NUM_GOOD.forEach(function(m){ goodSum += total[m] || 0; });
  NUM_BAD.forEach(function(m){ badSum += total[m] || 0; });
  var totalSum = goodSum + badSum;
  if (totalSum === 0) return '';

  var score = Math.round(goodSum / totalSum * 100);
  var level, color;
  if (score >= 75)      { level = '極佳';   color = '#059669'; }
  else if (score >= 60) { level = '良好';   color = '#65a30d'; }
  else if (score >= 45) { level = '持平';   color = '#9e9d24'; }
  else if (score >= 30) { level = '偏弱';   color = '#ea580c'; }
  else                  { level = '需注意'; color = '#dc2626'; }

  // SVG 半圓指針儀表
  var angleRad = Math.PI * (1 - score / 100);
  var pointerLen = 78;
  var px = (100 + pointerLen * Math.cos(angleRad)).toFixed(1);
  var py = (110 - pointerLen * Math.sin(angleRad)).toFixed(1);

  var gaugeSvg = '<svg viewBox="0 0 200 130" style="width:100%;max-width:200px;height:auto">' +
    '<path d="M 22 110 A 78 78 0 0 1 178 110" stroke="#e6e8eb" stroke-width="14" fill="none" stroke-linecap="round"/>' +
    '<path d="M 22 110 A 78 78 0 0 1 60 41"   stroke="#dc2626" stroke-width="14" fill="none" stroke-linecap="round"/>' +
    '<path d="M 60 41 A 78 78 0 0 1 100 32"   stroke="#f59e0b" stroke-width="14" fill="none" stroke-linecap="round"/>' +
    '<path d="M 100 32 A 78 78 0 0 1 140 41"  stroke="#84cc16" stroke-width="14" fill="none" stroke-linecap="round"/>' +
    '<path d="M 140 41 A 78 78 0 0 1 178 110" stroke="#059669" stroke-width="14" fill="none" stroke-linecap="round"/>' +
    '<line x1="100" y1="110" x2="' + px + '" y2="' + py + '" stroke="#1a1d21" stroke-width="3" stroke-linecap="round"/>' +
    '<circle cx="100" cy="110" r="7" fill="#1a1d21"/>' +
    '<circle cx="100" cy="110" r="3" fill="#fff"/>' +
  '</svg>';

  var goodPct = (goodSum / Math.max(1, goodSum + badSum)) * 100;
  var donut = '<div style="position:relative;width:128px;height:128px;border-radius:50%;background:conic-gradient(#059669 0% ' + goodPct.toFixed(2) + '%, #dc2626 ' + goodPct.toFixed(2) + '% 100%)">' +
    '<div style="position:absolute;top:24px;left:24px;right:24px;bottom:24px;border-radius:50%;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:inset 0 0 8px rgba(0,0,0,.05)">' +
      '<div style="font-size:14px;font-weight:bold"><span style="color:#059669">' + goodSum + '</span><span style="color:#9ca3af;margin:0 4px">/</span><span style="color:#dc2626">' + badSum + '</span></div>' +
      '<div style="font-size:10px;color:#9ca3af">吉 / 凶</div>' +
    '</div></div>';

  // 8 磁場音量條
  var maxC = 1;
  NUM_ALL.forEach(function(m){ if ((total[m]||0) > maxC) maxC = total[m]; });
  var barsHtml = '<div style="display:flex;gap:4px;align-items:flex-end;margin-bottom:14px">';
  NUM_ALL.forEach(function(m){
    var info = NUM_INFO[m];
    var n = total[m] || 0;
    var pct = (n / maxC) * 100;
    barsHtml += '<div style="flex:1;display:flex;flex-direction:column;align-items:center;min-width:0">' +
      '<div style="position:relative;height:80px;width:100%;background:#f3f4f6;border-radius:4px;overflow:hidden;display:flex;align-items:flex-end">' +
        '<div style="width:100%;background:' + (info.kind === '吉' ? '#059669' : '#dc2626') + ';height:' + pct + '%;min-height:' + (n > 0 ? '4px' : '0') + ';transition:all .3s">' +
          (n > 0 ? '<div style="font-size:10px;color:#fff;text-align:center;font-weight:bold;padding-top:2px">' + n + '</div>' : '') +
        '</div>' +
      '</div>' +
      '<div style="font-size:10px;font-weight:bold;margin-top:4px;color:' + info.color + '">' + m + '</div>' +
      '<div style="font-size:9px;color:#9ca3af">' + info.brief + '</div>' +
    '</div>';
  });
  barsHtml += '</div>';

  // 重點摘要（最強吉星 + 最需注意）
  var goodList = NUM_GOOD.map(function(m){ return { m: m, n: total[m] || 0 }; }).filter(function(x){ return x.n > 0; }).sort(function(a, b){ return b.n - a.n; });
  var badList  = NUM_BAD.map(function(m){ return { m: m, n: total[m] || 0 }; }).filter(function(x){ return x.n > 0; }).sort(function(a, b){ return b.n - a.n; });
  var sg = goodList[0], sb = badList[0];
  var insightsHtml = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px">';
  if (sg) {
    insightsHtml += '<div style="border:1px solid #bbf7d0;background:#f0fdf4;padding:8px;border-radius:8px">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">' +
        '<span style="font-size:10px;font-weight:bold;color:#16a34a;background:#dcfce7;padding:1px 8px;border-radius:4px">最強吉星</span>' +
        '<span style="font-size:14px;font-weight:bold;color:#15803d">' + sg.m + ' ×' + sg.n + '</span>' +
      '</div>' +
      '<p style="font-size:11px;color:#14532d;margin:0">' + NUM_INFO[sg.m].desc + '</p>' +
    '</div>';
  }
  if (sb) {
    insightsHtml += '<div style="border:1px solid #fecaca;background:#fef2f2;padding:8px;border-radius:8px">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">' +
        '<span style="font-size:10px;font-weight:bold;color:#dc2626;background:#fee2e2;padding:1px 8px;border-radius:4px">最需注意</span>' +
        '<span style="font-size:14px;font-weight:bold;color:#b91c1c">' + sb.m + ' ×' + sb.n + '</span>' +
      '</div>' +
      '<p style="font-size:11px;color:#7f1d1d;margin:0">' + NUM_INFO[sb.m].desc + '</p>' +
    '</div>';
  }
  insightsHtml += '</div>';

  return '<div style="background:#fff;border:2px solid #e9d5ff;border-radius:12px;padding:14px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,.04)">' +
    '<div style="text-align:center;margin-bottom:10px">' +
      '<h3 style="font-weight:bold;color:#1f2937;margin:0;font-size:15px">綜合磁場儀表</h3>' +
      '<p style="font-size:11px;color:#6b7280;margin:2px 0 0">身分證・生日・電話・車牌 整合分析</p>' +
    '</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:20px;align-items:center;justify-content:center;margin-bottom:14px">' +
      '<div style="text-align:center;flex:0 1 220px">' + gaugeSvg +
        '<div style="margin-top:-12px"><div style="font-size:30px;font-weight:800;color:' + color + '">' + score + '<span style="font-size:14px">%</span></div>' +
        '<div style="font-size:13px;font-weight:bold;color:' + color + '">' + level + '</div>' +
        '<div style="font-size:10px;color:#9ca3af">吉星比例</div></div>' +
      '</div>' +
      '<div style="display:flex;align-items:center;justify-content:center">' + donut + '</div>' +
    '</div>' +
    '<div style="font-size:12px;font-weight:bold;color:#4b5563;margin-bottom:6px">磁場強度</div>' +
    barsHtml +
    '<div style="font-size:12px;font-weight:bold;color:#4b5563;margin-bottom:6px">重點摘要</div>' +
    insightsHtml +
  '</div>';
}

// 年齡分區卡（從身分證解碼出的人生時間軸）
function _numAgeMappingCardHtml(am) {
  if (!am || am.error) return '';
  var ranges = am.primary_ranges || [];
  var timeline = (am.timeline || []).filter(function(e){ return e.age_start <= 70; });
  if (ranges.length === 0 && timeline.length === 0) return '';

  var maxAge = 70;
  ranges.forEach(function(r){ if (r.end > maxAge) maxAge = r.end; });
  var axisTicks = [0, 10, 20, 30, 40, 50, 60, 70].filter(function(a){ return a <= maxAge; });

  var html = '<div style="background:#fff;border:1px solid #e0e0e0;border-radius:10px;padding:10px;margin:6px 0">';
  html += '<h3 style="font-weight:bold;color:#1f2937;font-size:13px;margin:0">年齡分區</h3>';
  html += '<p style="font-size:11px;color:#6b7280;margin:2px 0 8px;font-family:monospace">' + (am.id_decoded || '') + '</p>';

  if (ranges.length > 0) {
    html += '<div style="font-size:11px;font-weight:bold;color:#4b5563;margin-bottom:4px">主磁場影響範圍（可重疊）</div>';
    html += '<div style="display:flex;justify-content:space-between;margin-bottom:4px;padding-left:70px;font-size:9px;color:#9ca3af">';
    axisTicks.forEach(function(a){ html += '<span>' + a + '</span>'; });
    html += '</div>';

    ranges.forEach(function(r){
      var left = (r.start / maxAge) * 100;
      var width = ((r.end - r.start) / maxAge) * 100;
      var info = NUM_INFO[r.magnet];
      if (!info) return;
      html += '<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">' +
        '<div style="width:64px;flex-shrink:0">' +
          '<div style="font-size:10px;font-weight:bold;color:' + info.color + '">' + r.magnet + '</div>' +
          '<div style="font-size:9px;color:#9ca3af">' + info.brief + '</div>' +
        '</div>' +
        '<div style="flex:1;position:relative;height:18px;background:#f3f4f6;border-radius:3px">' +
          '<div style="position:absolute;top:0;left:' + left + '%;width:' + width + '%;height:100%;background:' + info.color + ';border-radius:3px;color:#fff;font-size:9px;font-weight:bold;display:flex;align-items:center;justify-content:center">' +
            r.start + '–' + r.end +
          '</div>' +
        '</div>' +
      '</div>';
    });
  }

  if (timeline.length > 0) {
    html += '<div style="font-size:11px;font-weight:bold;color:#4b5563;margin-top:10px;margin-bottom:4px">年齡細節</div>';
    html += '<div style="overflow-x:auto"><table style="width:100%;font-size:11px;border-collapse:collapse">';
    html += '<thead><tr style="background:#f9fafb">';
    html += '<th style="text-align:left;padding:4px 6px;font-weight:bold;color:#4b5563">年齡</th>';
    html += '<th style="text-align:left;padding:4px 6px;font-weight:bold;color:#4b5563">數字組</th>';
    html += '<th style="text-align:left;padding:4px 6px;font-weight:bold;color:#4b5563">磁場</th>';
    html += '<th style="text-align:left;padding:4px 6px;font-weight:bold;color:#4b5563">說明</th>';
    html += '</tr></thead><tbody>';
    timeline.forEach(function(e){
      var info = NUM_INFO[e.magnet];
      var note = (e.magnet === '伏位' && e.continues) ? '（延續' + e.continues + '）' : '';
      html += '<tr style="border-top:1px solid #f3f4f6">' +
        '<td style="padding:4px 6px;white-space:nowrap">' + e.age_start + '–' + e.age_end + ' 歲</td>' +
        '<td style="padding:4px 6px;font-family:monospace">' + (e.pair || '') + '</td>' +
        '<td style="padding:4px 6px;font-weight:bold;color:' + (info ? info.color : '#000') + '">' + e.magnet + '</td>' +
        '<td style="padding:4px 6px;color:#6b7280">' + (info ? info.desc : '') + note + '</td>' +
      '</tr>';
    });
    html += '</tbody></table></div>';
  }

  html += '</div>';
  return html;
}

// 渲染 single 分析結果到 HTML
function _numAnalysisCardHtml(label, result) {
  if (!result) return '';
  if (result.error) {
    return '<div style="background:#FFEBEE;color:#C62828;padding:8px;border-radius:6px;margin:6px 0">'+label+'：'+result.error+'</div>';
  }
  var counts = result.magnet_count || {};
  var goodSum = 0, badSum = 0;
  NUM_GOOD.forEach(function(m){ goodSum += counts[m] || 0; });
  NUM_BAD.forEach(function(m){ badSum += counts[m] || 0; });
  var total = goodSum + badSum;
  var pct = total > 0 ? Math.round(goodSum / total * 100) : 0;
  var level, levelColor;
  if (pct >= 75) { level='極佳'; levelColor='#2E7D32'; }
  else if (pct >= 60) { level='良好'; levelColor='#558B2F'; }
  else if (pct >= 45) { level='持平'; levelColor='#9E9D24'; }
  else if (pct >= 30) { level='偏弱'; levelColor='#E65100'; }
  else { level='需注意'; levelColor='#C62828'; }

  var pairs = (result.pairs || []).filter(function(p){ return !p.extended; });

  var html = '<div style="background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:10px;margin:6px 0">';
  html += '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">';
  html += '<div><div style="font-size:11px;color:#999">'+label+'</div><div style="font-family:monospace;font-weight:bold">'+(result.input||'')+'</div></div>';
  html += '<div style="text-align:right"><b style="color:'+levelColor+'">'+level+' '+pct+'%</b><div style="font-size:10px;color:#999">吉 '+goodSum+' · 凶 '+badSum+'</div></div>';
  html += '</div>';

  if (pairs.length > 0) {
    html += '<div style="display:flex;flex-wrap:wrap;gap:3px;margin-top:6px">';
    pairs.forEach(function(p) {
      var info = NUM_INFO[p.magnet];
      if (!info) return;
      var disp = (p.raw_pair && p.after_assimilation && p.raw_pair !== p.after_assimilation)
                  ? p.raw_pair+'→'+p.after_assimilation : (p.raw_pair || '');
      var note = (p.magnet === '伏位' && p.continues) ? ('（延續'+p.continues+'）') : '';
      var op = (p.active === false) ? '0.4' : '1';
      html += '<span style="background:'+info.color+'20;color:'+info.color+';padding:2px 6px;border-radius:3px;font-size:10px;font-weight:600;opacity:'+op+'" title="'+info.desc+'">'+disp+' '+p.magnet+note+'</span>';
    });
    html += '</div>';
  }

  // 8 磁場 grid（一格一格的計數）
  html += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:3px;margin-top:8px;padding-top:6px;border-top:1px solid #f0f0f0">';
  NUM_ALL.forEach(function(m){
    var info = NUM_INFO[m];
    var n = counts[m] || 0;
    var bg = n > 0 ? info.color + '15' : '#F5F5F5';
    var c = n > 0 ? info.color : '#aaa';
    html += '<div style="background:'+bg+';color:'+c+';text-align:center;padding:4px 2px;border-radius:4px;font-size:10px"><div style="font-weight:bold">'+m+'</div><div style="font-size:14px;font-weight:bold">'+n+'</div><div style="opacity:0.7;font-size:9px">'+info.brief+'</div></div>';
  });
  html += '</div>';

  // 8 磁場 bar chart（前台同款,在一格一格的顯示之後）
  html += '<div style="margin-top:8px;padding-top:6px;border-top:1px solid #f0f0f0">';
  html += '<div style="font-size:10px;font-weight:bold;color:#6b7280;margin-bottom:4px">磁場分布</div>';
  html += _numMagnetBarChartHtml(counts);
  html += '</div>';

  // 伏位細分（前台同款）
  if (result.fuwei_breakdown && Object.keys(result.fuwei_breakdown).length > 0) {
    html += '<div style="margin-top:8px;padding-top:6px;border-top:1px solid #f0f0f0">';
    html += '<div style="font-size:10px;font-weight:bold;color:#6b7280;margin-bottom:4px">伏位細分</div>';
    html += '<div style="display:flex;flex-wrap:wrap;gap:4px">';
    Object.keys(result.fuwei_breakdown).forEach(function(k){
      var v = result.fuwei_breakdown[k];
      var labelText = (k === '純伏位') ? '純伏位' : ('延續' + k);
      html += '<span style="font-size:10px;background:#f3f4f6;padding:2px 8px;border-radius:99px">' + labelText + ' <strong>×' + v + '</strong></span>';
    });
    html += '</div></div>';
  }

  if (result.duplicate_marks && result.duplicate_marks.length) {
    html += '<div style="margin-top:6px;background:#F3E5F5;color:#6A1B9A;padding:4px 8px;border-radius:4px;font-size:10px"><b>重複磁場：</b>'+result.duplicate_marks.join('、')+'</div>';
  }
  html += '</div>';
  return html;
}

// ────── Tab 個人分析（API 一次回三項）──────
// 車牌字母 → 數字（A=1, B=2, ..., Z=26 單字單轉）。送 API 前轉換,顯示時還原成原文
function _numConvertLicense(s) {
  if (!s) return '';
  var clean = s.toUpperCase().replace(/[^A-Z0-9]/g, '');
  var out = '';
  for (var i = 0; i < clean.length; i++) {
    var ch = clean[i];
    if (ch >= 'A' && ch <= 'Z') out += String(ch.charCodeAt(0) - 'A'.charCodeAt(0) + 1);
    else out += ch;
  }
  return out;
}

// 從 API 回應抽取錯誤訊息(兼容 BOPINAN APIResponse 與 FastAPI HTTPException / ValidationError)
function _numExtractError(d, status) {
  if (!d) return 'HTTP ' + (status || '??');
  if (d.message) return d.message;
  if (typeof d.detail === 'string') return d.detail;
  if (Array.isArray(d.detail)) {
    return d.detail.map(function(e){ return (e && e.msg) ? e.msg : JSON.stringify(e); }).join(', ');
  }
  return 'HTTP ' + (status || '??');
}

async function numAutoSubmit() {
  var idn = document.getElementById('num-id').value.trim();
  var bday = document.getElementById('num-birthday').value.trim();
  var ph = document.getElementById('num-phone').value.trim();
  var ph2 = document.getElementById('num-phone2').value.trim();
  var lic = document.getElementById('num-license').value.trim();
  var lic2 = document.getElementById('num-license2').value.trim();
  var box = document.getElementById('num-personal-results');
  if (!idn && !bday && !ph && !ph2 && !lic && !lic2) {
    box.innerHTML = '<div style="background:#FFEBEE;color:#C62828;padding:8px;border-radius:6px">請至少輸入一項</div>';
    return;
  }
  // 車牌字母轉數字後送 API,但顯示時還原成使用者原本輸入
  var licSend = _numConvertLicense(lic);
  var lic2Send = _numConvertLicense(lic2);
  var licShown = lic.toUpperCase();
  var lic2Shown = lic2.toUpperCase();

  box.innerHTML = '<div style="text-align:center;color:#999;padding:20px"><span style="display:inline-block;animation:spin 1s linear infinite">⏳</span> 分析中⋯</div>';
  try {
    var r = await fetch(CONSOLE_API.replace('/admin-console','') + '/numerology/auto', {
      method:'POST',
      headers:{'Content-Type':'application/json','Authorization':'Bearer '+ADMIN_TOKEN},
      body: JSON.stringify({
        id: idn, birthday: bday,
        phone: ph, phone2: ph2,
        license: licSend, license2: lic2Send,
      }),
    });
    var d = await r.json().catch(function(){ return null; });
    if (!r.ok || !d || !d.success) {
      var msg = _numExtractError(d, r.status);
      console.warn('numerology /auto failed', r.status, d);
      box.innerHTML = '<div style="background:#FFEBEE;color:#C62828;padding:8px;border-radius:6px">分析失敗：'+msg+'</div>';
      return;
    }
    var data = d.data || {};
    window._numPersonalSnapshot = data;  // 儲存給智能建議用（含 6 個欄位）
    // 把車牌的 input 欄位還原成使用者輸入,避免暴露轉換後的數字
    if (data.license && licShown) data.license = Object.assign({}, data.license, { input: licShown });
    if (data.license2 && lic2Shown) data.license2 = Object.assign({}, data.license2, { input: lic2Shown });

    var html = '';
    // ① 綜合磁場儀表（最上方,前台同款）
    var hasAny = ['id','birthday','phone','phone2','license','license2'].some(function(k){ return data[k]; });
    if (hasAny) html += _numSummaryCardHtml(data);

    // ② 身分證 + 年齡分區
    if (data.id) html += _numAnalysisCardHtml('身分證', data.id);
    if (data.id_error) html += '<div style="background:#FFEBEE;color:#C62828;padding:6px 8px;border-radius:6px;margin:4px 0">身分證：'+data.id_error+'</div>';
    if (data.age_mapping) html += _numAgeMappingCardHtml(data.age_mapping);

    // ③ 其他欄位
    if (data.birthday) html += _numAnalysisCardHtml('生日', data.birthday);
    if (data.birthday_error) html += '<div style="background:#FFEBEE;color:#C62828;padding:6px 8px;border-radius:6px;margin:4px 0">生日：'+data.birthday_error+'</div>';
    if (data.phone) html += _numAnalysisCardHtml('電話', data.phone);
    if (data.phone_error) html += '<div style="background:#FFEBEE;color:#C62828;padding:6px 8px;border-radius:6px;margin:4px 0">電話：'+data.phone_error+'</div>';
    if (data.phone2) html += _numAnalysisCardHtml('電話 2', data.phone2);
    if (data.phone2_error) html += '<div style="background:#FFEBEE;color:#C62828;padding:6px 8px;border-radius:6px;margin:4px 0">電話 2：'+data.phone2_error+'</div>';
    if (data.license) html += _numAnalysisCardHtml('車牌', data.license);
    if (data.license_error) html += '<div style="background:#FFEBEE;color:#C62828;padding:6px 8px;border-radius:6px;margin:4px 0">車牌：'+data.license_error+'</div>';
    if (data.license2) html += _numAnalysisCardHtml('車牌 2', data.license2);
    if (data.license2_error) html += '<div style="background:#FFEBEE;color:#C62828;padding:6px 8px;border-radius:6px;margin:4px 0">車牌 2：'+data.license2_error+'</div>';
    box.innerHTML = html;
  } catch (e) {
    box.innerHTML = '<div style="background:#FFEBEE;color:#C62828;padding:8px;border-radius:6px">錯誤：'+e.message+'</div>';
  }
}

// ────── Tab 進階分析 ──────
async function numManualSubmit() {
  var v1 = document.getElementById('num-m1').value.trim();
  var v2 = document.getElementById('num-m2').value.trim();
  var v3 = document.getElementById('num-m3').value.trim();
  var inputs = [v1,v2,v3].filter(Boolean);
  var box = document.getElementById('num-manual-results');
  if (inputs.length === 0) {
    box.innerHTML = '<div style="background:#FFEBEE;color:#C62828;padding:8px;border-radius:6px">請至少輸入一組</div>';
    return;
  }
  box.innerHTML = '<div style="text-align:center;color:#999;padding:20px">分析中⋯</div>';
  try {
    var indiv = [];
    for (var i = 0; i < inputs.length; i++) {
      var rr = await fetch(CONSOLE_API.replace('/admin-console','') + '/numerology/analyze', {
        method:'POST',
        headers:{'Content-Type':'application/json','Authorization':'Bearer '+ADMIN_TOKEN},
        body: JSON.stringify({ input: inputs[i], mode: 'general' }),
      });
      var dd = await rr.json().catch(function(){ return null; });
      if (!rr.ok || !dd || !dd.success) {
        box.innerHTML = '<div style="background:#FFEBEE;color:#C62828;padding:8px;border-radius:6px">分析失敗（號碼 '+(i+1)+'）：'+_numExtractError(dd, rr.status)+'</div>';
        return;
      }
      indiv.push(dd.data || {});
    }
    var combined = indiv[0];
    if (inputs.length > 1) {
      var rc = await fetch(CONSOLE_API.replace('/admin-console','') + '/numerology/analyze', {
        method:'POST',
        headers:{'Content-Type':'application/json','Authorization':'Bearer '+ADMIN_TOKEN},
        body: JSON.stringify({ input: inputs.join(''), mode: 'general' }),
      });
      var dc = await rc.json().catch(function(){ return null; });
      if (!rc.ok || !dc || !dc.success) {
        box.innerHTML = '<div style="background:#FFEBEE;color:#C62828;padding:8px;border-radius:6px">合併分析失敗：'+_numExtractError(dc, rc.status)+'</div>';
        return;
      }
      combined = dc.data || {};
    }
    var html = '';
    if (inputs.length > 1) {
      html += '<p style="font-size:12px;font-weight:bold;color:#666;margin:6px 0">逐組分析：</p>';
      indiv.forEach(function(r, i){ html += _numAnalysisCardHtml('號碼 '+(i+1), r); });
      html += '<p style="font-size:12px;font-weight:bold;color:#666;margin:10px 0 6px">合併分析（含交互作用）：</p>';
    }
    html += _numAnalysisCardHtml(inputs.length > 1 ? '合併' : '分析', combined);
    box.innerHTML = html;
  } catch (e) {
    box.innerHTML = '<div style="background:#FFEBEE;color:#C62828;padding:8px;border-radius:6px">錯誤：'+e.message+'</div>';
  }
}

// ─── 智能建議視覺元件（前台同款）─────

// 5 瓣梅花 SVG（台灣新式車牌底紋）
function _numPlumBlossomSvg(color) {
  return '<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg" style="width:24px;height:24px">' +
    '<g fill="' + color + '">' +
      '<circle cx="20" cy="9" r="6.5"/>' +
      '<circle cx="30.5" cy="16" r="6.5"/>' +
      '<circle cx="26.5" cy="28" r="6.5"/>' +
      '<circle cx="13.5" cy="28" r="6.5"/>' +
      '<circle cx="9.5" cy="16" r="6.5"/>' +
    '</g>' +
    '<circle cx="20" cy="20" r="3" fill="#fde68a"/>' +
    '<g fill="#a16207" opacity="0.8">' +
      '<circle cx="20" cy="16.5" r="0.7"/><circle cx="22.5" cy="20" r="0.7"/>' +
      '<circle cx="17.5" cy="20" r="0.7"/><circle cx="20" cy="22.5" r="0.7"/>' +
    '</g>' +
  '</svg>';
}

// iPhone 整機外觀（電話建議用）
function _numPhoneGraphicHtml(number) {
  var display = number;
  if (number.length === 10) display = number.slice(0,4)+'-'+number.slice(4,7)+'-'+number.slice(7);
  else if (number.length === 9) display = number.slice(0,3)+'-'+number.slice(3,6)+'-'+number.slice(6);

  return '<div style="display:flex;justify-content:center;padding:8px 0">' +
    '<div style="position:relative;width:180px;height:360px;border-radius:35px;background:linear-gradient(180deg,#111827,#000);box-shadow:0 8px 24px rgba(0,0,0,.3);padding:6px">' +
      // 側鍵
      '<span style="position:absolute;left:-2px;top:60px;height:8px;width:4px;border-radius:2px 0 0 2px;background:#374151"></span>' +
      '<span style="position:absolute;left:-2px;top:100px;height:36px;width:4px;border-radius:2px 0 0 2px;background:#374151"></span>' +
      '<span style="position:absolute;left:-2px;top:145px;height:36px;width:4px;border-radius:2px 0 0 2px;background:#374151"></span>' +
      '<span style="position:absolute;right:-2px;top:110px;height:48px;width:4px;border-radius:0 2px 2px 0;background:#374151"></span>' +
      // 螢幕
      '<div style="position:relative;height:100%;width:100%;border-radius:30px;background:linear-gradient(180deg,#9333ea,#ec4899,#7e22ce);overflow:hidden;display:flex;flex-direction:column;align-items:center">' +
        // 動態島
        '<div style="margin-top:8px;height:20px;width:80px;border-radius:99px;background:#000;display:flex;align-items:center;justify-content:flex-end;padding-right:4px">' +
          '<span style="display:block;height:6px;width:6px;border-radius:50%;background:#374151"></span>' +
        '</div>' +
        // 狀態列
        '<div style="width:100%;padding:0 16px;margin-top:4px;display:flex;justify-content:space-between;font-size:10px;color:rgba(255,255,255,.9);font-weight:600">' +
          '<span>9:41</span><span>● ● ● ●</span>' +
        '</div>' +
        // 號碼
        '<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;width:100%;padding:0 12px">' +
          '<p style="font-size:11px;color:rgba(255,255,255,.7);margin:0 0 8px;letter-spacing:.1em">建議號碼</p>' +
          '<p style="font-size:22px;font-family:monospace;font-weight:bold;color:#fff;letter-spacing:.05em;margin:0;text-align:center;text-shadow:0 1px 2px rgba(0,0,0,.2);word-break:break-all">' + display + '</p>' +
        '</div>' +
        // Home indicator
        '<div style="margin-bottom:8px;height:4px;width:96px;border-radius:99px;background:rgba(255,255,255,.7)"></div>' +
      '</div>' +
    '</div>' +
  '</div>';
}

// 台灣新式自小客車牌（車牌建議用）
function _numPlateGraphicHtml(number) {
  var i = 0;
  while (i < number.length && /[A-Za-z]/.test(number[i])) i++;
  var prefix = number.slice(0, i);
  var suffix = number.slice(i);
  var display = (prefix && suffix) ? prefix + '-' + suffix : number;

  return '<div style="display:flex;justify-content:center;padding:8px 0">' +
    '<div style="position:relative;border-radius:6px;background:#fff;border:2px solid #d1d5db;box-shadow:0 4px 12px rgba(0,0,0,.1);padding:16px 16px 6px;width:100%;max-width:320px">' +
      // 上方螺絲孔（往中間靠攏一點點）
      '<div style="position:absolute;top:4px;left:36px;height:6px;width:28px;border-radius:99px;background:#e5e7eb"></div>' +
      '<div style="position:absolute;top:4px;right:36px;height:6px;width:28px;border-radius:99px;background:#e5e7eb"></div>' +
      // 號碼
      '<p style="text-align:center;font-size:28px;font-family:monospace;font-weight:900;letter-spacing:.15em;color:#111827;margin:0;line-height:1.1">' + display + '</p>' +
      // 三朵梅花（整列平分）
      '<div style="display:flex;align-items:center;justify-content:space-around;margin-top:2px;padding:0 8px">' +
        _numPlumBlossomSvg('#c4b5fd') + _numPlumBlossomSvg('#d1d5db') + _numPlumBlossomSvg('#c4b5fd') +
      '</div>' +
    '</div>' +
  '</div>';
}

// PIN / 一般用途（漸層大字塊）
function _numPinGraphicHtml(number, prefix) {
  var hasPrefix = prefix && number.indexOf(prefix) === 0;
  var numHtml;
  if (hasPrefix) {
    numHtml = '<span style="color:#c4b5fd">' + prefix + '</span><span style="color:#111827">' + number.slice(prefix.length) + '</span>';
  } else {
    numHtml = '<span style="color:#111827">' + number + '</span>';
  }
  return '<div style="display:flex;justify-content:center;padding:12px 0">' +
    '<div style="background:linear-gradient(135deg,#faf5ff,#fdf2f8);border:1px solid #e9d5ff;padding:14px 24px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.04)">' +
      '<p style="font-size:11px;color:#9333ea;margin:0 0 4px;text-align:center">建議號碼</p>' +
      '<p style="font-size:28px;font-family:monospace;font-weight:bold;letter-spacing:.05em;text-align:center;margin:0;word-break:break-all">' + numHtml + '</p>' +
    '</div>' +
  '</div>';
}

// 吉星 → 它能消的凶星
var NUM_GOOD_COUNTERS_BAD = {
  '天醫': ['絕命'],
  '延年': ['六煞'],
  '生氣': ['禍害', '五鬼'],
};

// ────── Tab 智能建議（30 組）──────
async function numRecommendSubmit() {
  var purpose = document.getElementById('num-rec-purpose').value;
  var length = parseInt(document.getElementById('num-rec-length').value, 10) || 10;
  var prefix = document.getElementById('num-rec-prefix').value.trim();
  // 含字母的 prefix 統一轉大寫送 API（與前台一致）
  if (/[A-Za-z]/.test(prefix)) prefix = prefix.toUpperCase();
  var box = document.getElementById('num-rec-results');

  // 從個人分析快照中推導 exclude / require — 6 個欄位整合
  var exclude = [], require = [];
  var COUNTER = { '絕命':'天醫', '五鬼':'生氣', '六煞':'延年', '禍害':'生氣' };
  if (window._numPersonalSnapshot) {
    var total = {};
    ['id','birthday','phone','phone2','license','license2'].forEach(function(k){
      var c = (window._numPersonalSnapshot[k] || {}).magnet_count || {};
      Object.keys(c).forEach(function(m){
        if (m === '中性') return;
        total[m] = (total[m] || 0) + c[m];
      });
    });
    NUM_BAD.forEach(function(b){
      if ((total[b] || 0) > 0) {
        exclude.push(b);
        var counter = COUNTER[b];
        if (counter && require.indexOf(counter) < 0) require.push(counter);
      }
    });
  }

  box.innerHTML = '<div style="text-align:center;color:#999;padding:20px">產生中⋯（首次喚醒服務約 30 秒）</div>';
  try {
    var r = await fetch(CONSOLE_API.replace('/admin-console','') + '/numerology/recommend', {
      method:'POST',
      headers:{'Content-Type':'application/json','Authorization':'Bearer '+ADMIN_TOKEN},
      body: JSON.stringify({
        purpose: purpose, length: length, prefix: prefix,
        exclude_magnets: exclude, require_magnets: require,
        top_n: 30,
      }),
    });
    var d = await r.json().catch(function(){ return null; });
    if (!r.ok || !d || !d.success) {
      console.warn('numerology /recommend failed', r.status, d);
      box.innerHTML = '<div style="background:#FFEBEE;color:#C62828;padding:8px;border-radius:6px">產生失敗：'+_numExtractError(d, r.status)+'</div>';
      return;
    }
    var recs = (d.data && d.data.recommendations) || [];
    if (recs.length === 0) {
      box.innerHTML = '<div style="text-align:center;color:#999;padding:20px">未能產生符合條件的號碼,請放寬條件再試</div>';
      return;
    }

    // 個人分析整合磁場（用來推算每組推薦能消使用者哪些凶星）
    var userTotal = {};
    if (window._numPersonalSnapshot) {
      ['id','birthday','phone','phone2','license','license2'].forEach(function(k){
        var c = (window._numPersonalSnapshot[k] || {}).magnet_count || {};
        Object.keys(c).forEach(function(m){
          if (m === '中性') return;
          userTotal[m] = (userTotal[m] || 0) + c[m];
        });
      });
    }

    // ── 建議邏輯摘要卡（前台同款）──
    var html = '';
    var detectedBad = NUM_BAD.filter(function(m){ return (userTotal[m]||0) > 0; });
    var detectedBadHtml = detectedBad.length
      ? detectedBad.map(function(m){ return '<span style="background:#fee2e2;color:#dc2626;padding:2px 8px;border-radius:99px;font-size:10px;font-weight:600">' + m + ' ' + userTotal[m] + '</span>'; }).join(' ')
      : '<span style="color:#9ca3af;font-size:10px">無凶星</span>';
    var requireGoodHtml = require.length
      ? require.map(function(m){ return '<span style="background:#dcfce7;color:#16a34a;padding:2px 8px;border-radius:99px;font-size:10px;font-weight:600">' + m + '</span>'; }).join(' ')
      : '<span style="color:#9ca3af;font-size:10px">—</span>';
    html += '<div style="background:#fff;border:1px solid #e0e0e0;border-radius:10px;padding:10px;margin-bottom:10px">' +
      '<div style="font-weight:bold;font-size:13px;color:#1f2937;margin-bottom:6px">建議邏輯（依您的個人分析）</div>' +
      '<div style="display:flex;align-items:center;gap:8px;font-size:11px;margin-bottom:4px">' +
        '<span style="color:#6b7280;min-width:60px">您的凶星：</span><span>' + detectedBadHtml + '</span>' +
      '</div>' +
      '<div style="display:flex;align-items:center;gap:8px;font-size:11px">' +
        '<span style="color:#6b7280;min-width:60px">需加強：</span><span>' + requireGoodHtml + '</span>' +
      '</div>' +
    '</div>';

    // ── 建議號碼列表 ──
    html += '<div style="display:flex;justify-content:space-between;align-items:center;margin:10px 0 6px">' +
      '<div style="font-weight:bold;font-size:13px;color:#1f2937">建議使用的號碼（共 ' + recs.length + ' 組）</div>' +
      '<button onclick="numRecommendSubmit()" style="background:#f3e8ff;color:#7c3aed;border:0;border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer">🔄 再換一組</button>' +
    '</div>';
    if (exclude.length || require.length) {
      html += '<p style="font-size:10px;color:#6b7280;margin:0 0 6px">';
      if (exclude.length) html += '已避開：' + exclude.join('、');
      if (exclude.length && require.length) html += '　|　';
      if (require.length) html += '強化：' + require.join('、');
      html += '</p>';
    }

    recs.forEach(function(r){
      var counts = r.magnet_count || {};
      var goodSum = 0, badSum = 0;
      NUM_GOOD.forEach(function(m){ goodSum += counts[m]||0; });
      NUM_BAD.forEach(function(m){ badSum += counts[m]||0; });

      // 推算這組推薦能消使用者身上哪些凶星
      var cancelled = {};
      Object.keys(NUM_GOOD_COUNTERS_BAD).forEach(function(g){
        if ((counts[g]||0) > 0) {
          NUM_GOOD_COUNTERS_BAD[g].forEach(function(b){
            if ((userTotal[b]||0) > 0) cancelled[b] = true;
          });
        }
      });
      var cancelStr = Object.keys(cancelled).join('、') || '—';
      var goodPresent = NUM_GOOD.filter(function(g){ return (counts[g]||0) > 0; }).map(function(g){ return g + '×' + counts[g]; });
      var goodStr = goodPresent.length ? goodPresent.join('、') : '—';

      // 視覺：依 purpose 切換
      var visual;
      if (purpose === 'phone') visual = _numPhoneGraphicHtml(r.number);
      else if (purpose === 'license') visual = _numPlateGraphicHtml(r.number);
      else visual = _numPinGraphicHtml(r.number, prefix);

      html += '<div style="background:#fff;border:2px solid #e9d5ff;border-radius:12px;padding:10px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,.04)">';
      // header: rank + 吉/凶 + 複製
      html += '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:4px">' +
        '<span style="background:linear-gradient(90deg,#9C27B0,#E91E63);color:#fff;font-size:11px;font-weight:bold;padding:2px 8px;border-radius:99px">#' + r.rank + '</span>' +
        '<div style="display:flex;align-items:center;gap:8px">' +
          '<span style="font-size:11px;color:#16a34a;font-weight:bold">吉 ' + goodSum + ' · 凶 ' + badSum + '</span>' +
          '<button onclick="navigator.clipboard.writeText(\\''+ r.number +'\\');this.textContent=\\'已複製\\';setTimeout(()=>this.textContent=\\'複製號碼\\',1500)" style="padding:2px 8px;font-size:10px;background:#E3F2FD;color:#1565C0;border:0;border-radius:4px;cursor:pointer">複製號碼</button>' +
        '</div>' +
      '</div>';
      // 視覺
      html += visual;
      // 推薦邏輯說明
      html += '<p style="font-size:11px;color:#374151;margin:8px 0 0;line-height:1.6">' +
        '含 <b style="color:#15803d">' + goodStr + '</b>';
      if (Object.keys(cancelled).length > 0) {
        html += ',以消除您身上的 <b style="color:#dc2626">' + cancelStr + '</b>';
      }
      html += '</p>';
      // 8 磁場 tag
      html += '<div style="display:flex;flex-wrap:wrap;gap:3px;margin-top:6px">';
      NUM_ALL.forEach(function(m){
        var n = counts[m] || 0;
        if (n === 0) return;
        var info = NUM_INFO[m];
        html += '<span style="background:'+info.color+'20;color:'+info.color+';padding:1px 6px;border-radius:3px;font-size:10px;font-weight:600">'+m+' ×'+n+'</span>';
      });
      html += '</div>';
      if (r.duplicate_marks && r.duplicate_marks.length) {
        html += '<div style="font-size:10px;color:#6A1B9A;margin-top:4px">'+r.duplicate_marks.join('、')+'</div>';
      }
      html += '</div>';
    });
    box.innerHTML = html;
  } catch (e) {
    box.innerHTML = '<div style="background:#FFEBEE;color:#C62828;padding:8px;border-radius:6px">錯誤：'+e.message+'</div>';
  }
}

// === 詢價工單（admin/agent 端）===
async function loadQuoteRequests(status) {
  var box = document.getElementById('quote-list');
  if (!box) return;
  // active filter UI
  document.querySelectorAll('.qr-filter').forEach(function(btn){
    if (btn.dataset.status === status) {
      btn.style.background = '#1565C0'; btn.style.color = '#fff'; btn.style.borderColor = '#1565C0';
    } else {
      btn.style.background = '#fff'; btn.style.color = '#333'; btn.style.borderColor = '#ddd';
    }
  });
  box.innerHTML = '<div style="padding:20px;text-align:center;color:#999">載入中...</div>';
  try {
    var qs = status ? ('?status=' + encodeURIComponent(status)) : '';
    var r = await fetch(CONSOLE_API + '/agent/quote-requests' + qs, { headers: consoleHeaders(false) });
    var d = await r.json();
    var rows = d.data || [];
    if (rows.length === 0) {
      box.innerHTML = '<div style="padding:30px;text-align:center;color:#999;font-size:13px">沒有符合條件的詢價工單</div>';
      return;
    }
    var html = '';
    rows.forEach(function(qr) {
      var statColor = {
        pending: '#E65100', in_progress: '#1565C0', quoted: '#2E7D32',
        completed: '#666', cancelled: '#D32F2F'
      }[qr.status] || '#666';
      var statLabel = {
        pending: '待處理', in_progress: '處理中', quoted: '已回報', completed: '已結案', cancelled: '已取消'
      }[qr.status] || qr.status;
      html += '<div style="border:1px solid #e0e0e0;border-radius:8px;padding:12px;margin-bottom:10px;background:#fff">';
      html += '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">';
      html += '<div>';
      html += '<span style="display:inline-block;padding:2px 8px;font-size:11px;font-weight:600;color:#fff;background:' + statColor + ';border-radius:4px">' + statLabel + '</span>';
      html += ' <b style="margin-left:6px">' + (qr.customer_name || '') + '</b>';
      if (qr.customer_phone) html += ' <span style="color:#999;font-size:11px">' + qr.customer_phone + '</span>';
      if (qr.vehicle_plate) html += ' <span style="color:#1565C0;font-family:monospace;margin-left:4px">' + qr.vehicle_plate + '</span>';
      if (qr.use_existing_policy) html += ' <span style="color:#0288D1;font-size:10px;background:#E3F2FD;padding:1px 6px;border-radius:3px">與原保單相同</span>';
      html += '<div style="font-size:11px;color:#666;margin-top:2px">送出：' + (qr.submitted_at ? qr.submitted_at.replace('T',' ').substring(0,16) : '-')
            + (qr.assigned_admin_name ? ' · 處理人：' + qr.assigned_admin_name : '') + '</div>';
      html += '</div>';
      html += '<button onclick="openQuoteRespond(\\'' + qr.id + '\\')" style="padding:6px 14px;font-size:12px;background:#1565C0;color:#fff;border:0;border-radius:6px;cursor:pointer">處理 / 回報報價</button>';
      html += '</div>';
      // 內容摘要
      if (qr.desired_items && qr.desired_items.length) {
        html += '<div style="margin-top:6px;font-size:11px;color:#666">勾選項目：';
        qr.desired_items.forEach(function(it){
          html += '<span style="display:inline-block;background:#F5F5F5;padding:2px 6px;border-radius:3px;margin:1px">'
                + it.name + (it.limit ? ' ' + (it.limit / 10000) + '萬' : '') + '</span>';
        });
        html += '</div>';
      }
      var meta = [];
      if (qr.driver_age != null) meta.push('駕駛年齡 ' + qr.driver_age);
      if (qr.claims_count_3y != null) meta.push('3 年出險 ' + qr.claims_count_3y + ' 次');
      if (qr.surcharge_pct != null) meta.push('已知加費 ' + qr.surcharge_pct + '%');
      if (meta.length) html += '<div style="margin-top:4px;font-size:11px;color:#666">' + meta.join(' · ') + '</div>';
      if (qr.notes) html += '<div style="margin-top:4px;font-size:11px;color:#888;background:#FFF8E1;padding:4px 8px;border-radius:4px">📝 ' + qr.notes + '</div>';
      // 已加的報價列表
      if (qr.responses && qr.responses.length) {
        html += '<div style="margin-top:8px;border-top:1px solid #f0f0f0;padding-top:8px">';
        html += '<div style="font-size:11px;color:#666;margin-bottom:4px">已加 ' + qr.responses.length + ' 家報價：</div>';
        qr.responses.forEach(function(rsp) {
          html += '<div style="background:' + (rsp.is_recommended?'#FFF3E0':'#F5F5F5')
                + ';padding:4px 8px;border-radius:4px;margin:2px 0;display:flex;justify-content:space-between;font-size:12px">';
          html += '<span><b>' + rsp.insurer_name + '</b>'
                + (rsp.is_recommended ? ' <span style="color:#E65100">⭐</span>' : '') + '</span>';
          html += '<span><b>$' + Number(rsp.quoted_premium).toLocaleString() + '</b>';
          html += ' <button onclick="deleteQuoteResponse(\\'' + rsp.id + '\\',\\'' + qr.id + '\\')" style="margin-left:6px;background:#FFEBEE;color:#C62828;border:0;border-radius:3px;padding:1px 6px;font-size:10px;cursor:pointer">刪</button></span>';
          html += '</div>';
        });
        html += '</div>';
      }
      html += '</div>';
    });
    box.innerHTML = html;
  } catch (e) {
    box.innerHTML = '<div style="color:#D32F2F;padding:20px">載入失敗：' + e.message + '</div>';
  }
}

window._respondingReqId = '';

function openQuoteRespond(reqId) {
  window._respondingReqId = reqId;
  // 先重置欄位
  ['qrsp-insurer','qrsp-premium','qrsp-notes','qrsp-valid-until','qrsp-coverage'].forEach(function(id){
    var el = document.getElementById(id);
    if (el) el.value = '';
  });
  document.getElementById('qrsp-recommend').checked = false;
  document.getElementById('quote-respond-modal').style.display = 'flex';
}

function closeQuoteRespond() {
  document.getElementById('quote-respond-modal').style.display = 'none';
  window._respondingReqId = '';
}

async function submitQuoteResponse() {
  var rid = window._respondingReqId;
  if (!rid) return;
  var insurer = document.getElementById('qrsp-insurer').value.trim();
  var premium = document.getElementById('qrsp-premium').value;
  if (!insurer || !premium) {
    showMsg('qrsp-msg','err','請填寫保險公司與保費'); return;
  }
  var coverageRaw = document.getElementById('qrsp-coverage').value.trim();
  var coverage = [];
  if (coverageRaw) {
    coverageRaw.split('\\n').forEach(function(line){
      line = line.trim();
      if (!line) return;
      // 格式：項目名稱|保額|保費（用 | 分割）
      var parts = line.split('|').map(function(s){return s.trim();});
      var obj = { name: parts[0] };
      if (parts[1]) obj.limit = parseInt(parts[1]) * 10000;  // 輸入「萬」單位
      if (parts[2]) obj.premium = parseFloat(parts[2]);
      coverage.push(obj);
    });
  }
  var body = {
    insurer_name: insurer,
    quoted_premium: parseFloat(parseThousand(premium) || premium),
    coverage_details: coverage,
    valid_until: document.getElementById('qrsp-valid-until').value || null,
    notes: document.getElementById('qrsp-notes').value.trim() || null,
    is_recommended: document.getElementById('qrsp-recommend').checked,
  };
  try {
    var r = await fetch(CONSOLE_API + '/quote-requests/' + rid + '/responses', {
      method: 'POST', headers: consoleHeaders(true), body: JSON.stringify(body),
    });
    var d = await r.json();
    if (d.success) {
      showMsg('qrsp-msg','ok','已加入報價');
      setTimeout(function(){ closeQuoteRespond(); loadQuoteRequests(''); }, 800);
    } else {
      showMsg('qrsp-msg','err','失敗：' + (d.message || ''));
    }
  } catch(e) {
    showMsg('qrsp-msg','err','錯誤：' + e.message);
  }
}

async function markQuoteRequestStatus(status) {
  var rid = window._respondingReqId;
  if (!rid) return;
  if (status === 'quoted') {
    if (!confirm('標記為「已回報」會通知客戶（站內 + LINE + Email），確定？')) return;
  }
  try {
    var r = await fetch(CONSOLE_API + '/quote-requests/' + rid, {
      method: 'PATCH', headers: consoleHeaders(true), body: JSON.stringify({ status: status }),
    });
    var d = await r.json();
    if (d.success) {
      showMsg('qrsp-msg','ok','狀態已更新');
      setTimeout(function(){ closeQuoteRespond(); loadQuoteRequests(''); }, 600);
    } else {
      showMsg('qrsp-msg','err','失敗：' + (d.message || ''));
    }
  } catch(e) {
    showMsg('qrsp-msg','err','錯誤：' + e.message);
  }
}

async function deleteQuoteResponse(rspId, reqId) {
  if (!confirm('確定刪除此筆報價？')) return;
  try {
    await fetch(CONSOLE_API + '/quote-responses/' + rspId, {
      method: 'DELETE', headers: consoleHeaders(false),
    });
    loadQuoteRequests('');
  } catch(e) { alert('刪除失敗：' + e.message); }
}

// === 業務員待辦提醒中心 ===
window._todoData = null;
window._todoActiveBucket = 'today';

async function loadAgentTasks() {
  var sumEl = document.getElementById('todo-summary');
  if (sumEl) sumEl.textContent = LANG==='en' ? 'Loading...' : '載入中⋯';
  try {
    var r = await fetch(CONSOLE_API + '/agent/tasks', { headers: consoleHeaders(false) });
    var d = await r.json();
    if (!d.success) {
      if (sumEl) sumEl.textContent = (LANG==='en'?'Failed: ':'失敗：') + (d.message || '');
      return;
    }
    window._todoData = d.data;
    var c = d.data.counts || {};
    if (sumEl) {
      sumEl.textContent = (LANG==='en'
        ? `截至 ${d.data.as_of}：總 ${(c.overdue||0)+(c.today||0)+(c.next_3d||0)+(c.next_7d||0)+(c.next_30d||0)} 項`
        : `截至 ${d.data.as_of}：共 ${(c.overdue||0)+(c.today||0)+(c.next_3d||0)+(c.next_7d||0)+(c.next_30d||0)} 項待辦`);
    }
    // 更新 tab 計數
    document.querySelectorAll('.todo-tab').forEach(function(btn){
      var b = btn.dataset.bucket;
      var cnt = c[b] || 0;
      var span = btn.querySelector('.todo-cnt');
      if (span) span.textContent = cnt > 0 ? '(' + cnt + ')' : '';
      // 高亮逾期 / 當天
      if (b === 'overdue' && cnt > 0) {
        btn.style.background = '#FFEBEE'; btn.style.borderColor = '#EF9A9A'; btn.style.color = '#C62828';
      } else if (b === 'today' && cnt > 0) {
        btn.style.background = '#FFF3E0'; btn.style.borderColor = '#FFB74D'; btn.style.color = '#E65100';
      } else {
        btn.style.background = '#fff'; btn.style.borderColor = '#ddd'; btn.style.color = '#333';
      }
    });
    // 預設展開：有逾期就先看逾期，否則看當天
    var firstBucket = (c.overdue > 0) ? 'overdue' : (c.today > 0 ? 'today' : 'next_30d');
    switchTodoBucket(window._todoActiveBucket || firstBucket);
  } catch(e) {
    if (sumEl) sumEl.textContent = (LANG==='en'?'Error: ':'錯誤：') + e.message;
  }
}

function switchTodoBucket(bucket) {
  window._todoActiveBucket = bucket;
  // active tab 視覺
  document.querySelectorAll('.todo-tab').forEach(function(btn){
    if (btn.dataset.bucket === bucket) {
      btn.style.fontWeight = '700';
      btn.style.borderWidth = '2px';
    } else {
      btn.style.fontWeight = '400';
      btn.style.borderWidth = '1px';
    }
  });
  var data = window._todoData;
  if (!data) return;
  var items = (data.buckets || {})[bucket] || [];
  var box = document.getElementById('todo-list');
  if (items.length === 0) {
    box.innerHTML = '<div style="padding:20px;text-align:center;color:#999;font-size:12px">' + (LANG==='en' ? 'No items in this bucket' : '此區段沒有待辦事項') + '</div>';
    return;
  }
  var html = '<table style="width:100%;font-size:12px"><thead><tr style="background:#F5F5F5"><th style="padding:6px">類別</th><th style="padding:6px">客戶</th><th style="padding:6px">車牌 / 保單</th><th style="padding:6px">到期日</th><th style="padding:6px">剩餘</th><th style="padding:6px">行事曆</th></tr></thead><tbody>';
  items.forEach(function(it) {
    var typeColor = it.type === 'inspection' ? '#0288D1' : (it.type === 'compulsory_renewal' ? '#E65100' : '#1565C0');
    var daysColor = it.days_left < 0 ? '#C62828' : (it.days_left <= 3 ? '#E65100' : '#666');
    var daysText = it.days_left < 0 ? ('已逾期 ' + Math.abs(it.days_left) + ' 天') : (it.days_left === 0 ? '今天' : ('剩 ' + it.days_left + ' 天'));
    var calTitle, calDesc, uid;
    if (it.type === 'inspection') {
      calTitle = '驗車到期 — ' + (it.plate || '');
      calDesc = '客戶：' + it.customer_name + (it.customer_phone ? '（' + it.customer_phone + '）' : '') + '\\n車牌：' + (it.plate || '');
      uid = 'bopinan-inspection-' + it.id + '@bopinan.ego-intl.com';
    } else if (it.type === 'compulsory_renewal') {
      calTitle = '強制險到期 — ' + (it.insurer || '') + ' ' + (it.policy_number || '');
      calDesc = '客戶：' + it.customer_name + '\\n車牌：' + (it.plate || '') + '\\n強制險保單號：' + (it.policy_number || '');
      uid = 'bopinan-compulsory-' + it.id + '@bopinan.ego-intl.com';
    } else {
      calTitle = '保單到期 — ' + (it.insurer || '') + ' ' + (it.policy_number || '');
      calDesc = '客戶：' + it.customer_name + '\\n車牌：' + (it.plate || '') + '\\n保單號：' + (it.policy_number || '');
      uid = 'bopinan-policy-' + it.id + '@bopinan.ego-intl.com';
    }
    html += '<tr style="border-bottom:1px solid #f0f0f0">';
    html += '<td style="padding:6px"><span style="color:' + typeColor + ';font-weight:600">' + it.type_label + '</span></td>';
    html += '<td style="padding:6px"><b>' + (it.customer_name || '') + '</b>' + (it.customer_phone ? '<br><span style="color:#999;font-size:10px">' + it.customer_phone + '</span>' : '') + '</td>';
    html += '<td style="padding:6px">' + (it.plate || '-') + (it.policy_number ? '<br><span style="color:#999;font-size:10px;font-family:monospace">' + it.policy_number + '</span>' : '') + '</td>';
    html += '<td style="padding:6px">' + it.due_date + '</td>';
    html += '<td style="padding:6px"><b style="color:' + daysColor + '">' + daysText + '</b></td>';
    html += '<td style="padding:6px;white-space:nowrap">' + _calBtnHtml(calTitle, it.due_date, calDesc, uid) + '</td>';
    html += '</tr>';
  });
  html += '</tbody></table>';
  box.innerHTML = html;
}

// === 整合 CSV 匯入 / 匯出 ===
// 點「上傳大量匯入」→ 跳出說明 modal，使用者勾「我已了解」後才能選檔
function onCsvImportClick() {
  var cb = document.getElementById('csv-confirm-cb');
  if (cb) cb.checked = false;
  onCsvConfirmToggle();
  document.getElementById('csv-import-modal').style.display = 'flex';
}
function closeCsvImportModal() {
  document.getElementById('csv-import-modal').style.display = 'none';
}
function onCsvConfirmToggle() {
  var cb = document.getElementById('csv-confirm-cb');
  var btn = document.getElementById('csv-pick-file-btn');
  if (!cb || !btn) return;
  if (cb.checked) {
    btn.disabled = false;
    btn.style.cursor = 'pointer';
    btn.style.opacity = '1';
  } else {
    btn.disabled = true;
    btn.style.cursor = 'not-allowed';
    btn.style.opacity = '0.5';
  }
}

async function downloadUnifiedCsv() {
  showMsg('csv-msg', 'ok', LANG==='en' ? 'Preparing CSV...' : '正在準備 CSV…');
  try {
    var r = await fetch(CONSOLE_API + '/export.csv', { headers: consoleHeaders(false) });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    var blob = await r.blob();
    var ts = new Date().toISOString().slice(0,16).replace(/[:T-]/g,'');
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = 'bopinan_export_' + ts + '.csv';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function(){ URL.revokeObjectURL(url); }, 1000);
    showMsg('csv-msg', 'ok', LANG==='en' ? 'Downloaded.' : '已下載。');
  } catch(e) {
    showMsg('csv-msg', 'err', (LANG==='en'?'Failed: ':'下載失敗：') + e.message);
  }
}

async function downloadCsvTemplate() {
  try {
    var r = await fetch(CONSOLE_API + '/export-template.csv', { headers: consoleHeaders(false) });
    var blob = await r.blob();
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = 'bopinan_csv_template.csv';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function(){ URL.revokeObjectURL(url); }, 1000);
  } catch(e) {
    showMsg('csv-msg', 'err', (LANG==='en'?'Failed: ':'下載失敗：') + e.message);
  }
}

async function onCsvFileChosen(input) {
  var file = input.files && input.files[0];
  if (!file) return;
  // 選好檔案 → 關掉說明 modal
  closeCsvImportModal();
  var doDryRun = confirm(LANG==='en'
    ? 'Dry-run first? (Recommended)\\n\\nOK = Try without saving (preview)\\nCancel = Save directly'
    : '是否先試跑（dry-run）？\\n\\n確定 = 試跑（不存檔）\\n取消 = 直接寫入');
  showMsg('csv-msg', 'ok', LANG==='en' ? 'Uploading...' : '上傳中⋯');
  document.getElementById('csv-result').innerHTML = '';

  var fd = new FormData();
  fd.append('file', file);
  fd.append('dry_run', doDryRun ? 'true' : 'false');

  try {
    var r = await fetch(CONSOLE_API + '/import.csv', {
      method:'POST',
      headers:{'Authorization':'Bearer ' + ADMIN_TOKEN},
      body: fd,
    });
    var d = await r.json();
    var s = d.data || {};
    var html = '<div style="background:'+(s.committed?'#E8F5E9':'#FFF3E0')+';padding:8px;border-radius:6px;border-left:3px solid '+(s.committed?'#2E7D32':'#E65100')+'">';
    html += '<b>' + (d.message || '') + '</b><br>';
    html += '處理列數：<b>' + (s.rows_total||0) + '</b>　|　';
    html += '客戶 +' + (s.customers_created||0) + ' / 更新 ' + (s.customers_updated||0) + '　|　';
    html += '車輛 +' + (s.vehicles_created||0) + ' / 更新 ' + (s.vehicles_updated||0) + '　|　';
    html += '保單 +' + (s.policies_created||0) + ' / 更新 ' + (s.policies_updated||0);
    if (s.errors && s.errors.length) {
      html += '<br><br><b style="color:#D32F2F">錯誤 (' + s.errors.length + ' 筆)：</b><ul style="margin:4px 0;padding-left:20px;font-size:11px">';
      s.errors.slice(0, 50).forEach(function(e){
        html += '<li>第 ' + e.row + ' 列：' + e.msg + '</li>';
      });
      if (s.errors.length > 50) html += '<li>...（還有 ' + (s.errors.length - 50) + ' 筆未顯示）</li>';
      html += '</ul>';
    }
    html += '</div>';
    document.getElementById('csv-result').innerHTML = html;
    showMsg('csv-msg', s.committed ? 'ok' : 'err', d.message || '');
    // 重整列表
    if (s.committed) {
      if (typeof loadVehicles === 'function') loadVehicles();
      if (typeof loadPolicies === 'function') loadPolicies();
      if (typeof loadCustomerList === 'function') loadCustomerList();
    }
  } catch(e) {
    showMsg('csv-msg', 'err', (LANG==='en'?'Upload failed: ':'上傳失敗：') + e.message);
  } finally {
    input.value = '';  // 讓同一檔案可以再選一次觸發
  }
}

// === 客戶 cell hover popover：滑到客戶欄就浮現該客戶所有保單 / 車輛 ===
// 共用 tooltip 容器（僅一個，重複利用）
function _ensureCustHoverTip() {
  if (document.getElementById('cust-hover-tip')) return;
  var t = document.createElement('div');
  t.id = 'cust-hover-tip';
  t.style.cssText = 'position:fixed;display:none;z-index:99999;background:#fff;color:#333;padding:10px 14px;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,.25);font-size:12px;max-width:440px;border:1px solid #ccc;pointer-events:none;line-height:1.5';
  document.body.appendChild(t);
}

function _renderCustPolicyTip(uid) {
  var items = (window._lastPolicies || []).filter(function(p){ return p.user_id === uid; });
  if (items.length === 0) return '<i style="color:#999">查無此客戶保單</i>';
  var html = '<div style="font-weight:bold;color:#1565C0;margin-bottom:6px;border-bottom:1px solid #eee;padding-bottom:4px">'
    + (items[0].customer_name || '') + ' · 共 ' + items.length + ' 張保單</div>';
  items.forEach(function(p){
    html += '<div style="padding:5px 0;border-top:1px dashed #f0f0f0">';
    html += '<b style="font-family:monospace">' + (p.policy_number||'') + '</b> · ' + (p.insurer_name||'')
         + ' · <span style="color:' + (p.status==='active'?'#2E7D32':p.status==='expired'?'#D32F2F':'#E65100') + '">' + (p.status||'') + '</span>';
    html += '<br><span style="color:#666;font-size:11px">任意險：' + (p.start_date||'') + (p.start_time?' '+p.start_time:'')
         + ' ~ ' + (p.end_date||'') + (p.end_time?' '+p.end_time:'') + '</span>';
    if (p.compulsory_insurer_name || p.compulsory_policy_number) {
      html += '<br><span style="color:#E65100;font-size:11px">強制險：' + (p.compulsory_insurer_name||'')
           + ' ' + (p.compulsory_policy_number||'')
           + (p.compulsory_start_date ? ' / ' + p.compulsory_start_date + ' ~ ' + (p.compulsory_end_date||'') : '')
           + '</span>';
    }
    if (p.vehicle_plate) html += '<br><span style="color:#666;font-size:11px">車輛：' + p.vehicle_plate + '</span>';
    if (p.total_premium) html += '<br><span style="color:#666;font-size:11px">保費：$' + Number(p.total_premium).toLocaleString() + '</span>';
    html += '</div>';
  });
  return html;
}

function _renderCustVehicleTip(uid) {
  var items = (window._lastVehicles || []).filter(function(v){ return v.user_id === uid; });
  if (items.length === 0) return '<i style="color:#999">查無此客戶車輛</i>';
  var html = '<div style="font-weight:bold;color:#1565C0;margin-bottom:6px;border-bottom:1px solid #eee;padding-bottom:4px">'
    + (items[0].customer_name || '') + ' · 共 ' + items.length + ' 輛車</div>';
  items.forEach(function(v){
    html += '<div style="padding:5px 0;border-top:1px dashed #f0f0f0">';
    html += '<b>' + (v.plate_number||'') + '</b> · ' + (v.brand||'') + ' ' + (v.model||'') + ' · ' + (v.vehicle_type||'-');
    html += '<br><span style="color:#666;font-size:11px">' + (v.year||'?') + (v.manufacture_month?'/'+String(v.manufacture_month).padStart(2,'0'):'')
         + ' · ' + (v.color||'') + ' · ' + (v.engine_cc?v.engine_cc+'cc':'') + ' · ' + (v.fuel_type||'') + '</span>';
    if (v.registration_expiry) html += '<br><span style="color:#666;font-size:11px">行照到期：' + v.registration_expiry + '</span>';
    if (v.vin) html += '<br><span style="color:#999;font-size:10px;font-family:monospace">VIN: ' + v.vin + '</span>';
    html += '</div>';
  });
  return html;
}

document.addEventListener('mouseover', function(e){
  var cell = e.target.closest('[data-hover-cust]');
  if (!cell) return;
  if (e.relatedTarget && cell.contains(e.relatedTarget)) return; // 還在 cell 內部移動
  _ensureCustHoverTip();
  var uid = cell.dataset.hoverCust;
  var type = cell.dataset.hoverType;
  var html = (type === 'policy') ? _renderCustPolicyTip(uid)
           : (type === 'vehicle') ? _renderCustVehicleTip(uid)
           : '';
  if (!html) return;
  var t = document.getElementById('cust-hover-tip');
  t.innerHTML = html;
  t.style.display = 'block';
});

document.addEventListener('mousemove', function(e){
  var t = document.getElementById('cust-hover-tip');
  if (!t || t.style.display === 'none') return;
  var w = t.offsetWidth, h = t.offsetHeight;
  var x = e.clientX + 14;
  var y = e.clientY + 14;
  if (x + w > window.innerWidth - 8) x = e.clientX - w - 14;
  if (y + h > window.innerHeight - 8) y = e.clientY - h - 14;
  if (x < 4) x = 4;
  if (y < 4) y = 4;
  t.style.left = x + 'px';
  t.style.top = y + 'px';
});

document.addEventListener('mouseout', function(e){
  var cell = e.target.closest('[data-hover-cust]');
  if (!cell) return;
  if (e.relatedTarget && cell.contains(e.relatedTarget)) return; // 還在 cell 內部
  var t = document.getElementById('cust-hover-tip');
  if (t) t.style.display = 'none';
});

function getInsurerValue(selectId, otherInputId) {
  var sel = document.getElementById(selectId);
  if (!sel) return '';
  var v = sel.value || '';
  if (v === '__other__' && otherInputId) {
    var other = document.getElementById(otherInputId);
    return other ? (other.value || '').trim() : '';
  }
  return v;
}

function onInsurerChange(selectId, otherInputId) {
  var sel = document.getElementById(selectId);
  var other = otherInputId ? document.getElementById(otherInputId) : null;
  if (!sel || !other) return;
  if (sel.value === '__other__') {
    other.style.display = 'block';
    other.focus();
  } else {
    other.style.display = 'none';
    other.value = '';
  }
}

// === 民國年顯示輔助 ===
// 西元 → 民國（保留月日 + 時:分）。
// 範例：'2026-03-14' → '民國 115 年 (2026 年) 03 月 14 日'
//       '2026-03-14T12:00' → '民國 115 年 (2026 年) 03 月 14 日 12:00'
function rocLabel(val) {
  if (!val) return '';
  var s = String(val);
  // 拆 datetime-local: 2026-03-14T12:00 → datePart=2026-03-14, timePart=12:00
  var hasT = s.indexOf('T') >= 0;
  var datePart = hasT ? s.split('T')[0] : s;
  var timePart = hasT ? s.split('T')[1] : '';
  var p = datePart.split('-');
  if (p.length < 2) return '';
  var y = parseInt(p[0]);
  if (isNaN(y) || y < 1912) return '';
  var roc = y - 1911;
  var mm = (p[1] || '').padStart(2, '0');
  var out = '民國 ' + roc + ' 年 (' + y + ' 年) ' + mm + ' 月';
  if (p.length >= 3 && p[2]) out += ' ' + p[2].padStart(2, '0') + ' 日';
  if (timePart) out += ' ' + timePart.slice(0, 5);  // 只取 HH:mm，丟掉秒
  return out;
}

// 取得 date input + 配對的 time input 值；time 空字串視為 null
// 日期/時間採分離 input（type=date 與 type=time），time 用 lang=en-GB 強制 24 小時
function _readDatePair(dateInputId) {
  var d = document.getElementById(dateInputId);
  var t = document.getElementById(dateInputId + '-time');
  return {
    date: d && d.value ? d.value : null,
    time: t && t.value ? t.value.slice(0, 5) : null,
  };
}
function _writeDatePair(dateInputId, dateVal, timeVal) {
  var d = document.getElementById(dateInputId);
  var t = document.getElementById(dateInputId + '-time');
  if (d) d.value = dateVal || '';
  if (t) t.value = timeVal ? String(timeVal).slice(0, 5) : '';
}

// 需要顯示民國年小標的 input id（行照欄位 + 任意險 + 強制險，含手動 modal 與編輯 modal）
var ROC_FIELDS = [
  've-year-month','ve-reg-date','ve-reissue-date','ve-expiry','ve-window-start','ve-window-end',
  'p-start','p-end','pe-start','pe-end',
  'p-cstart','p-cend','pe-cstart','pe-cend'
];

function _attachRocLabel(inputId) {
  var inp = document.getElementById(inputId);
  if (!inp) return;
  var lblId = inputId + '-roc';
  if (document.getElementById(lblId)) return; // 已附加過
  var lbl = document.createElement('small');
  lbl.id = lblId;
  lbl.style.cssText = 'display:block;color:#1565C0;font-size:11px;margin-top:3px;font-weight:600';
  // 若是 type=date 且有 companion -time 兄弟（由 inputId+'-time' 命名），把 label 放在最外層
  // 父元素之後，這樣可以涵蓋兩個 input
  var parent = inp.parentElement;
  parent.parentElement.insertBefore(lbl, parent.nextSibling);
  var timeInp = document.getElementById(inputId + '-time');
  function refresh() {
    var dateVal = inp.value || '';
    var timeVal = timeInp ? (timeInp.value || '') : '';
    var combined = dateVal + (timeVal ? 'T' + timeVal : '');
    lbl.textContent = rocLabel(combined) || '';
  }
  inp.addEventListener('input', refresh);
  inp.addEventListener('change', refresh);
  if (timeInp) {
    timeInp.addEventListener('input', refresh);
    timeInp.addEventListener('change', refresh);
  }
  refresh();
}

function initRocLabels() {
  ROC_FIELDS.forEach(_attachRocLabel);
}

// 程式化設值（如 _showEditForm / OCR 自動填）後手動更新標籤（addEventListener 不會自動觸發）
function refreshRocLabels() {
  ROC_FIELDS.forEach(function(id){
    var inp = document.getElementById(id);
    var lbl = document.getElementById(id + '-roc');
    if (!inp || !lbl) return;
    var timeInp = document.getElementById(id + '-time');
    var dateVal = inp.value || '';
    var timeVal = timeInp ? (timeInp.value || '') : '';
    var combined = dateVal + (timeVal ? 'T' + timeVal : '');
    lbl.textContent = rocLabel(combined) || '';
  });
}

document.addEventListener('DOMContentLoaded', initRocLabels);

// --- i18n (中/英切換) ---
var LANG = localStorage.getItem('admin_lang') || 'zh';
var I18N = {
  zh: {
    header_title: 'BOPINAN — 管理控制台',
    btn_logout: '登出',
    login_title: '管理員登入',
    login_hint: '使用管理員帳號密碼登入',
    lbl_username: '帳號',
    lbl_password: '密碼',
    ph_username: 'admin',
    ph_password: '密碼',
    btn_login: '登入',
    tab_vehicles: '車輛 / 行照',
    tab_policies: '保單管理',
    tab_claims: '理賠申請',
    tab_accidents: '事故照片',
    tab_overview: '資料總覽',
    tab_quotes: '詢價工單',
    h_quote_requests: '詢價工單',
    tab_agents: '業務員管理',
    tab_assign: '客戶分配',
    tab_logs: '操作日誌',
    ph_search: '搜尋：客戶姓名 / 電話 / Email / 車牌 / 保單號 / 理賠號',
    btn_search: '搜尋',
    btn_clear: '清除',
    qs_searching: '搜尋中…',
    qs_no_result: '查無資料',
    qs_failed: '搜尋失敗',
    qs_error: '搜尋錯誤',
    qs_view: '查看 →',
    qs_section_customers: '客戶',
    qs_section_vehicles: '車輛',
    qs_section_policies: '保單',
    qs_section_claims: '理賠',
    qs_tag_customer: '客戶',
    qs_tag_vehicle: '車輛',
    qs_tag_policy: '保單',
    qs_tag_claim: '理賠',
    qs_lbl_customer: '客戶: ',
    idle_warn_title: '⚠ 即將自動登出 - ',
    idle_logout_msg: '閒置超過 10 分鐘，已自動登出。',
    todo_title: '待辦提醒中心（保單 / 驗車到期）',
    btn_todo_refresh: '🔄 重新整理',
    csv_title: '資料匯入 / 匯出（客戶+車輛+保單一張表）',
    btn_csv_export: '⬇ 下載完整資料',
    btn_csv_template: '📥 下載空白範本',
    btn_csv_import: '⬆ 上傳大量匯入',
    csv_import_title: '⚠️ 上傳 CSV 大量匯入 — 上傳前必讀',
    csv_step_1: '必須使用本平台 CSV 範本格式（中文表頭）。如尚未下載，請點下方「📥 下載空白範本」按鈕。',
    csv_step_2: '表頭欄位請保持不動；範本第 2 列為示範資料，填新資料時可整列刪除。',
    csv_step_3: '配對規則（idempotent，可重複上傳同檔案不會重複建立）',
    csv_step_4: '建議第一次先選「試跑（dry-run）」確認解析無誤再正式匯入；任一列失敗整批會自動 rollback。',
    csv_step_5: '業務員只能匯入自己負責的客戶；嘗試匯入到他人客戶會被拒絕並列為錯誤。',
    csv_modal_dl_hint: '點此下載最新格式範本',
    csv_understood: '我已了解上述說明，並確認使用本平台範本格式的 CSV 檔',
    btn_csv_pick_file: '⬆ 選擇 CSV 檔案上傳',
    // Customer bar
    cur_customer_label: '操作客戶（新增車輛/保單時套用）：',
    btn_refresh_customers: '重新整理客戶清單',
    // Vehicles tab
    h_upload_reg: '上傳行照（自動辨識）',
    upload_reg_hint: '選擇車輛型式後上傳行照圖片，系統將自動辨識所有車輛資料（含驗車到期日）。',
    lbl_vehicle_type: '車輛型式（監理分類）',
    lbl_existing_vehicle: '現有車輛（更新）/ 新車',
    opt_new_vehicle: '+ 新增車輛',
    lbl_reg_image: '行照圖片 (JPG/PNG)',
    btn_upload_reg: '上傳行照',
    btn_ocr_reg: 'AI 辨識行照',
    btn_ocr_autofill: 'AI 辨識自動填入',
    msg_uploading: '上傳中...',
    msg_processing: '處理中...',
    h_ocr_result: 'AI 辨識結果',
    h_ocr_result_short: '辨識結果',
    ocr_hint_edit: '點擊各欄位值可直接編輯修正',
    lbl_customer_name: '客戶姓名',
    lbl_customer_email: '客戶 Email',
    lbl_plate: '車牌號碼',
    lbl_brand: '廠牌',
    lbl_model: '車型',
    lbl_year: '出廠年份',
    lbl_year_month: '出廠年月',
    lbl_orig_reg_date: '原發照日期',
    lbl_reissue_date: '換補照日期',
    lbl_inspection_window: '驗車期間',
    hint_inspection_window: '到期日前 30 天 ~ 後 30 天',
    lbl_color: '顏色',
    lbl_cc: '排氣量 (cc)',
    lbl_vin: '車身號碼',
    lbl_reg_date: '發照日期',
    lbl_expiry_date: '驗車到期日',
    lbl_fuel: '燃料種類',
    ph_customer_name: '此車輛所屬客戶（修改會更新客戶資料）',
    ph_customer_email: '設定後客戶可用此 Email 登入並看到自己的車輛保單',
    ph_customer_email_short: '設定後客戶可用此 Email 登入並看到此保單',
    reg_upload_direct_title: '行照圖片（直接上傳到此車輛）',
    btn_save_vehicle: '儲存車輛資料',
    btn_add_another_vehicle: '+ 新增此客戶另一輛車',
    btn_add_new_vehicle: '+ 新增車輛',
    btn_add_new_vehicle_manual: '+ 新增車輛（手動）',
    btn_add_new_vehicle_ocr: '+ 新增車輛（上傳行照）',
    btn_done_close: '完成 / 關閉',
    btn_new_customer: '+ 新增客戶',
    cc_title: '選擇 / 新增客戶',
    cc_hint: '先選一位現有客戶，或為轉介紹的新客戶建立稱呼（如「王大哥」「陳小姐」）。電話與 Email 之後再補。',
    cc_pick_existing: 'A. 選擇現有客戶',
    cc_pick_btn: '選此客戶',
    cc_create_new_section: 'B. 或新增客戶',
    cc_name: '客戶姓名 / 稱呼',
    cc_phone: '電話（選填）',
    cc_email: 'Email（選填）',
    cc_submit: '建立並選取',
    ph_cc_name: '例：王大哥 / 陳小姐 / 林美玲',
    ph_cc_phone: '0912-345-678',
    ph_cc_email: 'customer@example.com',
    msg_manual_new_vehicle: '新增車輛（手動） — {name}：請至少填入車牌後按「儲存車輛資料」',
    msg_select_customer_first: '請先在頁面頂部「操作客戶」選擇要新增車輛的對象',
    msg_vehicle_created: '車輛已新增',
    h_existing_vehicles: '現有車輛',
    th_customer: '客戶', th_plate: '車牌', th_type: '型式', th_brand: '品牌',
    th_model: '車型', th_year: '年份', th_color: '顏色', th_cc: '排氣量',
    th_reg_expiry: '行照到期', th_inspection_window: '驗車期間', th_reg_image: '行照', th_action: '操作',
    // Policies tab
    h_upload_policy: '上傳保單（AI 辨識）',
    upload_policy_hint: '上傳保單圖片，系統自動辨識保險公司、保單號碼、起迄日、保障項目等，一鍵建立保單。',
    lbl_policy_image: '保單圖片 (JPG/PNG)',
    btn_upload_policy: '上傳保單',
    btn_ocr_policy: 'AI 辨識保單',
    h_manual_policy: '手動新增保單',
    lbl_insurer: '保險公司',
    ph_insurer: '例：富邦產險',
    ph_insurer_other: '保險公司名稱',
    btn_add_new_policy_manual: '+ 新增保單（手動）',
    btn_add_new_policy_ocr: '+ 新增保單（上傳辨識）',
    btn_add_another_policy: '+ 新增此客戶另一張保單',
    lbl_policy_number: '保單號碼',
    ph_policy_number: '例：FBN-2026-001234',
    lbl_covered_vehicle: '承保車輛',
    opt_unspecified: '不指定',
    lbl_status: '狀態',
    opt_active: '有效', opt_expiring: '即將到期', opt_expired: '已到期',
    lbl_start_date: '起保日', lbl_end_date: '到期日', lbl_premium: '總保費',
    hint_plate_readonly: '車牌與車輛主檔同步，請至「車輛 / 行照」分頁修改',
    btn_align_insured: '📋 對齊車主',
    sec_policyholder: '要保人（可與客戶為不同人）',
    sec_insured: '被保人（受益對象，可與要保人不同）',
    lbl_ph_name: '要保人姓名', lbl_ph_id: '要保人身分證字號', lbl_ph_birth: '要保人生日', lbl_ph_gender: '要保人性別', lbl_ph_phone: '要保人電話',
    lbl_ph_relation: '與車主(=被保險人)的關係',
    lbl_in_name: '被保人姓名', lbl_in_id: '被保人身分證字號', lbl_in_birth: '被保人生日', lbl_in_gender: '被保人性別', lbl_in_phone: '被保人電話',
    sec_voluntary_period: '任意險 期間（綜合險 / 第三人責任 / 車體損失 等）',
    sec_compulsory_period: '強制險（汽車強制責任險，可能跟任意險不同家、不同保單號、不同期間）',
    lbl_compulsory_insurer: '強制險 保險公司',
    lbl_compulsory_policy_no: '強制險 保單號碼',
    lbl_compulsory_premium: '強制險 保費',
    lbl_compulsory_start: '強制險 起保日',
    lbl_compulsory_end: '強制險 到期日',
    h_coverage_items: '保障項目',
    btn_add_item: '+ 新增項目',
    btn_create_policy: '建立保單',
    h_existing_policies: '現有保單',
    policy_list_hint: '💡 點擊任一保單列可選取，<b>雙擊</b>查看承保項目明細',
    th_policy_number: '保單號碼', th_insurer: '保險公司', th_status: '狀態',
    th_start: '起保', th_end: '到期', th_premium: '保費', th_items: '項目',
    h_edit_policy: '編輯保單',
    lbl_policyholder: '要保人姓名',
    ph_policyholder: '此保單所屬客戶（修改會轉移保單）',
    btn_cancel: '取消', btn_save: '儲存',
    // Claims/Accidents/Overview/Agents/Assign/Logs
    h_claims: '理賠申請管理', claims_hint: '客戶送出的理賠申請', btn_load_claims: '載入理賠列表',
    h_accidents: '事故照片管理', accidents_hint: '客戶透過緊急救援上傳的事故現場照片', btn_load_accidents: '載入事故列表',
    h_overview: '系統資料總覽',
    h_add_agent: '新增業務員', btn_add_agent: '新增業務員',
    lbl_display_name: '顯示名稱', lbl_phone: '電話',
    lbl_ip_whitelist: 'IP 白名單（逗號分隔，空=不限）',
    h_agent_list: '業務員列表',
    th_name: '名稱', th_customer_count: '客戶數', th_last_login: '最後登入',
    h_assign_customer: '分配客戶給業務員',
    lbl_choose_agent: '選擇業務員', lbl_choose_customer: '選擇客戶', btn_assign: '分配',
    h_audit_logs: '操作日誌', btn_load_latest: '載入最新',
    th_time: '時間', th_admin: '管理員', th_action_col: '操作',
    th_target: '目標', th_detail: '說明', th_ip: 'IP',
    // Common JS messages（給 mlang 用，但保留 key 也方便日後用 t() 取）
    msg_pls_login_user: '請輸入帳號和密碼',
    msg_login_failed: '登入失敗',
    msg_conn_failed: '連線失敗',
    msg_no_permission: '您無此功能的權限',
    msg_load_failed: '載入失敗',
    // Vehicle types
    vt_group_private: '自用車輛', vt_group_commercial: '營業車輛', vt_group_moto: '機車', vt_group_other: '其他',
    vt_private_sedan: '自用小客車', vt_private_light_truck: '自用小貨車',
    vt_private_combo: '自用小客貨兩用車', vt_private_bus: '自用大客車',
    vt_private_heavy_truck: '自用大貨車', vt_private_special: '自用特種車',
    vt_taxi: '營業小客車（計程車）', vt_commercial_light_truck: '營業小貨車',
    vt_commercial_bus: '營業大客車', vt_commercial_heavy_truck: '營業大貨車',
    vt_tour_bus: '營業遊覽車', vt_commercial_special: '營業特種車',
    vt_moto_550: '大型重型機車（550cc以上）', vt_moto_250: '普通重型機車（250cc以上）',
    vt_moto_50_250: '普通重型機車（50~250cc）', vt_moto_light: '普通輕型機車',
    vt_moto_electric: '小型輕型機車（電動）',
    vt_trailer: '拖車', vt_tractor: '曳引車', vt_ev: '電動汽車',
    // Coverage items placeholders
    ph_item_name: '項目名稱 (如：強制汽車責任保險)',
    ph_coverage_limit: '保額', ph_deductible: '自負額', ph_premium: '保費',
    // Overview labels
    ov_customer_count: '客戶數', ov_vehicle_count: '車輛數', ov_policy_count: '保單總數',
    ov_policy_active: '有效保單', ov_policy_expiring: '即將到期', ov_policy_expired: '已到期',
    ov_total_premium: '累計保費', ov_upcoming_30d: '30 天內到期',
    ov_days_left: '剩餘天數', ov_days: '天',
    // Customer dropdown
    ph_choose: '請選擇', lbl_unnamed: '未命名',
    btn_choose_file: '選擇檔案', msg_no_file: '未選擇任何檔案',
    btn_change_password: '變更密碼',
    btn_iching: '✨ 幫自己和客戶拿副好牌',
    cp_title: '變更密碼',
    cp_hint: '請先輸入當前密碼確認本人，再設定新密碼。',
    cp_current: '當前密碼', cp_new: '新密碼（至少 8 字元）', cp_confirm: '確認新密碼',
    cp_submit: '變更',
    cp_success: '密碼已變更，請重新登入',
    cp_failed: '變更失敗',
    cp_err_required: '請填寫所有欄位',
    cp_err_short: '新密碼至少 8 字元',
    cp_err_mismatch: '兩次輸入的新密碼不相同',
    cp_err_same: '新密碼不可與當前密碼相同',
    forgot_pw_hint: '忘記密碼？請聯繫 super_admin 重設。本系統不支援自助式 Email 重設以保護帳號安全。',
  },
  en: {
    header_title: 'BOPINAN — Admin Console',
    btn_logout: 'Logout',
    login_title: 'Admin Login',
    login_hint: 'Sign in with admin credentials',
    lbl_username: 'Username',
    lbl_password: 'Password',
    ph_username: 'admin',
    ph_password: 'password',
    btn_login: 'Login',
    tab_vehicles: 'Vehicles / Reg.',
    tab_policies: 'Policies',
    tab_claims: 'Claims',
    tab_accidents: 'Accident Photos',
    tab_overview: 'Overview',
    tab_quotes: 'Quote Requests',
    h_quote_requests: 'Quote Requests',
    tab_agents: 'Agents',
    tab_assign: 'Customer Assign',
    tab_logs: 'Audit Logs',
    ph_search: 'Search: name / phone / email / plate / policy # / claim #',
    btn_search: 'Search',
    btn_clear: 'Clear',
    qs_searching: 'Searching…',
    qs_no_result: 'No results',
    qs_failed: 'Search failed',
    qs_error: 'Search error',
    qs_view: 'View →',
    qs_section_customers: 'Customers',
    qs_section_vehicles: 'Vehicles',
    qs_section_policies: 'Policies',
    qs_section_claims: 'Claims',
    qs_tag_customer: 'Cust.',
    qs_tag_vehicle: 'Veh.',
    qs_tag_policy: 'Pol.',
    qs_tag_claim: 'Clm.',
    qs_lbl_customer: 'Customer: ',
    idle_warn_title: '⚠ Auto-logout soon - ',
    idle_logout_msg: 'Idle over 10 minutes, you have been logged out.',
    todo_title: 'To-Do Center (Policy / Inspection Due)',
    btn_todo_refresh: '🔄 Refresh',
    csv_title: 'CSV Bulk Import / Export (Customer + Vehicle + Policy)',
    btn_csv_export: '⬇ Export All',
    btn_csv_template: '📥 Blank Template',
    btn_csv_import: '⬆ Bulk Import',
    csv_import_title: '⚠️ CSV Bulk Import — Read Before Upload',
    csv_step_1: 'Use the BOPINAN CSV template (Chinese headers). Click "📥 Blank Template" below if you have not downloaded it.',
    csv_step_2: 'Keep the header row unchanged. Row 2 in the template is sample data — delete it before adding real records.',
    csv_step_3: 'Matching rules (idempotent — repeat uploads of the same file will not create duplicates)',
    csv_step_4: 'Try "dry-run" first to verify parsing; any row failure rolls back the entire batch.',
    csv_step_5: 'Agents can only import their assigned customers. Attempting to import others will be rejected and listed as errors.',
    csv_modal_dl_hint: 'Click to download the latest template',
    csv_understood: 'I understand and will use the BOPINAN template-format CSV',
    btn_csv_pick_file: '⬆ Pick CSV File',
    cur_customer_label: 'Active customer (used for new vehicle / policy):',
    btn_refresh_customers: 'Refresh',
    h_upload_reg: 'Upload Reg. Card (auto-OCR)',
    upload_reg_hint: 'Pick vehicle type then upload the registration card image; system will auto-recognize all fields including inspection due date.',
    lbl_vehicle_type: 'Vehicle Type (DMV class)',
    lbl_existing_vehicle: 'Existing vehicle (update) / New',
    opt_new_vehicle: '+ New vehicle',
    lbl_reg_image: 'Reg. Card Image (JPG/PNG)',
    btn_upload_reg: 'Upload',
    btn_ocr_reg: 'AI OCR',
    btn_ocr_autofill: 'AI OCR Autofill',
    msg_uploading: 'Uploading...',
    msg_processing: 'Processing...',
    h_ocr_result: 'AI OCR Result',
    h_ocr_result_short: 'OCR Result',
    ocr_hint_edit: 'Click any field value to edit',
    lbl_customer_name: 'Customer Name',
    lbl_customer_email: 'Customer Email',
    lbl_plate: 'Plate Number',
    lbl_brand: 'Make',
    lbl_model: 'Model',
    lbl_year: 'Year',
    lbl_year_month: 'Manufacture Year/Month',
    lbl_orig_reg_date: 'Original Reg. Date',
    lbl_reissue_date: 'Re-issue Date',
    lbl_inspection_window: 'Inspection Window',
    hint_inspection_window: '30 days before ~ 30 days after due date',
    lbl_color: 'Color',
    lbl_cc: 'Engine cc',
    lbl_vin: 'VIN',
    lbl_reg_date: 'Reg. Date',
    lbl_expiry_date: 'Inspection Due',
    lbl_fuel: 'Fuel Type',
    ph_customer_name: 'Owner of this vehicle (will update customer data)',
    ph_customer_email: 'Setting an email lets the customer log in and see their vehicles & policies',
    ph_customer_email_short: 'Setting an email lets the customer log in and see this policy',
    reg_upload_direct_title: 'Reg. Card Image (upload directly to this vehicle)',
    btn_save_vehicle: 'Save Vehicle',
    btn_add_another_vehicle: '+ Add Another Vehicle for This Customer',
    btn_add_new_vehicle: '+ Add Vehicle',
    btn_add_new_vehicle_manual: '+ Add Vehicle (Manual)',
    btn_add_new_vehicle_ocr: '+ Add Vehicle (Upload Reg.)',
    btn_done_close: 'Done',
    btn_new_customer: '+ New Customer',
    cc_title: 'Pick / New Customer',
    cc_hint: 'Pick an existing customer, or create a new one — for referrals just use a friendly name like "Mr. Wang" or "Ms. Chen". Phone and email can be filled later.',
    cc_pick_existing: 'A. Pick existing customer',
    cc_pick_btn: 'Use this customer',
    cc_create_new_section: 'B. Or create new',
    cc_name: 'Name / Reference',
    cc_phone: 'Phone (optional)',
    cc_email: 'Email (optional)',
    cc_submit: 'Create & Use',
    ph_cc_name: 'e.g. Mr. Wang / Ms. Chen',
    ph_cc_phone: '0912-345-678',
    ph_cc_email: 'customer@example.com',
    msg_manual_new_vehicle: 'Manual Add Vehicle — {name}: enter at least a plate number then click "Save Vehicle"',
    msg_select_customer_first: 'Please select a customer at the top first',
    msg_vehicle_created: 'Vehicle created',
    h_existing_vehicles: 'Existing Vehicles',
    th_customer: 'Customer', th_plate: 'Plate', th_type: 'Type', th_brand: 'Make',
    th_model: 'Model', th_year: 'Year', th_color: 'Color', th_cc: 'cc',
    th_reg_expiry: 'Insp. Due', th_inspection_window: 'Insp. Window', th_reg_image: 'Reg.', th_action: 'Actions',
    h_upload_policy: 'Upload Policy (AI OCR)',
    upload_policy_hint: 'Upload a policy image; system auto-recognizes insurer, policy #, dates, coverage items and creates a policy with one click.',
    lbl_policy_image: 'Policy Image (JPG/PNG)',
    btn_upload_policy: 'Upload Policy',
    btn_ocr_policy: 'AI OCR Policy',
    h_manual_policy: 'Manual New Policy',
    lbl_insurer: 'Insurer',
    ph_insurer: 'e.g., Fubon P&C',
    ph_insurer_other: 'Insurer name',
    btn_add_new_policy_manual: '+ Add Policy (Manual)',
    btn_add_new_policy_ocr: '+ Add Policy (Upload OCR)',
    btn_add_another_policy: '+ Add Another Policy for This Customer',
    lbl_policy_number: 'Policy #',
    ph_policy_number: 'e.g., FBN-2026-001234',
    lbl_covered_vehicle: 'Covered Vehicle',
    opt_unspecified: 'Unspecified',
    lbl_status: 'Status',
    opt_active: 'Active', opt_expiring: 'Expiring', opt_expired: 'Expired',
    lbl_start_date: 'Start', lbl_end_date: 'End', lbl_premium: 'Premium',
    hint_plate_readonly: 'Plate is synced with vehicle master record — edit it in the Vehicles tab',
    btn_align_insured: '📋 Match Owner',
    sec_policyholder: 'Policyholder (may differ from customer)',
    sec_insured: 'Insured Person (beneficiary, may differ from policyholder)',
    lbl_ph_name: 'Policyholder Name', lbl_ph_id: 'Policyholder ID', lbl_ph_birth: 'Policyholder Birth', lbl_ph_gender: 'Policyholder Gender', lbl_ph_phone: 'Policyholder Phone',
    lbl_ph_relation: 'Relation to Vehicle Owner (= Insured)',
    lbl_in_name: 'Insured Name', lbl_in_id: 'Insured ID', lbl_in_birth: 'Insured Birth', lbl_in_gender: 'Insured Gender', lbl_in_phone: 'Insured Phone',
    sec_voluntary_period: 'Voluntary Coverage Period (Comprehensive / 3rd-Party / Collision etc.)',
    sec_compulsory_period: 'Compulsory (CALI — may have different insurer / policy # / period from voluntary)',
    lbl_compulsory_insurer: 'CALI Insurer',
    lbl_compulsory_policy_no: 'CALI Policy #',
    lbl_compulsory_premium: 'CALI Premium',
    lbl_compulsory_start: 'CALI Start',
    lbl_compulsory_end: 'CALI End',
    h_coverage_items: 'Coverage Items',
    btn_add_item: '+ Add Item',
    btn_create_policy: 'Create Policy',
    h_existing_policies: 'Existing Policies',
    policy_list_hint: '💡 Click row to select, <b>double-click</b> to view items',
    th_policy_number: 'Policy #', th_insurer: 'Insurer', th_status: 'Status',
    th_start: 'Start', th_end: 'End', th_premium: 'Premium', th_items: 'Items',
    h_edit_policy: 'Edit Policy',
    lbl_policyholder: 'Policyholder Name',
    ph_policyholder: 'Owner of this policy (modifying will transfer)',
    btn_cancel: 'Cancel', btn_save: 'Save',
    h_claims: 'Claims', claims_hint: 'Customer-submitted claims', btn_load_claims: 'Load Claims',
    h_accidents: 'Accident Photos', accidents_hint: 'Photos uploaded via emergency assistance', btn_load_accidents: 'Load Accidents',
    h_overview: 'System Overview',
    h_add_agent: 'New Agent', btn_add_agent: 'Add Agent',
    lbl_display_name: 'Display Name', lbl_phone: 'Phone',
    lbl_ip_whitelist: 'IP whitelist (comma-separated, empty = no limit)',
    h_agent_list: 'Agent List',
    th_name: 'Name', th_customer_count: '# Cust', th_last_login: 'Last Login',
    h_assign_customer: 'Assign Customer to Agent',
    lbl_choose_agent: 'Choose Agent', lbl_choose_customer: 'Choose Customer', btn_assign: 'Assign',
    h_audit_logs: 'Audit Logs', btn_load_latest: 'Load Latest',
    th_time: 'Time', th_admin: 'Admin', th_action_col: 'Action',
    th_target: 'Target', th_detail: 'Detail', th_ip: 'IP',
    msg_pls_login_user: 'Please enter username and password',
    msg_login_failed: 'Login failed',
    msg_conn_failed: 'Connection failed',
    msg_no_permission: 'You do not have permission for this feature',
    msg_load_failed: 'Load failed',
    vt_group_private: 'Private', vt_group_commercial: 'Commercial', vt_group_moto: 'Motorcycle', vt_group_other: 'Others',
    vt_private_sedan: 'Private Sedan', vt_private_light_truck: 'Private Light Truck',
    vt_private_combo: 'Private Combo Vehicle', vt_private_bus: 'Private Bus',
    vt_private_heavy_truck: 'Private Heavy Truck', vt_private_special: 'Private Special',
    vt_taxi: 'Taxi', vt_commercial_light_truck: 'Commercial Light Truck',
    vt_commercial_bus: 'Commercial Bus', vt_commercial_heavy_truck: 'Commercial Heavy Truck',
    vt_tour_bus: 'Tour Bus', vt_commercial_special: 'Commercial Special',
    vt_moto_550: 'Heavy Motorcycle (550cc+)', vt_moto_250: 'Standard Motorcycle (250cc+)',
    vt_moto_50_250: 'Standard Motorcycle (50-250cc)', vt_moto_light: 'Light Motorcycle',
    vt_moto_electric: 'Electric Light Moto',
    vt_trailer: 'Trailer', vt_tractor: 'Tractor Truck', vt_ev: 'Electric Vehicle',
    ph_item_name: 'Item name (e.g., Compulsory liability)',
    ph_coverage_limit: 'Coverage', ph_deductible: 'Deductible', ph_premium: 'Premium',
    ov_customer_count: 'Customers', ov_vehicle_count: 'Vehicles', ov_policy_count: 'Total Policies',
    ov_policy_active: 'Active', ov_policy_expiring: 'Expiring', ov_policy_expired: 'Expired',
    ov_total_premium: 'Total Premium', ov_upcoming_30d: 'Expiring within 30 days',
    ov_days_left: 'Days Left', ov_days: 'day(s)',
    ph_choose: 'Choose', lbl_unnamed: 'Unnamed',
    btn_choose_file: 'Choose File', msg_no_file: 'No file chosen',
    btn_change_password: 'Change Password',
    btn_iching: '✨ Lucky Cards (Numerology)',
    cp_title: 'Change Password',
    cp_hint: 'Enter your current password to confirm identity, then set a new password.',
    cp_current: 'Current Password', cp_new: 'New Password (≥ 8 chars)', cp_confirm: 'Confirm New Password',
    cp_submit: 'Change',
    cp_success: 'Password changed. Please log in again.',
    cp_failed: 'Change failed',
    cp_err_required: 'Please fill in all fields',
    cp_err_short: 'New password must be ≥ 8 chars',
    cp_err_mismatch: 'New passwords do not match',
    cp_err_same: 'New password must differ from current',
    forgot_pw_hint: 'Forgot password? Please contact a super_admin to reset. Self-service email reset is intentionally disabled for security.',
  }
};
// 給 JS 動態訊息的 inline bilingual helper（避免每個都加 i18n key）
function mlang(zh, en) { return LANG === 'en' ? en : zh; }
function t(key) { return (I18N[LANG] && I18N[LANG][key]) || I18N.zh[key] || key; }
function applyAdminLang() {
  document.querySelectorAll('[data-i18n]').forEach(function(el) {
    var k = el.getAttribute('data-i18n');
    el.textContent = t(k);
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(function(el) {
    var k = el.getAttribute('data-i18n-placeholder');
    el.placeholder = t(k);
  });
  // optgroup label 屬性
  document.querySelectorAll('[data-i18n-label]').forEach(function(el) {
    var k = el.getAttribute('data-i18n-label');
    el.label = t(k);
  });
  // 切換按鈕顯示對立語言
  var btn = document.getElementById('lang-toggle-btn');
  if (btn) btn.textContent = (LANG === 'zh') ? 'EN' : '中';
  // 設 lang 屬性（影響瀏覽器原生元件：date input、file input 按鈕）
  document.documentElement.lang = (LANG === 'en') ? 'en' : 'zh-TW';
  // 觸發 dynamic 內容重新渲染
  if (document.getElementById('admin-panel').style.display === 'block') {
    if (typeof loadCustomerList === 'function') loadCustomerList();
    if (typeof loadOverview === 'function') loadOverview();
    if (typeof loadVehicles === 'function') loadVehicles();
    if (typeof loadPolicies === 'function') loadPolicies();
  }
}
function toggleAdminLang() {
  LANG = (LANG === 'zh') ? 'en' : 'zh';
  localStorage.setItem('admin_lang', LANG);
  applyAdminLang();
  // 若搜尋結果還在，重跑一次（讓 JS 渲染的標籤跟著翻）
  var qsBox = document.getElementById('qs-results');
  if (qsBox && qsBox.innerHTML && document.getElementById('qs-input').value.trim()) {
    doQuickSearch();
  }
}

// --- Auth (Admin Account) ---
// localStorage key（持久化，瀏覽器重啟也保留；按上一頁不會被清掉）
var LS_TOKEN_KEY = 'admin_token_v1';
var LS_ROLE_KEY = 'admin_role_v1';
var LS_NAME_KEY = 'admin_name_v1';

// --- 閒置自動登出（10 分鐘無動作） ---
var IDLE_TIMEOUT_MS = 10 * 60 * 1000;  // 10 分鐘
var IDLE_WARN_MS    =  9 * 60 * 1000;  // 第 9 分鐘提醒（剩 1 分鐘）
var _idleTimer = null;
var _idleWarnTimer = null;
function _idleAutoLogout() {
  if (!ADMIN_TOKEN) return;
  alert(t('idle_logout_msg'));
  doLogout();
}
function _idleWarnSoon() {
  if (!ADMIN_TOKEN) return;
  // 用非阻塞 toast 提醒（用 console + 標題列閃爍）
  document.title = t('idle_warn_title') + (document.title || 'Admin');
}
function _resetIdleTimer() {
  if (!ADMIN_TOKEN) return;
  if (_idleTimer) clearTimeout(_idleTimer);
  if (_idleWarnTimer) clearTimeout(_idleWarnTimer);
  _idleTimer = setTimeout(_idleAutoLogout, IDLE_TIMEOUT_MS);
  _idleWarnTimer = setTimeout(_idleWarnSoon, IDLE_WARN_MS);
  // 還原標題（若已被警告過）
  if (document.title.indexOf('⚠') === 0) {
    document.title = document.title.replace(/^⚠[^-]*- /, '');
  }
}
function _bindIdleEvents() {
  var events = ['mousedown','mousemove','keydown','scroll','touchstart','click'];
  events.forEach(function(ev) {
    document.addEventListener(ev, _resetIdleTimer, {passive: true});
  });
}
function _stopIdleTimer() {
  if (_idleTimer) { clearTimeout(_idleTimer); _idleTimer = null; }
  if (_idleWarnTimer) { clearTimeout(_idleWarnTimer); _idleWarnTimer = null; }
}

function _enterAdminUI(token, role, displayName) {
  // 共用：登入成功 / restore 時把 UI 切到「已登入」狀態
  ADMIN_TOKEN = token;
  TOKEN = token;
  ADMIN_ROLE = role;
  document.getElementById('user-info').textContent = (displayName || '') + ' (' + role + ')';
  document.getElementById('login-section').style.display = 'none';
  document.getElementById('admin-panel').style.display = 'block';
  document.getElementById('logout-btn').style.display = 'inline-block';
  document.getElementById('change-pw-btn').style.display = 'inline-block';
  // 依角色顯示/隱藏分頁
  var allTabs = ['vehicles','policies','claims','accidents','overview','quotes','agents','assign','logs'];
  var agentTabs = ['overview','quotes'];
  var superTabs = allTabs;
  var visibleTabs = (role === 'super_admin') ? superTabs : agentTabs;
  for (var ti = 0; ti < allTabs.length; ti++) {
    var btn = document.getElementById('tab-btn-' + allTabs[ti]);
    if (btn) btn.style.display = visibleTabs.indexOf(allTabs[ti]) >= 0 ? '' : 'none';
  }
  if (role !== 'super_admin') switchTab(visibleTabs[0]);
  document.getElementById('customer-bar').style.display = 'block';
  loadCustomerList();
  loadVehicles(); loadPolicies(); loadOverview();
  loadAgentTasks();
  // 啟動閒置自動登出計時
  _bindIdleEvents();
  _resetIdleTimer();
}

async function doAdminLogin() {
  var user = document.getElementById('login-user').value.trim();
  var pass = document.getElementById('login-pass').value.trim();
  if (!user || !pass) { showMsg('login-msg','err',t('msg_pls_login_user')); return; }
  try {
    var r = await fetch(CONSOLE_API+'/login', {method:'POST', headers:{'Content-Type':'application/json', 'Accept-Language': _acceptLang()}, body:JSON.stringify({username:user,password:pass})});
    var d = await r.json();
    if (d.success && d.data && d.data.token) {
      // ★ 持久化到 localStorage（按上一頁/重整/換分頁都不會掉）
      localStorage.setItem(LS_TOKEN_KEY, d.data.token);
      localStorage.setItem(LS_ROLE_KEY, d.data.admin.role);
      localStorage.setItem(LS_NAME_KEY, d.data.admin.display_name || '');
      _enterAdminUI(d.data.token, d.data.admin.role, d.data.admin.display_name);
    } else {
      showMsg('login-msg','err', d.message || t('msg_login_failed'));
    }
  } catch(e) { showMsg('login-msg','err', t('msg_conn_failed') + ': '+e.message); }
}

// 頁面載入時嘗試自動 restore login 狀態
async function tryRestoreLogin() {
  var token = localStorage.getItem(LS_TOKEN_KEY);
  if (!token) return false;
  // 用 token 拉一個輕量 endpoint 驗證仍有效（用 /customers，admin 跟 agent 都可呼叫）
  try {
    var r = await fetch(CONSOLE_API+'/customers', {headers:{'Authorization':'Bearer '+token}});
    if (r.status === 200 || r.status === 201) {
      var role = localStorage.getItem(LS_ROLE_KEY) || 'agent';
      var name = localStorage.getItem(LS_NAME_KEY) || '';
      _enterAdminUI(token, role, name);
      return true;
    }
  } catch(e) {}
  // token 失效（過期 / 後端重啟換 secret） → 清掉
  localStorage.removeItem(LS_TOKEN_KEY);
  localStorage.removeItem(LS_ROLE_KEY);
  localStorage.removeItem(LS_NAME_KEY);
  return false;
}

// ★ 頁面載入立刻嘗試 restore（多重觸發確保各種情境都覆蓋）
// 1. 直接呼叫（inline script 在 body 末端，DOM 已就緒）
applyAdminLang();   // 載入時先套語言
tryRestoreLogin();
// 2. DOMContentLoaded（保險，若 1 太早跑完）
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', tryRestoreLogin);
}
// 3. pageshow（處理瀏覽器「上一頁」從 bfcache 還原的情境）
window.addEventListener('pageshow', function(e) {
  // 從 bfcache 回來時，舊的紅色錯誤訊息會還在 → 清掉
  // （不只 bfcache，每次 pageshow 都清比較簡單一致）
  var lm = document.getElementById('login-msg');
  if (lm) { lm.textContent = ''; lm.className = 'msg'; }
  // 若當前已是登入狀態（admin-panel 顯示中）就不再 restore
  if (document.getElementById('admin-panel').style.display === 'block') return;
  tryRestoreLogin();
});

function togglePw(inputId, btn) {
  var inp = document.getElementById(inputId);
  if (inp.type === 'password') { inp.type = 'text'; btn.textContent = '🙈'; }
  else { inp.type = 'password'; btn.textContent = '👁'; }
}

// --- 變更密碼 ---
function openChangePwModal() {
  document.getElementById('cp-current').value = '';
  document.getElementById('cp-new').value = '';
  document.getElementById('cp-confirm').value = '';
  var m = document.getElementById('cp-msg'); if (m) { m.textContent=''; m.className='msg'; }
  document.getElementById('change-pw-modal').style.display = 'flex';
}
function closeChangePwModal() {
  document.getElementById('change-pw-modal').style.display = 'none';
}
async function doChangePassword() {
  var cur = document.getElementById('cp-current').value;
  var nw = document.getElementById('cp-new').value;
  var cf = document.getElementById('cp-confirm').value;
  if (!cur || !nw || !cf) { showMsg('cp-msg','err', t('cp_err_required')); return; }
  if (nw.length < 8) { showMsg('cp-msg','err', t('cp_err_short')); return; }
  if (nw !== cf) { showMsg('cp-msg','err', t('cp_err_mismatch')); return; }
  if (nw === cur) { showMsg('cp-msg','err', t('cp_err_same')); return; }
  try {
    var r = await fetch(CONSOLE_API+'/change-password', {
      method:'POST',
      headers: {'Authorization':'Bearer '+ADMIN_TOKEN, 'Content-Type':'application/json', 'Accept-Language': _acceptLang()},
      body: JSON.stringify({current_password: cur, new_password: nw}),
    });
    var d = await r.json();
    if (d.success) {
      showMsg('cp-msg','ok', d.message || t('cp_success'));
      setTimeout(function(){ closeChangePwModal(); doLogout(); }, 1500);
    } else {
      showMsg('cp-msg','err', d.message || d.detail || t('cp_failed'));
    }
  } catch(e) { showMsg('cp-msg','err', t('msg_conn_failed') + ': ' + e.message); }
}

function doLogout() {
  TOKEN = ''; ADMIN_TOKEN = ''; ADMIN_ROLE = '';
  // 清 localStorage（明確登出才清，按上一頁不會清）
  localStorage.removeItem(LS_TOKEN_KEY);
  localStorage.removeItem(LS_ROLE_KEY);
  localStorage.removeItem(LS_NAME_KEY);
  document.getElementById('admin-panel').style.display = 'none';
  document.getElementById('logout-btn').style.display = 'none';
  document.getElementById('change-pw-btn').style.display = 'none';
  document.getElementById('customer-bar').style.display = 'none';
  document.getElementById('login-section').style.display = 'block';
  document.getElementById('login-user').value = '';
  document.getElementById('login-pass').value = '';
  document.getElementById('user-info').textContent = '';
  // 清登入頁殘留錯誤訊息（避免下次顯示時看到舊紅字）
  var lm = document.getElementById('login-msg');
  if (lm) { lm.textContent = ''; lm.className = 'msg'; }
  // 停掉閒置計時 + 清空快速搜尋
  _stopIdleTimer();
  var qsBox = document.getElementById('qs-results'); if (qsBox) qsBox.innerHTML = '';
  // 清空數字易經所有欄位 + 結果（防個資殘留）
  if (typeof _numClearAllInputs === 'function') _numClearAllInputs();
  var qsIn = document.getElementById('qs-input'); if (qsIn) qsIn.value = '';
  document.title = document.title.replace(/^⚠[^-]*- /, '');
}

function _acceptLang() {
  return (LANG === 'en') ? 'en' : 'zh-TW';
}
function authHeaders(json) {
  var h = {'Authorization':'Bearer '+TOKEN, 'Accept-Language': _acceptLang()};
  if (json) h['Content-Type'] = 'application/json';
  return h;
}
function consoleHeaders(json) {
  var h = {'Authorization':'Bearer '+ADMIN_TOKEN, 'Accept-Language': _acceptLang()};
  if (json) h['Content-Type'] = 'application/json';
  return h;
}

// 「目前操作客戶」下拉的當前選擇 ID
function currentCustomerId() {
  var sel = document.getElementById('cur-customer');
  return sel && sel.value ? sel.value : '';
}

async function loadCustomerList() {
  try {
    var r = await fetch(CONSOLE_API+'/customers', {headers:consoleHeaders()});
    var d = await r.json();
    var customers = d.data || [];
    var sel = document.getElementById('cur-customer');
    var prev = sel.value;
    var html = '<option value="">— ' + t('ph_choose') + ' —</option>';
    for (var i = 0; i < customers.length; i++) {
      var c = customers[i];
      var label = (c.name || ('(' + t('lbl_unnamed') + ')')) + (c.phone ? ' · '+c.phone : '') + (c.email ? ' · '+c.email : '');
      html += '<option value="'+c.id+'">'+label+'</option>';
    }
    sel.innerHTML = html;
    if (prev) sel.value = prev;
    document.getElementById('customer-bar-msg').textContent = (LANG === 'en')
      ? (customers.length + ' customer(s)')
      : ('共 ' + customers.length + ' 位客戶');
  } catch(e) { document.getElementById('customer-bar-msg').textContent = t('msg_load_failed'); }
}

// --- Tabs ---
function switchTab(name) {
  // 業務員權限檢查
  var adminOnly = ['vehicles','policies','claims','accidents','agents','assign','logs'];
  if (ADMIN_ROLE === 'agent' && adminOnly.indexOf(name) >= 0) {
    showMsg('login-msg', 'err', t('msg_no_permission'));
    return;
  }
  document.querySelectorAll('.tab-content').forEach(function(e) { e.classList.remove('active'); });
  document.querySelectorAll('.tab').forEach(function(e) { e.classList.remove('active'); });
  document.getElementById('tab-'+name).classList.add('active');
  var btn = document.getElementById('tab-btn-'+name);
  if (btn) btn.classList.add('active');
  if (name === 'agents') loadAgents();
  if (name === 'assign') loadAssignSelects();
  if (name === 'logs') loadLogs();
  if (name === 'quotes') loadQuoteRequests('');
}

// --- 全域快速搜尋 ---
function clearQuickSearch() {
  document.getElementById('qs-input').value = '';
  document.getElementById('qs-results').innerHTML = '';
}

async function doQuickSearch() {
  var q = document.getElementById('qs-input').value.trim();
  var box = document.getElementById('qs-results');
  if (!q) { box.innerHTML = ''; return; }
  box.innerHTML = '<div style="color:#999;padding:8px">' + t('qs_searching') + '</div>';
  try {
    var resp = await fetch('/api/v1/admin-console/search?q=' + encodeURIComponent(q),
      {headers: {'Authorization':'Bearer ' + ADMIN_TOKEN}});
    var json = await resp.json();
    if (!json.success) { box.innerHTML = '<div style="color:#d32f2f;padding:8px">' + t('qs_failed') + '：' + (json.message||'') + '</div>'; return; }
    var d = json.data || {};
    var html = '';
    var cust = d.customers || [], veh = d.vehicles || [], pol = d.policies || [], clm = d.claims || [];
    var total = cust.length + veh.length + pol.length + clm.length;
    if (total === 0) { box.innerHTML = '<div style="color:#666;padding:8px">' + t('qs_no_result') + '</div>'; return; }

    var rowStyle = 'padding:8px 12px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:8px';
    var tagStyle = 'display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600';

    if (cust.length) {
      html += '<div style="font-size:12px;color:#666;padding:4px 0;margin-top:4px"><b>' + t('qs_section_customers') + ' ('+cust.length+')</b></div>';
      cust.forEach(function(c) {
        html += '<div style="'+rowStyle+'" onclick="qsGoCustomer(\\''+c.id+'\\')" >' +
          '<span style="'+tagStyle+';background:#e3f2fd;color:#1565c0">' + t('qs_tag_customer') + '</span>' +
          '<b>' + (c.name || '(no name)') + '</b>' +
          '<span style="color:#666;font-size:13px">' + (c.email || '') + ' ' + (c.phone || '') + '</span>' +
          '<span style="margin-left:auto;color:#1976d2;font-size:12px">' + t('qs_view') + '</span></div>';
      });
    }
    if (veh.length) {
      html += '<div style="font-size:12px;color:#666;padding:4px 0;margin-top:4px"><b>' + t('qs_section_vehicles') + ' ('+veh.length+')</b></div>';
      veh.forEach(function(v) {
        html += '<div style="'+rowStyle+'" onclick="qsGoVehicle(\\''+v.id+'\\',\\''+v.user_id+'\\')">' +
          '<span style="'+tagStyle+';background:#fff3e0;color:#e65100">' + t('qs_tag_vehicle') + '</span>' +
          '<b>' + (v.plate_number || '') + '</b>' +
          '<span style="color:#666;font-size:13px">' + ((v.brand||'') + ' ' + (v.model||'')) + ' ('+(v.year||'')+')</span>' +
          '<span style="color:#999;font-size:12px">' + t('qs_lbl_customer') + (v.user_name || '') + '</span>' +
          '<span style="margin-left:auto;color:#1976d2;font-size:12px">' + t('qs_view') + '</span></div>';
      });
    }
    if (pol.length) {
      html += '<div style="font-size:12px;color:#666;padding:4px 0;margin-top:4px"><b>' + t('qs_section_policies') + ' ('+pol.length+')</b></div>';
      pol.forEach(function(p) {
        html += '<div style="'+rowStyle+'" onclick="qsGoPolicy(\\''+p.id+'\\',\\''+p.user_id+'\\')">' +
          '<span style="'+tagStyle+';background:#e8f5e9;color:#2e7d32">' + t('qs_tag_policy') + '</span>' +
          '<b>' + (p.policy_number || '') + '</b>' +
          '<span style="color:#666;font-size:13px">' + (p.insurer_name || '') + '</span>' +
          '<span style="color:#999;font-size:12px">' + (p.start_date||'') + ' ~ ' + (p.end_date||'') + ' / ' + (p.status||'') + '</span>' +
          '<span style="color:#999;font-size:12px">' + t('qs_lbl_customer') + (p.user_name || '') + '</span>' +
          '<span style="margin-left:auto;color:#1976d2;font-size:12px">' + t('qs_view') + '</span></div>';
      });
    }
    if (clm.length) {
      html += '<div style="font-size:12px;color:#666;padding:4px 0;margin-top:4px"><b>' + t('qs_section_claims') + ' ('+clm.length+')</b></div>';
      clm.forEach(function(cl) {
        html += '<div style="'+rowStyle+'" onclick="qsGoClaim(\\''+cl.id+'\\',\\''+cl.user_id+'\\')">' +
          '<span style="'+tagStyle+';background:#fce4ec;color:#c2185b">' + t('qs_tag_claim') + '</span>' +
          '<b>' + (cl.claim_number || '') + '</b>' +
          '<span style="color:#666;font-size:13px">' + (cl.claim_type || '') + '</span>' +
          '<span style="color:#999;font-size:12px">' + (cl.status || '') + '</span>' +
          '<span style="color:#999;font-size:12px">' + t('qs_lbl_customer') + (cl.user_name || '') + '</span>' +
          '<span style="margin-left:auto;color:#1976d2;font-size:12px">' + t('qs_view') + '</span></div>';
      });
    }
    html = '<div style="background:#fafafa;border:1px solid #e0e0e0;border-radius:6px;max-height:400px;overflow:auto">' + html + '</div>';
    box.innerHTML = html;
    // 加 hover 效果
    box.querySelectorAll('div[onclick]').forEach(function(el) {
      el.style.cursor = 'pointer';
      el.addEventListener('mouseenter', function() { el.style.background = '#f5f5f5'; });
      el.addEventListener('mouseleave', function() { el.style.background = ''; });
    });
  } catch (e) {
    box.innerHTML = '<div style="color:#d32f2f;padding:8px">' + t('qs_error') + '：' + e + '</div>';
  }
}

// 點搜尋結果 → 跳轉到對應 tab 並聚焦該客戶
function qsGoCustomer(uid) {
  switchTab('vehicles');  // 預設跳車輛 tab，因為車輛/保單都掛在客戶下
  if (typeof loadVehiclesForUser === 'function') loadVehiclesForUser(uid);
}
function qsGoVehicle(vid, uid) {
  switchTab('vehicles');
  if (typeof loadVehiclesForUser === 'function') loadVehiclesForUser(uid);
  // 嘗試 highlight 該 vehicle row
  setTimeout(function() {
    var row = document.querySelector('[data-vehicle-id="' + vid + '"]');
    if (row) { row.scrollIntoView({block:'center'}); row.style.background = '#fff9c4'; }
  }, 500);
}
function qsGoPolicy(pid, uid) {
  switchTab('policies');
  if (typeof loadPoliciesForUser === 'function') loadPoliciesForUser(uid);
  setTimeout(function() {
    var row = document.querySelector('[data-policy-id="' + pid + '"]');
    if (row) { row.scrollIntoView({block:'center'}); row.style.background = '#fff9c4'; }
  }, 500);
}
function qsGoClaim(cid, uid) {
  switchTab('claims');
  if (typeof loadClaimsForUser === 'function') loadClaimsForUser(uid);
}

// --- 車輛型式 → 驗車規定對照 ---
var INSPECTION_RULES = {
  '自用小客車': '出廠5年內免驗；5~10年每年驗車1次；超過10年每年驗車2次（每6個月）',
  '自用小貨車': '出廠5年內免驗；5~10年每年驗車1次；超過10年每年驗車2次',
  '自用小客貨兩用車': '出廠5年內免驗；5~10年每年驗車1次；超過10年每年驗車2次',
  '自用大客車': '每年驗車1次；出廠10年以上每年驗車2次',
  '自用大貨車': '每年驗車1次；出廠10年以上每年驗車2次',
  '自用特種車': '每年驗車1次',
  '營業小客車（計程車）': '每年驗車1次；出廠5年以上每年驗車2次',
  '營業小貨車': '每年驗車1次；出廠5年以上每年驗車2次',
  '營業大客車': '每年驗車3次（每4個月）',
  '營業大貨車': '每年驗車2次（每6個月）',
  '營業遊覽車': '每年驗車3次（每4個月）',
  '營業特種車': '每年驗車1次',
  '大型重型機車（550cc以上）': '出廠5年內免驗；超過5年每年驗車1次',
  '普通重型機車（250cc以上）': '出廠5年內免驗；超過5年每年驗車1次',
  '普通重型機車（50~250cc）': '出廠5年內免驗；超過5年每年驗車1次',
  '普通輕型機車': '出廠5年內免驗；超過5年每年驗車1次',
  '小型輕型機車（電動）': '出廠5年內免驗；超過5年每年驗車1次',
  '拖車': '每年驗車1次',
  '曳引車': '每年驗車1次',
  '電動汽車': '出廠5年內免驗；5~10年每年驗車1次；超過10年每年驗車2次'
};

// === 選擇 / 新增客戶 modal ===
// _pendingPickAction：選/建立成功後要執行的動作（讓「+ 新增車輛」按鈕無縫接上）
window._pendingPickAction = null;

function openCreateCustomerModal(pendingAction) {
  document.getElementById('cc-name').value = '';
  document.getElementById('cc-phone').value = '';
  document.getElementById('cc-email').value = '';
  var msg = document.getElementById('cc-msg');
  if (msg) { msg.textContent = ''; msg.className = 'msg'; }
  // 填入「選擇現有客戶」dropdown
  var src = document.getElementById('cur-customer');
  var pick = document.getElementById('cc-pick');
  if (src && pick) {
    pick.innerHTML = src.innerHTML;  // 直接複製 cur-customer 的 options
    pick.value = src.value || '';
  }
  window._pendingPickAction = (typeof pendingAction === 'function') ? pendingAction : null;
  document.getElementById('create-customer-modal').style.display = 'flex';
  setTimeout(function(){
    var p = document.getElementById('cc-pick');
    if (p) p.focus();
  }, 50);
}
function closeCreateCustomerModal() {
  document.getElementById('create-customer-modal').style.display = 'none';
  window._pendingPickAction = null;
}
function _afterCustomerChosen(cid) {
  var sel = document.getElementById('cur-customer');
  if (sel) sel.value = cid;
  // ★ 必須在 closeCreateCustomerModal() 前抓 callback —
  //   close 內部會把 _pendingPickAction 清成 null（給「取消」按鈕用），
  //   若先 close 再讀 callback，就永遠拿不到、變成無限迴圈彈 picker。
  var fn = window._pendingPickAction;
  closeCreateCustomerModal();
  if (typeof fn === 'function') {
    setTimeout(fn, 50); // 等 modal 關閉動畫
  }
}
function doPickExistingCustomer() {
  var cid = document.getElementById('cc-pick').value;
  if (!cid) {
    showMsg('cc-msg','err', LANG==='en' ? 'Please select a customer' : '請從下拉選單選一位客戶');
    return;
  }
  _afterCustomerChosen(cid);
}
async function doCreateCustomer() {
  var name = document.getElementById('cc-name').value.trim();
  var phone = document.getElementById('cc-phone').value.trim();
  var email = document.getElementById('cc-email').value.trim();
  if (!name) { showMsg('cc-msg','err', LANG==='en' ? 'Name is required' : '請輸入姓名 / 稱呼'); return; }
  try {
    var body = { name: name };
    if (phone) body.phone = phone;
    if (email) body.email = email;
    var r = await fetch(CONSOLE_API+'/customers', {
      method:'POST', headers: consoleHeaders(true), body: JSON.stringify(body)
    });
    var d = await r.json();
    if (!d.success) {
      showMsg('cc-msg','err', d.message || (LANG==='en' ? 'Create failed' : '建立失敗'));
      return;
    }
    var newId = d.data && d.data.id;
    await loadCustomerList();
    document.getElementById('customer-bar-msg').textContent =
      (LANG==='en') ? ('Customer "' + name + '" created') : ('客戶「' + name + '」已建立');
    if (newId) _afterCustomerChosen(newId);
    else closeCreateCustomerModal();
  } catch(e) {
    showMsg('cc-msg','err', (LANG==='en' ? 'Network error: ' : '網路錯誤：') + e.message);
  }
}

// === 手動新增車輛（不需上傳行照）===
// 入口：每次按「+ 新增車輛（手動）」都先彈「選擇/新增客戶」 picker —
// 即便 cur-customer 已預選，picker 也會幫使用者預選同一位，按「選此客戶」一鍵確認；
// 這樣可避免儲存後再點「+ 新增車輛」誤套到剛剛的客戶身上、也防止操作者誤建到錯人。
function openManualVehicleForm() {
  openCreateCustomerModal(function() { _doOpenManualVehicleFormForCurrent(); });
}

// 內部：直接以目前 cur-customer 開啟手動新增表單（給「+新增此客戶另一輛車」等已選好客戶的場景使用）
function _doOpenManualVehicleFormForCurrent() {
  var cid = currentCustomerId();
  if (!cid) return;
  var sel = document.getElementById('cur-customer');
  var custName = '';
  if (sel && sel.selectedIndex >= 0) {
    var lbl = sel.options[sel.selectedIndex].text || '';
    custName = lbl.split(' · ')[0].trim();
  }
  // 進入「手動新增」模式：vid 為空字串代表新建
  window._editVid = '';
  window._editIsNew = true;
  window._editUserId = cid;
  window._editCustomerNameOrig = custName;
  window._editCustomerEmailOrig = '';

  // 填表單：客戶姓名/Email 預設帶入目前所選；其餘清空
  document.getElementById('v-edit-title').textContent =
    (LANG==='en')
      ? ('Manual Add Vehicle — ' + (custName || ''))
      : ('手動新增車輛 — ' + (custName || ''));
  document.getElementById('ve-customer-name').value = custName;
  document.getElementById('ve-customer-email').value = '';
  document.getElementById('ve-plate').value = '';
  document.getElementById('ve-brand').value = '';
  document.getElementById('ve-model').value = '';
  document.getElementById('ve-year-month').value = '';
  document.getElementById('ve-color').value = '';
  document.getElementById('ve-cc').value = '';
  document.getElementById('ve-vin').value = '';
  document.getElementById('ve-reg-date').value = '';
  document.getElementById('ve-reissue-date').value = '';
  document.getElementById('ve-expiry').value = '';
  document.getElementById('ve-fuel').value = '';
  updateInspectionWindow();

  // 隱藏編輯表單內的「行照圖片直接上傳」區（沒 vid 無法上傳，先儲存後再上傳）
  var dirImg = document.getElementById('ve-current-image');
  if (dirImg) dirImg.style.display = 'none';
  var dirFile = document.getElementById('ve-file');
  if (dirFile) dirFile.value = '';
  var dirPreview = document.getElementById('ve-file-preview');
  if (dirPreview) dirPreview.style.display = 'none';

  var msg = document.getElementById('ve-msg');
  if (msg) { msg.textContent = ''; msg.className = 'msg'; }

  document.getElementById('v-edit-form').style.display = 'flex';
  refreshRocLabels();
  showMsg('ve-msg','ok',
    t('msg_manual_new_vehicle').replace('{name}', custName || ''));
}

// === 上傳行照 modal 開關 ===
function closeVehicleUploadModal() {
  var m = document.getElementById('v-upload-modal');
  if (m) m.style.display = 'none';
}
function closeVehicleFormModal() {
  var m = document.getElementById('v-edit-form');
  if (m) m.style.display = 'none';
  window._editIsNew = false;
}

// 「+ 新增車輛（上傳行照）」按鈕 → 一律先彈出「選擇/新增客戶」 picker，再開上傳 modal
// （理由同 openManualVehicleForm：每次新增都明確選定客戶，避免誤套到剛剛的客戶）
function scrollToAddVehicle() {
  openCreateCustomerModal(function() { _doOpenVehicleUploadModalForCurrent(); });
}

// 內部：直接以目前 cur-customer 開啟上傳行照 modal
function _doOpenVehicleUploadModalForCurrent() {
  var cid = currentCustomerId();
  if (!cid) return;
  // 確保編輯表單 modal 是關閉的（避免兩個 modal 疊加）
  closeVehicleFormModal();
  // 重置 vid 等狀態，避免上傳被誤導向舊車
  window._editVid = '';
  window._editIsNew = false;
  window._editUserId = '';
  var sel = document.getElementById('v-select');
  if (sel) sel.value = '__new__';
  var file = document.getElementById('v-file');
  if (file) file.value = '';
  var nameSpan = document.getElementById('v-file-name');
  if (nameSpan) nameSpan.textContent = t('msg_no_file');
  var preview = document.getElementById('v-preview');
  if (preview) preview.style.display = 'none';
  var msg = document.getElementById('v-msg');
  if (msg) { msg.textContent = ''; msg.className = 'msg'; }
  var loading = document.getElementById('v-loading');
  if (loading) loading.style.display = 'none';
  var ocrBtn = document.getElementById('v-ocr-btn');
  if (ocrBtn) ocrBtn.style.display = 'none';
  var upBtn = document.getElementById('v-upload-btn');
  if (upBtn) upBtn.disabled = false;
  // 顯示目前操作客戶於 modal header
  var custSel = document.getElementById('cur-customer');
  var custName = '';
  if (custSel && custSel.selectedIndex >= 0) {
    custName = (custSel.options[custSel.selectedIndex].text || '').split(' · ')[0].trim();
  }
  var lbl = document.getElementById('v-upload-modal-customer');
  if (lbl) lbl.textContent = custName || '(未選擇)';
  // 開啟 modal
  document.getElementById('v-upload-modal').style.display = 'flex';
}

// 在編輯某輛車時，按「新增此客戶另一輛車」→ 關閉編輯 modal，重新以手動模式開啟
function addAnotherVehicleSameCustomer() {
  var uid = window._editUserId;
  if (!uid) {
    showMsg('ve-msg','err', LANG === 'en' ? 'No customer context' : '找不到目前車輛的客戶');
    return;
  }
  // 確保「操作客戶」dropdown 選到此車主
  var custSel = document.getElementById('cur-customer');
  if (custSel) custSel.value = uid;
  closeVehicleFormModal();
  // 直接走內部入口（不再彈 picker，因為使用者已明確表態要「同客戶再加一輛」）
  setTimeout(function(){ _doOpenManualVehicleFormForCurrent(); }, 50);
}

// v-select 切換 → 「+ 新增車輛」收起編輯表單，避免使用者誤把舊車輛資料當新增填入
function onVSelectChange() {
  var v = document.getElementById('v-select').value;
  if (v === '__new__') {
    // 收起編輯表單；清掉 _editVid 防止後續操作誤動到舊車
    var f = document.getElementById('v-edit-form');
    if (f) f.style.display = 'none';
    window._editVid = '';
    window._editUserId = '';
    var msg = document.getElementById('v-msg');
    if (msg) { msg.textContent = ''; msg.className = 'msg'; }
  }
}

function onTypeChange() {
  var type = document.getElementById('v-type').value;
  var ruleDiv = document.getElementById('v-inspection-rule');
  var rule = INSPECTION_RULES[type];
  if (rule) {
    ruleDiv.innerHTML = '<b>' + type + '</b> 驗車規定：' + rule;
    ruleDiv.style.display = 'block';
  } else {
    ruleDiv.style.display = 'none';
  }
  // 改車型 → 重新自動推算驗車到期日
  autoComputeExpiry();
}

// ── 各車型驗車頻率規則：fn(ageYears) → freqMonths（0 = 免驗） ──
var INSPECTION_FREQ_FN = {
  '自用小客車':           function(a) { if (a < 5) return 0; if (a < 10) return 12; return 6; },
  '自用小貨車':           function(a) { if (a < 5) return 0; if (a < 10) return 12; return 6; },
  '自用小客貨兩用車':     function(a) { if (a < 5) return 0; if (a < 10) return 12; return 6; },
  '自用大客車':           function(a) { return a < 10 ? 12 : 6; },
  '自用大貨車':           function(a) { return a < 10 ? 12 : 6; },
  '自用特種車':           function(a) { return 12; },
  '營業小客車（計程車）': function(a) { return a < 5 ? 12 : 6; },
  '營業小貨車':           function(a) { return a < 5 ? 12 : 6; },
  '營業大客車':           function(a) { return 4; },   // 每年 3 次
  '營業大貨車':           function(a) { return 6; },   // 每年 2 次
  '營業遊覽車':           function(a) { return 4; },   // 每年 3 次
  '營業特種車':           function(a) { return 12; },
  '大型重型機車（550cc以上）': function(a) { return a < 5 ? 0 : 12; },
  '普通重型機車（250cc以上）': function(a) { return a < 5 ? 0 : 12; },
  '普通重型機車（50~250cc）':  function(a) { return a < 5 ? 0 : 12; },
  '普通輕型機車':         function(a) { return a < 5 ? 0 : 12; },
  '小型輕型機車（電動）': function(a) { return a < 5 ? 0 : 12; },
  '拖車':                 function(a) { return 12; },
  '曳引車':               function(a) { return 12; },
  '電動汽車':             function(a) { if (a < 5) return 0; if (a < 10) return 12; return 6; },
};

function _addMonths(d, months) {
  var nd = new Date(d.getTime());
  nd.setMonth(nd.getMonth() + months);
  return nd;
}
function _fmtDate(d) {
  var y = d.getFullYear();
  var m = String(d.getMonth() + 1).padStart(2, '0');
  var dd = String(d.getDate()).padStart(2, '0');
  return y + '-' + m + '-' + dd;
}

// 推算下一個驗車到期日。輸入：vehicleType / 出廠 year / 出廠 month / 原發照 yyyy-mm-dd
function nextInspectionDue(vehicleType, year, month, regDateStr) {
  var ruleFn = INSPECTION_FREQ_FN[vehicleType];
  if (!ruleFn || !year || !regDateStr) return null;
  var manuf = new Date(parseInt(year), (parseInt(month || 1) - 1), 1);
  var regD  = new Date(regDateStr + 'T00:00:00');
  if (isNaN(manuf.getTime()) || isNaN(regD.getTime())) return null;
  var today = new Date(); today.setHours(0,0,0,0);

  // 從 regDate 開始走，找第一個 > today 的到期日
  var cursor = new Date(regD.getTime());
  for (var i = 0; i < 600; i++) {  // 上限 50 年
    var ageMs = cursor.getTime() - manuf.getTime();
    var ageYr = ageMs / (365.25 * 24 * 3600 * 1000);
    var freq = ruleFn(ageYr);
    if (freq === 0) {
      // 免驗階段：往前 1 年再判
      cursor = _addMonths(cursor, 12);
      continue;
    }
    var nextDue = _addMonths(cursor, freq);
    if (nextDue > today) return nextDue;
    cursor = nextDue;
  }
  return null;
}

// 自動填驗車到期日（依車型 + 出廠年月 + 原發照日期）
function autoComputeExpiry() {
  var vt = document.getElementById('v-type').value;
  var ym = document.getElementById('ve-year-month').value;
  var rd = document.getElementById('ve-reg-date').value;
  if (!vt || !ym || !rd) { updateInspectionWindow(); return; }
  var ymParts = ym.split('-');
  if (ymParts.length !== 2) { updateInspectionWindow(); return; }
  var due = nextInspectionDue(vt, ymParts[0], ymParts[1], rd);
  var expEl = document.getElementById('ve-expiry');
  if (due) {
    expEl.value = _fmtDate(due);
  } else {
    // 法規屬於免驗或推算失敗 → 留空（讓使用者手動填）
    expEl.value = '';
  }
  updateInspectionWindow();
}

// --- Vehicles ---
async function loadVehicles() {
  try {
    // 用 admin token 抓全部客戶的車輛（不再只看 admin@system 一人）
    var r = await fetch(CONSOLE_API+'/all/vehicles', {headers: consoleHeaders(false)});
    var d = await r.json();
    var vehicles = d.data || [];
    window._lastVehicles = vehicles;  // 快取給「客戶欄 hover popover」使用
    // Populate vehicle select (existing + new)
    var sel = document.getElementById('v-select');
    var psel = document.getElementById('p-vehicle');
    var opts = '<option value="__new__">' + t('opt_new_vehicle') + '</option>';
    var popts = '<option value="">' + t('opt_unspecified') + '</option>';
    for (var i = 0; i < vehicles.length; i++) {
      var v = vehicles[i];
      var owner = v.customer_name ? ' [' + v.customer_name + ']' : '';
      var label = v.plate_number + ' (' + [v.brand, v.model].filter(Boolean).join(' ') + ')' + owner;
      opts += '<option value="' + v.id + '">' + label + '</option>';
      popts += '<option value="' + v.id + '">' + v.plate_number + owner + '</option>';
    }
    sel.innerHTML = opts;
    psel.innerHTML = popts;
    // Table
    var tb = document.getElementById('v-table');
    var rows = '';
    for (var i = 0; i < vehicles.length; i++) {
      var v = vehicles[i];
      // 行照欄：圖片預覽（如有）+ 上傳/更換按鈕
      var btnLabel = v.registration_image_url ? '更換' : '上傳';
      var imgCell = '';
      if (v.registration_image_url) {
        imgCell = '<img src="' + v.registration_image_url + '" class="preview" style="max-width:80px;max-height:50px;display:block;margin-bottom:3px;border-radius:4px"><a href="' + v.registration_image_url + '" target="_blank" style="font-size:10px;color:#1565C0">看大圖</a><br>';
      } else {
        imgCell = '<span style="color:#999;font-size:11px">未上傳</span><br>';
      }
      imgCell += '<button onclick="uploadRowRegistration(&quot;' + v.id + '&quot;,&quot;' + v.plate_number + '&quot;)" style="padding:3px 10px;font-size:11px;background:#2E7D32;color:#fff;border:none;border-radius:4px;cursor:pointer;margin-top:3px">' + btnLabel + '</button>';
      var ownerCell = v.customer_name
        ? '<div data-hover-cust="' + (v.user_id||'') + '" data-hover-type="vehicle" style="cursor:help">'
            + '<b>' + v.customer_name + '</b>'
            + (v.customer_phone ? '<br><span style="font-size:11px;color:#666">' + v.customer_phone + '</span>' : '')
          + '</div>'
        : '<span style="color:#999">-</span>';
      // 驗車期間 = 到期日 ±30 天 + 顏色標示（過期/即將到期）
      var windowCell = '<span style="color:#999">-</span>';
      if (v.registration_expiry) {
        var expD = new Date(v.registration_expiry + 'T00:00:00');
        if (!isNaN(expD.getTime())) {
          var ws = new Date(expD.getTime()); ws.setDate(ws.getDate() - 30);
          var we = new Date(expD.getTime()); we.setDate(we.getDate() + 30);
          var nowD = new Date(); nowD.setHours(0,0,0,0);
          var color = '#666';  // 預設
          var note = '';
          if (nowD >= ws && nowD <= we) {
            color = '#E65100'; note = (LANG==='en'?' (now)':' (驗車中)');
          } else if (nowD > we) {
            color = '#D32F2F'; note = (LANG==='en'?' (overdue)':' (已逾期)');
          } else if ((ws - nowD) / (24*3600*1000) <= 14) {
            color = '#FF9800'; note = (LANG==='en'?' (soon)':' (即將開始)');
          }
          windowCell = '<span style="font-size:11px;color:' + color + '">'
            + _fmtDate(ws) + '<br>~ ' + _fmtDate(we) + note + '</span>';
        }
      }
      rows += '<tr><td>' + ownerCell + '</td>'
        + '<td><b>' + v.plate_number + '</b></td>'
        + '<td><span style="font-size:11px">' + (v.vehicle_type||'-') + '</span></td>'
        + '<td>' + (v.brand||'-') + '</td>'
        + '<td>' + (v.model||'-') + '</td>'
        + '<td>' + (v.year||'-') + '</td>'
        + '<td>' + (v.color||'-') + '</td>'
        + '<td>' + (v.engine_cc ? v.engine_cc+'cc' : '-') + '</td>'
        + '<td>' + (v.registration_expiry || '<span style="color:#999">-</span>')
        + (v.registration_expiry ? _calBtnHtml('驗車到期 — ' + (v.plate_number||''), v.registration_expiry, '車主：' + (v.customer_name||'') + '\\n品牌車型：' + (v.brand||'') + ' ' + (v.model||'') + '\\n車牌：' + (v.plate_number||'')) : '')
        + '</td>'
        + '<td>' + windowCell + '</td>'
        + '<td>' + imgCell + '</td>'
        + '<td style="white-space:nowrap">'
        + '<button class="btn" style="padding:4px 10px;font-size:11px;margin:1px;background:#1565C0" onclick="editVehicleFromList(&quot;' + v.id + '&quot;)">編輯</button>'
        + '<button class="btn danger" style="padding:4px 10px;font-size:11px;margin:1px" onclick="deleteVehicle(&quot;' + v.id + '&quot;,&quot;' + v.plate_number + '&quot;)">刪除</button>'
        + '</td></tr>';
    }
    tb.innerHTML = rows || '<tr><td colspan="11" style="color:#999;text-align:center">尚無車輛資料</td></tr>';
    // Show initial rule
    onTypeChange();
  } catch(e) {
    console.error('loadVehicles error:', e);
  }
}

function onFileChange() {
  var fileInput = document.getElementById('v-file');
  var file = fileInput.files[0];
  var nameEl = document.getElementById('v-file-name');
  if (nameEl) nameEl.textContent = file ? file.name : t('msg_no_file');
  if (file) {
    var preview = document.getElementById('v-preview');
    if (file.type === 'application/pdf') {
      preview.src = '';
      preview.alt = 'PDF: ' + file.name;
      preview.style.display = 'none';
      showMsg('v-msg', 'ok', 'PDF 已選擇: ' + file.name + ' (上傳後自動轉為圖片)');
    } else {
      var reader = new FileReader();
      reader.onload = function(ev) { preview.src = ev.target.result; preview.style.display = 'block'; };
      reader.readAsDataURL(file);
    }
  }
}

async function uploadRegistration() {
  var vid = document.getElementById('v-select').value;
  var vtype = document.getElementById('v-type').value;
  var fileInput = document.getElementById('v-file');
  var file = fileInput.files[0];
  if (!file) { showMsg('v-msg','err','請選擇行照圖片檔案'); return; }

  // If new vehicle, create one first with the type — 必須先選客戶
  if (vid === '__new__') {
    var cid = currentCustomerId();
    if (!cid) { showMsg('v-msg','err','請先在頂部「操作客戶」選擇要新增車輛的對象'); return; }
    try {
      var createBody = {plate_number: 'NEW-' + Date.now().toString().slice(-6), vehicle_type: vtype};
      var cr = await fetch(CONSOLE_API+'/customer/'+cid+'/vehicles', {method:'POST', headers:consoleHeaders(true), body:JSON.stringify(createBody)});
      var cd = await cr.json();
      if (cd.success && cd.data) {
        vid = cd.data.id;
      } else {
        showMsg('v-msg','err','建立車輛失敗: ' + (cd.detail||cd.message||'')); return;
      }
    } catch(e) { showMsg('v-msg','err','建立車輛失敗: ' + e.message); return; }
  }
  var fd = new FormData();
  fd.append('file', file);
  // Show loading
  document.getElementById('v-upload-btn').disabled = true;
  document.getElementById('v-loading').style.display = 'block';
  document.getElementById('v-loading-text').textContent = '上傳中...';
  document.getElementById('v-edit-form').style.display = 'none';
  document.getElementById('v-ocr-btn').style.display = 'none';
  document.getElementById('v-msg').style.display = 'none';
  try {
    var r = await fetch(CONSOLE_API+'/vehicles/'+vid+'/registration', {
      method: 'POST',
      headers: {'Authorization': 'Bearer ' + ADMIN_TOKEN},
      body: fd
    });
    var d = await r.json();
    document.getElementById('v-loading').style.display = 'none';
    document.getElementById('v-upload-btn').disabled = false;
    if (d.success) {
      showMsg('v-msg', 'ok', d.message);
      window._lastUploadVid = vid;
      window._editVid = vid;
      // 防止下次新增車輛時 state 殘留：明確重置上傳區
      document.getElementById('v-select').value = '__new__';
      document.getElementById('v-file').value = '';
      var nameSpan = document.getElementById('v-file-name');
      if (nameSpan) nameSpan.textContent = t('msg_no_file');
      var preview = document.getElementById('v-preview');
      if (preview) preview.style.display = 'none';
      loadVehicles();
      // 顯示編輯表單 + AI 辨識按鈕
      var veh = d.data.vehicle || {};
      _showEditForm(vid, veh, '行照已上傳，請填寫車輛資料或點 AI 辨識');
      document.getElementById('v-ocr-btn').style.display = 'inline-block';
    } else {
      showMsg('v-msg', 'err', '上傳失敗: ' + (d.detail || d.message));
    }
  } catch(e) {
    document.getElementById('v-loading').style.display = 'none';
    document.getElementById('v-upload-btn').disabled = false;
    showMsg('v-msg', 'err', '上傳失敗: ' + e.message);
  }
}

async function runOcr() {
  var vid = window._editVid || window._lastUploadVid;
  if (!vid) { showMsg('v-msg','err','請先上傳行照'); return; }
  document.getElementById('v-ocr-btn').disabled = true;
  document.getElementById('v-loading').style.display = 'block';
  document.getElementById('v-loading-text').textContent = 'AI 辨識中（首次約 15 秒，配額限制時最多 60 秒）...';
  try {
    var r = await fetch(CONSOLE_API+'/vehicles/'+vid+'/ocr', {
      method: 'POST', headers: {'Authorization': 'Bearer ' + ADMIN_TOKEN}
    });
    var d = await r.json();
    document.getElementById('v-loading').style.display = 'none';
    document.getElementById('v-ocr-btn').disabled = false;
    if (d.success && d.data && d.data.ocr_available) {
      showMsg('v-msg', 'ok', d.message);
      loadVehicles();
      var veh = d.data.vehicle || {};
      _showEditForm(vid, veh, 'AI 辨識結果（可修正後儲存）');
    } else {
      var msg = (d.data && d.message) ? d.message : (d.detail || '辨識失敗');
      if (msg.indexOf('配額') >= 0 || msg.indexOf('quota') >= 0 || msg.indexOf('429') >= 0) {
        showMsg('v-msg', 'err', 'AI 每日免費額度已用完，明天自動恢復。請先手動填寫。');
      } else if (msg.indexOf('餘額') >= 0 || msg.indexOf('credit') >= 0) {
        showMsg('v-msg', 'err', 'AI 帳戶餘額不足，請先手動填寫。');
      } else {
        showMsg('v-msg', 'err', 'AI 暫時不可用，請先手動填寫。');
      }
      _showEditForm(vid, d.data ? (d.data.vehicle || {}) : {}, '請手動填寫車輛資料');
    }
  } catch(e) {
    document.getElementById('v-loading').style.display = 'none';
    document.getElementById('v-ocr-btn').disabled = false;
    showMsg('v-msg', 'err', 'AI 暫時不可用，請先手動填寫。');
    _showEditForm(vid, {}, '請手動填寫車輛資料');
  }
}

function _showEditForm(vid, veh, title) {
  // 從 OCR / upload 流程進來時，先關掉上傳 modal，避免兩層 modal 疊加
  closeVehicleUploadModal();
  window._editVid = vid;
  window._editIsNew = false;
  window._editUserId = veh.user_id || '';
  window._editCustomerNameOrig = veh.customer_name || '';
  window._editCustomerEmailOrig = veh.customer_email || '';
  document.getElementById('v-edit-title').textContent = title;
  document.getElementById('ve-customer-name').value = veh.customer_name || '';
  document.getElementById('ve-customer-email').value = veh.customer_email || '';
  // 顯示已上傳的行照（如有）
  var curImg = document.getElementById('ve-current-image');
  if (veh.registration_image_url) {
    curImg.src = veh.registration_image_url;
    curImg.style.display = 'block';
  } else {
    curImg.style.display = 'none';
  }
  // 重置上傳區
  document.getElementById('ve-file').value = '';
  document.getElementById('ve-file-preview').style.display = 'none';
  document.getElementById('ve-ocr-btn').style.display = 'none';
  document.getElementById('ve-upload-loading').style.display = 'none';
  document.getElementById('ve-plate').value = veh.plate_number || '';
  document.getElementById('ve-brand').value = veh.brand || '';
  document.getElementById('ve-model').value = veh.model || '';
  // 出廠年月：YYYY-MM 格式給 month picker
  var ymVal = '';
  if (veh.year) {
    var mm = veh.manufacture_month ? String(veh.manufacture_month).padStart(2, '0') : '01';
    ymVal = veh.year + '-' + mm;
  }
  document.getElementById('ve-year-month').value = ymVal;
  document.getElementById('ve-color').value = veh.color || '';
  document.getElementById('ve-cc').value = veh.engine_cc || '';
  document.getElementById('ve-vin').value = veh.vin || '';
  document.getElementById('ve-reg-date').value = veh.registration_date || '';
  document.getElementById('ve-reissue-date').value = veh.reissue_date || '';
  document.getElementById('ve-expiry').value = veh.registration_expiry || '';
  document.getElementById('ve-fuel').value = veh.fuel_type || '';
  updateInspectionWindow();
  document.getElementById('v-edit-form').style.display = 'flex';
  refreshRocLabels();
}

async function editVehicleFromList(vid) {
  try {
    // 從全部客戶車輛列表找
    var r = await fetch(CONSOLE_API+'/all/vehicles', {headers: consoleHeaders(false)});
    var d = await r.json();
    var vehicles = d.data || [];
    var veh = vehicles.find(function(v){return v.id === vid;});
    if (!veh) { showMsg('v-msg','err','找不到車輛'); return; }
    _showEditForm(vid, veh, '編輯車輛 — ' + veh.plate_number + ' [' + (veh.customer_name||'?') + ']');
  } catch(e) { showMsg('v-msg','err','讀取失敗: ' + e.message); }
}

// 驗車期間 = 驗車到期日 ± 30 天（依監理規則：到期前 30 天可驗、逾期後 30 天內仍可驗）
function updateInspectionWindow() {
  var exp = document.getElementById('ve-expiry').value;
  var ws = document.getElementById('ve-window-start');
  var we = document.getElementById('ve-window-end');
  if (!exp) { ws.value = ''; we.value = ''; return; }
  var d = new Date(exp + 'T00:00:00');
  if (isNaN(d.getTime())) { ws.value = ''; we.value = ''; return; }
  function fmt(date) {
    var y = date.getFullYear();
    var m = String(date.getMonth() + 1).padStart(2, '0');
    var dd = String(date.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + dd;
  }
  var start = new Date(d.getTime()); start.setDate(start.getDate() - 30);
  var end = new Date(d.getTime()); end.setDate(end.getDate() + 30);
  ws.value = fmt(start);
  we.value = fmt(end);
  refreshRocLabels();
}

// 手動新增車輛 → POST /customer/{cid}/vehicles，成功後切回 PATCH 編輯模式
async function _saveNewVehicleManual() {
  var cid = window._editUserId || currentCustomerId();
  if (!cid) { showMsg('ve-msg','err', t('msg_select_customer_first')); return; }
  var plate = document.getElementById('ve-plate').value.trim();
  if (!plate) {
    showMsg('ve-msg','err',
      LANG==='en' ? 'Plate number is required' : '請至少輸入車牌號碼');
    return;
  }
  var body = { plate_number: plate };
  var brand = document.getElementById('ve-brand').value.trim();
  if (brand) body.brand = brand;
  var model = document.getElementById('ve-model').value.trim();
  if (model) body.model = model;
  var ym = document.getElementById('ve-year-month').value;
  if (ym && /^\\d{4}-\\d{2}$/.test(ym)) {
    var ymParts = ym.split('-');
    body.year = parseInt(ymParts[0]);
    body.manufacture_month = parseInt(ymParts[1]);
  }
  var color = document.getElementById('ve-color').value.trim();
  if (color) body.color = color;
  var cc = document.getElementById('ve-cc').value;
  if (cc) body.engine_cc = parseInt(cc);
  var vin = document.getElementById('ve-vin').value.trim();
  if (vin) body.vin = vin;
  var regDate = document.getElementById('ve-reg-date').value;
  if (regDate) body.registration_date = regDate;
  var reissueDate = document.getElementById('ve-reissue-date').value;
  if (reissueDate) body.reissue_date = reissueDate;
  var expiry = document.getElementById('ve-expiry').value;
  if (expiry) body.registration_expiry = expiry;
  var vtype = document.getElementById('v-type').value;
  if (vtype) body.vehicle_type = vtype;
  var fuel = document.getElementById('ve-fuel').value;
  if (fuel) body.fuel_type = fuel;

  try {
    var r = await fetch(CONSOLE_API+'/customer/'+cid+'/vehicles', {
      method:'POST', headers: consoleHeaders(true), body: JSON.stringify(body)
    });
    var d = await r.json();
    if (!d.success) {
      showMsg('ve-msg','err', d.message || (LANG==='en' ? 'Create failed' : '建立失敗'));
      return;
    }
    var newVid = d.data && d.data.id;
    // 切換到「編輯模式」：後續儲存改走 PATCH，使用者可繼續編輯/上傳行照
    window._editIsNew = false;
    window._editVid = newVid;
    showMsg('ve-msg','ok', t('msg_vehicle_created') +
      (LANG==='en' ? ' — you can now upload registration or continue editing' : '，可繼續上傳行照或編輯'));
    // 客戶 email 若有填，走 email 同步流程（重用 saveEditedVehicle 的後續邏輯）
    var newEmail = document.getElementById('ve-customer-email').value.trim();
    if (newEmail) {
      window._editCustomerEmailOrig = '';
      // 觸發 saveEditedVehicle 走 email-only path
      await saveEditedVehicle();
    }
    if (typeof loadVehicles === 'function') loadVehicles();
  } catch(e) {
    showMsg('ve-msg','err', (LANG==='en' ? 'Network error: ' : '網路錯誤：') + e.message);
  }
}

async function saveEditedVehicle() {
  // ★ 手動新增模式（_editIsNew 且無 vid）→ POST 建立新車輛
  if (window._editIsNew && !window._editVid && !window._lastUploadVid) {
    return await _saveNewVehicleManual();
  }
  var vid = window._editVid || window._lastUploadVid;
  if (!vid) { showMsg('ve-msg','err','找不到車輛 ID'); return; }
  var body = {};
  var plate = document.getElementById('ve-plate').value.trim();
  if (plate) body.plate_number = plate;
  var brand = document.getElementById('ve-brand').value.trim();
  if (brand) body.brand = brand;
  var model = document.getElementById('ve-model').value.trim();
  if (model) body.model = model;
  // 出廠年月：解析 YYYY-MM 為 year + manufacture_month
  var ym = document.getElementById('ve-year-month').value;
  if (ym && /^\\d{4}-\\d{2}$/.test(ym)) {
    var ymParts = ym.split('-');
    body.year = parseInt(ymParts[0]);
    body.manufacture_month = parseInt(ymParts[1]);
  }
  var color = document.getElementById('ve-color').value.trim();
  if (color) body.color = color;
  var cc = document.getElementById('ve-cc').value;
  if (cc) body.engine_cc = parseInt(cc);
  var vin = document.getElementById('ve-vin').value.trim();
  if (vin) body.vin = vin;
  var regDate = document.getElementById('ve-reg-date').value;
  if (regDate) body.registration_date = regDate;
  var reissueDate = document.getElementById('ve-reissue-date').value;
  if (reissueDate) body.reissue_date = reissueDate;
  var expiry = document.getElementById('ve-expiry').value;
  if (expiry) body.registration_expiry = expiry;
  var vtype = document.getElementById('v-type').value;
  if (vtype) body.vehicle_type = vtype;
  try {
    // ① 先更新車輛資料（如有變動）
    var vehicle_changed = Object.keys(body).length > 0;
    var d = {success:true};
    if (vehicle_changed) {
      var r = await fetch(CONSOLE_API+'/vehicles/'+vid, {
        method: 'PATCH', headers: consoleHeaders(true), body: JSON.stringify(body)
      });
      d = await r.json();
    }
    // ② 客戶姓名若有變動 → 找/建立新客戶並轉移車輛（不再 rename 既有客戶）
    var newName = document.getElementById('ve-customer-name').value.trim();
    var origName = window._editCustomerNameOrig || '';
    var transferMsg = '';
    if (newName && newName !== origName) {
      // 撈所有客戶找名稱完全相符的
      var lr = await fetch(CONSOLE_API+'/customers', {headers:consoleHeaders()});
      var allCustomers = (await lr.json()).data || [];
      var match = allCustomers.find(function(c){ return (c.name||'').trim() === newName; });
      var targetCid = '';

      if (match) {
        // 已有同名客戶：詢問是否轉移
        var confirmTransfer = confirm('已存在客戶「' + newName + '」' +
          (match.phone ? ' (電話 ' + match.phone + ')' : '') +
          '\\n\\n要把這台車轉移到該客戶名下嗎？\\n（連同這台車的所有保單一起轉移）');
        if (!confirmTransfer) {
          showMsg('ve-msg', 'ok', '車輛資料已儲存（客戶姓名未變更）');
          if (vehicle_changed) loadVehicles();
          return;
        }
        targetCid = match.id;
      } else {
        // 沒同名 → 建立新客戶並轉移
        var confirmCreate = confirm('找不到客戶「' + newName + '」。\\n\\n要新建客戶並把這台車轉移到他名下嗎？');
        if (!confirmCreate) {
          showMsg('ve-msg', 'ok', '車輛資料已儲存（客戶姓名未變更）');
          if (vehicle_changed) loadVehicles();
          return;
        }
        var cr = await fetch(CONSOLE_API+'/customers', {
          method:'POST', headers:consoleHeaders(true),
          body: JSON.stringify({name: newName})
        });
        var cd = await cr.json();
        if (!cd.success) {
          showMsg('ve-msg', 'err', '建立客戶失敗: ' + (cd.detail || cd.message));
          return;
        }
        targetCid = cd.data.id;
        transferMsg = '（已新建客戶「' + newName + '」並轉移）';
      }

      // 執行轉移
      var tr = await fetch(CONSOLE_API+'/vehicles/'+vid+'/transfer', {
        method:'POST', headers:consoleHeaders(true),
        body: JSON.stringify({customer_id: targetCid})
      });
      var td = await tr.json();
      if (!td.success) {
        showMsg('ve-msg', 'err', '車輛轉移失敗: ' + (td.detail || td.message));
        return;
      }
      window._editCustomerNameOrig = newName;
      window._editUserId = targetCid;
      if (!transferMsg) transferMsg = '（已轉移到既有客戶「' + newName + '」）';
    }
    // ③ Email 若有變動 → 更新目標客戶的 email（轉移後使用最終 user_id）
    var newEmail = document.getElementById('ve-customer-email').value.trim();
    var origEmail = window._editCustomerEmailOrig || '';
    var emailMsg = '';
    if (newEmail !== origEmail) {
      var targetUserId = window._editUserId;
      if (targetUserId) {
        // ★ 先檢查 email 是否屬於「別的」客戶 → 提供轉移選項而非報錯
        if (newEmail) {
          try {
            var cr = await fetch(CONSOLE_API+'/customers', {headers:consoleHeaders()});
            var cd = await cr.json();
            var conflict = (cd.data || []).find(function(c){
              return c.email && c.email.toLowerCase() === newEmail.toLowerCase() && c.id !== targetUserId;
            });
            if (conflict) {
              var msg = (LANG === 'en')
                ? ('This email already belongs to customer "' + conflict.name + '".\\n\\n'
                   + 'Transfer this vehicle (and its policies) to that customer?')
                : ('此 Email 已屬於客戶「' + conflict.name + '」。\\n\\n'
                   + '要將此車輛（含保單）轉移到該客戶嗎？');
              if (!confirm(msg)) {
                showMsg('ve-msg', 'err',
                  (LANG === 'en') ? 'Cancelled. Email not changed.' : '已取消，Email 未更新');
                return;
              }
              // 轉移車輛到目標客戶
              var tr = await fetch(CONSOLE_API+'/vehicles/'+vid+'/transfer', {
                method:'POST', headers:consoleHeaders(true),
                body: JSON.stringify({customer_id: conflict.id})
              });
              var td = await tr.json();
              if (td.success) {
                showMsg('ve-msg', 'ok',
                  (LANG === 'en')
                    ? ('Vehicle transferred to ' + conflict.name)
                    : ('車輛已轉移到「' + conflict.name + '」'));
                loadVehicles();
                return;
              } else {
                showMsg('ve-msg', 'err',
                  (LANG === 'en' ? 'Transfer failed: ' : '轉移失敗: ')
                  + (td.detail || td.message));
                return;
              }
            }
          } catch(_chkE) { /* 偵測失敗 → 走原本流程 */ }
        }
        try {
          var er = await fetch(CONSOLE_API+'/customer/'+targetUserId, {
            method:'PATCH', headers:consoleHeaders(true),
            body: JSON.stringify({email: newEmail || null})
          });
          var ed = await er.json();
          if (ed.success) {
            window._editCustomerEmailOrig = newEmail;
            emailMsg = newEmail
              ? '（Email 已更新為 ' + newEmail + '，客戶可用此 Email 登入）'
              : '（Email 已清除）';
          } else {
            showMsg('ve-msg', 'err', 'Email 更新失敗: ' + (ed.detail || ed.message));
            return;
          }
        } catch(ex) {
          showMsg('ve-msg', 'err', 'Email 更新失敗: ' + ex.message);
          return;
        }
      }
    }
    if (d.success) {
      showMsg('ve-msg', 'ok', '車輛資料已儲存' + transferMsg + emailMsg);
      showMsg('v-msg', 'ok', '車輛資料已儲存');
      loadVehicles();
    } else {
      showMsg('ve-msg', 'err', '儲存失敗: ' + (d.detail || d.message));
    }
  } catch(e) {
    showMsg('ve-msg', 'err', '儲存失敗: ' + e.message);
  }
}

// ── 編輯表單內的行照直接上傳 ──
function onEditFileChange() {
  var f = document.getElementById('ve-file').files[0];
  var preview = document.getElementById('ve-file-preview');
  var nameEl = document.getElementById('ve-file-name');
  if (nameEl) nameEl.textContent = f ? f.name : t('msg_no_file');
  if (!f) { preview.style.display = 'none'; return; }
  if (f.type === 'application/pdf') {
    preview.style.display = 'none';
    showMsg('ve-msg','ok','PDF 已選擇: ' + f.name);
  } else {
    var reader = new FileReader();
    reader.onload = function(ev){ preview.src = ev.target.result; preview.style.display = 'block'; };
    reader.readAsDataURL(f);
  }
}

async function uploadRegistrationDirect() {
  var vid = window._editVid;
  if (!vid) { showMsg('ve-msg','err','尚未選擇車輛'); return; }
  var file = document.getElementById('ve-file').files[0];
  if (!file) { showMsg('ve-msg','err','請先選擇行照圖片'); return; }
  var fd = new FormData(); fd.append('file', file);
  document.getElementById('ve-upload-loading').style.display = 'block';
  document.getElementById('ve-upload-text').textContent = '上傳中...';
  try {
    var r = await fetch(CONSOLE_API+'/vehicles/'+vid+'/registration', {
      method: 'POST',
      headers: {'Authorization': 'Bearer ' + ADMIN_TOKEN},
      body: fd
    });
    var d = await r.json();
    document.getElementById('ve-upload-loading').style.display = 'none';
    if (d.success) {
      showMsg('ve-msg', 'ok', '行照已上傳');
      // 立即更新預覽顯示新上傳的圖
      var veh = d.data.vehicle || {};
      if (veh.registration_image_url) {
        var ci = document.getElementById('ve-current-image');
        ci.src = veh.registration_image_url + '?t=' + Date.now();
        ci.style.display = 'block';
      }
      document.getElementById('ve-ocr-btn').style.display = 'inline-block';
      loadVehicles();
    } else {
      showMsg('ve-msg','err','上傳失敗: ' + (d.detail || d.message));
    }
  } catch(e) {
    document.getElementById('ve-upload-loading').style.display = 'none';
    showMsg('ve-msg','err','上傳失敗: ' + e.message);
  }
}

async function ocrRegistrationDirect() {
  var vid = window._editVid;
  if (!vid) { showMsg('ve-msg','err','尚未選擇車輛'); return; }
  document.getElementById('ve-upload-loading').style.display = 'block';
  document.getElementById('ve-upload-text').textContent = 'AI 辨識中（首次約 15 秒）...';
  try {
    var r = await fetch(CONSOLE_API+'/vehicles/'+vid+'/ocr', {
      method: 'POST', headers: {'Authorization': 'Bearer ' + ADMIN_TOKEN}
    });
    var d = await r.json();
    document.getElementById('ve-upload-loading').style.display = 'none';
    if (d.success && d.data && d.data.ocr_available) {
      showMsg('ve-msg','ok','AI 辨識完成，欄位已自動填入');
      // 把辨識結果回填到表單
      var veh = d.data.vehicle || {};
      document.getElementById('ve-plate').value = veh.plate_number || document.getElementById('ve-plate').value;
      document.getElementById('ve-brand').value = veh.brand || document.getElementById('ve-brand').value;
      document.getElementById('ve-model').value = veh.model || document.getElementById('ve-model').value;
      // 出廠年月：veh.year + veh.manufacture_month → YYYY-MM
      if (veh.year) {
        var _mm = veh.manufacture_month ? String(veh.manufacture_month).padStart(2, '0') : '01';
        document.getElementById('ve-year-month').value = veh.year + '-' + _mm;
      }
      document.getElementById('ve-color').value = veh.color || document.getElementById('ve-color').value;
      document.getElementById('ve-cc').value = veh.engine_cc || document.getElementById('ve-cc').value;
      document.getElementById('ve-vin').value = veh.vin || document.getElementById('ve-vin').value;
      if (veh.registration_date) document.getElementById('ve-reg-date').value = veh.registration_date;
      if (veh.reissue_date) document.getElementById('ve-reissue-date').value = veh.reissue_date;
      if (veh.registration_expiry) document.getElementById('ve-expiry').value = veh.registration_expiry;
      if (veh.fuel_type) document.getElementById('ve-fuel').value = veh.fuel_type;
      updateInspectionWindow();
      loadVehicles();
    } else {
      showMsg('ve-msg','err','AI 辨識失敗或配額不足，請手動填寫');
    }
  } catch(e) {
    document.getElementById('ve-upload-loading').style.display = 'none';
    showMsg('ve-msg','err','AI 辨識失敗: ' + e.message);
  }
}

// ── 表格 row 內的「上傳/更換」按鈕 ──
function uploadRowRegistration(vid, plate) {
  window._rowUploadVid = vid;
  window._rowUploadPlate = plate;
  document.getElementById('row-upload-file').value = '';
  document.getElementById('row-upload-file').click();  // 觸發系統檔案選擇對話框
}

async function onRowFileSelected() {
  var file = document.getElementById('row-upload-file').files[0];
  if (!file) return;
  var vid = window._rowUploadVid;
  var plate = window._rowUploadPlate || '';
  if (!vid) { showMsg('v-msg','err','找不到車輛 ID'); return; }

  var fd = new FormData(); fd.append('file', file);
  showMsg('v-msg','ok','上傳中：' + plate + ' …');
  try {
    var r = await fetch(CONSOLE_API+'/vehicles/'+vid+'/registration', {
      method: 'POST',
      headers: {'Authorization': 'Bearer ' + ADMIN_TOKEN},
      body: fd
    });
    var d = await r.json();
    if (d.success) {
      // 詢問是否立即 OCR
      var doOcr = confirm('行照已上傳成功（' + plate + '）。\\n\\n要立即執行 AI 自動辨識並填入車輛資料嗎？');
      if (doOcr) {
        showMsg('v-msg','ok','AI 辨識中（首次約 15 秒）...');
        try {
          var or = await fetch(CONSOLE_API+'/vehicles/'+vid+'/ocr', {
            method: 'POST', headers: {'Authorization':'Bearer ' + ADMIN_TOKEN}
          });
          var od = await or.json();
          if (od.success && od.data && od.data.ocr_available) {
            showMsg('v-msg','ok',plate + ' 行照已上傳 + AI 辨識完成');
          } else {
            showMsg('v-msg','ok',plate + ' 行照已上傳（AI 辨識失敗或配額不足）');
          }
        } catch(e) { showMsg('v-msg','ok',plate + ' 行照已上傳（AI 辨識異常）'); }
      } else {
        showMsg('v-msg','ok',plate + ' 行照已上傳');
      }
      loadVehicles();  // 刷新表格
    } else {
      showMsg('v-msg','err','上傳失敗: ' + (d.detail || d.message));
    }
  } catch(e) {
    showMsg('v-msg','err','上傳失敗: ' + e.message);
  }
}

async function deleteVehicle(vid, plate) {
  if (!confirm('確定要刪除車輛 ' + plate + ' 嗎？此操作無法復原。')) return;
  try {
    var r = await fetch(CONSOLE_API+'/vehicles/'+vid, {
      method: 'DELETE', headers: consoleHeaders(false)
    });
    var d = await r.json();
    if (d.success) {
      showMsg('v-msg', 'ok', plate + ' 已刪除');
      loadVehicles();
    } else {
      showMsg('v-msg', 'err', '刪除失敗: ' + (d.detail || d.message));
    }
  } catch(e) {
    showMsg('v-msg', 'err', '刪除失敗: ' + e.message);
  }
}

// --- Policy Upload + OCR ---
function onPolicyFileChange() {
  var file = document.getElementById('p-file').files[0];
  var nameEl = document.getElementById('p-file-name');
  if (nameEl) nameEl.textContent = file ? file.name : t('msg_no_file');
  if (file) {
    var preview = document.getElementById('p-preview');
    if (file.type === 'application/pdf') {
      preview.src = '';
      preview.style.display = 'none';
      showMsg('p-upload-msg', 'ok', 'PDF 已選擇: ' + file.name);
    } else {
      var reader = new FileReader();
      reader.onload = function(ev) { preview.src = ev.target.result; preview.style.display = 'block'; };
      reader.readAsDataURL(file);
    }
  }
}

async function uploadPolicy() {
  var file = document.getElementById('p-file').files[0];
  if (!file) { showMsg('p-upload-msg','err','請選擇保單檔案'); return; }
  var fd = new FormData();
  fd.append('file', file);
  document.getElementById('p-upload-btn').disabled = true;
  document.getElementById('p-upload-loading').style.display = 'block';
  document.getElementById('p-loading-text').textContent = '上傳中...';
  document.getElementById('p-ocr-result').style.display = 'none';
  document.getElementById('p-ocr-btn').style.display = 'none';
  document.getElementById('p-upload-msg').style.display = 'none';
  try {
    var r = await fetch(CONSOLE_API+'/policies/upload-scan', {
      method: 'POST', headers: {'Authorization':'Bearer '+ADMIN_TOKEN}, body: fd
    });
    var d = await r.json();
    document.getElementById('p-upload-loading').style.display = 'none';
    document.getElementById('p-upload-btn').disabled = false;
    if (d.success) {
      showMsg('p-upload-msg', 'ok', d.message);
      window._lastPolicyFilename = d.data.filename;
      document.getElementById('p-ocr-btn').style.display = 'inline-block';
    } else {
      showMsg('p-upload-msg', 'err', '上傳失敗: ' + (d.detail || d.message));
    }
  } catch(e) {
    document.getElementById('p-upload-loading').style.display = 'none';
    document.getElementById('p-upload-btn').disabled = false;
    showMsg('p-upload-msg', 'err', '上傳失敗: ' + e.message);
  }
}

async function runPolicyOcr() {
  var fn = window._lastPolicyFilename;
  if (!fn) { showMsg('p-upload-msg','err', LANG==='en' ? 'Upload policy file first' : '請先上傳保單'); return; }
  var cid = currentCustomerId();
  if (!cid) { showMsg('p-upload-msg','err', LANG==='en' ? 'No customer context' : '找不到操作客戶'); return; }
  document.getElementById('p-ocr-btn').disabled = true;
  document.getElementById('p-upload-loading').style.display = 'block';
  document.getElementById('p-loading-text').textContent = 'AI 辨識中（首次約 15 秒，配額限制時最多 60 秒）...';
  document.getElementById('p-ocr-result').style.display = 'none';
  try {
    var r = await fetch(CONSOLE_API+'/customer/'+cid+'/policies/ocr-scan?filename='+encodeURIComponent(fn), {
      method: 'POST', headers: {'Authorization':'Bearer '+ADMIN_TOKEN}
    });
    var d = await r.json();
    document.getElementById('p-upload-loading').style.display = 'none';
    document.getElementById('p-ocr-btn').disabled = false;
    if (d.success) {
      showMsg('p-upload-msg', 'ok', d.message);
      loadPolicies();
      if (d.data && d.data.ocr_available && d.data.ocr_result) {
        var ocr = d.data.ocr_result;
        var fields = [
          ['保險公司', ocr.insurer_name], ['保單號碼', ocr.policy_number],
          ['被保險人', ocr.insured_name], ['車牌號碼', ocr.plate_number],
          ['起保日', ocr.start_date], ['到期日', ocr.end_date],
          ['總保費', ocr.total_premium ? '$'+Number(ocr.total_premium).toLocaleString() : null],
        ];
        var html = '';
        for (var i = 0; i < fields.length; i++) {
          var display = fields[i][1] ? String(fields[i][1]) : '<span style="color:#999">未辨識</span>';
          html += '<tr><td style="width:100px;color:#666;padding:4px 8px"><b>'+fields[i][0]+'</b></td>'
            + '<td style="padding:4px 8px">'+display+'</td></tr>';
        }
        var items = ocr.items || [];
        if (items.length > 0) {
          html += '<tr><td colspan="2" style="padding:8px 0 4px;color:#1565C0;font-weight:bold">保障項目 ('+items.length+')</td></tr>';
          for (var j = 0; j < items.length; j++) {
            var it = items[j];
            var cov = it.coverage_limit ? ' $'+Number(it.coverage_limit).toLocaleString() : '';
            html += '<tr><td style="padding:2px 8px;color:#666">'+(j+1)+'.</td>'
              + '<td style="padding:2px 8px">'+it.item_name+cov+'</td></tr>';
          }
        }
        document.getElementById('p-ocr-table').querySelector('tbody').innerHTML = html;
        document.getElementById('p-ocr-result').style.display = 'block';
      }
      if (d.data && d.data.policy) {
        var pol = d.data.policy;
        showMsg('p-upload-msg', 'ok', '保單已建立: '+pol.insurer_name+' '+pol.policy_number+' ('+pol.items.length+' 項保障)');
      }
    } else {
      var pmsg = d.message || d.detail || '';
      if (pmsg.indexOf('配額') >= 0 || pmsg.indexOf('quota') >= 0 || pmsg.indexOf('429') >= 0) {
        showMsg('p-upload-msg', 'err', 'AI 每日免費額度已用完，明天自動恢復。請用下方手動表單建立保單。');
      } else {
        showMsg('p-upload-msg', 'err', 'AI 暫時不可用，請用下方手動表單建立保單。');
      }
    }
  } catch(e) {
    document.getElementById('p-upload-loading').style.display = 'none';
    document.getElementById('p-ocr-btn').disabled = false;
    showMsg('p-upload-msg', 'err', 'AI 暫時不可用，請用下方手動表單建立保單。');
  }
}

// --- Claims ---
async function loadClaims() {
  try {
    var r = await fetch(API+'/api/v1/claims', {headers: authHeaders(false)});
    var d = await r.json();
    var claims = d.data || [];
    if (claims.length === 0) {
      document.getElementById('claims-list').innerHTML = '<p style="color:#999">尚無理賠申請</p>';
      return;
    }
    var html = '<table><thead><tr><th>案號</th><th>狀態</th><th>類型</th><th>申請金額</th><th>申請時間</th><th>操作</th></tr></thead><tbody>';
    for (var i = 0; i < claims.length; i++) {
      var c = claims[i];
      var amt = c.claimed_amount ? '$' + Number(c.claimed_amount).toLocaleString() : '-';
      var time = c.submitted_at ? c.submitted_at.substring(0, 16).replace('T', ' ') : '-';
      html += '<tr><td><b>' + c.claim_number + '</b></td><td>' + c.status + '</td><td>' + (c.claim_type||'-') + '</td>';
      html += '<td>' + amt + '</td><td style="font-size:12px">' + time + '</td>';
      html += '<td style="white-space:nowrap">';
      html += '<a class="btn" style="padding:3px 8px;font-size:11px;margin:1px;text-decoration:none" href="' + API + '/api/v1/claims/' + c.id + '/export-pdf" target="_blank">PDF</a>';
      html += '<a class="btn success" style="padding:3px 8px;font-size:11px;margin:1px;text-decoration:none" href="' + API + '/api/v1/claims/' + c.id + '/export-csv" target="_blank">CSV</a>';
      html += '</td></tr>';
    }
    html += '</tbody></table>';
    document.getElementById('claims-list').innerHTML = html;
  } catch(e) {
    document.getElementById('claims-list').innerHTML = '<p style="color:red">載入失敗: ' + e.message + '</p>';
  }
}

// --- Accidents ---
async function loadAccidents() {
  try {
    var r = await fetch(API+'/api/v1/accidents', {headers: authHeaders(false)});
    var d = await r.json();
    var accidents = d.data || [];
    if (accidents.length === 0) {
      document.getElementById('acc-list').innerHTML = '<p style="color:#999">尚無事故記錄</p>';
      return;
    }
    var html = '';
    for (var i = 0; i < accidents.length; i++) {
      var acc = accidents[i];
      html += '<div class="card" style="margin-bottom:12px;padding:12px">';
      html += '<div style="display:flex;justify-content:space-between;align-items:center">';
      html += '<b>事故 #' + (acc.id || '').substring(0,8) + '</b>';
      html += '<span style="font-size:11px;color:#888">' + (acc.occurred_at || acc.created_at || '') + '</span>';
      html += '</div>';
      // Load photos for this accident
      html += '<div id="acc-photos-' + acc.id + '" style="margin-top:8px"><button class="btn" style="padding:4px 10px;font-size:11px" onclick="loadAccidentPhotos(&quot;' + acc.id + '&quot;)">載入照片</button></div>';
      html += '</div>';
    }
    document.getElementById('acc-list').innerHTML = html;
  } catch(e) {
    document.getElementById('acc-list').innerHTML = '<p style="color:red">載入失敗: ' + e.message + '</p>';
  }
}

async function loadAccidentPhotos(accId) {
  var container = document.getElementById('acc-photos-' + accId);
  try {
    var r = await fetch(API+'/api/v1/accidents/' + accId, {headers: authHeaders(false)});
    var d = await r.json();
    var acc = d.data || {};
    var photos = acc.photos || [];
    var photoLabels = {
      my_plate_front:'我方前車牌', my_plate_rear:'我方後車牌',
      other_plate_front:'對方前車牌', other_plate_rear:'對方後車牌',
      left_front:'車輛左前', front:'車輛正前', right_front:'車輛右前',
      right_side:'車輛右側', right_rear:'車輛右後', rear:'車輛正後',
      left_rear:'車輛左後', left_side:'車輛左側',
      scene_1:'事故現場1', scene_2:'事故現場2', scene_3:'事故現場3',
      police_report:'警方三聯單'
    };
    if (photos.length === 0) {
      container.innerHTML = '<p style="font-size:12px;color:#999">尚無照片</p>';
      return;
    }
    var html = '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-top:8px">';
    for (var i = 0; i < photos.length; i++) {
      var p = photos[i];
      var label = photoLabels[p.photo_type] || p.photo_type || ('照片' + (i+1));
      html += '<div style="text-align:center">';
      html += '<img src="' + p.image_url + '" style="width:100%;height:60px;object-fit:cover;border-radius:4px;border:1px solid #ddd">';
      html += '<p style="font-size:9px;color:#666;margin-top:2px">' + label + '</p>';
      html += '</div>';
    }
    html += '</div>';
    container.innerHTML = html;
  } catch(e) {
    container.innerHTML = '<p style="font-size:12px;color:red">載入失敗</p>';
  }
}

// --- Policies (Manual) ---

// === 保單上傳/手動 modal 開關 ===
function closePolicyUploadModal() {
  var m = document.getElementById('p-upload-modal');
  if (m) m.style.display = 'none';
}
async function closePolicyFormModal() {
  // 表單若有實質內容 → 詢問是否要先儲存（避免 user 按完成卻沒按建立保單就資料遺失）
  if (typeof _policyFormHasContent === 'function' && _policyFormHasContent()) {
    var ans = confirm(LANG === 'en'
      ? 'You have unsaved policy data.\\n\\nOK = Save before closing\\nCancel = Discard and close'
      : '保單尚未儲存。\\n\\n[確定] = 儲存後關閉\\n[取消] = 不儲存直接關閉');
    if (ans) {
      var ok = await createPolicy();
      if (!ok) return;  // 儲存失敗就停在 modal，不關閉
    }
  }
  var m = document.getElementById('p-form-modal');
  if (m) m.style.display = 'none';
}

// 「+ 新增保單（手動）」入口：一律先彈「選擇/新增客戶」 picker
function openManualPolicyForm() {
  openCreateCustomerModal(function() { _doOpenManualPolicyFormForCurrent(); });
}
function _doOpenManualPolicyFormForCurrent() {
  var cid = currentCustomerId();
  if (!cid) return;
  closePolicyUploadModal();
  // 客戶名稱顯示
  var sel = document.getElementById('cur-customer');
  var custName = '';
  if (sel && sel.selectedIndex >= 0) {
    custName = (sel.options[sel.selectedIndex].text || '').split(' · ')[0].trim();
  }
  var lbl = document.getElementById('p-form-modal-customer');
  if (lbl) lbl.textContent = custName || '(未選擇)';
  // 載入此客戶的車輛清單到 p-vehicle
  loadVehiclesForPolicySelect(cid);
  // 重置表單
  _resetPolicyFormFields();
  var msg = document.getElementById('p-msg');
  if (msg) { msg.textContent = ''; msg.className = 'msg'; }
  document.getElementById('p-form-modal').style.display = 'flex';
  setTimeout(function(){ _recheckInsuredAlignment('p'); }, 0);
}

// 「+ 新增保單（上傳辨識）」入口
function openPolicyUploadModal() {
  openCreateCustomerModal(function() { _doOpenPolicyUploadModalForCurrent(); });
}
function _doOpenPolicyUploadModalForCurrent() {
  var cid = currentCustomerId();
  if (!cid) return;
  closePolicyFormModal();
  var sel = document.getElementById('cur-customer');
  var custName = '';
  if (sel && sel.selectedIndex >= 0) {
    custName = (sel.options[sel.selectedIndex].text || '').split(' · ')[0].trim();
  }
  var lbl = document.getElementById('p-upload-modal-customer');
  if (lbl) lbl.textContent = custName || '(未選擇)';
  // 重置上傳區
  document.getElementById('p-file').value = '';
  var nameSpan = document.getElementById('p-file-name');
  if (nameSpan) nameSpan.textContent = t('msg_no_file');
  var preview = document.getElementById('p-preview');
  if (preview) preview.style.display = 'none';
  var ocrBtn = document.getElementById('p-ocr-btn');
  if (ocrBtn) ocrBtn.style.display = 'none';
  var loading = document.getElementById('p-upload-loading');
  if (loading) loading.style.display = 'none';
  var msg = document.getElementById('p-upload-msg');
  if (msg) { msg.textContent = ''; msg.className = 'msg'; }
  var ocrResult = document.getElementById('p-ocr-result');
  if (ocrResult) ocrResult.style.display = 'none';
  var upBtn = document.getElementById('p-upload-btn');
  if (upBtn) upBtn.disabled = false;
  document.getElementById('p-upload-modal').style.display = 'flex';
}

// 「+ 新增此客戶另一張保單」按鈕（modal 內）→ 不再彈 picker，直接重置表單繼續
function addAnotherPolicySameCustomer() {
  var cid = currentCustomerId();
  if (!cid) {
    showMsg('p-msg','err', LANG === 'en' ? 'No customer context' : '找不到目前操作客戶');
    return;
  }
  _resetPolicyFormFields();
  var msg = document.getElementById('p-msg');
  if (msg) { msg.textContent = ''; msg.className = 'msg'; }
}

// 撈該客戶名下的車輛 → 填入 p-vehicle dropdown
async function loadVehiclesForPolicySelect(cid) {
  var dd = document.getElementById('p-vehicle');
  if (!dd) return;
  dd.innerHTML = '<option value="">' + (LANG==='en' ? 'Not specified' : '不指定') + '</option>';
  try {
    var r = await fetch(CONSOLE_API+'/customer/'+cid+'/vehicles', {headers: consoleHeaders(false)});
    var d = await r.json();
    var vs = d.data || [];
    for (var i = 0; i < vs.length; i++) {
      var v = vs[i];
      // 此 endpoint 把車牌存成 v.plate（非 v.plate_number），先 plate 後 plate_number 兼容
      var plate = v.plate || v.plate_number || (LANG==='en' ? '(no plate)' : '(無車牌)');
      var brand = v.brand || '';
      var model = v.model || '';
      var label = plate + (brand || model ? ' — ' + (brand + ' ' + model).trim() : '');
      dd.innerHTML += '<option value="' + v.id + '">' + label + '</option>';
    }
  } catch(e) { /* ignore */ }
}

let itemCount = 0;
// 共用建項目 row 的工具：containerId 指定要 append 到哪個 div；values 可選預填 {item_name, coverage_limit, deductible, premium}
function _buildItemRow(containerId, values) {
  itemCount++;
  values = values || {};
  const div = document.createElement('div');
  div.className = 'item-row';
  div.id = 'item-' + itemCount;
  // helper: 把數字 → 千分位字串
  function fmt(v){ if (v == null || v === '') return ''; return Number(v).toLocaleString('en-US', {maximumFractionDigits:2}); }
  function esc(v){ return (v == null ? '' : String(v).replace(/"/g,'&quot;')); }
  // 最後一欄（保費）按 Enter → 自動加新一列並 focus 到「項目名稱」
  var enterHook = "if(event.key==='Enter'){event.preventDefault();_onItemPremiumEnter(this,'" + containerId + "');}";
  div.innerHTML =
    '<input placeholder="' + t('ph_item_name') + '" data-field="item_name" value="' + esc(values.item_name) + '">' +
    '<input type="text" inputmode="decimal" oninput="formatThousand(this)" placeholder="' + t('ph_coverage_limit') + '" data-field="coverage_limit" style="max-width:120px" value="' + esc(fmt(values.coverage_limit)) + '">' +
    '<input type="text" inputmode="decimal" oninput="formatThousand(this)" placeholder="' + t('ph_deductible') + '" data-field="deductible" style="max-width:100px" value="' + esc(fmt(values.deductible)) + '">' +
    '<input type="text" inputmode="decimal" oninput="formatThousand(this)" onkeydown="' + enterHook + '" placeholder="' + t('ph_premium') + '" data-field="premium" style="max-width:100px" value="' + esc(fmt(values.premium)) + '">' +
    '<button class="btn danger" onclick="this.parentElement.remove()">X</button>';
  document.getElementById(containerId).appendChild(div);
}

// 保費欄按 Enter → 加一列空 row 並聚焦第一格（連續快速輸入專用）
function _onItemPremiumEnter(inp, containerId) {
  if (containerId === 'pe-items') addEditItemRow();
  else addItemRow();
  setTimeout(function(){
    var rows = document.querySelectorAll('#' + containerId + ' .item-row');
    var newRow = rows[rows.length - 1];
    if (newRow) {
      var first = newRow.querySelector('input[data-field="item_name"]');
      if (first) first.focus();
    }
  }, 0);
}

function addItemRow() { _buildItemRow('p-items'); }
function addEditItemRow() { _buildItemRow('pe-items'); }

// 從 .item-row 列表收集成 array（金額用 parseThousand 拆千分位）
function _collectItemRows(containerId) {
  var out = [];
  document.querySelectorAll('#' + containerId + ' .item-row').forEach(function(row){
    var item = {};
    row.querySelectorAll('input').forEach(function(inp){
      var f = inp.dataset.field;
      if (!f) return;
      if (f === 'item_name') item[f] = inp.value;
      else if (inp.value) {
        var n = parseThousand(inp.value);
        if (n != null) item[f] = n;
      }
    });
    if (item.item_name) out.push(item);
  });
  return out;
}

async function createPolicy() {
  const insurer = getInsurerValue('p-insurer', 'p-insurer-other');
  const number = document.getElementById('p-number').value.trim();
  if (!insurer || !number) { showMsg('p-msg','err', LANG==='en' ? 'Insurer and policy number are required' : '請填寫保險公司和保單號碼'); return; }
  // 防呆：被保人 vs 車主姓名不一致 → 二次確認
  var __pInName = (document.getElementById('p-in-name').value || '').trim();
  var __pCustName = _getCustomerNameForPolicy('p');
  if (__pInName && __pCustName && __pInName !== __pCustName) {
    if (!confirm('⚠️ 被保人「' + __pInName + '」與車主「' + __pCustName + '」不一致。\\n\\n台灣車險被保人通常應為車輛登記車主，否則理賠時可能受影響。\\n\\n確定要繼續儲存嗎？')) return false;
  }
  var sParts = _readDatePair('p-start');
  var eParts = _readDatePair('p-end');
  var csParts = _readDatePair('p-cstart');
  var ceParts = _readDatePair('p-cend');
  const body = {
    insurer_name: insurer,
    policy_number: number,
    vehicle_id: document.getElementById('p-vehicle').value || null,
    status: document.getElementById('p-status').value,
    start_date: sParts.date,
    end_date: eParts.date,
    start_time: sParts.time,
    end_time: eParts.time,
    compulsory_insurer_name: getInsurerValue('p-cinsurer','p-cinsurer-other') || null,
    compulsory_policy_number: (document.getElementById('p-cnumber').value || '').trim() || null,
    compulsory_premium: parseThousand(document.getElementById('p-cpremium').value),
    compulsory_start_date: csParts.date,
    compulsory_end_date: ceParts.date,
    compulsory_start_time: csParts.time,
    compulsory_end_time: ceParts.time,
    // 要保人 / 被保人
    policyholder_name: (document.getElementById('p-ph-name').value || '').trim() || null,
    policyholder_id_number: (document.getElementById('p-ph-id').value || '').trim().toUpperCase() || null,
    policyholder_birth_date: document.getElementById('p-ph-birth').value || null,
    policyholder_gender: document.getElementById('p-ph-gender').value || null,
    policyholder_phone: (document.getElementById('p-ph-phone').value || '').trim() || null,
    policyholder_relation_to_owner: (document.getElementById('p-ph-relation').value || '').trim() || null,
    insured_name: (document.getElementById('p-in-name').value || '').trim() || null,
    insured_id_number: (document.getElementById('p-in-id').value || '').trim().toUpperCase() || null,
    insured_birth_date: document.getElementById('p-in-birth').value || null,
    insured_gender: document.getElementById('p-in-gender').value || null,
    insured_phone: (document.getElementById('p-in-phone').value || '').trim() || null,
    total_premium: parseThousand(document.getElementById('p-premium').value),
    items: []
  };
  // Collect items（金額欄位有千分位逗號 → 用 parseThousand）
  document.querySelectorAll('.item-row').forEach(row => {
    const item = {};
    row.querySelectorAll('input').forEach(inp => {
      const f = inp.dataset.field;
      if (f) {
        if (f === 'item_name') item[f] = inp.value;
        else if (inp.value) {
          var n = parseThousand(inp.value);
          if (n != null) item[f] = n;
        }
      }
    });
    if (item.item_name) body.items.push(item);
  });
  var cid = currentCustomerId();
  if (!cid) { showMsg('p-msg','err', LANG==='en' ? 'No customer context' : '找不到操作客戶'); return; }
  try {
    const r = await fetch(CONSOLE_API+'/customer/'+cid+'/policies', {method:'POST', headers:consoleHeaders(true), body:JSON.stringify(body)});
    const d = await r.json();
    if (d.success) {
      showMsg('p-msg','ok', (LANG==='en' ? 'Policy created: ' : '保單建立成功：') + d.data.policy_number);
      loadPolicies();
      // 留在 modal、清空表單，方便接續按「+新增此客戶另一張保單」或關閉
      _resetPolicyFormFields();
      return true;
    } else {
      showMsg('p-msg','err', (LANG==='en' ? 'Create failed: ' : '建立失敗：') + (d.detail||d.message));
      return false;
    }
  } catch(e) {
    showMsg('p-msg','err', (LANG==='en' ? 'Create failed: ' : '建立失敗：') + e.message);
    return false;
  }
}

// 偵測手動新增保單表單是否有實質內容（提醒未儲存用）
function _policyFormHasContent() {
  if (getInsurerValue('p-insurer','p-insurer-other')) return true;
  if ((document.getElementById('p-number').value || '').trim()) return true;
  if (parseThousand(document.getElementById('p-premium').value) != null) return true;
  if (getInsurerValue('p-cinsurer','p-cinsurer-other')) return true;
  if ((document.getElementById('p-cnumber').value || '').trim()) return true;
  if (parseThousand(document.getElementById('p-cpremium').value) != null) return true;
  if ((document.getElementById('p-start').value || '').trim()) return true;
  if ((document.getElementById('p-cstart').value || '').trim()) return true;
  if (document.querySelectorAll('.item-row').length > 0) return true;
  return false;
}

function _resetPolicyFormFields() {
  fillInsurerSelect('p-insurer', 'p-insurer-other', '');
  fillInsurerSelect('p-cinsurer', 'p-cinsurer-other', '');
  ['p-number','p-premium','p-cnumber','p-cpremium',
   'p-ph-name','p-ph-id','p-ph-birth','p-ph-gender','p-ph-phone','p-ph-relation',
   'p-in-name','p-in-id','p-in-birth','p-in-gender','p-in-phone'].forEach(function(id){
    var el = document.getElementById(id);
    if (el) el.value = '';
  });
  _writeDatePair('p-start', '', '');
  _writeDatePair('p-end', '', '');
  _writeDatePair('p-cstart', '', '');
  _writeDatePair('p-cend', '', '');
  // 清手動編輯標記，下次新建起保日仍能自動帶到期
  ['p-end','p-end-time','p-cend','p-cend-time'].forEach(function(id){
    var el = document.getElementById(id);
    if (el) delete el.dataset.manualEdit;
  });
  document.getElementById('p-status').value = 'active';
  document.getElementById('p-items').innerHTML = '';
  itemCount = 0;
  refreshRocLabels();
}

// 起保日 / 起保時 變動 → 到期日 = 起保日 + 1 年（同月日 + 同時分；除非使用者已手動修改到期）
function autoComputePolicyEnd() {
  var startD = document.getElementById('p-start');
  var startT = document.getElementById('p-start-time');
  var endD = document.getElementById('p-end');
  var endT = document.getElementById('p-end-time');
  if (!startD || !endD) return;
  if ((endD.dataset.manualEdit === '1') || (endT && endT.dataset.manualEdit === '1')) return;
  var s = startD.value;
  if (!s) return;
  var d = new Date(s + 'T00:00:00');
  if (isNaN(d.getTime())) return;
  d.setFullYear(d.getFullYear() + 1);
  var y = d.getFullYear();
  var m = String(d.getMonth() + 1).padStart(2, '0');
  var dd = String(d.getDate()).padStart(2, '0');
  endD.value = y + '-' + m + '-' + dd;
  if (endT) endT.value = startT ? (startT.value || '') : '';
  refreshRocLabels();
}

// 使用者手動改了到期日 / 到期時 → 標記後續起保變動不再自動覆蓋
function markPolicyEndManual() {
  var endD = document.getElementById('p-end');
  var endT = document.getElementById('p-end-time');
  if (endD) endD.dataset.manualEdit = endD.value ? '1' : '0';
  if (endT) endT.dataset.manualEdit = endT.value ? '1' : '0';
}

// === 強制險 期間 自動帶 +1 年（與任意險邏輯一致，獨立旗標） ===
function autoComputeCompulsoryEnd() {
  var startD = document.getElementById('p-cstart');
  var startT = document.getElementById('p-cstart-time');
  var endD = document.getElementById('p-cend');
  var endT = document.getElementById('p-cend-time');
  if (!startD || !endD) return;
  if ((endD.dataset.manualEdit === '1') || (endT && endT.dataset.manualEdit === '1')) return;
  var s = startD.value;
  if (!s) return;
  var d = new Date(s + 'T00:00:00');
  if (isNaN(d.getTime())) return;
  d.setFullYear(d.getFullYear() + 1);
  var y = d.getFullYear();
  var m = String(d.getMonth() + 1).padStart(2, '0');
  var dd = String(d.getDate()).padStart(2, '0');
  endD.value = y + '-' + m + '-' + dd;
  if (endT) endT.value = startT ? (startT.value || '') : '';
  refreshRocLabels();
}
function markCompulsoryEndManual() {
  var endD = document.getElementById('p-cend');
  var endT = document.getElementById('p-cend-time');
  if (endD) endD.dataset.manualEdit = endD.value ? '1' : '0';
  if (endT) endT.dataset.manualEdit = endT.value ? '1' : '0';
}

// 全域保留最近一次抓的保單（雙擊展開時不再重新打 API）
window._lastPolicies = [];

async function loadPolicies() {
  // 用 admin token 抓全部客戶的保單
  const r = await fetch(CONSOLE_API+'/all/policies', {headers:consoleHeaders(false)});
  const d = await r.json();
  const policies = d.data || [];
  window._lastPolicies = policies;
  const tb = document.getElementById('p-table');
  if (policies.length === 0) {
    tb.innerHTML = '<tr><td colspan="10" style="color:#999;text-align:center">尚無保單</td></tr>';
    return;
  }
  var html = '';
  for (var i = 0; i < policies.length; i++) {
    var p = policies[i];
    var cls = p.status==='active'?'active':p.status==='expired'?'expired':'expiring';
    var label = p.status==='active'?'有效':p.status==='expired'?'已到期':'即將到期';
    var owner = p.customer_name
      ? '<div data-hover-cust="' + (p.user_id||'') + '" data-hover-type="policy" style="cursor:help">'
          + '<b>'+p.customer_name+'</b>'
          + (p.customer_phone ? '<br><span style="font-size:11px;color:#666">'+p.customer_phone+'</span>' : '')
        + '</div>'
      : '<span style="color:#999">-</span>';
    var plate = p.vehicle_plate || '<span style="color:#999">-</span>';
    var cidEsc = (p.user_id||'');
    var nameEsc = (p.customer_name||'').replace(/"/g,'&quot;');
    // 主列：點擊選取（高亮）、雙擊展開
    html += '<tr style="cursor:pointer" onclick="selectPolicyRow(this)" ondblclick="togglePolicyDetails(&quot;'+p.id+'&quot;)">';
    html += '<td>'+owner+'</td>';
    html += '<td>'+plate+'</td>';
    html += '<td style="font-family:monospace;font-size:11px">'+p.policy_number+'</td>';
    html += '<td>'+p.insurer_name+'</td>';
    html += '<td><span class="badge '+cls+'">'+label+'</span></td>';
    html += '<td>'+(p.start_date||'-')+(p.start_time?' '+p.start_time:'')+'</td>';
    var endCell = (p.end_date||'-')+(p.end_time?' '+p.end_time:'');
    if (p.end_date) {
      endCell += _calBtnHtml('保單到期 — ' + (p.insurer_name||'') + ' ' + (p.policy_number||''), p.end_date,
        '客戶：' + (p.customer_name||'') + '\\n保單號：' + (p.policy_number||'') + '\\n保險公司：' + (p.insurer_name||'') + '\\n承保車輛：' + (p.vehicle_plate||'-'));
    }
    html += '<td>'+endCell+'</td>';
    html += '<td>'+(p.total_premium?'$'+Number(p.total_premium).toLocaleString():'-')+'</td>';
    html += '<td>'+(p.items?p.items.length:0)+'項</td>';
    html += '<td style="white-space:nowrap" onclick="event.stopPropagation()">';
    html += '<button class="btn" style="padding:3px 8px;font-size:10px;background:#2E7D32;color:#fff;margin:1px" onclick="uploadPolicyForRow(&quot;'+cidEsc+'&quot;,&quot;'+nameEsc+'&quot;)" title="為此客戶上傳保單掃描並 OCR">上傳</button>';
    html += '<button class="btn" style="padding:3px 8px;font-size:10px;background:#1565C0;color:#fff;margin:1px" onclick="editPolicyFromList(&quot;'+p.id+'&quot;)">編輯</button>';
    html += '<button class="btn danger" style="padding:3px 8px;font-size:10px;margin:1px" onclick="deletePolicyById(&quot;'+p.id+'&quot;,&quot;'+p.policy_number+'&quot;)">刪除</button>';
    html += '</td></tr>';
    // 隱藏的展開行（雙擊顯示承保項目）
    html += '<tr id="pdetails-'+p.id+'" style="display:none"><td colspan="10" style="background:#f9f9f9;padding:14px"><div id="pdetails-content-'+p.id+'"></div></td></tr>';
  }
  tb.innerHTML = html;
}

function selectPolicyRow(tr) {
  // 取消其他列高亮
  var rows = document.querySelectorAll('#p-table tr');
  rows.forEach(function(r){ r.style.background = ''; });
  tr.style.background = '#fff3cd';  // 黃色高亮
}

function togglePolicyDetails(pid) {
  var row = document.getElementById('pdetails-'+pid);
  if (!row) return;
  if (row.style.display === 'none' || !row.style.display) {
    row.style.display = '';
    renderPolicyDetails(pid);
  } else {
    row.style.display = 'none';
  }
}

function renderPolicyDetails(pid) {
  var p = (window._lastPolicies || []).find(function(x){return x.id === pid;});
  var content = document.getElementById('pdetails-content-'+pid);
  if (!p) { content.innerHTML = '<span style="color:#999">找不到資料</span>'; return; }
  var items = p.items || [];
  // ★ 紅色 × 關閉按鈕：data-pid 帶 pid，由全域 click 代理處理（最穩）
  var html = '<div style="position:relative;padding:8px 38px 8px 4px">';
  html += '<button class="policy-close-btn" data-pid="'+pid+'" title="關閉" '
        + 'style="position:absolute;top:0;right:0;width:30px;height:30px;background:#D32F2F;color:#fff;border:none;border-radius:50%;cursor:pointer;font-size:16px;font-weight:bold;line-height:1;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 3px rgba(0,0,0,.3);z-index:10">✕</button>';
  html += '<div style="font-weight:bold;color:#1565C0;margin-bottom:8px">📄 承保項目（共 '+items.length+' 項）</div>';
  if (items.length === 0) {
    html += '<div style="color:#999;font-size:12px">無項目</div>';
  } else {
    html += '<table style="width:100%;font-size:12px;background:#fff;border:1px solid #ddd">';
    html += '<thead><tr style="background:#1565C0;color:#fff"><th>險種</th><th style="text-align:right">保費</th><th style="text-align:right">保額</th><th style="text-align:right">自負額</th><th>備註</th></tr></thead><tbody>';
    items.forEach(function(it){
      html += '<tr>';
      html += '<td>'+(it.item_name||'-')+'</td>';
      html += '<td style="text-align:right;color:#2E7D32">'+(it.premium?'$'+Number(it.premium).toLocaleString():'-')+'</td>';
      html += '<td style="text-align:right">'+(it.coverage_limit?'$'+Number(it.coverage_limit).toLocaleString():'-')+'</td>';
      html += '<td style="text-align:right">'+(it.deductible?'$'+Number(it.deductible).toLocaleString():'-')+'</td>';
      html += '<td style="font-size:11px;color:#666">'+(it.description||'-')+'</td>';
      html += '</tr>';
    });
    html += '</tbody></table>';
  }
  html += '</div>';
  content.innerHTML = html;
}

// ★ 全域事件代理：document 上監聽，所有 .policy-close-btn 都被抓到（最穩）
//   只註冊一次即可，DOM 重新渲染也不影響
if (!window._policyCloseDelegateBound) {
  document.addEventListener('click', function(e) {
    var t = e.target;
    while (t && t !== document) {
      if (t.classList && t.classList.contains('policy-close-btn')) {
        e.preventDefault();
        e.stopPropagation();
        var pid = t.getAttribute('data-pid');
        if (pid) {
          var row = document.getElementById('pdetails-' + pid);
          if (row) row.style.display = 'none';
        }
        return;
      }
      t = t.parentNode;
    }
  }, true);  // 用 capture 階段，更早攔截
  window._policyCloseDelegateBound = true;
}

// ── 為某客戶上傳保單（row 上傳按鈕）──
function uploadPolicyForRow(cid, name) {
  if (!cid) { showMsg('p-msg','err','此保單無客戶資訊'); return; }
  window._rowPolicyCid = cid;
  window._rowPolicyName = name;
  document.getElementById('row-policy-file').value = '';
  document.getElementById('row-policy-file').click();
}

async function onPolicyFileSelectedRow() {
  var file = document.getElementById('row-policy-file').files[0];
  if (!file) return;
  var cid = window._rowPolicyCid;
  var name = window._rowPolicyName || '';
  if (!cid) { showMsg('p-msg','err','找不到客戶'); return; }

  showMsg('p-msg','ok','上傳保單檔案中...');
  try {
    // Step 1: upload-scan
    var fd = new FormData(); fd.append('file', file);
    var r1 = await fetch(CONSOLE_API+'/policies/upload-scan', {
      method:'POST', headers:{'Authorization':'Bearer '+ADMIN_TOKEN}, body:fd
    });
    var d1 = await r1.json();
    if (!d1.success) { showMsg('p-msg','err','上傳失敗: '+(d1.detail||d1.message)); return; }
    var fn = d1.data.filename;

    // Step 2: 詢問是否 OCR
    var doOcr = confirm('保單檔案已上傳（'+name+'）。\\n\\n要立即執行 AI 自動辨識並建立保單嗎？');
    if (!doOcr) {
      showMsg('p-msg','ok','保單已上傳但未辨識。檔名: '+fn);
      return;
    }

    showMsg('p-msg','ok','AI 辨識中（首次約 15 秒）...');
    var r2 = await fetch(CONSOLE_API+'/customer/'+cid+'/policies/ocr-scan?filename='+encodeURIComponent(fn), {
      method:'POST', headers:{'Authorization':'Bearer '+ADMIN_TOKEN}
    });
    var d2 = await r2.json();
    if (d2.success && d2.data && d2.data.policy) {
      showMsg('p-msg','ok','保單已建立（'+name+'）: '+d2.data.policy.policy_number);
      loadPolicies();
    } else {
      showMsg('p-msg','err','辨識/建立失敗: '+(d2.message||d2.detail||''));
    }
  } catch(e) {
    showMsg('p-msg','err','操作失敗: '+e.message);
  }
}

// ── 編輯保單（彈窗）──
function editPolicyFromList(pid) {
  var p = (window._lastPolicies || []).find(function(x){return x.id === pid;});
  if (!p) { showMsg('p-msg','err','找不到保單'); return; }
  window._editPolicyId = pid;
  window._editPolicyUserId = p.user_id || '';
  window._editPolicyCustomerNameOrig = p.customer_name || '';
  window._editPolicyCustomerEmailOrig = p.customer_email || '';
  document.getElementById('pe-customer-name').value = p.customer_name || '';
  document.getElementById('pe-customer-email').value = p.customer_email || '';
  document.getElementById('pe-number').value = p.policy_number || '';
  // 承保車牌（唯讀，僅顯示）— 跟車輛主檔連結
  var plateInfo = document.getElementById('pe-vehicle-info');
  if (plateInfo) {
    if (p.vehicle_plate) {
      plateInfo.textContent = p.vehicle_plate
        + (p.vehicle_brand || p.vehicle_model ? '  （' + (p.vehicle_brand||'') + ' ' + (p.vehicle_model||'') + '）' : '');
      plateInfo.style.color = '#333';
    } else {
      plateInfo.textContent = LANG === 'en' ? '— (not linked to a vehicle)' : '— （此保單未關聯車輛）';
      plateInfo.style.color = '#999';
    }
  }
  fillInsurerSelect('pe-insurer', 'pe-insurer-other', p.insurer_name || '');
  _writeDatePair('pe-start', p.start_date, p.start_time);
  _writeDatePair('pe-end', p.end_date, p.end_time);
  _writeDatePair('pe-cstart', p.compulsory_start_date, p.compulsory_start_time);
  _writeDatePair('pe-cend', p.compulsory_end_date, p.compulsory_end_time);
  fillInsurerSelect('pe-cinsurer', 'pe-cinsurer-other', p.compulsory_insurer_name || '');
  document.getElementById('pe-cnumber').value = p.compulsory_policy_number || '';
  setNumberWithComma('pe-cpremium', p.compulsory_premium);
  setNumberWithComma('pe-premium', p.total_premium);
  // 要保人 / 被保人
  document.getElementById('pe-ph-name').value   = p.policyholder_name || '';
  document.getElementById('pe-ph-id').value     = p.policyholder_id_number || '';
  document.getElementById('pe-ph-birth').value  = p.policyholder_birth_date || '';
  document.getElementById('pe-ph-gender').value = p.policyholder_gender || '';
  document.getElementById('pe-ph-phone').value  = p.policyholder_phone || '';
  document.getElementById('pe-ph-relation').value = p.policyholder_relation_to_owner || '';
  document.getElementById('pe-in-name').value   = p.insured_name || '';
  document.getElementById('pe-in-id').value     = p.insured_id_number || '';
  document.getElementById('pe-in-birth').value  = p.insured_birth_date || '';
  document.getElementById('pe-in-gender').value = p.insured_gender || '';
  document.getElementById('pe-in-phone').value  = p.insured_phone || '';
  // 被保人 ↔ 車主 對齊狀態
  setTimeout(function(){ _recheckInsuredAlignment('pe'); }, 0);
  // 載入既有保障項目到 pe-items
  document.getElementById('pe-items').innerHTML = '';
  (p.items || []).forEach(function(it){
    _buildItemRow('pe-items', {
      item_name: it.item_name,
      coverage_limit: it.coverage_limit,
      deductible: it.deductible,
      premium: it.premium,
    });
  });
  document.getElementById('pe-status').value = p.status || 'active';
  document.getElementById('p-edit-modal').style.display = 'flex';
  refreshRocLabels();
}

function closePolicyEdit() {
  document.getElementById('p-edit-modal').style.display = 'none';
}

async function savePolicyEdit() {
  var pid = window._editPolicyId;
  if (!pid) return;
  // 防呆：被保人 vs 車主姓名不一致 → 二次確認
  var __peInName = (document.getElementById('pe-in-name').value || '').trim();
  var __peCustName = _getCustomerNameForPolicy('pe');
  if (__peInName && __peCustName && __peInName !== __peCustName) {
    if (!confirm('⚠️ 被保人「' + __peInName + '」與車主「' + __peCustName + '」不一致。\\n\\n台灣車險被保人通常應為車輛登記車主，否則理賠時可能受影響。\\n\\n確定要繼續儲存嗎？')) return;
  }
  var pesParts = _readDatePair('pe-start');
  var peeParts = _readDatePair('pe-end');
  var pcsParts = _readDatePair('pe-cstart');
  var pceParts = _readDatePair('pe-cend');
  var body = {
    policy_number: document.getElementById('pe-number').value.trim(),
    insurer_name: getInsurerValue('pe-insurer', 'pe-insurer-other'),
    start_date: pesParts.date,
    end_date: peeParts.date,
    start_time: pesParts.time,
    end_time: peeParts.time,
    compulsory_insurer_name: getInsurerValue('pe-cinsurer','pe-cinsurer-other') || null,
    compulsory_policy_number: (document.getElementById('pe-cnumber').value || '').trim() || null,
    compulsory_premium: parseThousand(document.getElementById('pe-cpremium').value),
    compulsory_start_date: pcsParts.date,
    compulsory_end_date: pceParts.date,
    compulsory_start_time: pcsParts.time,
    compulsory_end_time: pceParts.time,
    // 要保人 / 被保人
    policyholder_name: (document.getElementById('pe-ph-name').value || '').trim() || null,
    policyholder_id_number: (document.getElementById('pe-ph-id').value || '').trim().toUpperCase() || null,
    policyholder_birth_date: document.getElementById('pe-ph-birth').value || null,
    policyholder_gender: document.getElementById('pe-ph-gender').value || null,
    policyholder_phone: (document.getElementById('pe-ph-phone').value || '').trim() || null,
    policyholder_relation_to_owner: (document.getElementById('pe-ph-relation').value || '').trim() || null,
    insured_name: (document.getElementById('pe-in-name').value || '').trim() || null,
    insured_id_number: (document.getElementById('pe-in-id').value || '').trim().toUpperCase() || null,
    insured_birth_date: document.getElementById('pe-in-birth').value || null,
    insured_gender: document.getElementById('pe-in-gender').value || null,
    insured_phone: (document.getElementById('pe-in-phone').value || '').trim() || null,
    status: document.getElementById('pe-status').value,
  };
  var prem = parseThousand(document.getElementById('pe-premium').value);
  if (prem != null) body.total_premium = prem;
  // 蒐集保障項目（整批 replace；後端會先刪舊再插新）
  body.items = _collectItemRows('pe-items');

  // ① 先更新保單欄位
  try {
    var r = await fetch(CONSOLE_API+'/policies/'+pid, {
      method:'PUT', headers:consoleHeaders(true), body:JSON.stringify(body)
    });
    var d = await r.json();
    if (!d.success) {
      showMsg('pe-msg','err','更新失敗: '+(d.detail||d.message));
      return;
    }
  } catch(e) { showMsg('pe-msg','err','操作失敗: '+e.message); return; }

  // ② 要保人姓名若有變動 → 找/建立新客戶並轉移保單（不會 rename 既有客戶）
  var newName = document.getElementById('pe-customer-name').value.trim();
  var origName = window._editPolicyCustomerNameOrig || '';
  var transferMsg = '';
  if (newName && newName !== origName) {
    try {
      var lr = await fetch(CONSOLE_API+'/customers', {headers:consoleHeaders()});
      var allCustomers = (await lr.json()).data || [];
      var match = allCustomers.find(function(c){ return (c.name||'').trim() === newName; });
      var targetCid = '';
      if (match) {
        var ok = confirm('已存在客戶「' + newName + '」' +
          (match.phone ? ' (電話 ' + match.phone + ')' : '') +
          '\\n\\n要把這張保單轉移到該客戶名下嗎？');
        if (!ok) {
          showMsg('pe-msg','ok','保單已更新（要保人未變更）');
          setTimeout(function(){ closePolicyEdit(); loadPolicies(); }, 800);
          return;
        }
        targetCid = match.id;
      } else {
        var ok2 = confirm('找不到客戶「' + newName + '」。\\n\\n要新建客戶並把這張保單轉移到他名下嗎？');
        if (!ok2) {
          showMsg('pe-msg','ok','保單已更新（要保人未變更）');
          setTimeout(function(){ closePolicyEdit(); loadPolicies(); }, 800);
          return;
        }
        var cr = await fetch(CONSOLE_API+'/customers', {
          method:'POST', headers:consoleHeaders(true),
          body: JSON.stringify({name: newName})
        });
        var cd = await cr.json();
        if (!cd.success) {
          showMsg('pe-msg','err','建立客戶失敗: '+(cd.detail||cd.message));
          return;
        }
        targetCid = cd.data.id;
        transferMsg = '（已新建客戶「' + newName + '」並轉移要保人）';
      }
      var tr = await fetch(CONSOLE_API+'/policies/'+pid+'/transfer', {
        method:'POST', headers:consoleHeaders(true),
        body: JSON.stringify({customer_id: targetCid})
      });
      var td = await tr.json();
      if (!td.success) {
        showMsg('pe-msg','err','要保人變更失敗: '+(td.detail||td.message));
        return;
      }
      if (!transferMsg) transferMsg = '（已將要保人變更為「'+newName+'」）';
      window._editPolicyUserId = targetCid;
      window._editPolicyCustomerNameOrig = newName;
    } catch(e) { showMsg('pe-msg','err','要保人轉移異常: '+e.message); return; }
  }

  // ③ Email 若有變動 → 更新最終目標客戶的 email
  var newEmail = document.getElementById('pe-customer-email').value.trim();
  var origEmail = window._editPolicyCustomerEmailOrig || '';
  var emailMsg = '';
  if (newEmail !== origEmail) {
    var targetUid = window._editPolicyUserId;
    if (targetUid) {
      try {
        var er = await fetch(CONSOLE_API+'/customer/'+targetUid, {
          method:'PATCH', headers:consoleHeaders(true),
          body: JSON.stringify({email: newEmail || null})
        });
        var ed = await er.json();
        if (ed.success) {
          window._editPolicyCustomerEmailOrig = newEmail;
          emailMsg = newEmail
            ? '（Email 已更新為 ' + newEmail + '，客戶可用此 Email 登入）'
            : '（Email 已清除）';
        } else {
          showMsg('pe-msg','err','Email 更新失敗: '+(ed.detail||ed.message));
          return;
        }
      } catch(ex) {
        showMsg('pe-msg','err','Email 更新失敗: '+ex.message);
        return;
      }
    }
  }

  showMsg('pe-msg','ok','保單已更新'+transferMsg+emailMsg);
  setTimeout(function(){ closePolicyEdit(); loadPolicies(); }, 1000);
}

async function deletePolicyById(pid, num) {
  if (!confirm('確定刪除保單「' + num + '」？\\n（此操作無法復原，相關 PolicyItem 也會一起刪除）')) return;
  try {
    var r = await fetch(CONSOLE_API+'/policies/'+pid, {
      method:'DELETE', headers:consoleHeaders(false)
    });
    var d = await r.json();
    if (d.success) {
      showMsg('p-msg','ok','保單 '+num+' 已刪除');
      loadPolicies();
    } else {
      showMsg('p-msg','err','刪除失敗: '+(d.detail||d.message));
    }
  } catch(e) { showMsg('p-msg','err','操作失敗: '+e.message); }
}

// --- Overview ---
async function loadOverview() {
  if (ADMIN_ROLE === 'super_admin') {
    try {
      var or = await fetch(CONSOLE_API+'/all/overview', {headers:consoleHeaders()}).then(function(r){return r.json();});
      var o = or.data || {};
      var html = '<table style="margin-bottom:14px">' +
        '<tr><td style="width:200px"><b>' + t('ov_customer_count') + '</b></td><td><span style="font-size:18px;color:#1565C0">'+(o.customer_count||0)+'</span></td></tr>' +
        '<tr><td><b>' + t('ov_vehicle_count') + '</b></td><td><span style="font-size:18px;color:#1565C0">'+(o.vehicle_count||0)+'</span></td></tr>' +
        '<tr><td><b>' + t('ov_policy_count') + '</b></td><td><span style="font-size:18px;color:#1565C0">'+(o.policy_count||0)+'</span></td></tr>' +
        '<tr><td><b>' + t('ov_policy_active') + '</b></td><td><span style="color:#2E7D32">'+(o.policy_active||0)+'</span></td></tr>' +
        '<tr><td><b>' + t('ov_policy_expiring') + '</b></td><td><span style="color:#FF9800">'+(o.policy_expiring||0)+'</span></td></tr>' +
        '<tr><td><b>' + t('ov_policy_expired') + '</b></td><td><span style="color:#999">'+(o.policy_expired||0)+'</span></td></tr>' +
        '<tr><td><b>' + t('ov_total_premium') + '</b></td><td>$'+Number(o.total_premium||0).toLocaleString()+'</td></tr>' +
        '</table>';
      var upcoming = o.upcoming_30d || [];
      if (upcoming.length > 0) {
        html += '<h3 style="margin-top:14px;color:#FF9800">' + t('ov_upcoming_30d') + ' ('+upcoming.length+')</h3>';
        html += '<table><thead><tr><th>' + t('th_policy_number') + '</th><th>' + t('th_insurer') + '</th><th>' + t('th_end') + '</th><th>' + t('ov_days_left') + '</th></tr></thead><tbody>';
        for (var i = 0; i < upcoming.length; i++) {
          var u = upcoming[i];
          var color = u.days_left <= 7 ? '#D32F2F' : u.days_left <= 14 ? '#FF9800' : '#666';
          html += '<tr><td style="font-family:monospace;font-size:11px">'+u.policy_number+'</td><td>'+u.insurer+'</td><td>'+u.end_date+'</td>';
          html += '<td><span style="color:'+color+';font-weight:bold">'+u.days_left+' ' + t('ov_days') + '</span></td></tr>';
        }
        html += '</tbody></table>';
      }
      document.getElementById('overview-content').innerHTML = html;
    } catch(e) { document.getElementById('overview-content').innerHTML = '<p style="color:#999">' + t('msg_load_failed') + ': '+e.message+'</p>'; }
  } else {
    // 業務員：顯示自己的客戶列表
    try {
      var cr = await fetch(CONSOLE_API+'/customers', {headers:consoleHeaders()});
      var cd = await cr.json();
      var customers = cd.data || [];
      var html = '<p style="margin-bottom:12px;color:#666">您負責的客戶（共 '+customers.length+' 位）</p>';
      if (customers.length > 0) {
        html += '<table><thead><tr><th>姓名</th><th>電話</th><th>Email</th></tr></thead><tbody>';
        for (var ci = 0; ci < customers.length; ci++) {
          var c = customers[ci];
          html += '<tr><td>'+(c.name||'-')+'</td><td>'+(c.phone||'-')+'</td><td>'+(c.email||'-')+'</td></tr>';
        }
        html += '</tbody></table>';
      } else {
        html += '<p style="color:#999">尚無分配的客戶</p>';
      }
      document.getElementById('overview-content').innerHTML = html;
    } catch(e) { document.getElementById('overview-content').innerHTML = '<p style="color:#999">載入失敗</p>'; }
  }
}

// --- Util ---
function showMsg(id, type, text) {
  const el = document.getElementById(id);
  el.className = 'msg ' + type;
  el.textContent = text;
  el.style.display = 'block';
  if (type==='ok') setTimeout(()=>{el.style.display='none';}, 5000);
}

// Auto-add one item row
addItemRow();

// ═══ Console: Agents ═══
async function loadAgents() {
  try {
    var r = await fetch(CONSOLE_API+'/agents', {headers:consoleHeaders()});
    var d = await r.json();
    var agents = d.data || [];
    var html = '';
    for (var i = 0; i < agents.length; i++) {
      var a = agents[i];
      var st = a.is_active ? '<span style="color:#22c55e;font-weight:bold">啟用</span>' : '<span style="color:#ef4444;font-weight:bold">停用</span>';
      html += '<tr><td><b>'+a.username+'</b></td><td>'+a.display_name+'</td><td>'+st+'</td>';
      html += '<td>'+a.customer_count+'</td><td style="font-size:11px">'+(a.last_login||'-')+'</td>';
      html += '<td style="white-space:nowrap">';
      if (a.is_active) html += '<button class="btn danger" style="padding:3px 8px;font-size:11px;margin:1px" onclick="toggleAgent(&quot;'+a.id+'&quot;,false)">停用</button>';
      else html += '<button class="btn success" style="padding:3px 8px;font-size:11px;margin:1px" onclick="toggleAgent(&quot;'+a.id+'&quot;,true)">啟用</button>';
      html += '</td></tr>';
    }
    document.getElementById('agents-table').innerHTML = html || '<tr><td colspan="6" style="color:#999">尚無業務員</td></tr>';
  } catch(e) { console.error(e); }
}
async function createAgent() {
  var body = {username:document.getElementById('ag-user').value, password:document.getElementById('ag-pass').value,
    display_name:document.getElementById('ag-name').value, email:document.getElementById('ag-email').value,
    phone:document.getElementById('ag-phone').value, ip_whitelist:document.getElementById('ag-ip').value};
  if (!body.username || !body.password) { showMsg('ag-msg','err','帳號和密碼必填'); return; }
  var r = await fetch(CONSOLE_API+'/agents', {method:'POST', headers:consoleHeaders(true), body:JSON.stringify(body)});
  var d = await r.json();
  if (d.success) { showMsg('ag-msg','ok',d.message); loadAgents(); } else showMsg('ag-msg','err',d.message||d.detail);
}
async function toggleAgent(id, active) {
  await fetch(CONSOLE_API+'/agents/'+id, {method:'PATCH', headers:consoleHeaders(true), body:JSON.stringify({is_active:active})});
  loadAgents();
}

// ═══ Console: Assign ═══
async function loadAssignSelects() {
  var r1 = await fetch(CONSOLE_API+'/agents', {headers:consoleHeaders()});
  var d1 = await r1.json();
  var ah = '<option value="">選擇業務員</option>';
  for (var i = 0; i < (d1.data||[]).length; i++) {
    var a = d1.data[i];
    if (a.is_active) ah += '<option value="'+a.id+'">'+a.display_name+' ('+a.username+')</option>';
  }
  document.getElementById('assign-agent').innerHTML = ah;
  var r2 = await fetch(CONSOLE_API+'/customers', {headers:consoleHeaders()});
  var d2 = await r2.json();
  var ch = '<option value="">選擇客戶</option>';
  for (var j = 0; j < (d2.data||[]).length; j++) {
    var c = d2.data[j];
    ch += '<option value="'+c.id+'">'+(c.name||c.phone||c.email||c.id.substring(0,8))+'</option>';
  }
  document.getElementById('assign-customer').innerHTML = ch;
}
async function assignCustomer() {
  var agentId = document.getElementById('assign-agent').value;
  var customerId = document.getElementById('assign-customer').value;
  if (!agentId || !customerId) { showMsg('assign-msg','err','請選擇業務員和客戶'); return; }
  var r = await fetch(CONSOLE_API+'/assign-customer', {method:'POST', headers:consoleHeaders(true), body:JSON.stringify({agent_id:agentId,customer_id:customerId})});
  var d = await r.json();
  if (d.success) showMsg('assign-msg','ok',d.message); else showMsg('assign-msg','err',d.message||d.detail);
}

// ═══ Console: Logs ═══
async function loadLogs() {
  var r = await fetch(CONSOLE_API+'/audit-logs', {headers:consoleHeaders()});
  var d = await r.json();
  var logs = d.data || [];
  var html = '';
  for (var i = 0; i < logs.length; i++) {
    var l = logs[i];
    html += '<tr><td style="font-size:11px">'+l.timestamp.substring(0,19).replace('T',' ')+'</td>';
    html += '<td>'+l.admin+'</td><td><b>'+l.action+'</b></td>';
    html += '<td style="font-size:11px">'+(l.target_type||'')+' '+(l.target_id?l.target_id.substring(0,8):'')+'</td>';
    html += '<td style="font-size:11px">'+(l.detail||'')+'</td><td style="font-size:11px">'+(l.ip||'')+'</td></tr>';
  }
  document.getElementById('logs-table').innerHTML = html || '<tr><td colspan="6" style="color:#999">尚無日誌</td></tr>';
}
</script>
</body>
</html>"""


@router.get("", response_class=HTMLResponse)
async def admin_page():
    """後台管理頁面（不快取，確保每次拿最新 HTML/JS）"""
    return HTMLResponse(content=ADMIN_HTML, headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    })
