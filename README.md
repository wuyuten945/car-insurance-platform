# BOPINAN — 車險智能服務平台

[![CI](https://github.com/wuyuten945/car-insurance-platform/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/wuyuten945/car-insurance-platform/actions/workflows/ci.yml)

業務員 + 客戶端的車險 SaaS。前台給客戶管理保單、查驗車、發詢價工單、SOS 救援；後台給業務員 / 管理員查看與處理客戶資料。

---

## 技術堆疊

| 層 | 用什麼 |
|---|---|
| Backend | FastAPI + SQLAlchemy async + PostgreSQL (Render PG) |
| Frontend | Next.js 16.2 + React 19.2 + Tailwind 4 + TanStack Query + Zustand |
| 認證 | JWT(雙系統:客戶 type=access + 業務員 type=admin),OTP + Email |
| 部署 | Render(雙 service:frontend + backend),Persistent Disk 存上傳檔 |
| 通訊 | LINE Messaging API(push)+ Resend(email) |
| 安全 | bcrypt + token rotation + slowapi rate limit + gitleaks scan |

---

## 主要功能

- **客戶端**:保單管理、車輛/行照、駕照、理賠申請、SOS 緊急救援、續保比價、詢價工單、保費試算、數字易經、通知偏好
- **業務員端**:客戶 CRUD、車輛/保單管理、CSV 大量匯入、稽核日誌、詢價工單派發、數字易經(代客分析)
- **共通**:OTP 雙因子、進階保護密碼、LINE OAuth + 推播、多語(zh/en)、Idle 自動登出

---

## 本機開發

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env                              # 填入 JWT_SECRET_KEY 等
python -m uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm ci
npm run dev                                          # http://localhost:3000
```

**JWT_SECRET_KEY 必填**(production 啟動會 raise);dev 環境留空會自動生隨機值並警告。

---

## 測試

```bash
cd backend && python -m pytest -v
```

涵蓋:密碼雜湊(bcrypt + 舊 SHA-256 dual mode)、上傳驗證(size/type/magic/filename)、token rotation、rate-limit log。

---

## CI / CD

每次 push 到 `main` 或開 PR 會跑三個並行 job:

- **Backend pytest**(Python 3.13,~30s)
- **Frontend build**(Node 20,Next.js build 含 TS type-check)
- **Secret leak scan**(gitleaks 掃 git history)

設定見 `.github/workflows/ci.yml`。Render 在 push 後自動 redeploy 兩個 service。

---

## 安全層

| 攻擊向量 | 防護 |
|---|---|
| Brute-force 登入 | 帳號 5/10 次階段鎖定 + 同 IP 20 次/hour 鎖 + slowapi 全域 |
| Token 外洩 | 1 小時 expiry + token_version (改密碼立即撤銷所有舊 token) |
| Rate limit / DDoS | slowapi:120/min + 2000/hour + 上傳 endpoint 加嚴 |
| 上傳濫用 | size + Content-Type + magic bytes + 像素 + 每用戶 hourly quota |
| Stored XSS | admin innerHTML 全過 esc(),StaticFiles 加 nosniff |
| Path traversal | filename regex + resolve() 比對 UPLOAD_DIR |
| OOM(PDF/PNG bomb) | PDF ≤ 20 頁 + 60MP / 圖片 ≤ 100MP |
| Race condition | DB unique constraint + IntegrityError catch |
| Secret leak | gitleaks scan 在 CI 擋誤 commit |

詳見 `feedback_security_audit.md`(memory)。

---

## 專案結構(精簡版)

```
backend/
├── app/
│   ├── main.py              # FastAPI app + middleware + scheduler
│   ├── config.py            # Settings + JWT secret guard
│   ├── database.py          # Async engine + pool config
│   ├── core/                # 跨模組共用(security, cache, line, upload validation, ...)
│   ├── models/              # SQLAlchemy ORM
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # 業務邏輯
│   └── routers/             # FastAPI endpoints
├── tests/                   # pytest
└── requirements.txt

frontend/
├── src/
│   ├── app/                 # Next 16 App Router(login, profile, policies, ...)
│   ├── components/          # 共用 UI
│   ├── lib/                 # api-client, i18n, hooks
│   └── stores/              # zustand
└── package.json

.github/workflows/ci.yml     # CI:pytest + build + gitleaks
.gitleaks.toml               # gitleaks allowlist
.env.example                 # env 範本(實際 .env 不入 git)
```

---

## 授權

私有專案,版權 © 2026 BOPINAN
