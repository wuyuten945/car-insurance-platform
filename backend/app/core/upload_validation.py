"""
共用上傳檔案驗證 — 大小、Content-Type、magic bytes、filename sanitize。

用法:
    from app.core.upload_validation import validate_upload

    @router.post("/upload")
    async def upload(file: UploadFile = File(...)):
        await validate_upload(file, kind="image_or_pdf", max_mb=10)
        ...
"""
from __future__ import annotations

from fastapi import UploadFile

from app.config import settings
from app.exceptions import BadRequestError


# 各種 kind 對應的:Content-Type 白名單 + magic bytes prefix
# magic bytes 來源:https://en.wikipedia.org/wiki/List_of_file_signatures
_PROFILES = {
    "image": {
        "mimes": {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"},
        "magic": [
            b"\xff\xd8\xff",          # JPEG (any)
            b"\x89PNG\r\n\x1a\n",     # PNG
            b"RIFF",                  # WebP (RIFF...WEBP)
            b"GIF87a", b"GIF89a",     # GIF
        ],
    },
    "pdf": {
        "mimes": {"application/pdf"},
        "magic": [b"%PDF-"],
    },
    "image_or_pdf": {
        "mimes": {
            "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif",
            "application/pdf",
        },
        "magic": [
            b"\xff\xd8\xff",
            b"\x89PNG\r\n\x1a\n",
            b"RIFF",
            b"GIF87a", b"GIF89a",
            b"%PDF-",
        ],
    },
    "csv": {
        # CSV 沒固定 magic bytes,放鬆 magic 檢查只驗 mime + extension
        "mimes": {
            "text/csv", "application/csv", "application/vnd.ms-excel",
            "text/plain", "application/octet-stream",  # 部分瀏覽器送 .csv 用這些
        },
        "magic": None,
    },
}


# 圖檔解碼後最大像素(防 decompression bomb / pixel flood)
# 100MP 已遠超手機相機(典型 12-50MP),夠寬鬆但能擋 100K x 100K 的攻擊用 PNG
MAX_IMAGE_PIXELS = 100_000_000


def _validate_image_dimensions(data: bytes) -> None:
    """
    驗證圖片解碼後尺寸不會把 RAM 吃光。Pillow 解碼大尺寸 PNG 會把每個 pixel 展開成
    至少 4 bytes,100K x 100K = 40GB,足以打死 Render free tier。

    用 ImageFile.LOAD_TRUNCATED_IMAGES 讀 header 不真的解碼,夠快。
    """
    try:
        from PIL import Image
        import io
        with Image.open(io.BytesIO(data)) as img:
            w, h = img.size
            if w * h > MAX_IMAGE_PIXELS:
                raise BadRequestError(
                    f"圖片尺寸過大 ({w}x{h} = {w*h:,} px),上限 {MAX_IMAGE_PIXELS:,} px"
                )
    except BadRequestError:
        raise
    except Exception:
        # 不是圖片或解析失敗都讓上層處理(此函式只負責 pixel-flood 防護)
        pass


async def validate_upload(
    file: UploadFile,
    *,
    kind: str = "image_or_pdf",
    max_mb: int | None = None,
) -> bytes:
    """
    驗證上傳檔案。回傳已讀完的 bytes(避免 caller 再讀一次 multipart stream 而錯位)。

    raises BadRequestError 若任一項驗證失敗。

    kind 選項: 'image' / 'pdf' / 'image_or_pdf' / 'csv'
    max_mb: None 表示用 settings.MAX_UPLOAD_SIZE_MB (預設 10)
    """
    if kind not in _PROFILES:
        raise BadRequestError(f"unknown upload kind: {kind}")
    profile = _PROFILES[kind]
    limit = (max_mb if max_mb is not None else settings.MAX_UPLOAD_SIZE_MB) * 1024 * 1024

    # ── 1. filename sanitize:不可含 path separator / null byte / 控制字元 ──
    fn = (file.filename or "").strip()
    if not fn:
        raise BadRequestError("檔名缺失")
    if "/" in fn or "\\" in fn or "\x00" in fn or ".." in fn:
        raise BadRequestError("檔名含不允許字元")
    if len(fn) > 200:
        raise BadRequestError("檔名過長")

    # ── 2. Content-Type 白名單 ──
    content_type = (file.content_type or "").lower()
    if content_type not in profile["mimes"]:
        raise BadRequestError(f"不支援的檔案類型: {content_type or '(未知)'}")

    # ── 3. 讀整個檔案到 bytes 並檢查大小 ──
    # 為 magic bytes 驗證需要,順便擋掉超大檔(FastAPI 預設會吃進記憶體;
    # 真正生產級的話應在 reverse proxy / starlette body limit 層擋,這裡是後備)
    data = await file.read()
    size = len(data)
    if size == 0:
        raise BadRequestError("空檔案")
    if size > limit:
        raise BadRequestError(f"檔案過大: {size / 1024 / 1024:.1f}MB > {limit / 1024 / 1024:.0f}MB 上限")

    # ── 4. magic bytes 檢查(若有設定) ──
    if profile["magic"]:
        head = data[:16]
        if not any(head.startswith(sig) for sig in profile["magic"]):
            raise BadRequestError("檔案內容與宣稱類型不符(magic bytes 驗證失敗)")

    # ── 5. 圖檔像素 flood 防護(只對宣稱是圖片的檔案驗) ──
    if content_type.startswith("image/"):
        _validate_image_dimensions(data)

    # 把 file pointer 重置回頭,讓 caller 還可以用 file.read() 或 file.file 操作
    try:
        await file.seek(0)
    except Exception:
        try:
            file.file.seek(0)
        except Exception:
            pass

    return data
