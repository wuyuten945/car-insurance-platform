"""
批次匯入 桌面/車險記錄表{1..12}月.csv 至車險智能平台 DB

執行：
  cd C:\\Users\\User\\car-insurance-platform\\backend
  python import_csv_monthly.py

特性：
- 自動處理 12 個月份檔案
- 個人車險 → User + Vehicle + Policy + PolicyItems
- 機構商業險（如公共意外責任險、產品責任險）→ User(機構)+Policy（無 Vehicle）
- 支援「車種」欄位（3 月起的新格式）
- idempotent：重跑不會重複建檔
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


DESKTOP = Path(r"C:\Users\User\Desktop")
MONTHS = list(range(1, 13))
# CSV 月份代表的西元年（1 月車險到期日 116/xx 對應 2027，→ 投保是 2026）
IMPORT_YEAR = 2026


def normalize_phone(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def hash_id(idn: str) -> str:
    if not idn:
        return ""
    return hashlib.sha256(idn.strip().encode()).hexdigest()


def parse_roc_date(s: str):
    s = (s or "").strip().replace(" ", "")
    m = re.match(r"^(\d+)/(\d+)/(\d+)$", s)
    if not m:
        return None
    try:
        return date(int(m.group(1)) + 1911, int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def parse_birth(s: str):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def parse_int(s: str):
    m = re.search(r"\d+", s or "")
    return int(m.group()) if m else None


def parse_engine_cc(s: str):
    """C.C.數：'1798 cc' → 1798；'255馬力' → None；'8.0HP' → None"""
    s = (s or "").strip()
    if "馬力" in s or "hp" in s.lower():
        return None
    return parse_int(s)


def parse_year(s: str):
    """製造年份：'2019年01月' → 2019；'114 年06月' → 2025（民國轉西元）"""
    s = (s or "").strip()
    if not s:
        return None
    m = re.match(r"^(\d+)", s)
    if not m:
        return None
    n = int(m.group(1))
    # 民國年（< 200）→ 西元
    if n < 200:
        n += 1911
    return n


def parse_decimal(s: str):
    s = (s or "").strip().replace(",", "")
    if not s:
        return None
    try:
        return Decimal(s)
    except Exception:
        return None


def detect_fuel_type(brand_model: str, vehicle_type: str, note: str) -> str:
    blob = f"{brand_model} {vehicle_type} {note}".lower()
    if "tesla" in blob or "電車" in blob or "電動" in blob:
        return "電動"
    return "汽油"


def is_business_record(row: dict) -> bool:
    """機構商業險：要保人有但車牌空"""
    holder = (row.get("要保人") or "").strip()
    plate = (row.get("車號") or "").strip()
    return bool(holder) and not plate


def is_personal_record(row: dict) -> bool:
    holder = (row.get("要保人") or "").strip()
    plate = (row.get("車號") or "").strip()
    return bool(holder) and bool(plate)


# ── 建檔工具 ─────────────────────────────────────────────────

async def get_or_create_user_by_phone(db, phone: str, name: str, row: dict) -> User:
    res = await db.execute(select(User).where(User.phone == phone))
    user = res.scalar_one_or_none()
    if user:
        return user
    user = User(
        phone=phone,
        name=name,
        id_number_hash=hash_id(row.get("身份證字號") or ""),
        birth_date=parse_birth(row.get("出生年月日") or ""),
        address=(row.get("聯絡地址") or "").strip() or None,
        registered_address=(row.get("聯絡地址") or "").strip() or None,
    )
    db.add(user)
    await db.flush()
    db.add(UserConsent(
        user_id=user.id, consent_type="privacy_policy",
        is_granted=True, granted_at=datetime.now(timezone.utc),
    ))
    return user


async def get_or_create_business_user(db, name: str, address: str) -> User:
    """機構：用 name 當搜尋鍵（同名視為同機構）。phone/email 留 None。"""
    res = await db.execute(select(User).where(User.name == name, User.phone.is_(None)))
    user = res.scalar_one_or_none()
    if user:
        return user
    user = User(
        phone=None,
        name=name,
        address=address or None,
        registered_address=address or None,
    )
    db.add(user)
    await db.flush()
    return user


async def get_or_create_vehicle(db, user_id: str, row: dict) -> UserVehicle:
    plate = (row.get("車號") or "").strip()
    res = await db.execute(
        select(UserVehicle).where(
            UserVehicle.user_id == user_id,
            UserVehicle.plate_number == plate,
        )
    )
    veh = res.scalar_one_or_none()
    if veh:
        return veh

    brand_model = (row.get("廠牌型式及代號") or "").strip()
    if "/" in brand_model:
        brand_part, model_part = brand_model.split("/", 1)
    else:
        brand_part, model_part = brand_model, ""

    vehicle_type = (row.get("車種") or "").strip() or None
    note = (row.get("備註") or "").strip()

    veh = UserVehicle(
        user_id=user_id,
        plate_number=plate,
        brand=brand_part.strip() or None,
        model=model_part.strip() or None,
        year=parse_year(row.get("製造年份") or ""),
        vin=(row.get("引擎/車身號碼") or "").strip() or None,
        engine_cc=parse_engine_cc(row.get("C.C.數") or ""),
        fuel_type=detect_fuel_type(brand_model, vehicle_type or "", note),
        vehicle_type=vehicle_type,
        is_primary=True,
    )
    db.add(veh)
    await db.flush()
    return veh


async def import_personal(db, row: dict, month: int) -> str:
    """個人車險：建/沿用 user/vehicle/policy"""
    name_holder = (row.get("要保人") or "").strip()
    name_insured = (row.get("被保險人") or "").strip()
    phone = normalize_phone(row.get("聯絡電話") or "")
    plate = (row.get("車號") or "").strip()
    end_date = parse_roc_date(row.get("到期日") or "")

    # phone 為空仍允許（如 1 月蘇呈那筆，CSV 沒填電話，用車牌+生日當辨識）
    # 但需要至少有一個 unique key — 這裡用「車牌+到期日」確保 policy 不重複
    if not (name_holder and plate and end_date):
        return "skip-incomplete"

    # User：phone 有就用 phone 查重，否則用 name+id_number 組合
    if phone:
        user = await get_or_create_user_by_phone(db, phone, name_holder, row)
    else:
        # 沒電話 → 用 (name, id_number_hash) 查重；沒身份證就用 name
        idh = hash_id(row.get("身份證字號") or "")
        if idh:
            res = await db.execute(
                select(User).where(User.name == name_holder, User.id_number_hash == idh)
            )
        else:
            res = await db.execute(
                select(User).where(User.name == name_holder, User.phone.is_(None))
            )
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                phone=None,
                name=name_holder,
                id_number_hash=idh or None,
                birth_date=parse_birth(row.get("出生年月日") or ""),
                address=(row.get("聯絡地址") or "").strip() or None,
                registered_address=(row.get("聯絡地址") or "").strip() or None,
            )
            db.add(user)
            await db.flush()

    vehicle = await get_or_create_vehicle(db, user.id, row)

    plate_clean = re.sub(r"[^A-Z0-9]", "", plate.upper())
    policy_number = f"IMPORT-{plate_clean}-{end_date.strftime('%Y%m%d')}"
    res = await db.execute(select(Policy).where(Policy.policy_number == policy_number))
    if res.scalar_one_or_none():
        return "skip-exists"

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

    # PolicyItems
    notes_extra = []
    if name_insured and name_insured != name_holder:
        notes_extra.append(f"被保險人: {name_insured}（與要保人不同）")
    notes_extra.append(f"要保人: {name_holder}")
    cf = (row.get("車體險係數") or "").strip()
    if cf:
        notes_extra.append(f"車體險係數: {cf}")
    note = (row.get("備註") or "").strip()
    if note:
        notes_extra.append(f"備註: {note}")
    cv = (row.get("車種") or "").strip()
    if cv:
        notes_extra.append(f"車種: {cv}")

    items = []
    forced = parse_decimal(row.get("強制險保費") or "")
    if forced and forced > 0:
        items.append(("強制汽車責任保險", forced, "; ".join(notes_extra)))
        notes_extra = []

    optional = parse_decimal(row.get("任意險保險") or "")
    if optional and optional > 0:
        items.append(("任意險（綜合）", optional, "; ".join(notes_extra) or None))
        notes_extra = []

    yi = parse_decimal(row.get("乙式保費") or "")
    bing = parse_decimal(row.get("丙式保費") or "")
    if yi and yi > 0:
        items.append(("車體損失險（乙式）", yi, "; ".join(notes_extra) or None))
        notes_extra = []
    elif bing and bing > 0:
        items.append(("車體損失險（丙式）", bing, "; ".join(notes_extra) or None))
        notes_extra = []

    # 若都沒明細，至少建一筆「總保費」item 帶備註
    if not items:
        items.append(("車險（綜合）", total_premium or Decimal(0), "; ".join(notes_extra) or None))

    for item_name, premium, description in items:
        db.add(PolicyItem(
            policy_id=policy.id, item_name=item_name, premium=premium,
            is_active=True, description=description,
        ))

    return f"created (險種 {len(items)} 項)"


async def import_business(db, row: dict, month: int) -> str:
    """機構商業險：無車輛、無個人資料

    險種來源優先順序：備註 → 車種 → fallback「商業綜合保險」
    （因不同月份格式差異：1/9/10 月險種寫在備註欄；4 月寫在車種欄）

    到期日：優先用 CSV「到期日」民國轉西元；無才用「該月 1 號 + 1 年」推算
    """
    name = (row.get("要保人") or "").strip()
    address = (row.get("聯絡地址") or "").strip()
    note = (row.get("備註") or "").strip()
    veh_type = (row.get("車種") or "").strip()
    total_premium = parse_decimal(row.get("總保費") or "")

    if not name:
        return "skip-noname"

    # 險種：備註 > 車種 > fallback
    item_name = note or veh_type or "商業綜合保險"

    user = await get_or_create_business_user(db, name, address)

    # policy_number：name + 險種 + 月份 → 區分同月同機構不同險種
    type_hash = hashlib.sha256(item_name.encode()).hexdigest()[:6]
    name_hash = hashlib.sha256(name.encode()).hexdigest()[:10]
    yyyymm = f"{IMPORT_YEAR}{month:02d}"
    policy_number = f"IMPORT-BIZ-{name_hash}-{type_hash}-{yyyymm}"
    res = await db.execute(select(Policy).where(Policy.policy_number == policy_number))
    if res.scalar_one_or_none():
        return "skip-exists"

    # 到期日：優先 CSV，否則用「該月 1 號 + 1 年」
    csv_end = parse_roc_date(row.get("到期日") or "")
    if csv_end:
        end_date = csv_end
        try:
            start_date = end_date.replace(year=end_date.year - 1)
        except ValueError:
            start_date = end_date.replace(year=end_date.year - 1, day=28)
    else:
        start_date = date(IMPORT_YEAR, month, 1)
        try:
            end_date = start_date.replace(year=start_date.year + 1)
        except ValueError:
            end_date = start_date.replace(year=start_date.year + 1, day=28)

    today = date.today()
    if end_date < today:
        status = "expired"
    elif (end_date - today).days <= 30:
        status = "expiring"
    else:
        status = "active"

    insurer = (row.get("投保公司") or "").strip() or "未指定"
    policy = Policy(
        user_id=user.id,
        vehicle_id=None,
        insurer_name=insurer,
        policy_number=policy_number,
        status=status,
        start_date=start_date,
        end_date=end_date,
        total_premium=total_premium,
    )
    db.add(policy)
    await db.flush()

    desc = f"機構: {name}"
    if csv_end:
        desc += f"; 到期日來源: CSV 民國轉西元"
    else:
        desc += f"; 投保月份: {yyyymm}（推算保單期 1 年）"
    if address:
        desc += f"; 地址: {address}"

    db.add(PolicyItem(
        policy_id=policy.id, item_name=item_name,
        premium=total_premium or Decimal(0),
        is_active=True, description=desc,
    ))

    return f"created (機構險: {item_name})"


async def import_month(db, month: int):
    path = DESKTOP / f"車險記錄表{month}月.csv"
    if not path.exists():
        print(f"[{month:>2}月] 檔案不存在")
        return {"month": month, "missing": True}

    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            holder = (row.get("要保人") or "").strip()
            if not holder:
                continue
            rows.append(row)

    print(f"\n=== {month:>2}月：{len(rows)} 筆有效資料 ===")
    counts = {"personal": 0, "business": 0, "skip": 0, "fail": 0}

    for i, row in enumerate(rows, 1):
        try:
            if is_personal_record(row):
                result = await import_personal(db, row, month)
                tag = "個人"
                counts["personal"] += 1 if result.startswith("created") else 0
            elif is_business_record(row):
                result = await import_business(db, row, month)
                tag = "機構"
                counts["business"] += 1 if result.startswith("created") else 0
            else:
                result = "skip-no-classification"
                tag = "?"

            holder = (row.get("要保人") or "")
            plate = (row.get("車號") or "")
            print(f"  [{i:>2}] {tag} {holder} {plate} → {result}")
            if result.startswith("skip"):
                counts["skip"] += 1
        except Exception as e:
            print(f"  [{i:>2}] 失敗: {type(e).__name__}: {e}")
            counts["fail"] += 1
            await db.rollback()
            continue

    return {"month": month, **counts}


async def main():
    await create_tables()
    summary = []
    async with AsyncSessionLocal() as db:
        for m in MONTHS:
            r = await import_month(db, m)
            summary.append(r)
        await db.commit()

    print("\n" + "=" * 50)
    print("=== 全部月份匯入摘要 ===")
    print("=" * 50)
    total_p = total_b = total_s = total_f = 0
    for r in summary:
        m = r["month"]
        if r.get("missing"):
            print(f"{m:>2}月: 檔案不存在")
            continue
        p = r.get("personal", 0)
        b = r.get("business", 0)
        s = r.get("skip", 0)
        f = r.get("fail", 0)
        total_p += p; total_b += b; total_s += s; total_f += f
        print(f"{m:>2}月: 個人 {p} | 機構 {b} | 跳過 {s} | 失敗 {f}")
    print("-" * 50)
    print(f"總計: 個人 {total_p} | 機構 {total_b} | 跳過 {total_s} | 失敗 {total_f}")


if __name__ == "__main__":
    asyncio.run(main())
