"""
Migration 001: users.phone 改 nullable + email 加 unique

執行：
  cd C:\\Users\\User\\car-insurance-platform\\backend
  python migrations/001_phone_nullable.py

背景：
- 原 schema 中 users.phone 是 NOT NULL UNIQUE，導致 OAuth 註冊時用 phone="" 入庫，
  第二個 OAuth 用戶會撞 unique 衝突。
- 改成 nullable=True 後，phone=NULL 不算衝突，同一手機號仍不允許多帳號。
- email 加 unique 確保 OAuth 用 email 查找時 1:1 對應。

SQLite 不支援 ALTER COLUMN 改 nullability，需重建表。
"""
import asyncio
import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

from app.database import engine, AsyncSessionLocal


DB_PATH = Path(__file__).parent.parent / "car_insurance.db"


async def main():
    if not DB_PATH.exists():
        print(f"[ERR] 找不到 DB：{DB_PATH}")
        return

    # 備份
    backup = DB_PATH.with_suffix(f".db.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(DB_PATH, backup)
    print(f"[BACKUP] {backup.name}")

    async with engine.begin() as conn:
        # 1. 關閉外鍵檢查
        await conn.execute(text("PRAGMA foreign_keys=OFF"))

        # 2. 看 users 表現有 schema
        res = await conn.execute(text(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"
        ))
        old_sql = res.scalar_one_or_none() or ""
        print(f"[INFO] 現有 users 表 SQL：\n{old_sql}\n")

        # 3. 建新表
        await conn.execute(text("DROP TABLE IF EXISTS users_new"))
        await conn.execute(text("""
            CREATE TABLE users_new (
                id VARCHAR(36) PRIMARY KEY,
                phone VARCHAR(20),
                name VARCHAR(100),
                email VARCHAR(255),
                id_number_hash VARCHAR(255),
                birth_date DATETIME,
                address VARCHAR(500),
                registered_address VARCHAR(500),
                emergency_contact_name VARCHAR(100),
                emergency_contact_phone VARCHAR(20),
                emergency_contact_relation VARCHAR(50),
                license_number VARCHAR(50),
                license_expiry DATETIME,
                avatar_url VARCHAR(500),
                is_active BOOLEAN DEFAULT 1,
                last_login_at DATETIME,
                created_at DATETIME,
                updated_at DATETIME
            )
        """))

        # 4. 搬資料（phone="" 轉 NULL，避免 unique 衝突）
        await conn.execute(text("""
            INSERT INTO users_new
            SELECT
                id,
                CASE WHEN phone='' OR phone IS NULL THEN NULL ELSE phone END AS phone,
                name, email, id_number_hash, birth_date, address, registered_address,
                emergency_contact_name, emergency_contact_phone, emergency_contact_relation,
                license_number, license_expiry, avatar_url, is_active, last_login_at,
                created_at, updated_at
            FROM users
        """))
        res = await conn.execute(text("SELECT COUNT(*) FROM users_new"))
        moved = res.scalar()
        print(f"[INFO] 搬移 {moved} 筆 user 資料")

        # 5. 換表
        await conn.execute(text("DROP TABLE users"))
        await conn.execute(text("ALTER TABLE users_new RENAME TO users"))

        # 6. 重建 index
        await conn.execute(text("CREATE UNIQUE INDEX ix_users_phone ON users(phone)"))
        await conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON users(email)"))
        print("[INFO] 重建 ix_users_phone (UNIQUE), ix_users_email (UNIQUE)")

        # 7. 啟回外鍵 + 驗證完整性
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        res = await conn.execute(text("PRAGMA foreign_key_check"))
        broken = res.fetchall()
        if broken:
            print(f"[ERR] foreign_key_check 異常：{broken}")
        else:
            print("[OK] foreign_key_check 通過")

    # 8. 驗證查詢
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT COUNT(*) FROM users"))
        total = res.scalar()
        res = await db.execute(text("SELECT COUNT(*) FROM users WHERE phone IS NULL"))
        null_phone = res.scalar()
        res = await db.execute(text("SELECT COUNT(*) FROM users WHERE phone IS NOT NULL"))
        with_phone = res.scalar()
        print(f"\n[DONE] users 共 {total} 筆 | phone IS NULL={null_phone} | phone NOT NULL={with_phone}")
        print(f"[INFO] 備份檔保留於：{backup}")


if __name__ == "__main__":
    asyncio.run(main())
