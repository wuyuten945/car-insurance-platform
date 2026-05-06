"""
管理員 / 業務員專用：客戶 + 車輛 + 保單 統一 CSV 匯出 / 匯入。

格式：one row = (customer × vehicle × policy) — 一個客戶可能對應多列：
- 客戶有 0 車：1 列（vehicle、policy 全空）
- 客戶有 1 車 0 保單：1 列（policy 全空）
- 客戶有 1 車 2 保單：2 列（同 customer + vehicle，policy 不同）

Upsert 鍵：
- customer：by customer_id (UUID) → phone → email → 新建
- vehicle：by vehicle_id → plate_number under that customer → 新建
- policy：by voluntary_policy_number → 新建（只有當至少一個 policy 欄位有值時才建）
"""
from __future__ import annotations

import csv
import io
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.vehicle import UserVehicle
from app.models.policy import Policy, PolicyItem


# 內部 field name ↔ 對外的中文表頭。
# Export 用中文表頭（業務員容易讀寫）；Import 同時接受中文與英文 header（兼容舊檔）
COLUMN_DEF: list[tuple[str, str]] = [
    # 客戶
    ("customer_id",                          "客戶ID"),
    ("customer_name",                        "客戶姓名"),
    ("customer_phone",                       "客戶電話"),
    ("customer_email",                       "客戶Email"),
    ("customer_birth_date",                  "客戶生日"),
    ("customer_address",                     "通訊地址"),
    ("customer_registered_address",          "戶籍地址"),
    ("customer_license_number",              "駕照號碼"),
    ("customer_license_expiry",              "駕照到期日"),
    ("customer_emergency_contact_name",      "緊急聯絡人姓名"),
    ("customer_emergency_contact_phone",     "緊急聯絡人電話"),
    ("customer_emergency_contact_relation",  "緊急聯絡人關係"),
    # 車輛
    ("vehicle_id",            "車輛ID"),
    ("plate_number",          "車牌號碼"),
    ("vehicle_type",          "車輛型式"),
    ("brand",                 "廠牌"),
    ("model",                 "車型"),
    ("year",                  "出廠年"),
    ("manufacture_month",     "出廠月"),
    ("color",                 "顏色"),
    ("engine_cc",             "排氣量(cc)"),
    ("vin",                   "車身號碼VIN"),
    ("fuel_type",             "燃料種類"),
    ("registration_date",     "原發照日期"),
    ("reissue_date",          "換補照日期"),
    ("registration_expiry",   "驗車到期日"),
    ("vehicle_data_source",   "車輛資料來源(agent/self)"),
    # 任意險
    ("voluntary_insurer",       "任意險保險公司"),
    ("voluntary_policy_number", "任意險保單號碼"),
    ("voluntary_status",        "任意險狀態(active/expiring/expired/cancelled)"),
    ("voluntary_start",         "任意險起保日"),
    ("voluntary_end",           "任意險到期日"),
    ("voluntary_premium",       "任意險保費"),
    # 強制險
    ("compulsory_insurer",       "強制險保險公司"),
    ("compulsory_policy_number", "強制險保單號碼"),
    ("compulsory_start",         "強制險起保日"),
    ("compulsory_end",           "強制險到期日"),
    ("compulsory_premium",       "強制險保費"),
    # 保障項目 + 其他
    ("coverage_items",     "保障項目(名稱|保額|自付額|保費;名稱2|...)"),
    ("policy_data_source", "保單資料來源(agent/self)"),
    ("notes",              "備註"),
]

# 內部 field name → 對外 header（給 DictWriter 用）
ZH_HEADER_BY_FIELD: dict[str, str] = {f: zh for f, zh in COLUMN_DEF}
# 對外 header → 內部 field name；同時接受中文與英文（兼容）
FIELD_BY_HEADER: dict[str, str] = {}
for f, zh in COLUMN_DEF:
    FIELD_BY_HEADER[zh] = f
    FIELD_BY_HEADER[f] = f
# Excel 有時欄位前後會被加引號或空白，讀取時正規化
def _normalize_header(h: str) -> str:
    if h is None:
        return ""
    return h.strip().lstrip("﻿")

def _resolve_field(header: str) -> str | None:
    h = _normalize_header(header)
    return FIELD_BY_HEADER.get(h)

# 給其他地方查詢「內部欄位順序」用（保留 list 形式 — 外部仍叫 COLUMNS 兼容舊 import 路徑）
COLUMNS: list[str] = [f for f, _ in COLUMN_DEF]
ZH_HEADERS: list[str] = [zh for _, zh in COLUMN_DEF]


def _str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (date, datetime)):
        return v.isoformat()[:10]
    if isinstance(v, time):
        return v.strftime("%H:%M")
    if isinstance(v, Decimal):
        return f"{v}"
    return str(v)


def _serialize_items(items: list[PolicyItem]) -> str:
    parts: list[str] = []
    for it in items or []:
        name = (it.item_name or "").replace(";", "；").replace("|", "／")
        cov = _str(it.coverage_limit)
        ded = _str(it.deductible)
        prem = _str(it.premium)
        parts.append(f"{name}|{cov}|{ded}|{prem}")
    return ";".join(parts)


def _row_for(customer: User, vehicle: UserVehicle | None, policy: Policy | None) -> dict[str, str]:
    row = {c: "" for c in COLUMNS}
    row["customer_id"] = customer.id
    row["customer_name"] = _str(customer.name)
    row["customer_phone"] = _str(customer.phone)
    row["customer_email"] = _str(customer.email)
    row["customer_birth_date"] = _str(customer.birth_date)
    row["customer_address"] = _str(customer.address)
    row["customer_registered_address"] = _str(customer.registered_address)
    row["customer_license_number"] = _str(customer.license_number)
    row["customer_license_expiry"] = _str(customer.license_expiry)
    row["customer_emergency_contact_name"] = _str(customer.emergency_contact_name)
    row["customer_emergency_contact_phone"] = _str(customer.emergency_contact_phone)
    row["customer_emergency_contact_relation"] = _str(customer.emergency_contact_relation)

    if vehicle is not None:
        row["vehicle_id"] = vehicle.id
        row["plate_number"] = _str(vehicle.plate_number)
        row["vehicle_type"] = _str(vehicle.vehicle_type)
        row["brand"] = _str(vehicle.brand)
        row["model"] = _str(vehicle.model)
        row["year"] = _str(vehicle.year)
        row["manufacture_month"] = _str(vehicle.manufacture_month)
        row["color"] = _str(vehicle.color)
        row["engine_cc"] = _str(vehicle.engine_cc)
        row["vin"] = _str(vehicle.vin)
        row["fuel_type"] = _str(vehicle.fuel_type)
        row["registration_date"] = _str(vehicle.registration_date)
        row["reissue_date"] = _str(vehicle.reissue_date)
        row["registration_expiry"] = _str(vehicle.registration_expiry)
        row["vehicle_data_source"] = _str(vehicle.data_source) or "agent"

    if policy is not None:
        row["voluntary_insurer"] = _str(policy.insurer_name)
        row["voluntary_policy_number"] = _str(policy.policy_number)
        row["voluntary_status"] = _str(policy.status)
        row["voluntary_start"] = _str(policy.start_date)
        row["voluntary_end"] = _str(policy.end_date)
        row["voluntary_premium"] = _str(policy.total_premium)
        row["compulsory_insurer"] = _str(policy.compulsory_insurer_name)
        row["compulsory_policy_number"] = _str(policy.compulsory_policy_number)
        row["compulsory_start"] = _str(policy.compulsory_start_date)
        row["compulsory_end"] = _str(policy.compulsory_end_date)
        row["compulsory_premium"] = _str(policy.compulsory_premium)
        row["coverage_items"] = _serialize_items(policy.items)
        row["policy_data_source"] = _str(policy.data_source) or "agent"

    return row


async def export_csv_for_customers(db: AsyncSession, customer_ids: list[str] | None) -> str:
    """
    匯出 CSV（utf-8-sig 加 BOM 給 Excel 認）。
    customer_ids = None → 全部；list → 限定這些 ID（給 agent 看自己負責的客戶）
    """
    q = (
        select(User)
        .options(
            selectinload(User.vehicles),
            selectinload(User.policies).selectinload(Policy.items),
        )
    )
    if customer_ids is not None:
        if not customer_ids:
            customers: list[User] = []
        else:
            q = q.where(User.id.in_(customer_ids))
            r = await db.execute(q)
            customers = list(r.scalars().unique().all())
    else:
        r = await db.execute(q)
        customers = list(r.scalars().unique().all())

    buf = io.StringIO()
    buf.write("﻿")  # BOM 給 Excel
    # 用中文表頭輸出，業務員直接看得懂
    w = csv.DictWriter(buf, fieldnames=ZH_HEADERS, extrasaction="ignore")
    w.writeheader()

    def _to_zh_row(en_row: dict[str, str]) -> dict[str, str]:
        return {ZH_HEADER_BY_FIELD[f]: v for f, v in en_row.items() if f in ZH_HEADER_BY_FIELD}

    for cust in customers:
        veh_list = list(cust.vehicles or [])
        # 把每張保單對應的車輛找出來；policies 沒車也要留
        policies = list(cust.policies or [])

        # 已經 emit 過的 (vehicle_id, policy_id) 跟「孤立車輛」追蹤
        emitted_pol_ids: set[str] = set()
        emitted_veh_ids: set[str] = set()

        if not veh_list and not policies:
            # 純客戶（沒車沒保單）→ 還是輸出一列，方便客戶資料異動
            w.writerow(_to_zh_row(_row_for(cust, None, None)))
            continue

        # 先依 vehicle_id 分組保單
        for veh in veh_list:
            veh_policies = [p for p in policies if p.vehicle_id == veh.id]
            if veh_policies:
                for p in veh_policies:
                    w.writerow(_to_zh_row(_row_for(cust, veh, p)))
                    emitted_pol_ids.add(p.id)
                    emitted_veh_ids.add(veh.id)
            else:
                # 此車沒保單 → 輸出 vehicle 那列（policy 空）
                w.writerow(_to_zh_row(_row_for(cust, veh, None)))
                emitted_veh_ids.add(veh.id)

        # 沒被 emit 的保單（vehicle_id 為 NULL，或對應車輛已不存在）
        for p in policies:
            if p.id in emitted_pol_ids:
                continue
            w.writerow(_to_zh_row(_row_for(cust, None, p)))

    return buf.getvalue()


# ───────────────── Import ─────────────────


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    s = s.strip().replace("/", "-")
    try:
        return date.fromisoformat(s[:10])
    except Exception:
        return None


def _parse_decimal(s: str | None) -> Decimal | None:
    if not s:
        return None
    raw = str(s).replace(",", "").strip()
    if not raw:
        return None
    try:
        return Decimal(raw)
    except Exception:
        return None


def _parse_int(s: str | None) -> int | None:
    if s is None or s == "":
        return None
    try:
        return int(str(s).replace(",", "").strip())
    except Exception:
        return None


def _parse_items(s: str | None) -> list[dict]:
    if not s:
        return []
    out: list[dict] = []
    for chunk in s.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split("|")
        if not parts or not parts[0].strip():
            continue
        item = {"item_name": parts[0].strip()}
        if len(parts) >= 2:
            v = _parse_decimal(parts[1])
            if v is not None:
                item["coverage_limit"] = v
        if len(parts) >= 3:
            v = _parse_decimal(parts[2])
            if v is not None:
                item["deductible"] = v
        if len(parts) >= 4:
            v = _parse_decimal(parts[3])
            if v is not None:
                item["premium"] = v
        out.append(item)
    return out


async def import_csv(
    db: AsyncSession,
    csv_text: str,
    *,
    dry_run: bool,
    accessible_customer_ids: list[str] | None,
) -> dict:
    """
    讀 CSV → upsert customer / vehicle / policy。
    回傳：summary dict 含成功 / 失敗筆數 + 失敗原因列表。
    accessible_customer_ids = None → 不限（super_admin）；list → 只允許這些客戶
    """
    # 去 BOM
    if csv_text and csv_text[0] == "﻿":
        csv_text = csv_text[1:]
    reader = csv.DictReader(io.StringIO(csv_text))

    summary = {
        "rows_total": 0,
        "customers_created": 0,
        "customers_updated": 0,
        "vehicles_created": 0,
        "vehicles_updated": 0,
        "policies_created": 0,
        "policies_updated": 0,
        "errors": [],  # [{"row": int, "msg": str}]
    }

    # 為了避免跨 row 重複 query 同個客戶，做小快取
    cust_by_id: dict[str, User] = {}
    cust_by_phone: dict[str, User] = {}
    cust_by_email: dict[str, User] = {}

    for idx, raw in enumerate(reader, start=2):  # start=2 因為第 1 列是 header
        summary["rows_total"] += 1
        # header 可能是中文也可能是英文 — 一律先翻成內部 field name
        row: dict[str, str] = {}
        for k, v in raw.items():
            if not k:
                continue
            field = _resolve_field(k)
            if not field:
                continue
            row[field] = (v.strip() if isinstance(v, str) else v)

        try:
            # ── 1. 解析 / upsert 客戶 ──
            cust: User | None = None
            cid = row.get("customer_id") or ""
            if cid and cid in cust_by_id:
                cust = cust_by_id[cid]
            elif cid:
                r = await db.execute(select(User).where(User.id == cid))
                cust = r.scalar_one_or_none()
                if cust:
                    cust_by_id[cid] = cust

            if not cust:
                phone = row.get("customer_phone") or ""
                email = row.get("customer_email") or ""
                if phone and phone in cust_by_phone:
                    cust = cust_by_phone[phone]
                elif phone:
                    r = await db.execute(select(User).where(User.phone == phone))
                    cust = r.scalar_one_or_none()
                if not cust and email and email in cust_by_email:
                    cust = cust_by_email[email]
                elif not cust and email:
                    r = await db.execute(select(User).where(User.email == email))
                    cust = r.scalar_one_or_none()

            if cust:
                # 權限檢查：accessible_customer_ids 限定
                if accessible_customer_ids is not None and cust.id not in accessible_customer_ids:
                    raise ValueError("無權限存取此客戶")
                # 更新可選欄位（空值不覆蓋）
                changed = False
                for col, attr in [
                    ("customer_name", "name"), ("customer_phone", "phone"), ("customer_email", "email"),
                    ("customer_address", "address"), ("customer_registered_address", "registered_address"),
                    ("customer_license_number", "license_number"),
                    ("customer_emergency_contact_name", "emergency_contact_name"),
                    ("customer_emergency_contact_phone", "emergency_contact_phone"),
                    ("customer_emergency_contact_relation", "emergency_contact_relation"),
                ]:
                    val = row.get(col) or ""
                    if val and getattr(cust, attr, None) != val:
                        setattr(cust, attr, val)
                        changed = True
                bd = _parse_date(row.get("customer_birth_date"))
                if bd:
                    if cust.birth_date is None or (hasattr(cust.birth_date, "date") and cust.birth_date.date() != bd):
                        cust.birth_date = datetime.combine(bd, time(0, 0))
                        changed = True
                ld = _parse_date(row.get("customer_license_expiry"))
                if ld:
                    cust.license_expiry = datetime.combine(ld, time(0, 0))
                    changed = True
                if changed:
                    summary["customers_updated"] += 1
            else:
                # 新建客戶 — 至少要有姓名
                name = row.get("customer_name") or ""
                if not name:
                    raise ValueError("找不到客戶且 customer_name 為空，無法建立")
                cust = User(
                    name=name,
                    phone=(row.get("customer_phone") or None),
                    email=(row.get("customer_email") or None),
                    address=(row.get("customer_address") or None),
                    registered_address=(row.get("customer_registered_address") or None),
                    license_number=(row.get("customer_license_number") or None),
                    emergency_contact_name=(row.get("customer_emergency_contact_name") or None),
                    emergency_contact_phone=(row.get("customer_emergency_contact_phone") or None),
                    emergency_contact_relation=(row.get("customer_emergency_contact_relation") or None),
                )
                bd = _parse_date(row.get("customer_birth_date"))
                if bd:
                    cust.birth_date = datetime.combine(bd, time(0, 0))
                ld = _parse_date(row.get("customer_license_expiry"))
                if ld:
                    cust.license_expiry = datetime.combine(ld, time(0, 0))
                db.add(cust)
                await db.flush()
                summary["customers_created"] += 1
            cust_by_id[cust.id] = cust
            if cust.phone:
                cust_by_phone[cust.phone] = cust
            if cust.email:
                cust_by_email[cust.email] = cust

            # ── 2. 車輛 ──
            veh: UserVehicle | None = None
            plate = row.get("plate_number") or ""
            vid = row.get("vehicle_id") or ""
            if vid:
                r = await db.execute(select(UserVehicle).where(UserVehicle.id == vid))
                veh = r.scalar_one_or_none()
            if not veh and plate:
                r = await db.execute(select(UserVehicle).where(
                    UserVehicle.plate_number == plate, UserVehicle.user_id == cust.id
                ))
                veh = r.scalar_one_or_none()

            if plate or veh:
                if veh:
                    changed = False
                    for col, attr in [
                        ("plate_number", "plate_number"), ("vehicle_type", "vehicle_type"),
                        ("brand", "brand"), ("model", "model"), ("color", "color"),
                        ("vin", "vin"), ("fuel_type", "fuel_type"),
                    ]:
                        val = row.get(col) or ""
                        if val and getattr(veh, attr) != val:
                            setattr(veh, attr, val)
                            changed = True
                    yr = _parse_int(row.get("year"))
                    if yr is not None:
                        veh.year = yr
                        changed = True
                    mm = _parse_int(row.get("manufacture_month"))
                    if mm is not None:
                        veh.manufacture_month = mm
                        changed = True
                    cc = _parse_int(row.get("engine_cc"))
                    if cc is not None:
                        veh.engine_cc = cc
                        changed = True
                    rd = _parse_date(row.get("registration_date"))
                    if rd:
                        veh.registration_date = rd; changed = True
                    rid = _parse_date(row.get("reissue_date"))
                    if rid:
                        veh.reissue_date = rid; changed = True
                    re_ = _parse_date(row.get("registration_expiry"))
                    if re_:
                        veh.registration_expiry = re_; changed = True
                    if changed:
                        summary["vehicles_updated"] += 1
                else:
                    # 新建車輛
                    if not plate:
                        raise ValueError("有車輛欄位但缺 plate_number")
                    veh = UserVehicle(
                        user_id=cust.id,
                        plate_number=plate,
                        vehicle_type=(row.get("vehicle_type") or None),
                        brand=(row.get("brand") or None),
                        model=(row.get("model") or None),
                        year=_parse_int(row.get("year")),
                        manufacture_month=_parse_int(row.get("manufacture_month")),
                        color=(row.get("color") or None),
                        engine_cc=_parse_int(row.get("engine_cc")),
                        vin=(row.get("vin") or None),
                        fuel_type=(row.get("fuel_type") or None),
                        registration_date=_parse_date(row.get("registration_date")),
                        reissue_date=_parse_date(row.get("reissue_date")),
                        registration_expiry=_parse_date(row.get("registration_expiry")),
                        data_source=(row.get("vehicle_data_source") or "agent"),
                    )
                    db.add(veh)
                    await db.flush()
                    summary["vehicles_created"] += 1

            # ── 3. 保單（任意險） ──
            v_insurer = row.get("voluntary_insurer") or ""
            v_polno = row.get("voluntary_policy_number") or ""
            has_policy_data = bool(v_insurer or v_polno or row.get("compulsory_insurer") or row.get("compulsory_policy_number"))
            if has_policy_data:
                if not v_insurer or not v_polno:
                    raise ValueError("有保單資料但 voluntary_insurer / voluntary_policy_number 必須都填")
                v_start = _parse_date(row.get("voluntary_start"))
                v_end = _parse_date(row.get("voluntary_end"))
                if not v_start or not v_end:
                    raise ValueError("voluntary_start 與 voluntary_end 都必須填")

                r = await db.execute(select(Policy).where(Policy.policy_number == v_polno))
                pol = r.scalar_one_or_none()
                items_payload = _parse_items(row.get("coverage_items") or "")

                if pol:
                    if pol.user_id != cust.id:
                        raise ValueError(f"保單號 {v_polno} 已存在於另一位客戶")
                    pol.insurer_name = v_insurer
                    pol.start_date = v_start
                    pol.end_date = v_end
                    pol.status = (row.get("voluntary_status") or pol.status or "active")
                    prem = _parse_decimal(row.get("voluntary_premium"))
                    if prem is not None:
                        pol.total_premium = prem
                    pol.vehicle_id = veh.id if veh else pol.vehicle_id
                    pol.compulsory_insurer_name = (row.get("compulsory_insurer") or None)
                    pol.compulsory_policy_number = (row.get("compulsory_policy_number") or None)
                    pol.compulsory_start_date = _parse_date(row.get("compulsory_start"))
                    pol.compulsory_end_date = _parse_date(row.get("compulsory_end"))
                    cprem = _parse_decimal(row.get("compulsory_premium"))
                    if cprem is not None:
                        pol.compulsory_premium = cprem
                    # items：若有提供就整批 replace
                    if items_payload:
                        for it in list(pol.items):
                            await db.delete(it)
                        await db.flush()
                        for ip in items_payload:
                            db.add(PolicyItem(policy_id=pol.id, **ip))
                    summary["policies_updated"] += 1
                else:
                    pol = Policy(
                        user_id=cust.id,
                        vehicle_id=veh.id if veh else None,
                        insurer_name=v_insurer,
                        policy_number=v_polno,
                        status=(row.get("voluntary_status") or "active"),
                        start_date=v_start,
                        end_date=v_end,
                        total_premium=_parse_decimal(row.get("voluntary_premium")),
                        compulsory_insurer_name=(row.get("compulsory_insurer") or None),
                        compulsory_policy_number=(row.get("compulsory_policy_number") or None),
                        compulsory_start_date=_parse_date(row.get("compulsory_start")),
                        compulsory_end_date=_parse_date(row.get("compulsory_end")),
                        compulsory_premium=_parse_decimal(row.get("compulsory_premium")),
                        data_source=(row.get("policy_data_source") or "agent"),
                    )
                    db.add(pol)
                    await db.flush()
                    for ip in items_payload:
                        db.add(PolicyItem(policy_id=pol.id, **ip))
                    summary["policies_created"] += 1
        except Exception as e:
            summary["errors"].append({"row": idx, "msg": str(e)})

    if dry_run:
        await db.rollback()
    else:
        if summary["errors"]:
            await db.rollback()
            summary["committed"] = False
            return summary
        await db.commit()

    summary["committed"] = (not dry_run) and not summary["errors"]
    return summary
