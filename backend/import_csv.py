"""
從 桌面/車險記錄表.csv import 至車險智能平台 DB

執行：
  cd C:\\Users\\User\\car-insurance-platform\\backend
  python import_csv.py

特性：
- 以 phone 為 unique key 查找 User，已存在則沿用
- 以 (user_id, plate_number) 查找 UserVehicle，已存在則沿用
- policy_number 自動產生：IMPORT-{plate}-{end_yyyymmdd}，已存在則跳過（idempotent）
- 民國年到期日自動轉西元、推算 start_date = end_date - 1 年
- 被保險人 ≠ 要保人時，差異記在第一筆 PolicyItem.description
"""
import asyncio
import csv
import hashlib
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.database import AsyncSessionLocal, create_tables
from app.models.user import User, UserConsent
from app.models.vehicle import UserVehicle
from app.models.policy import Policy, PolicyItem


CSV_PATH = Path(r"C:\Users\User\Desktop\車險記錄表.csv")


def normalize_phone(s: str) -> str:
    """'0952-156100' → '0952156100'"""
    return re.sub(r"\D", "", s or "")


def hash_id_number(idn: str) -> str:
    if not idn:
        return ""
    return hashlib.sha256(idn.strip().encode()).hexdigest()


def parse_roc_date(s: str):
    """民國 '115 /08/21' → date(2026, 8, 21)"""
    s = (s or "").strip().replace(" ", "")
    m = re.match(r"^(\d+)/(\d+)/(\d+)$", s)
    if not m:
        return None
    roc_y = int(m.group(1))
    try:
        return date(roc_y + 1911, int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def parse_birth(s: str):
    s = (s or "").strip()
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return None


def parse_int(s: str):
    m = re.search(r"\d+", s or "")
    return int(m.group()) if m else None


def parse_engine_cc(s: str):
    """C.C.數欄位：'1998' → 1998；'255馬力' → None（電車沒 cc 概念）"""
    s = (s or "").strip()
    if "馬力" in s or not s:
        return None
    return parse_int(s)


def parse_decimal(s: str):
    s = (s or "").strip().replace(",", "")
    if not s:
        return None
    try:
        return Decimal(s)
    except Exception:
        return None


def detect_fuel_type(brand_model: str, note: str) -> str:
    blob = f"{brand_model} {note}".lower()
    if "tesla" in blob or "電車" in blob or "電動" in blob:
        return "電動"
    return "汽油"


async def import_row(db, row):
    name_holder = (row.get("要保人") or "").strip()
    name_insured = (row.get("被保險人") or "").strip()
    phone = normalize_phone(row.get("聯絡電話") or "")
    plate = (row.get("車號") or "").strip()
    end_date = parse_roc_date(row.get("到期日") or "")

    if not (name_holder and phone and plate and end_date):
        print(f"  跳過：必要欄位不完整 (要保人={name_holder!r} 電話={phone!r} 車牌={plate!r} 到期={end_date})")
        return False

    # ── User：以 phone 為 unique key ──
    res = await db.execute(select(User).where(User.phone == phone))
    user = res.scalar_one_or_none()
    if user:
        print(f"  ✓ User 已存在，沿用：{user.name} ({phone})")
    else:
        user = User(
            phone=phone,
            name=name_holder,
            id_number_hash=hash_id_number(row.get("身份證字號") or ""),
            birth_date=parse_birth(row.get("出生年月日") or ""),
            address=(row.get("聯絡地址") or "").strip() or None,
            registered_address=(row.get("聯絡地址") or "").strip() or None,
        )
        db.add(user)
        await db.flush()
        db.add(UserConsent(
            user_id=user.id,
            consent_type="privacy_policy",
            is_granted=True,
            granted_at=datetime.now(timezone.utc),
        ))
        print(f"  + 建立 User：{name_holder} ({phone})")

    # ── UserVehicle：以 (user_id, plate_number) 查重 ──
    res = await db.execute(
        select(UserVehicle).where(
            UserVehicle.user_id == user.id,
            UserVehicle.plate_number == plate,
        )
    )
    vehicle = res.scalar_one_or_none()

    brand_model = (row.get("廠牌型式及代號") or "").strip()
    if "/" in brand_model:
        brand_part, model_part = brand_model.split("/", 1)
    else:
        brand_part, model_part = brand_model, ""

    note = (row.get("備註") or "").strip()

    if not vehicle:
        vehicle = UserVehicle(
            user_id=user.id,
            plate_number=plate,
            brand=brand_part.strip() or None,
            model=model_part.strip() or None,
            year=parse_int(row.get("製造年份") or ""),
            vin=(row.get("引擎/車身號碼") or "").strip() or None,
            engine_cc=parse_engine_cc(row.get("C.C.數") or ""),
            fuel_type=detect_fuel_type(brand_model, note),
            is_primary=True,
        )
        db.add(vehicle)
        await db.flush()
        print(f"  + 建立 Vehicle：{plate} {brand_model}")
    else:
        print(f"  ✓ Vehicle 已存在，沿用：{plate}")

    # ── Policy：policy_number 用 plate + end_date 確保 unique 與 idempotent ──
    plate_clean = re.sub(r"[^A-Z0-9]", "", plate.upper())
    policy_number = f"IMPORT-{plate_clean}-{end_date.strftime('%Y%m%d')}"

    res = await db.execute(select(Policy).where(Policy.policy_number == policy_number))
    if res.scalar_one_or_none():
        print(f"  = Policy 已存在，跳過：{policy_number}")
        return False

    # 推算 start_date：end_date - 1 年
    try:
        start_date = end_date.replace(year=end_date.year - 1)
    except ValueError:
        start_date = end_date.replace(year=end_date.year - 1, day=28)

    today = date.today()
    if end_date < today:
        status = "expired"
    elif (end_date - today).days <= 30:
        status = "expiring"
    else:
        status = "active"

    total_premium = parse_decimal(row.get("總保費") or "")

    policy = Policy(
        user_id=user.id,
        vehicle_id=vehicle.id,
        insurer_name=(row.get("投保公司") or "").strip() or "未指定",
        policy_number=policy_number,
        status=status,
        start_date=start_date,
        end_date=end_date,
        total_premium=total_premium,
    )
    db.add(policy)
    await db.flush()

    # ── PolicyItems ──
    notes_extra = []
    if name_insured and name_insured != name_holder:
        notes_extra.append(f"被保險人: {name_insured}（與要保人不同）")
    notes_extra.append(f"要保人: {name_holder}")
    coverage_factor = (row.get("車體險係數") or "").strip()
    if coverage_factor:
        notes_extra.append(f"車體險係數: {coverage_factor}")
    if note:
        notes_extra.append(f"備註: {note}")

    items = []
    forced_premium = parse_decimal(row.get("強制險保費") or "")
    if forced_premium and forced_premium > 0:
        items.append(("強制汽車責任保險", forced_premium, "; ".join(notes_extra)))
        notes_extra = []

    yi = parse_decimal(row.get("乙式保費") or "")
    bing = parse_decimal(row.get("丙式保費") or "")
    if yi and yi > 0:
        items.append(("車體損失險（乙式）", yi, "; ".join(notes_extra) or None))
    elif bing and bing > 0:
        items.append(("車體損失險（丙式）", bing, "; ".join(notes_extra) or None))

    for item_name, premium, description in items:
        db.add(PolicyItem(
            policy_id=policy.id,
            item_name=item_name,
            premium=premium,
            is_active=True,
            description=description,
        ))

    print(f"  + 建立 Policy：{policy_number} | {policy.insurer_name} | 總保費 ${total_premium} | 狀態 {status} | 險種 {len(items)} 項")
    return True


async def main():
    await create_tables()

    if not CSV_PATH.exists():
        print(f"[ERR] 找不到 CSV：{CSV_PATH}")
        return

    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not (row.get("要保人") or "").strip():
                continue
            rows.append(row)

    print(f"[INFO] 讀入 {len(rows)} 筆有效資料\n")

    async with AsyncSessionLocal() as db:
        success = 0
        skipped = 0
        for i, row in enumerate(rows, 1):
            print(f"[{i}/{len(rows)}] 要保人={row.get('要保人')} 車牌={row.get('車號')}")
            try:
                if await import_row(db, row):
                    success += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"  [FAIL] {type(e).__name__}: {e}")
                await db.rollback()
                continue
        await db.commit()
        print(f"\n[DONE] 建立 {success} 筆 / 跳過 {skipped} 筆 / 共 {len(rows)} 筆")


if __name__ == "__main__":
    asyncio.run(main())
