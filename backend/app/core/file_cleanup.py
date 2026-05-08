"""
共用檔案清理 helper — 刪除保單/車輛/理賠時順便清掉對應上傳檔,避免孤兒檔。

設計原則:
  - 永遠 best-effort,失敗不擋 DB 刪除(把警告記 log 給 ops 後續清理)
  - 只刪 UPLOAD_DIR 下的檔案,絕不接受任意路徑
"""
from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlparse

from app.config import settings

logger = logging.getLogger(__name__)


def _safe_local_path_from_url(url_or_path: str | None) -> Path | None:
    """
    把 'document_url' / 'image_url' 等 DB 字串轉成檔案系統 Path,並確保仍在 UPLOAD_DIR 內。

    支援格式:
      - '/uploads/policies/policy_xxx.jpg'  → UPLOAD_DIR/policies/policy_xxx.jpg
      - 'http(s)://host/uploads/policies/policy_xxx.jpg' → 同上(只取 path)
      - 已是檔案系統路徑(舊資料):若在 UPLOAD_DIR 下就接受
    回傳 None 代表不可清(空、外部 URL、或 path traversal 風險)。
    """
    if not url_or_path:
        return None
    try:
        # 抽取 path 部分(若是 URL)
        parsed = urlparse(url_or_path)
        rel = parsed.path if parsed.scheme in ("http", "https") else url_or_path

        # 我們的 upload 路徑都是 /uploads/<subfolder>/<filename>
        # 把 leading /uploads/ 拿掉,留下相對 UPLOAD_DIR 的部分
        if rel.startswith("/uploads/"):
            rel = rel[len("/uploads/"):]
        elif rel.startswith("/"):
            rel = rel.lstrip("/")

        upload_root = Path(settings.UPLOAD_DIR).resolve()
        candidate = (upload_root / rel).resolve()

        # 雙保險:resolve 後仍在 upload_root 之下
        if not str(candidate).startswith(str(upload_root)):
            logger.warning(f"[cleanup] path traversal 風險,拒絕清理: {url_or_path}")
            return None
        return candidate
    except Exception as e:
        logger.warning(f"[cleanup] 路徑解析失敗 {url_or_path}: {e}")
        return None


def cleanup_files(*urls_or_paths: str | None) -> int:
    """
    刪除多個上傳檔(若它們在 UPLOAD_DIR 下且存在)。
    回傳實際刪除的檔案數。失敗 best-effort log 但不 raise。
    """
    deleted = 0
    for raw in urls_or_paths:
        if not raw:
            continue
        path = _safe_local_path_from_url(raw)
        if path is None:
            continue
        try:
            if path.exists() and path.is_file():
                path.unlink()
                deleted += 1
                logger.info(f"[cleanup] 刪除上傳檔: {path}")
        except Exception as e:
            logger.warning(f"[cleanup] 刪檔失敗 {path}: {e}")
    return deleted


def cleanup_folder(folder_rel: str) -> int:
    """
    遞迴刪 UPLOAD_DIR 下的子資料夾(用於 claim 多張附件、accident 多張照片)。
    folder_rel 例:'claims/CLM-xxx' → UPLOAD_DIR/claims/CLM-xxx/
    回傳刪除的檔案數。
    """
    if not folder_rel:
        return 0
    upload_root = Path(settings.UPLOAD_DIR).resolve()
    folder = (upload_root / folder_rel.lstrip("/")).resolve()
    if not str(folder).startswith(str(upload_root)):
        logger.warning(f"[cleanup] 資料夾不在 UPLOAD_DIR 內,拒絕: {folder_rel}")
        return 0

    if not folder.exists() or not folder.is_dir():
        return 0

    deleted = 0
    try:
        for child in folder.rglob("*"):
            if child.is_file():
                try:
                    child.unlink()
                    deleted += 1
                except Exception as e:
                    logger.warning(f"[cleanup] 刪檔失敗 {child}: {e}")
        # 移除空資料夾
        for sub in sorted(folder.rglob("*"), key=lambda p: -len(p.parts)):
            if sub.is_dir():
                try:
                    sub.rmdir()
                except Exception:
                    pass
        try:
            folder.rmdir()
        except Exception:
            pass
        logger.info(f"[cleanup] 清理資料夾 {folder} 共 {deleted} 檔")
    except Exception as e:
        logger.warning(f"[cleanup] 清理資料夾失敗 {folder}: {e}")
    return deleted
