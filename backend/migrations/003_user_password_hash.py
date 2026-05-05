"""
Migration 003: users 加 password_hash（進階保護密碼，二因子用）

執行：
  cd C:\\Users\\User\\car-insurance-platform\\backend
  python migrations/003_user_password_hash.py

null 表示未啟用密碼保護（沿用 OTP 單因子）；有值表示啟用 OTP+密碼雙因子。
"""
import asyncio
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.database import engine


DB_PATH = Path(__file__).parent.parent / "car_insurance.db"


async def main():
    is_sqlite = "sqlite" in str(engine.url)
    if is_sqlite and not DB_PATH.exists():
        print(f"[ERR] 找不到 DB：{DB_PATH}")
        return

    if is_sqlite:
        backup = DB_PATH.with_suffix(f".db.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        shutil.copy2(DB_PATH, backup)
        print(f"[BACKUP] {backup.name}")

    async with engine.begin() as conn:
        existing = await _existing_columns(conn, "users")
        print(f"[INFO] 現有 users 欄位：{sorted(existing)}")

        if "password_hash" not in existing:
            await conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
            print("[OK] 已加 password_hash")
        else:
            print("[SKIP] password_hash 已存在")

    print("[DONE] migration 003 完成")


async def _existing_columns(conn, table: str) -> set[str]:
    is_sqlite = "sqlite" in str(engine.url)
    if is_sqlite:
        res = await conn.execute(text(f"PRAGMA table_info({table})"))
        return {row[1] for row in res.fetchall()}
    res = await conn.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = :t"
    ), {"t": table})
    return {row[0] for row in res.fetchall()}


if __name__ == "__main__":
    asyncio.run(main())
