# BOPINAN 訂閱制 SPEC v1.0

> 業務員後台訂閱付費,客戶前台永久免費。
> Module 設計成可獨立抽出,未來可單獨服務化(其他 SaaS 也能用同一套訂閱引擎)。

## 1. 商業規則

| 項目 | 設定 |
|---|---|
| 試用期 | 7 天免費(從業務員帳號建立當下開始) |
| 月費 | NT$149 / 30 天 |
| 試用結束 → 未付費 | 阻擋大部分後台功能,但仍可登入並看到續訂頁 |
| 付費 | 啟用 30 天;到期前後 N 天可續訂 |
| 取消 | 用到當期結束才停權,不退費 |
| 寬限期 | 期末過後 3 天內仍可使用(避開繳費 race),3 天後封鎖 |
| super_admin | 永不被擋(系統管理者免訂閱) |

## 2. 資料模型(AdminUser 直接加欄位,簡單為主)

```python
# 新增欄位 (透過 _ensure_columns 自動 migration)
subscription_status: str       # trial / active / past_due / cancelled / expired
trial_started_at: DateTime     # 帳號建立 = trial 開始
subscription_period_end: DateTime  # trial 或 paid 期間的結束時間
subscription_cancelled_at: DateTime  # 取消那一刻(period_end 不變)
subscription_price_twd: int    # 149 (預留未來不同方案)
subscription_payment_ref: str  # 外部金流系統的訂閱/交易編號(provider-agnostic)
```

狀態機:
```
[新建 agent] → trial(7d)
                ├ 7d 內付款 → active(+30d)
                ├ 7d 後沒付 → expired(寬限 3d) → 封鎖
                └ 在 trial 內取消 → cancelled(用到 trial 末)

active(月付)
  ├ 付下個月 → active(period_end +30d)
  ├ 超過寬限 → past_due → 封鎖
  └ 取消 → cancelled(用到 period_end)
```

## 3. API

### 業務員自己看 (任何 admin 可用)
- `GET /api/v1/billing/subscription/me`
  → 回傳:status, period_end, days_remaining, price, can_use

### super_admin 管理 (全部 agent)
- `GET /api/v1/billing/subscriptions` — 列出所有 agent 訂閱狀態
- `POST /api/v1/billing/subscriptions/{agent_id}/extend` body: `{months: 1, payment_ref: "ECPAY-xxx"}` — 手動延期(收到匯款後 super_admin 標記)
- `POST /api/v1/billing/subscriptions/{agent_id}/cancel` — 立即取消(管理用,真實取消由 agent 自己呼叫)
- `POST /api/v1/billing/subscriptions/{agent_id}/reactivate` — 重啟已取消的訂閱

### 業務員自助
- `POST /api/v1/billing/subscription/cancel` — 取消自己訂閱(用到當期結束)

### 外部金流 webhook(預留,未來綠界/Stripe 串接用)
- `POST /api/v1/billing/webhook/{provider}` body: provider-specific payload
  - 驗證簽章 → 確認付款成功 → 自動 extend

## 4. 存取控制

新增 dependency:
```python
async def require_active_subscription(admin = Depends(get_current_admin)) -> AdminUser:
    """檢查訂閱有效,過期則 raise SubscriptionExpiredError(403)"""
    if admin.role == 'super_admin':
        return admin
    status = compute_status(admin)  # 即時計算（讀 period_end + now）
    if status not in ('trial', 'active', 'cancelled_with_remaining'):
        raise ForbiddenError("訂閱已過期,請續訂")
    return admin
```

套用範圍:
- ✅ 大部分 admin endpoint(查客戶/車輛/保單/上傳/OCR 等)
- ❌ 自己看訂閱狀態(`/billing/subscription/me`)永遠開放
- ❌ 取消訂閱永遠開放
- ❌ 變更密碼永遠開放

login endpoint **不擋**,過期 agent 仍可登入(否則沒辦法續訂)。

## 5. UI

### 後台頂部 banner(永遠顯示)
```
[trial] 🎉 免費試用中,還剩 5 天 → [立即訂閱]
[active] ✓ 已訂閱,下次扣款 2026-06-08
[past_due] ⚠️ 訂閱已過期,大部分功能已停用 → [立即續訂]
[cancelled_with_remaining] 已取消,可使用至 2026-06-08
```

### 訂閱專頁 (`/admin/billing` 或 admin console 內 tab)
- 目前狀態 + 訂閱期間
- 續訂按鈕(MVP:顯示銀行帳號讓 agent 匯款 → super_admin 收到後手動 extend)
- 取消按鈕
- 過往訂閱紀錄 (audit log)

### 過期時的封鎖 UI
所有 admin 主功能 tab 顯示 overlay:「訂閱已過期,請先續訂」+ 跳到訂閱頁的按鈕。

## 6. 通知

排程(已有 APScheduler):
- 試用 day 5:Email「還有 2 天試用結束,記得訂閱」
- 試用 day 6:Email + LINE
- 試用 day 7:今天最後一天
- 訂閱到期前 3 天:同上提醒
- 訂閱當天到期未續:封鎖 + 通知 super_admin

## 7. MVP 實作範圍 vs 延後

✅ **MVP 做**:
- DB schema + migration
- 試用自動開始(agent 建立時)
- subscription_period_end 即時計算狀態
- 6 個 API endpoint
- require_active_subscription dependency
- 後台 banner + 訂閱頁
- 試用結束封鎖
- super_admin 手動 extend
- 試用到期通知(Email)

⏳ **Phase 2 延後**:
- 綠界/Stripe 自動定期定額
- Webhook 自動 extend
- Coupon / 折扣碼
- 多種方案(年付折扣、團隊版)
- LINE 通知
- 自動發票

## 8. 串接「外部訂閱平台」

設計上保持「provider-agnostic」:
- `subscription_payment_ref` 欄位記錄外部系統的 ID
- Webhook endpoint 用 `provider` 路徑參數隔離不同金流
- SubscriptionService 只 expose `extend(payment_ref, months)` 等高階 API

未來真要把訂閱系統獨立成一個 SaaS module 服務多個產品時:
- 把 `app/services/subscription_service.py` + `app/routers/billing.py` 抽成獨立 microservice
- 車險平台只要呼叫該 service 的 API 取得 status / extend
- 此 SPEC 已朝這個方向設計

---

實作順序(下面 7 個 commits,逐 commit push 觀察):
1. Schema 欄位 + 加 migration
2. SubscriptionService(計算狀態邏輯 + helpers)
3. 6 個 billing API endpoints
4. agent 建立時自動啟動 trial
5. require_active_subscription gate 套用
6. 後台 banner + 訂閱頁 UI
7. 試用到期通知排程 + 測試
