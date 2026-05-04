"""
Migration 002: users 加 is_line_friend + line_friend_at 兩欄

執行：
  cd C:\\Users\\User\\car-insurance-platform\\backend
  python migrations/002_user_line_friend_fields.py

背景：
- 接 LINE Messaging API webhook，需追蹤用戶是否已加 BOPINAN OA 為好友
- 沒加好友的用戶無法接收 push 訊息（LINE 平台限制）
- 用 ALTER TABLE ADD COLUMN（SQLite + PostgreSQL 都支援）

Render Free 層 ephemeral filesystem 會在每次 redeploy 重建 DB，schema 會自動帶
新欄位（透過 Base.metadata.create_all），所以這支 migration 主要服務本機 dev DB。
"""
import asyncio
import shutil
import sys
from datetime import datetime
from pathlib import Path

# 讓 script 能 import app/ 套件（從 migrations/ 子目錄跑時）
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

        if "is_line_friend" not in existing:
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN is_line_friend BOOLEAN NOT NULL DEFAULT 0"
            ))
            print("[OK] 已加 is_line_friend")
        else:
            print("[SKIP] is_line_friend 已存在")

        if "line_friend_at" not in existing:
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN line_friend_at DATETIME"
            ))
            print("[OK] 已加 line_friend_at")
        else:
            print("[SKIP] line_friend_at 已存在")

    print("[DONE] migration 002 完成")


async def _existing_columns(conn, table: str) -> set[str]:
    is_sqlite = "sqlite" in str(engine.url)
    if is_sqlite:
        res = await conn.execute(text(f"PRAGMA table_info({table})"))
        return {row[1] for row in res.fetchall()}
    res = await conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = :t"
    ), {"t": table})
    return {row[0] for row in res.fetchall()}


if __name__ == "__main__":
    asyncio.run(main())
