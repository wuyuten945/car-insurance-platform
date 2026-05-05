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
</style>
</head>
<body>
<div class="header">
  <h1>BOPINAN — 管理控制台</h1>
  <small id="user-info"></small>
  <button class="btn danger" id="logout-btn" style="display:none;padding:4px 12px;font-size:12px;margin-left:10px" onclick="doLogout()">登出</button>
  <div id="customer-bar" style="display:none;margin-top:10px;padding:10px;background:rgba(255,255,255,0.15);border-radius:6px;font-size:13px">
    <span style="margin-right:8px">操作客戶（新增車輛/保單時套用）：</span>
    <select id="cur-customer" style="background:#fff;color:#000;padding:4px 8px;border-radius:4px;border:0;min-width:280px"></select>
    <button class="btn" style="padding:4px 10px;font-size:11px;margin-left:8px;background:#0288D1" onclick="loadCustomerList()">重新整理客戶清單</button>
    <span id="customer-bar-msg" style="margin-left:10px;color:#FFD54F;font-size:11px"></span>
  </div>
</div>

<!-- Login (Admin Account) -->
<div id="login-section" class="container">
  <div class="card">
    <h2>管理員登入</h2>
    <p style="color:#666;margin-bottom:16px">使用管理員帳號密碼登入</p>
    <label>帳號</label>
    <input type="text" id="login-user" placeholder="admin">
    <label>密碼</label>
    <div class="pw-wrap">
      <input type="password" id="login-pass" placeholder="密碼" onkeydown="if(event.key==='Enter')doAdminLogin()">
      <button type="button" class="pw-toggle" onclick="togglePw('login-pass',this)">👁</button>
    </div>
    <button class="btn" onclick="doAdminLogin()" style="width:100%;margin-top:14px">登入</button>
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
             style="flex:1;border:1px solid #ddd;border-radius:6px;padding:8px 12px;font-size:14px"
             onkeydown="if(event.key==='Enter')doQuickSearch()">
      <button onclick="doQuickSearch()" style="background:#1976d2;color:#fff;border:0;border-radius:6px;padding:8px 18px;font-weight:600;cursor:pointer">搜尋</button>
      <button onclick="clearQuickSearch()" style="background:#f5f5f5;color:#666;border:1px solid #ddd;border-radius:6px;padding:8px 12px;cursor:pointer">清除</button>
    </div>
    <div id="qs-results" style="margin-top:10px"></div>
  </div>

  <div class="tabs">
    <button class="tab active" id="tab-btn-vehicles" onclick="switchTab('vehicles')">車輛 / 行照</button>
    <button class="tab" id="tab-btn-policies" onclick="switchTab('policies')">保單管理</button>
    <button class="tab" id="tab-btn-claims" onclick="switchTab('claims')">理賠申請</button>
    <button class="tab" id="tab-btn-accidents" onclick="switchTab('accidents')">事故照片</button>
    <button class="tab" id="tab-btn-overview" onclick="switchTab('overview')">資料總覽</button>
    <button class="tab" id="tab-btn-agents" onclick="switchTab('agents')" style="display:none">業務員管理</button>
    <button class="tab" id="tab-btn-assign" onclick="switchTab('assign')" style="display:none">客戶分配</button>
    <button class="tab" id="tab-btn-logs" onclick="switchTab('logs')" style="display:none">操作日誌</button>
  </div>

  <!-- Tab: Vehicles -->
  <div id="tab-vehicles" class="tab-content active">
    <div class="card">
      <h2>上傳行照（自動辨識）</h2>
      <p style="color:#666;font-size:13px;margin-bottom:12px">選擇車輛型式後上傳行照圖片，系統將自動辨識所有車輛資料（含驗車到期日）。</p>

      <div class="row">
        <div>
          <label>車輛型式（監理分類）</label>
          <select id="v-type" onchange="onTypeChange()">
            <optgroup label="自用車輛">
              <option value="自用小客車">自用小客車</option>
              <option value="自用小貨車">自用小貨車</option>
              <option value="自用小客貨兩用車">自用小客貨兩用車</option>
              <option value="自用大客車">自用大客車</option>
              <option value="自用大貨車">自用大貨車</option>
              <option value="自用特種車">自用特種車</option>
            </optgroup>
            <optgroup label="營業車輛">
              <option value="營業小客車（計程車）">營業小客車（計程車）</option>
              <option value="營業小貨車">營業小貨車</option>
              <option value="營業大客車">營業大客車</option>
              <option value="營業大貨車">營業大貨車</option>
              <option value="營業遊覽車">營業遊覽車</option>
              <option value="營業特種車">營業特種車</option>
            </optgroup>
            <optgroup label="機車">
              <option value="大型重型機車（550cc以上）">大型重型機車（550cc以上）</option>
              <option value="普通重型機車（250cc以上）">普通重型機車（250cc以上）</option>
              <option value="普通重型機車（50~250cc）">普通重型機車（50~250cc）</option>
              <option value="普通輕型機車">普通輕型機車</option>
              <option value="小型輕型機車（電動）">小型輕型機車（電動）</option>
            </optgroup>
            <optgroup label="其他">
              <option value="拖車">拖車</option>
              <option value="曳引車">曳引車</option>
              <option value="電動汽車">電動汽車</option>
            </optgroup>
          </select>
        </div>
        <div>
          <label>現有車輛（更新）/ 新車</label>
          <select id="v-select">
            <option value="__new__">+ 新增車輛</option>
          </select>
        </div>
      </div>

      <div id="v-inspection-rule" style="margin-top:10px;padding:10px;background:#E3F2FD;border-radius:8px;font-size:12px;color:#1565C0;display:none"></div>

      <label style="margin-top:14px">行照圖片 (JPG/PNG)</label>
      <input type="file" id="v-file" accept="image/jpeg,image/png,image/webp,application/pdf,.pdf" onchange="onFileChange()">
      <img id="v-preview" class="preview" style="display:none">
      <button class="btn" id="v-upload-btn" onclick="uploadRegistration()">上傳行照</button>
      <button class="btn success" id="v-ocr-btn" style="display:none" onclick="runOcr()">AI 辨識行照</button>
      <div id="v-loading" style="display:none;margin-top:12px;color:#1565C0;font-size:14px">
        <span style="display:inline-block;animation:spin 1s linear infinite;margin-right:8px">&#9696;</span>
        <span id="v-loading-text">上傳中...</span>
      </div>
      <div id="v-msg" class="msg"></div>

      <!-- OCR / Edit Form (unified) -->
      <div id="v-edit-form" style="display:none;margin-top:16px">
        <h3 id="v-edit-title" style="font-size:14px;color:#2E7D32;margin-bottom:10px">AI 辨識結果</h3>
        <p style="font-size:11px;color:#888;margin-bottom:10px">點擊各欄位值可直接編輯修正</p>
        <table style="font-size:13px;width:100%"><tbody>
          <tr><td style="width:130px;color:#666;padding:6px"><b>客戶姓名</b></td><td><input type="text" id="ve-customer-name" placeholder="此車輛所屬客戶（修改會更新客戶資料）" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%;background:#fffbea"></td></tr>
          <tr><td style="color:#666;padding:6px"><b>客戶 Email</b></td><td><input type="email" id="ve-customer-email" placeholder="設定後客戶可用此 Email 登入並看到自己的車輛保單" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%;background:#e8f5e9"></td></tr>
          <tr><td style="color:#666;padding:6px"><b>車牌號碼</b></td><td><input type="text" id="ve-plate" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b>廠牌</b></td><td><input type="text" id="ve-brand" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b>車型</b></td><td><input type="text" id="ve-model" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b>出廠年份</b></td><td><input type="number" id="ve-year" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b>顏色</b></td><td><input type="text" id="ve-color" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b>排氣量 (cc)</b></td><td><input type="number" id="ve-cc" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b>車身號碼</b></td><td><input type="text" id="ve-vin" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b>發照日期</b></td><td><input type="date" id="ve-reg-date" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b>驗車到期日</b></td><td><input type="date" id="ve-expiry" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%"></td></tr>
          <tr><td style="color:#666;padding:6px"><b>燃料種類</b></td><td>
            <select id="ve-fuel" style="border:1px solid #ddd;border-radius:4px;padding:4px 8px;width:100%">
              <option value="">--</option><option value="汽油">汽油</option><option value="柴油">柴油</option>
              <option value="油電混合">油電混合</option><option value="電動">電動</option><option value="LPG">LPG</option>
            </select>
          </td></tr>
        </tbody></table>

        <!-- 行照圖片直接上傳 -->
        <div style="margin-top:14px;padding:12px;background:#f5f7fa;border-radius:8px;border:1px solid #ddd">
          <div style="font-size:13px;color:#1565C0;font-weight:bold;margin-bottom:8px">行照圖片（直接上傳到此車輛）</div>
          <img id="ve-current-image" class="preview" style="display:none;max-width:200px;max-height:140px;margin-bottom:8px;border-radius:6px;border:1px solid #ccc">
          <input type="file" id="ve-file" accept="image/jpeg,image/png,image/webp,application/pdf,.pdf" onchange="onEditFileChange()" style="font-size:12px">
          <img id="ve-file-preview" class="preview" style="display:none;max-width:200px;max-height:140px;margin:6px 0;border-radius:6px;border:1px solid #ccc">
          <div style="margin-top:6px">
            <button class="btn" style="padding:6px 14px;font-size:12px;background:#1565C0;color:#fff" onclick="uploadRegistrationDirect()">上傳行照</button>
            <button class="btn success" style="padding:6px 14px;font-size:12px;display:none" id="ve-ocr-btn" onclick="ocrRegistrationDirect()">AI 辨識自動填入</button>
          </div>
          <div id="ve-upload-loading" style="display:none;margin-top:6px;color:#1565C0;font-size:12px">
            <span style="display:inline-block;animation:spin 1s linear infinite;margin-right:6px">&#9696;</span>
            <span id="ve-upload-text">處理中...</span>
          </div>
        </div>

        <button class="btn success" style="margin-top:14px" onclick="saveEditedVehicle()">儲存車輛資料</button>
        <div id="ve-msg" class="msg"></div>
      </div>
    </div>
    <div class="card">
      <h2>現有車輛</h2>
      <!-- 隱藏的 file input：給 row 內「上傳/更換」按鈕共用 -->
      <input type="file" id="row-upload-file" accept="image/jpeg,image/png,image/webp,application/pdf,.pdf" style="display:none" onchange="onRowFileSelected()">
      <table><thead><tr><th>客戶</th><th>車牌</th><th>型式</th><th>品牌</th><th>車型</th><th>年份</th><th>顏色</th><th>排氣量</th><th>行照到期</th><th>行照</th><th>操作</th></tr></thead>
      <tbody id="v-table"></tbody></table>
    </div>
  </div>

  <!-- Tab: Policies -->
  <div id="tab-policies" class="tab-content">
    <div class="card">
      <h2>上傳保單（AI 辨識）</h2>
      <p style="color:#666;font-size:13px;margin-bottom:12px">上傳保單圖片，系統自動辨識保險公司、保單號碼、起迄日、保障項目等，一鍵建立保單。</p>
      <label>保單圖片 (JPG/PNG)</label>
      <input type="file" id="p-file" accept="image/jpeg,image/png,image/webp,application/pdf,.pdf" onchange="onPolicyFileChange()">
      <img id="p-preview" class="preview" style="display:none">
      <button class="btn" id="p-upload-btn" onclick="uploadPolicy()">上傳保單</button>
      <button class="btn success" id="p-ocr-btn" style="display:none" onclick="runPolicyOcr()">AI 辨識保單</button>
      <div id="p-upload-loading" style="display:none;margin-top:12px;color:#1565C0;font-size:14px">
        <span style="display:inline-block;animation:spin 1s linear infinite;margin-right:8px">&#9696;</span>
        <span id="p-loading-text">上傳中...</span>
      </div>
      <div id="p-upload-msg" class="msg"></div>
      <!-- OCR result for policy -->
      <div id="p-ocr-result" style="display:none;margin-top:16px">
        <h3 style="font-size:14px;color:#2E7D32;margin-bottom:8px">辨識結果</h3>
        <table id="p-ocr-table" style="font-size:13px"><tbody></tbody></table>
      </div>
    </div>
    <div class="card">
      <h2>手動新增保單</h2>
      <div class="row">
        <div>
          <label>保險公司</label>
          <input type="text" id="p-insurer" placeholder="例：富邦產險">
        </div>
        <div>
          <label>保單號碼</label>
          <input type="text" id="p-number" placeholder="例：FBN-2026-001234">
        </div>
      </div>
      <div class="row">
        <div>
          <label>承保車輛</label>
          <select id="p-vehicle"><option value="">不指定</option></select>
        </div>
        <div>
          <label>狀態</label>
          <select id="p-status">
            <option value="active">有效</option>
            <option value="expiring">即將到期</option>
            <option value="expired">已到期</option>
          </select>
        </div>
      </div>
      <div class="row">
        <div><label>起保日</label><input type="date" id="p-start"></div>
        <div><label>到期日</label><input type="date" id="p-end"></div>
        <div><label>總保費</label><input type="number" id="p-premium" placeholder="18500"></div>
      </div>
      <div style="margin-top:16px">
        <h3 style="font-size:14px;color:#666">保障項目</h3>
        <div id="p-items"></div>
        <button class="btn" style="background:#666;margin-top:8px" onclick="addItemRow()">+ 新增項目</button>
      </div>
      <button class="btn" onclick="createPolicy()">建立保單</button>
      <div id="p-msg" class="msg"></div>
    </div>
    <div class="card">
      <h2>現有保單</h2>
      <p style="font-size:12px;color:#666;margin-bottom:8px">💡 點擊任一保單列可選取，<b>雙擊</b>查看承保項目明細</p>
      <!-- 隱藏 file input：給 row 上傳保單按鈕共用 -->
      <input type="file" id="row-policy-file" accept="image/jpeg,image/png,image/webp,application/pdf,.pdf" style="display:none" onchange="onPolicyFileSelectedRow()">
      <table><thead><tr>
        <th>客戶</th><th>車牌</th><th>保單號碼</th><th>保險公司</th><th>狀態</th>
        <th>起保</th><th>到期</th><th>保費</th><th>項目</th><th>操作</th>
      </tr></thead>
      <tbody id="p-table"></tbody></table>
    </div>

    <!-- 保單編輯彈窗 -->
    <div id="p-edit-modal" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:9999;align-items:center;justify-content:center">
      <div style="background:#fff;padding:24px;border-radius:12px;max-width:500px;width:90%;max-height:90vh;overflow-y:auto">
        <h3 style="color:#1565C0;margin-bottom:14px">編輯保單</h3>
        <table style="width:100%"><tbody>
          <tr><td style="width:90px;padding:6px;color:#666">要保人姓名</td><td><input type="text" id="pe-customer-name" placeholder="此保單所屬客戶（修改會轉移保單）" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px;background:#fffbea"></td></tr>
          <tr><td style="padding:6px;color:#666">客戶 Email</td><td><input type="email" id="pe-customer-email" placeholder="設定後客戶可用此 Email 登入並看到此保單" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px;background:#e8f5e9"></td></tr>
          <tr><td style="padding:6px;color:#666">保單號碼</td><td><input type="text" id="pe-number" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666">保險公司</td><td><input type="text" id="pe-insurer" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666">起保日</td><td><input type="date" id="pe-start" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666">到期日</td><td><input type="date" id="pe-end" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666">總保費</td><td><input type="number" id="pe-premium" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px"></td></tr>
          <tr><td style="padding:6px;color:#666">狀態</td><td>
            <select id="pe-status" style="width:100%;padding:6px;border:1px solid #ddd;border-radius:4px">
              <option value="active">active 有效</option>
              <option value="expiring">expiring 即將到期</option>
              <option value="expired">expired 已到期</option>
              <option value="cancelled">cancelled 已取消</option>
            </select>
          </td></tr>
        </tbody></table>
        <div style="margin-top:14px;text-align:right">
          <button class="btn" style="background:#999;color:#fff" onclick="closePolicyEdit()">取消</button>
          <button class="btn success" onclick="savePolicyEdit()">儲存</button>
        </div>
        <div id="pe-msg" class="msg"></div>
      </div>
    </div>
  </div>

  <!-- Tab: Overview -->
  <!-- Tab: Claims -->
  <div id="tab-claims" class="tab-content">
    <div class="card">
      <h2>理賠申請管理</h2>
      <p style="color:#666;font-size:13px;margin-bottom:12px">客戶送出的理賠申請</p>
      <button class="btn" onclick="loadClaims()">載入理賠列表</button>
      <div id="claims-list" style="margin-top:16px"></div>
    </div>
  </div>

  <!-- Tab: Accidents -->
  <div id="tab-accidents" class="tab-content">
    <div class="card">
      <h2>事故照片管理</h2>
      <p style="color:#666;font-size:13px;margin-bottom:12px">客戶透過緊急救援上傳的事故現場照片</p>
      <button class="btn" onclick="loadAccidents()">載入事故列表</button>
      <div id="acc-list" style="margin-top:16px"></div>
    </div>
  </div>

  <div id="tab-overview" class="tab-content">
    <div class="card">
      <h2>系統資料總覽</h2>
      <div id="overview-content"></div>
    </div>
  </div>

  <!-- Console: Agents -->
  <div id="tab-agents" class="tab-content">
    <div class="card">
      <h2>新增業務員</h2>
      <div class="row"><div><label>帳號</label><input id="ag-user" placeholder="agent01"></div><div><label>密碼</label><div class="pw-wrap"><input id="ag-pass" type="password"><button type="button" class="pw-toggle" onclick="togglePw('ag-pass',this)">👁</button></div></div></div>
      <div class="row"><div><label>顯示名稱</label><input id="ag-name"></div><div><label>Email</label><input id="ag-email"></div></div>
      <div class="row"><div><label>電話</label><input id="ag-phone"></div><div><label>IP 白名單（逗號分隔，空=不限）</label><input id="ag-ip"></div></div>
      <button class="btn" onclick="createAgent()">新增業務員</button>
      <div id="ag-msg" class="msg"></div>
    </div>
    <div class="card">
      <h2>業務員列表</h2>
      <table><thead><tr><th>帳號</th><th>名稱</th><th>狀態</th><th>客戶數</th><th>最後登入</th><th>操作</th></tr></thead>
      <tbody id="agents-table"></tbody></table>
    </div>
  </div>

  <!-- Console: Assign -->
  <div id="tab-assign" class="tab-content">
    <div class="card">
      <h2>分配客戶給業務員</h2>
      <div class="row"><div><label>選擇業務員</label><select id="assign-agent"></select></div><div><label>選擇客戶</label><select id="assign-customer"></select></div></div>
      <button class="btn success" onclick="assignCustomer()">分配</button>
      <div id="assign-msg" class="msg"></div>
    </div>
  </div>

  <!-- Console: Logs -->
  <div id="tab-logs" class="tab-content">
    <div class="card">
      <h2>操作日誌</h2>
      <button class="btn" onclick="loadLogs()" style="margin-bottom:8px">載入最新</button>
      <table><thead><tr><th>時間</th><th>管理員</th><th>操作</th><th>目標</th><th>說明</th><th>IP</th></tr></thead>
      <tbody id="logs-table"></tbody></table>
    </div>
  </div>
</div>

<script>
var API = '';
var TOKEN = '';
var ADMIN_TOKEN = '';
var ADMIN_ROLE = '';
var CONSOLE_API = '/api/v1/admin-console';

// --- Auth (Admin Account) ---
// localStorage key（持久化，瀏覽器重啟也保留；按上一頁不會被清掉）
var LS_TOKEN_KEY = 'admin_token_v1';
var LS_ROLE_KEY = 'admin_role_v1';
var LS_NAME_KEY = 'admin_name_v1';

// --- 閒置自動登出（10 分鐘無動作） ---
var IDLE_TIMEOUT_MS = 10 * 60 * 1000;  // 10 分鐘
var IDLE_WARN_MS    = 9 * 60 * 1000;   // 第 9 分鐘提醒（剩 1 分鐘）
var _idleTimer = null;
var _idleWarnTimer = null;
function _idleAutoLogout() {
  if (!ADMIN_TOKEN) return;
  alert('閒置超過 10 分鐘，已自動登出。');
  doLogout();
}
function _idleWarnSoon() {
  if (!ADMIN_TOKEN) return;
  // 用非阻塞 toast 提醒（用 console + 標題列閃爍）
  document.title = '⚠ 即將自動登出 - ' + (document.title || '管理後台');
}
function _resetIdleTimer() {
  if (!ADMIN_TOKEN) return;
  if (_idleTimer) clearTimeout(_idleTimer);
  if (_idleWarnTimer) clearTimeout(_idleWarnTimer);
  _idleTimer = setTimeout(_idleAutoLogout, IDLE_TIMEOUT_MS);
  _idleWarnTimer = setTimeout(_idleWarnSoon, IDLE_WARN_MS);
  // 還原標題（若已被警告過）
  if (document.title.indexOf('⚠') === 0) {
    document.title = document.title.replace(/^⚠ 即將自動登出 - /, '');
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
  // 依角色顯示/隱藏分頁
  var allTabs = ['vehicles','policies','claims','accidents','overview','agents','assign','logs'];
  var agentTabs = ['overview'];
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
  // 啟動閒置自動登出計時
  _bindIdleEvents();
  _resetIdleTimer();
}

async function doAdminLogin() {
  var user = document.getElementById('login-user').value.trim();
  var pass = document.getElementById('login-pass').value.trim();
  if (!user || !pass) { showMsg('login-msg','err','請輸入帳號和密碼'); return; }
  try {
    var r = await fetch(CONSOLE_API+'/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:user,password:pass})});
    var d = await r.json();
    if (d.success && d.data && d.data.token) {
      // ★ 持久化到 localStorage（按上一頁/重整/換分頁都不會掉）
      localStorage.setItem(LS_TOKEN_KEY, d.data.token);
      localStorage.setItem(LS_ROLE_KEY, d.data.admin.role);
      localStorage.setItem(LS_NAME_KEY, d.data.admin.display_name || '');
      _enterAdminUI(d.data.token, d.data.admin.role, d.data.admin.display_name);
    } else {
      showMsg('login-msg','err', d.message || '登入失敗');
    }
  } catch(e) { showMsg('login-msg','err','連線失敗: '+e.message); }
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
tryRestoreLogin();
// 2. DOMContentLoaded（保險，若 1 太早跑完）
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', tryRestoreLogin);
}
// 3. pageshow（處理瀏覽器「上一頁」從 bfcache 還原的情境）
window.addEventListener('pageshow', function(e) {
  // 若當前已是登入狀態（admin-panel 顯示中）就不再 restore
  if (document.getElementById('admin-panel').style.display === 'block') return;
  tryRestoreLogin();
});

function togglePw(inputId, btn) {
  var inp = document.getElementById(inputId);
  if (inp.type === 'password') { inp.type = 'text'; btn.textContent = '🙈'; }
  else { inp.type = 'password'; btn.textContent = '👁'; }
}

function doLogout() {
  TOKEN = ''; ADMIN_TOKEN = ''; ADMIN_ROLE = '';
  // 清 localStorage（明確登出才清，按上一頁不會清）
  localStorage.removeItem(LS_TOKEN_KEY);
  localStorage.removeItem(LS_ROLE_KEY);
  localStorage.removeItem(LS_NAME_KEY);
  document.getElementById('admin-panel').style.display = 'none';
  document.getElementById('logout-btn').style.display = 'none';
  document.getElementById('customer-bar').style.display = 'none';
  document.getElementById('login-section').style.display = 'block';
  document.getElementById('login-user').value = '';
  document.getElementById('login-pass').value = '';
  document.getElementById('user-info').textContent = '';
  // 停掉閒置計時 + 清空快速搜尋
  _stopIdleTimer();
  var qsBox = document.getElementById('qs-results'); if (qsBox) qsBox.innerHTML = '';
  var qsIn = document.getElementById('qs-input'); if (qsIn) qsIn.value = '';
  document.title = document.title.replace(/^⚠ 即將自動登出 - /, '');
}

function authHeaders(json) {
  var h = {'Authorization':'Bearer '+TOKEN};
  if (json) h['Content-Type'] = 'application/json';
  return h;
}
function consoleHeaders(json) {
  var h = {'Authorization':'Bearer '+ADMIN_TOKEN};
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
    var html = '<option value="">— 請選擇 —</option>';
    for (var i = 0; i < customers.length; i++) {
      var c = customers[i];
      var label = (c.name||'(未命名)') + (c.phone ? ' · '+c.phone : '') + (c.email ? ' · '+c.email : '');
      html += '<option value="'+c.id+'">'+label+'</option>';
    }
    sel.innerHTML = html;
    if (prev) sel.value = prev;
    document.getElementById('customer-bar-msg').textContent = '共 '+customers.length+' 位客戶';
  } catch(e) { document.getElementById('customer-bar-msg').textContent = '載入失敗'; }
}

// --- Tabs ---
function switchTab(name) {
  // 業務員權限檢查
  var adminOnly = ['vehicles','policies','claims','accidents','agents','assign','logs'];
  if (ADMIN_ROLE === 'agent' && adminOnly.indexOf(name) >= 0) {
    showMsg('login-msg', 'err', '您無此功能的權限');
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
  box.innerHTML = '<div style="color:#999;padding:8px">搜尋中…</div>';
  try {
    var resp = await fetch('/api/v1/admin-console/search?q=' + encodeURIComponent(q),
      {headers: {'Authorization':'Bearer ' + ADMIN_TOKEN}});
    var json = await resp.json();
    if (!json.success) { box.innerHTML = '<div style="color:#d32f2f;padding:8px">搜尋失敗：' + (json.message||'') + '</div>'; return; }
    var d = json.data || {};
    var html = '';
    var cust = d.customers || [], veh = d.vehicles || [], pol = d.policies || [], clm = d.claims || [];
    var total = cust.length + veh.length + pol.length + clm.length;
    if (total === 0) { box.innerHTML = '<div style="color:#666;padding:8px">查無資料</div>'; return; }

    var rowStyle = 'padding:8px 12px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:8px';
    var tagStyle = 'display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600';

    if (cust.length) {
      html += '<div style="font-size:12px;color:#666;padding:4px 0;margin-top:4px"><b>客戶 ('+cust.length+')</b></div>';
      cust.forEach(function(c) {
        html += '<div style="'+rowStyle+'" onclick="qsGoCustomer(\\''+c.id+'\\')" >' +
          '<span style="'+tagStyle+';background:#e3f2fd;color:#1565c0">客戶</span>' +
          '<b>' + (c.name || '(無名)') + '</b>' +
          '<span style="color:#666;font-size:13px">' + (c.email || '') + ' ' + (c.phone || '') + '</span>' +
          '<span style="margin-left:auto;color:#1976d2;font-size:12px">查看 →</span></div>';
      });
    }
    if (veh.length) {
      html += '<div style="font-size:12px;color:#666;padding:4px 0;margin-top:4px"><b>車輛 ('+veh.length+')</b></div>';
      veh.forEach(function(v) {
        html += '<div style="'+rowStyle+'" onclick="qsGoVehicle(\\''+v.id+'\\',\\''+v.user_id+'\\')">' +
          '<span style="'+tagStyle+';background:#fff3e0;color:#e65100">車輛</span>' +
          '<b>' + (v.plate_number || '') + '</b>' +
          '<span style="color:#666;font-size:13px">' + ((v.brand||'') + ' ' + (v.model||'')) + ' ('+(v.year||'')+')</span>' +
          '<span style="color:#999;font-size:12px">客戶: ' + (v.user_name || '') + '</span>' +
          '<span style="margin-left:auto;color:#1976d2;font-size:12px">查看 →</span></div>';
      });
    }
    if (pol.length) {
      html += '<div style="font-size:12px;color:#666;padding:4px 0;margin-top:4px"><b>保單 ('+pol.length+')</b></div>';
      pol.forEach(function(p) {
        html += '<div style="'+rowStyle+'" onclick="qsGoPolicy(\\''+p.id+'\\',\\''+p.user_id+'\\')">' +
          '<span style="'+tagStyle+';background:#e8f5e9;color:#2e7d32">保單</span>' +
          '<b>' + (p.policy_number || '') + '</b>' +
          '<span style="color:#666;font-size:13px">' + (p.insurer_name || '') + '</span>' +
          '<span style="color:#999;font-size:12px">' + (p.start_date||'') + ' ~ ' + (p.end_date||'') + ' / ' + (p.status||'') + '</span>' +
          '<span style="color:#999;font-size:12px">客戶: ' + (p.user_name || '') + '</span>' +
          '<span style="margin-left:auto;color:#1976d2;font-size:12px">查看 →</span></div>';
      });
    }
    if (clm.length) {
      html += '<div style="font-size:12px;color:#666;padding:4px 0;margin-top:4px"><b>理賠 ('+clm.length+')</b></div>';
      clm.forEach(function(cl) {
        html += '<div style="'+rowStyle+'" onclick="qsGoClaim(\\''+cl.id+'\\',\\''+cl.user_id+'\\')">' +
          '<span style="'+tagStyle+';background:#fce4ec;color:#c2185b">理賠</span>' +
          '<b>' + (cl.claim_number || '') + '</b>' +
          '<span style="color:#666;font-size:13px">' + (cl.claim_type || '') + '</span>' +
          '<span style="color:#999;font-size:12px">' + (cl.status || '') + '</span>' +
          '<span style="color:#999;font-size:12px">客戶: ' + (cl.user_name || '') + '</span>' +
          '<span style="margin-left:auto;color:#1976d2;font-size:12px">查看 →</span></div>';
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
    box.innerHTML = '<div style="color:#d32f2f;padding:8px">搜尋錯誤：' + e + '</div>';
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
}

// --- Vehicles ---
async function loadVehicles() {
  try {
    // 用 admin token 抓全部客戶的車輛（不再只看 admin@system 一人）
    var r = await fetch(CONSOLE_API+'/all/vehicles', {headers: consoleHeaders(false)});
    var d = await r.json();
    var vehicles = d.data || [];
    // Populate vehicle select (existing + new)
    var sel = document.getElementById('v-select');
    var psel = document.getElementById('p-vehicle');
    var opts = '<option value="__new__">+ 新增車輛</option>';
    var popts = '<option value="">不指定</option>';
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
        ? '<b>' + v.customer_name + '</b>' + (v.customer_phone ? '<br><span style="font-size:11px;color:#666">' + v.customer_phone + '</span>' : '')
        : '<span style="color:#999">-</span>';
      rows += '<tr><td>' + ownerCell + '</td>'
        + '<td><b>' + v.plate_number + '</b></td>'
        + '<td><span style="font-size:11px">' + (v.vehicle_type||'-') + '</span></td>'
        + '<td>' + (v.brand||'-') + '</td>'
        + '<td>' + (v.model||'-') + '</td>'
        + '<td>' + (v.year||'-') + '</td>'
        + '<td>' + (v.color||'-') + '</td>'
        + '<td>' + (v.engine_cc ? v.engine_cc+'cc' : '-') + '</td>'
        + '<td>' + (v.registration_expiry || '<span style="color:#999">未設定</span>') + '</td>'
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
  window._editVid = vid;
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
  document.getElementById('ve-year').value = veh.year || '';
  document.getElementById('ve-color').value = veh.color || '';
  document.getElementById('ve-cc').value = veh.engine_cc || '';
  document.getElementById('ve-vin').value = veh.vin || '';
  document.getElementById('ve-reg-date').value = veh.registration_date || '';
  document.getElementById('ve-expiry').value = veh.registration_expiry || '';
  document.getElementById('ve-fuel').value = veh.fuel_type || '';
  document.getElementById('v-edit-form').style.display = 'block';
  document.getElementById('v-edit-form').scrollIntoView({behavior:'smooth'});
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

async function saveEditedVehicle() {
  var vid = window._editVid || window._lastUploadVid;
  if (!vid) { showMsg('ve-msg','err','找不到車輛 ID'); return; }
  var body = {};
  var plate = document.getElementById('ve-plate').value.trim();
  if (plate) body.plate_number = plate;
  var brand = document.getElementById('ve-brand').value.trim();
  if (brand) body.brand = brand;
  var model = document.getElementById('ve-model').value.trim();
  if (model) body.model = model;
  var year = document.getElementById('ve-year').value;
  if (year) body.year = parseInt(year);
  var color = document.getElementById('ve-color').value.trim();
  if (color) body.color = color;
  var cc = document.getElementById('ve-cc').value;
  if (cc) body.engine_cc = parseInt(cc);
  var vin = document.getElementById('ve-vin').value.trim();
  if (vin) body.vin = vin;
  var regDate = document.getElementById('ve-reg-date').value;
  if (regDate) body.registration_date = regDate;
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
      document.getElementById('ve-year').value = veh.year || document.getElementById('ve-year').value;
      document.getElementById('ve-color').value = veh.color || document.getElementById('ve-color').value;
      document.getElementById('ve-cc').value = veh.engine_cc || document.getElementById('ve-cc').value;
      document.getElementById('ve-vin').value = veh.vin || document.getElementById('ve-vin').value;
      if (veh.registration_date) document.getElementById('ve-reg-date').value = veh.registration_date;
      if (veh.registration_expiry) document.getElementById('ve-expiry').value = veh.registration_expiry;
      if (veh.fuel_type) document.getElementById('ve-fuel').value = veh.fuel_type;
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
  if (!fn) { showMsg('p-upload-msg','err','請先上傳保單'); return; }
  var cid = currentCustomerId();
  if (!cid) { showMsg('p-upload-msg','err','請先在頂部「操作客戶」選擇要建保單的對象'); return; }
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
let itemCount = 0;
function addItemRow() {
  itemCount++;
  const div = document.createElement('div');
  div.className = 'item-row';
  div.id = 'item-'+itemCount;
  div.innerHTML =
    '<input placeholder="項目名稱 (如：強制汽車責任保險)" data-field="item_name">' +
    '<input type="number" placeholder="保額" data-field="coverage_limit" style="max-width:120px">' +
    '<input type="number" placeholder="自負額" data-field="deductible" style="max-width:100px">' +
    '<input type="number" placeholder="保費" data-field="premium" style="max-width:100px">' +
    '<button class="btn danger" onclick="this.parentElement.remove()">X</button>';
  document.getElementById('p-items').appendChild(div);
}

async function createPolicy() {
  const insurer = document.getElementById('p-insurer').value.trim();
  const number = document.getElementById('p-number').value.trim();
  if (!insurer || !number) { showMsg('p-msg','err','請填寫保險公司和保單號碼'); return; }
  const body = {
    insurer_name: insurer,
    policy_number: number,
    vehicle_id: document.getElementById('p-vehicle').value || null,
    status: document.getElementById('p-status').value,
    start_date: document.getElementById('p-start').value,
    end_date: document.getElementById('p-end').value,
    total_premium: parseFloat(document.getElementById('p-premium').value) || null,
    items: []
  };
  // Collect items
  document.querySelectorAll('.item-row').forEach(row => {
    const item = {};
    row.querySelectorAll('input').forEach(inp => {
      const f = inp.dataset.field;
      if (f) {
        if (f === 'item_name') item[f] = inp.value;
        else if (inp.value) item[f] = parseFloat(inp.value);
      }
    });
    if (item.item_name) body.items.push(item);
  });
  var cid = currentCustomerId();
  if (!cid) { showMsg('p-msg','err','請先在頂部「操作客戶」選擇要建保單的對象'); return; }
  try {
    const r = await fetch(CONSOLE_API+'/customer/'+cid+'/policies', {method:'POST', headers:consoleHeaders(true), body:JSON.stringify(body)});
    const d = await r.json();
    if (d.success) {
      showMsg('p-msg','ok','保單建立成功: '+d.data.policy_number);
      loadPolicies();
      // Clear form
      ['p-insurer','p-number','p-premium'].forEach(id => document.getElementById(id).value='');
      document.getElementById('p-items').innerHTML = '';
      itemCount = 0;
    } else { showMsg('p-msg','err','建立失敗: '+(d.detail||d.message)); }
  } catch(e) { showMsg('p-msg','err','建立失敗: '+e.message); }
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
      ? '<b>'+p.customer_name+'</b>' + (p.customer_phone ? '<br><span style="font-size:11px;color:#666">'+p.customer_phone+'</span>' : '')
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
    html += '<td>'+(p.start_date||'-')+'</td><td>'+(p.end_date||'-')+'</td>';
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
  document.getElementById('pe-insurer').value = p.insurer_name || '';
  document.getElementById('pe-start').value = p.start_date || '';
  document.getElementById('pe-end').value = p.end_date || '';
  document.getElementById('pe-premium').value = p.total_premium || '';
  document.getElementById('pe-status').value = p.status || 'active';
  document.getElementById('p-edit-modal').style.display = 'flex';
}

function closePolicyEdit() {
  document.getElementById('p-edit-modal').style.display = 'none';
}

async function savePolicyEdit() {
  var pid = window._editPolicyId;
  if (!pid) return;
  var body = {
    policy_number: document.getElementById('pe-number').value.trim(),
    insurer_name: document.getElementById('pe-insurer').value.trim(),
    start_date: document.getElementById('pe-start').value,
    end_date: document.getElementById('pe-end').value,
    status: document.getElementById('pe-status').value,
  };
  var prem = document.getElementById('pe-premium').value;
  if (prem) body.total_premium = parseFloat(prem);

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
        '<tr><td style="width:200px"><b>客戶數</b></td><td><span style="font-size:18px;color:#1565C0">'+(o.customer_count||0)+'</span></td></tr>' +
        '<tr><td><b>車輛數</b></td><td><span style="font-size:18px;color:#1565C0">'+(o.vehicle_count||0)+'</span></td></tr>' +
        '<tr><td><b>保單總數</b></td><td><span style="font-size:18px;color:#1565C0">'+(o.policy_count||0)+'</span></td></tr>' +
        '<tr><td><b>有效保單</b></td><td><span style="color:#2E7D32">'+(o.policy_active||0)+'</span></td></tr>' +
        '<tr><td><b>即將到期</b></td><td><span style="color:#FF9800">'+(o.policy_expiring||0)+'</span></td></tr>' +
        '<tr><td><b>已到期</b></td><td><span style="color:#999">'+(o.policy_expired||0)+'</span></td></tr>' +
        '<tr><td><b>累計保費</b></td><td>$'+Number(o.total_premium||0).toLocaleString()+'</td></tr>' +
        '</table>';
      var upcoming = o.upcoming_30d || [];
      if (upcoming.length > 0) {
        html += '<h3 style="margin-top:14px;color:#FF9800">30 天內到期 ('+upcoming.length+' 張)</h3>';
        html += '<table><thead><tr><th>保單號碼</th><th>保險公司</th><th>到期日</th><th>剩餘天數</th></tr></thead><tbody>';
        for (var i = 0; i < upcoming.length; i++) {
          var u = upcoming[i];
          var color = u.days_left <= 7 ? '#D32F2F' : u.days_left <= 14 ? '#FF9800' : '#666';
          html += '<tr><td style="font-family:monospace;font-size:11px">'+u.policy_number+'</td><td>'+u.insurer+'</td><td>'+u.end_date+'</td>';
          html += '<td><span style="color:'+color+';font-weight:bold">'+u.days_left+' 天</span></td></tr>';
        }
        html += '</tbody></table>';
      }
      document.getElementById('overview-content').innerHTML = html;
    } catch(e) { document.getElementById('overview-content').innerHTML = '<p style="color:#999">載入失敗: '+e.message+'</p>'; }
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
