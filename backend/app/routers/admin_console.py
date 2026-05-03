"""管理後台控制台 — 直接 redirect 到 /admin（白底版完整功能介面）

舊 /admin-console 暗黑版 UI 已停用，內容保留於本檔備份但不再 serve。
若需要新版功能（重複偵測、合併工具）會在 /admin 內補實作。
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter()

CONSOLE_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>管理控制台</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Microsoft JhengHei',Arial,sans-serif;background:#f5f7fa;color:#333}
.header{background:#1565C0;color:#fff;padding:14px 24px;display:flex;align-items:center;justify-content:space-between}
.header h1{font-size:18px;color:#fff} .header .user{font-size:13px;color:rgba(255,255,255,.85)}
.container{max-width:1200px;margin:0 auto;padding:20px}
.tabs{display:flex;gap:4px;margin-bottom:20px;border-bottom:2px solid #1565C0;padding-bottom:0}
.tab{padding:10px 20px;background:#e0e0e0;border:none;color:#555;cursor:pointer;font-size:13px;font-weight:bold;border-radius:8px 8px 0 0;margin-right:4px}
.tab.active{background:#1565C0;color:#fff}
.card{background:#fff;border-radius:12px;padding:20px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
.card h2{font-size:15px;color:#1565C0;margin-bottom:14px}
label{display:block;font-size:12px;color:#666;margin-bottom:4px;margin-top:10px}
input,select{width:100%;padding:8px;background:#fff;border:1px solid #ccc;border-radius:6px;color:#333;font-size:13px}
input:focus,select:focus{outline:none;border-color:#1565C0;box-shadow:0 0 0 2px rgba(21,101,192,.15)}
.btn{padding:10px 20px;border:none;border-radius:8px;font-size:13px;font-weight:bold;cursor:pointer;margin-top:10px}
.btn-primary{background:#1565C0;color:#fff} .btn-primary:hover{background:#0D47A1}
.btn-danger{background:#D32F2F;color:#fff} .btn-danger:hover{background:#B71C1C}
.btn-success{background:#2E7D32;color:#fff} .btn-success:hover{background:#1B5E20}
.btn-sm{padding:4px 10px;font-size:11px;margin:2px}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
th{background:#1565C0;padding:10px;text-align:left;color:#fff;font-size:12px;font-weight:bold}
td{padding:9px 10px;border-bottom:1px solid #eee}
tr:hover td{background:#f5f7fa}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:bold}
.badge-green{background:#E8F5E9;color:#2E7D32;border:1px solid #A5D6A7}
.badge-red{background:#FFEBEE;color:#C62828;border:1px solid #EF9A9A}
.badge-blue{background:#E3F2FD;color:#1565C0;border:1px solid #90CAF9}
.row{display:flex;gap:12px} .row>div{flex:1}
.msg{padding:10px;border-radius:6px;margin-top:8px;font-size:12px;display:none}
.msg.ok{display:block;background:#E8F5E9;color:#2E7D32;border:1px solid #A5D6A7}
.msg.err{display:block;background:#FFEBEE;color:#C62828;border:1px solid #EF9A9A}
#login-box{max-width:400px;margin:100px auto}
.tab-content{display:none} .tab-content.active{display:block}
.log-row{font-size:12px;color:#555}
</style>
</head>
<body>

<!-- Login -->
<div id="login-box">
  <div class="card">
    <h2>管理控制台登入</h2>
    <label>帳號</label><input type="text" id="login-user" placeholder="admin">
    <label>密碼</label><input type="password" id="login-pass" placeholder="密碼" onkeydown="if(event.key==='Enter')doLogin()">
    <button class="btn btn-primary" style="width:100%;margin-top:14px" onclick="doLogin()">登入</button>
    <div id="login-msg" class="msg"></div>
  </div>
</div>

<!-- Console (hidden until login) -->
<div id="console" style="display:none">
  <div class="header">
    <h1>管理控制台</h1>
    <div><span class="user" id="admin-info"></span> <button class="btn btn-sm btn-danger" onclick="doLogout()">登出</button></div>
  </div>
  <div class="container">
    <div class="tabs" id="main-tabs">
      <button class="tab active" onclick="switchTab('agents')">業務員管理</button>
      <button class="tab" onclick="switchTab('customers')">客戶管理</button>
      <button class="tab" onclick="switchTab('assign')">客戶分配</button>
      <button class="tab" onclick="switchTab('duplicates')">重複偵測</button>
      <button class="tab" onclick="switchTab('logs')">操作日誌</button>
    </div>

    <!-- Agents Tab -->
    <div id="tab-agents" class="tab-content active">
      <div class="card">
        <h2>新增業務員</h2>
        <div class="row">
          <div><label>帳號</label><input id="ag-user" placeholder="agent01"></div>
          <div><label>密碼</label><input id="ag-pass" type="password" placeholder="強密碼"></div>
        </div>
        <div class="row">
          <div><label>顯示名稱</label><input id="ag-name" placeholder="王小明"></div>
          <div><label>Email</label><input id="ag-email"></div>
        </div>
        <div class="row">
          <div><label>電話</label><input id="ag-phone"></div>
          <div><label>IP 白名單（逗號分隔，空=不限）</label><input id="ag-ip" placeholder="1.2.3.4,5.6.7.8"></div>
        </div>
        <button class="btn btn-primary" onclick="createAgent()">新增業務員</button>
        <div id="ag-msg" class="msg"></div>
      </div>
      <div class="card">
        <h2>業務員列表</h2>
        <table><thead><tr><th>帳號</th><th>名稱</th><th>狀態</th><th>客戶數</th><th>最後登入</th><th>API Key</th><th>操作</th></tr></thead>
        <tbody id="agents-table"></tbody></table>
      </div>
    </div>

    <!-- Customers Tab -->
    <div id="tab-customers" class="tab-content">
      <div class="card">
        <h2>客戶列表</h2>
        <button class="btn btn-primary btn-sm" onclick="loadCustomers()">重新載入</button>
        <table><thead><tr><th>姓名</th><th>電話</th><th>Email</th><th>建立時間</th><th>操作</th></tr></thead>
        <tbody id="customers-table"></tbody></table>
        <div id="cust-msg" class="msg"></div>
      </div>
    </div>

    <!-- Duplicates Tab -->
    <div id="tab-duplicates" class="tab-content">
      <div class="card">
        <h2>重複客戶偵測</h2>
        <p style="font-size:12px;color:#666;margin-bottom:8px">
          找出可能是同一個人但有多個帳號的客戶（同身份證 hash、或同名+同生日）。<br>
          常見情境：客戶用 Google/Apple 登入時建了新 user，與業務員 import 的 phone-only 帳號分離。
        </p>
        <button class="btn btn-primary btn-sm" onclick="loadDuplicates()">掃描重複帳號</button>
        <div id="dup-list" style="margin-top:14px"></div>
        <div id="dup-msg" class="msg"></div>
      </div>
    </div>

    <!-- Assign Tab -->
    <div id="tab-assign" class="tab-content">
      <div class="card">
        <h2>分配客戶給業務員</h2>
        <div class="row">
          <div><label>選擇業務員</label><select id="assign-agent"></select></div>
          <div><label>選擇客戶</label><select id="assign-customer"></select></div>
        </div>
        <button class="btn btn-success" onclick="assignCustomer()">分配</button>
        <div id="assign-msg" class="msg"></div>
      </div>
    </div>

    <!-- Logs Tab -->
    <div id="tab-logs" class="tab-content">
      <div class="card">
        <h2>操作日誌</h2>
        <button class="btn btn-primary btn-sm" onclick="loadLogs()">載入最新</button>
        <table><thead><tr><th>時間</th><th>管理員</th><th>操作</th><th>目標</th><th>說明</th><th>IP</th></tr></thead>
        <tbody id="logs-table"></tbody></table>
      </div>
    </div>
  </div>
</div>

<script>
var API = '/api/v1/admin-console';
var TOKEN = '';

function authHeaders(json) {
  var h = {'Authorization': 'Bearer ' + TOKEN};
  if (json) h['Content-Type'] = 'application/json';
  return h;
}
function showMsg(id, type, text) {
  var el = document.getElementById(id);
  el.className = 'msg ' + type; el.textContent = text; el.style.display = 'block';
  if (type === 'ok') setTimeout(function(){el.style.display='none';}, 5000);
}
function switchTab(name) {
  document.querySelectorAll('.tab-content').forEach(function(e){e.classList.remove('active');});
  document.querySelectorAll('.tab').forEach(function(e){e.classList.remove('active');});
  document.getElementById('tab-'+name).classList.add('active');
  event.target.classList.add('active');
  if (name === 'agents') loadAgents();
  if (name === 'customers') loadCustomers();
  if (name === 'assign') { loadAgentsForSelect(); loadCustomersForSelect(); }
  if (name === 'duplicates') {} // 等使用者按掃描鍵才跑
  if (name === 'logs') loadLogs();
}

async function doLogin() {
  var user = document.getElementById('login-user').value;
  var pass = document.getElementById('login-pass').value;
  try {
    var r = await fetch(API+'/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:user,password:pass})});
    var d = await r.json();
    if (d.success && d.data && d.data.token) {
      TOKEN = d.data.token;
      document.getElementById('admin-info').textContent = d.data.admin.display_name + ' (' + d.data.admin.role + ')';
      document.getElementById('login-box').style.display = 'none';
      document.getElementById('console').style.display = 'block';
      // Hide agent-only tabs for non-super-admin
      if (d.data.admin.role !== 'super_admin') {
        document.getElementById('main-tabs').querySelectorAll('.tab')[0].style.display = 'none'; // agents
        document.getElementById('main-tabs').querySelectorAll('.tab')[2].style.display = 'none'; // assign
        document.getElementById('main-tabs').querySelectorAll('.tab')[3].style.display = 'none'; // logs
        switchTab('customers');
      } else {
        loadAgents();
      }
    } else {
      showMsg('login-msg', 'err', d.message || '登入失敗');
    }
  } catch(e) { showMsg('login-msg', 'err', '連線失敗'); }
}
function doLogout() {
  TOKEN = '';
  document.getElementById('console').style.display = 'none';
  document.getElementById('login-box').style.display = 'block';
}

async function loadAgents() {
  var r = await fetch(API+'/agents', {headers:authHeaders()});
  var d = await r.json();
  var agents = d.data || [];
  var html = '';
  for (var i = 0; i < agents.length; i++) {
    var a = agents[i];
    var status = a.is_active ? '<span class="badge badge-green">啟用</span>' : '<span class="badge badge-red">停用</span>';
    html += '<tr><td><b>'+a.username+'</b></td><td>'+a.display_name+'</td><td>'+status+'</td>';
    html += '<td>'+a.customer_count+'</td><td style="font-size:11px">'+(a.last_login||'-')+'</td>';
    html += '<td style="font-size:11px">'+a.api_key+'</td>';
    html += '<td style="white-space:nowrap">';
    if (a.is_active) {
      html += '<button class="btn btn-danger btn-sm" onclick="toggleAgent(&quot;'+a.id+'&quot;,false)">停用</button>';
    } else {
      html += '<button class="btn btn-success btn-sm" onclick="toggleAgent(&quot;'+a.id+'&quot;,true)">啟用</button>';
    }
    html += '</td></tr>';
  }
  document.getElementById('agents-table').innerHTML = html || '<tr><td colspan="7" style="color:#666">尚無業務員</td></tr>';
}

async function createAgent() {
  var body = {
    username: document.getElementById('ag-user').value,
    password: document.getElementById('ag-pass').value,
    display_name: document.getElementById('ag-name').value,
    email: document.getElementById('ag-email').value,
    phone: document.getElementById('ag-phone').value,
    ip_whitelist: document.getElementById('ag-ip').value,
  };
  if (!body.username || !body.password) { showMsg('ag-msg','err','帳號和密碼必填'); return; }
  var r = await fetch(API+'/agents', {method:'POST', headers:authHeaders(true), body:JSON.stringify(body)});
  var d = await r.json();
  if (d.success) { showMsg('ag-msg','ok',d.message+' API Key: '+d.data.api_key); loadAgents(); }
  else { showMsg('ag-msg','err',d.message || d.detail); }
}

async function toggleAgent(id, active) {
  await fetch(API+'/agents/'+id, {method:'PATCH', headers:authHeaders(true), body:JSON.stringify({is_active:active})});
  loadAgents();
}

async function loadCustomers() {
  var r = await fetch(API+'/customers', {headers:authHeaders()});
  var d = await r.json();
  var list = d.data || [];
  var html = '';
  for (var i = 0; i < list.length; i++) {
    var c = list[i];
    var nameEsc = (c.name||'').replace(/"/g,'&quot;');
    html += '<tr><td>'+(c.name||'-')+'</td><td>'+(c.phone||'-')+'</td><td>'+(c.email||'-')+'</td>';
    html += '<td style="font-size:11px">'+(c.created_at||'').substring(0,10)+'</td>';
    html += '<td style="white-space:nowrap">';
    html += '<button class="btn btn-sm" style="background:#0891b2;color:#fff;margin-right:4px" onclick="toggleDetails(&quot;'+c.id+'&quot;)">車輛/保單</button>';
    html += '<button class="btn btn-primary btn-sm" onclick="editCustomer(&quot;'+c.id+'&quot;,&quot;'+nameEsc+'&quot;,&quot;'+(c.phone||'')+'&quot;,&quot;'+(c.email||'')+'&quot;)">編輯</button>';
    html += '</td></tr>';
    // 隱藏的展開行
    html += '<tr id="details-'+c.id+'" style="display:none"><td colspan="5" style="background:#f5f7fa;padding:14px"><div id="details-content-'+c.id+'">載入中...</div></td></tr>';
  }
  document.getElementById('customers-table').innerHTML = html || '<tr><td colspan="5" style="color:#666">尚無客戶</td></tr>';
}

async function toggleDetails(customerId) {
  var row = document.getElementById('details-'+customerId);
  if (row.style.display === 'none' || !row.style.display) {
    row.style.display = '';
    await loadCustomerDetails(customerId);
  } else {
    row.style.display = 'none';
  }
}

function statusBadge(s) {
  if (s === 'active') return '<span class="badge badge-green">' + s + '</span>';
  if (s === 'expired') return '<span class="badge badge-red">' + s + '</span>';
  if (s === 'expiring') return '<span style="background:#78350f;color:#fcd34d;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold">' + s + '</span>';
  return '<span class="badge badge-blue">' + s + '</span>';
}

function fmtMoney(n) {
  if (n === null || n === undefined || n === 0) return '-';
  return '$' + Number(n).toLocaleString();
}

async function loadCustomerDetails(customerId) {
  var content = document.getElementById('details-content-'+customerId);
  content.innerHTML = '<div style="color:#666;font-size:12px">載入中...</div>';

  try {
    var [vRes, pRes] = await Promise.all([
      fetch(API+'/customer/'+customerId+'/vehicles', {headers:authHeaders()}),
      fetch(API+'/customer/'+customerId+'/policies', {headers:authHeaders()}),
    ]);
    var vehicles = (await vRes.json()).data || [];
    var policies = (await pRes.json()).data || [];

    var html = '';

    // ── 車輛區 ──────────────────────────────
    html += '<div style="margin-bottom:18px"><div style="color:#1565C0;font-size:14px;font-weight:bold;margin-bottom:8px">🚗 車輛 (' + vehicles.length + ')</div>';
    if (vehicles.length === 0) {
      html += '<div style="color:#888;font-size:12px;padding:10px;background:#fff;border-radius:6px">此客戶名下無車輛（如機構商業險、僅責任險）</div>';
    } else {
      html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:12px">';
      for (var i = 0; i < vehicles.length; i++) {
        var v = vehicles[i];
        html += '<div style="background:#fff;padding:12px;border-radius:8px;border:1px solid #ddd">';
        html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">';
        html += '<div style="font-family:monospace;font-size:15px;font-weight:bold;color:#F57C00">' + (v.plate||'-') + '</div>';
        if (v.is_primary) html += '<span class="badge badge-blue">主要</span>';
        html += '</div>';

        html += '<table style="font-size:12px;width:100%"><tbody>';
        html += '<tr><td style="color:#666;width:80px">廠牌/型號</td><td>' + (v.brand||'-') + ' / ' + (v.model||'-') + '</td></tr>';
        html += '<tr><td style="color:#666">車種</td><td>' + (v.vehicle_type||'-') + '</td></tr>';
        html += '<tr><td style="color:#666">年份</td><td>' + (v.year||'-') + '</td></tr>';
        html += '<tr><td style="color:#666">引擎</td><td>' + (v.engine_cc ? v.engine_cc+' cc' : '-') + ' (' + (v.fuel_type||'-') + ')</td></tr>';
        html += '<tr><td style="color:#666">VIN</td><td style="font-family:monospace;font-size:11px">' + (v.vin||'-') + '</td></tr>';
        html += '<tr><td style="color:#666">行照到期</td><td>' + (v.registration_expiry||'-') + '</td></tr>';
        html += '</tbody></table>';

        // 行照圖片
        html += '<div style="margin-top:10px">';
        if (v.registration_image_url) {
          html += '<a href="' + v.registration_image_url + '" target="_blank" style="display:inline-block">';
          html += '<img src="' + v.registration_image_url + '" style="max-width:100%;max-height:120px;border-radius:6px;border:1px solid #475569" alt="行照">';
          html += '<div style="font-size:11px;color:#1565C0;margin-top:4px">📷 點擊看大圖</div>';
          html += '</a>';
        } else {
          html += '<div style="font-size:11px;color:#888;font-style:italic">尚未上傳行照</div>';
        }
        html += '</div>';
        html += '</div>';
      }
      html += '</div>';
    }
    html += '</div>';

    // ── 保單區 ──────────────────────────────
    html += '<div><div style="color:#1565C0;font-size:14px;font-weight:bold;margin-bottom:8px">📄 保單 (' + policies.length + ')</div>';
    if (policies.length === 0) {
      html += '<div style="color:#888;font-size:12px;padding:10px;background:#fff;border-radius:6px">無保單紀錄</div>';
    } else {
      for (var j = 0; j < policies.length; j++) {
        var p = policies[j];
        html += '<div style="background:#fff;padding:12px;border-radius:8px;border:1px solid #ddd;margin-bottom:10px">';

        // 保單抬頭
        html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:6px">';
        html += '<div><span style="font-weight:bold;color:#222">' + (p.insurer||'-') + '</span>';
        html += ' <span style="color:#666;font-size:11px;font-family:monospace">' + (p.number||'-') + '</span></div>';
        html += '<div>' + statusBadge(p.status) + ' <span style="color:#666;font-size:12px;margin-left:8px">' + (p.start||'') + ' ~ ' + (p.end||'') + '</span></div>';
        html += '</div>';

        // 車輛掛接（若有）
        if (p.vehicle_plate) {
          html += '<div style="font-size:12px;color:#666;margin-bottom:6px">掛車：<span style="font-family:monospace;color:#F57C00">' + p.vehicle_plate + '</span></div>';
        }

        // 總保費
        html += '<div style="font-size:13px;color:#2E7D32;margin-bottom:8px">總保費：<span style="font-weight:bold">' + fmtMoney(p.premium) + '</span></div>';

        // 險種項目
        var items = p.items || [];
        if (items.length > 0) {
          html += '<table style="font-size:12px;width:100%;margin-top:6px"><thead><tr>';
          html += '<th>險種</th><th style="text-align:right">保費</th><th style="text-align:right">保額</th><th style="text-align:right">自負額</th><th>說明</th>';
          html += '</tr></thead><tbody>';
          for (var k = 0; k < items.length; k++) {
            var it = items[k];
            html += '<tr>';
            html += '<td>' + (it.item_name||'-') + '</td>';
            html += '<td style="text-align:right;color:#2E7D32">' + fmtMoney(it.premium) + '</td>';
            html += '<td style="text-align:right">' + fmtMoney(it.coverage_limit) + '</td>';
            html += '<td style="text-align:right">' + fmtMoney(it.deductible) + '</td>';
            html += '<td style="font-size:11px;color:#555">' + (it.description||'-') + '</td>';
            html += '</tr>';
          }
          html += '</tbody></table>';
        }

        html += '</div>';
      }
    }
    html += '</div>';

    content.innerHTML = html;
  } catch (e) {
    content.innerHTML = '<div style="color:#C62828">載入失敗：'+e+'</div>';
  }
}

async function editCustomer(id, curName, curPhone, curEmail) {
  var name = prompt('姓名（留空保留原值）：', curName);
  if (name === null) return;
  var phone = prompt('電話（留空清除）：', curPhone);
  if (phone === null) return;
  var email = prompt('Email（留空清除）：', curEmail);
  if (email === null) return;

  var body = {};
  if (name !== curName) body.name = name;
  if (phone !== curPhone) body.phone = phone;
  if (email !== curEmail) body.email = email;
  if (Object.keys(body).length === 0) { showMsg('cust-msg','ok','無變更'); return; }

  var r = await fetch(API+'/customer/'+id, {method:'PATCH', headers:authHeaders(true), body:JSON.stringify(body)});
  var d = await r.json();
  if (d.success) { showMsg('cust-msg','ok','已更新'); loadCustomers(); }
  else { showMsg('cust-msg','err',d.message || d.detail || '更新失敗'); }
}

async function loadDuplicates() {
  var r = await fetch(API+'/customers/duplicates', {headers:authHeaders()});
  var d = await r.json();
  if (!d.success) { showMsg('dup-msg','err',d.message||'掃描失敗'); return; }
  var data = d.data || {};
  var groups = (data.by_id_number||[]).concat(data.by_name_birthdate||[]);

  if (groups.length === 0) {
    document.getElementById('dup-list').innerHTML = '<p style="color:#34d399;font-size:13px">沒有偵測到重複帳號</p>';
    return;
  }

  var html = '<p style="font-size:12px;color:#F57C00;margin-bottom:10px">共偵測到 '+groups.length+' 組可能重複</p>';
  for (var i = 0; i < groups.length; i++) {
    var g = groups[i];
    var typeLabel = g.match_type === 'id_number' ? '身份證 hash 相同' : '同名+同生日';
    html += '<div style="background:#f5f7fa;padding:12px;border-radius:8px;margin-bottom:10px;border:1px solid #ddd">';
    html += '<div style="font-size:12px;color:#1565C0;margin-bottom:8px">比對方式：'+typeLabel+'</div>';
    html += '<table style="margin:0"><thead><tr><th>選</th><th>姓名</th><th>電話</th><th>Email</th><th>建立時間</th></tr></thead><tbody>';
    for (var j = 0; j < g.users.length; j++) {
      var u = g.users[j];
      html += '<tr><td><input type="radio" name="dup_'+i+'_primary" value="'+u.id+'"'+(j===0?' checked':'')+'></td>';
      html += '<td>'+(u.name||'-')+'</td><td>'+(u.phone||'-')+'</td><td>'+(u.email||'-')+'</td>';
      html += '<td style="font-size:11px">'+((u.created_at||'').substring(0,10))+'</td></tr>';
    }
    html += '</tbody></table>';
    html += '<button class="btn btn-success btn-sm" onclick="mergeGroup('+i+',['+g.users.map(function(u){return '&quot;'+u.id+'&quot;';}).join(',')+'])">合併到選定的主帳號</button>';
    html += '</div>';
  }
  document.getElementById('dup-list').innerHTML = html;
}

async function mergeGroup(idx, ids) {
  var radios = document.querySelectorAll('input[name="dup_'+idx+'_primary"]');
  var primary = '';
  for (var i = 0; i < radios.length; i++) if (radios[i].checked) primary = radios[i].value;
  if (!primary) { showMsg('dup-msg','err','請選一個主帳號'); return; }
  var others = ids.filter(function(id){ return id !== primary; });
  if (!confirm('確認把 '+others.length+' 個次帳號合併到主帳號？\\n（次帳號的車輛、保單、事故、理賠、通知都會轉移到主帳號，次帳號將刪除）')) return;

  for (var i = 0; i < others.length; i++) {
    var r = await fetch(API+'/customers/merge', {method:'POST', headers:authHeaders(true),
      body:JSON.stringify({primary_user_id:primary, secondary_user_id:others[i]})});
    var d = await r.json();
    if (!d.success) { showMsg('dup-msg','err','合併失敗：'+(d.message||d.detail)); return; }
  }
  showMsg('dup-msg','ok','已合併 '+others.length+' 個帳號');
  loadDuplicates();
}

async function loadAgentsForSelect() {
  var r = await fetch(API+'/agents', {headers:authHeaders()});
  var d = await r.json();
  var html = '<option value="">選擇業務員</option>';
  for (var i = 0; i < (d.data||[]).length; i++) {
    var a = d.data[i];
    if (a.is_active) html += '<option value="'+a.id+'">'+a.display_name+' ('+a.username+')</option>';
  }
  document.getElementById('assign-agent').innerHTML = html;
}
async function loadCustomersForSelect() {
  var r = await fetch(API+'/customers', {headers:authHeaders()});
  var d = await r.json();
  var html = '<option value="">選擇客戶</option>';
  for (var i = 0; i < (d.data||[]).length; i++) {
    var c = d.data[i];
    html += '<option value="'+c.id+'">'+(c.name||c.phone||c.email)+'</option>';
  }
  document.getElementById('assign-customer').innerHTML = html;
}
async function assignCustomer() {
  var agentId = document.getElementById('assign-agent').value;
  var customerId = document.getElementById('assign-customer').value;
  if (!agentId || !customerId) { showMsg('assign-msg','err','請選擇業務員和客戶'); return; }
  var r = await fetch(API+'/assign-customer', {method:'POST', headers:authHeaders(true), body:JSON.stringify({agent_id:agentId,customer_id:customerId})});
  var d = await r.json();
  if (d.success) showMsg('assign-msg','ok',d.message);
  else showMsg('assign-msg','err',d.message||d.detail);
}

async function loadLogs() {
  var r = await fetch(API+'/audit-logs', {headers:authHeaders()});
  var d = await r.json();
  var logs = d.data || [];
  var html = '';
  for (var i = 0; i < logs.length; i++) {
    var l = logs[i];
    html += '<tr class="log-row"><td>'+l.timestamp.substring(0,19).replace('T',' ')+'</td>';
    html += '<td>'+l.admin+'</td><td><span class="badge badge-blue">'+l.action+'</span></td>';
    html += '<td>'+(l.target_type||'')+' '+(l.target_id?l.target_id.substring(0,8):'')+'</td>';
    html += '<td>'+(l.detail||'')+'</td><td>'+(l.ip||'')+'</td></tr>';
  }
  document.getElementById('logs-table').innerHTML = html || '<tr><td colspan="6" style="color:#666">尚無日誌</td></tr>';
}
</script>
</body></html>"""

@router.get("")
async def admin_console_redirect():
    """Redirect 到 /admin（用戶選擇的白底版介面）"""
    return RedirectResponse(url="/admin", status_code=307)
