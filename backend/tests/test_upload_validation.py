"""
上傳檔案驗證測試:size、Content-Type、magic bytes、filename sanitize、像素 bomb。
"""
import io
import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.core.upload_validation import validate_upload, MAX_IMAGE_PIXELS
from app.exceptions import BadRequestError


def _mock_upload(name: str, ctype: str, body: bytes) -> UploadFile:
    return UploadFile(
        filename=name,
        file=io.BytesIO(body),
        headers=Headers({"content-type": ctype}),
    )


# ── 一個合法 PNG header(1x1 px,夠通過 magic bytes 跟像素檢查) ──
_TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c62000100000005000100"
    "0d0a2db40000000049454e44ae426082"
)


class TestFilenameSanitize:
    async def test_path_traversal_blocked(self):
        f = _mock_upload("../../etc/passwd.jpg", "image/jpeg", b"\xff\xd8\xff" + b"x" * 100)
        with pytest.raises(BadRequestError, match="不允許字元"):
            await validate_upload(f, kind="image", max_mb=10)

    async def test_backslash_blocked(self):
        f = _mock_upload("a\\b.jpg", "image/jpeg", b"\xff\xd8\xff" + b"x" * 100)
        with pytest.raises(BadRequestError, match="不允許字元"):
            await validate_upload(f, kind="image", max_mb=10)

    async def test_null_byte_blocked(self):
        f = _mock_upload("a\x00.jpg", "image/jpeg", b"\xff\xd8\xff" + b"x" * 100)
        with pytest.raises(BadRequestError, match="不允許字元"):
            await validate_upload(f, kind="image", max_mb=10)

    async def test_empty_filename_rejected(self):
        f = _mock_upload("", "image/jpeg", b"\xff\xd8\xff")
        with pytest.raises(BadRequestError, match="檔名"):
            await validate_upload(f, kind="image", max_mb=10)

    async def test_long_filename_rejected(self):
        f = _mock_upload("x" * 300 + ".jpg", "image/jpeg", b"\xff\xd8\xff")
        with pytest.raises(BadRequestError, match="檔名過長"):
            await validate_upload(f, kind="image", max_mb=10)


class TestContentType:
    async def test_disallowed_type_rejected(self):
        f = _mock_upload("a.exe", "application/x-msdownload", b"MZ" + b"x" * 100)
        with pytest.raises(BadRequestError, match="不支援的檔案類型"):
            await validate_upload(f, kind="image", max_mb=10)

    async def test_pdf_rejected_for_image_kind(self):
        f = _mock_upload("a.pdf", "application/pdf", b"%PDF-1.4" + b"x" * 100)
        with pytest.raises(BadRequestError, match="不支援的檔案類型"):
            await validate_upload(f, kind="image", max_mb=10)


class TestMagicBytes:
    async def test_jpeg_with_wrong_magic_rejected(self):
        # 宣稱是 JPEG 但內容是 'XXX...'
        f = _mock_upload("a.jpg", "image/jpeg", b"XXXX" + b"x" * 100)
        with pytest.raises(BadRequestError, match="magic bytes"):
            await validate_upload(f, kind="image", max_mb=10)

    async def test_png_passes(self):
        f = _mock_upload("a.png", "image/png", _TINY_PNG)
        data = await validate_upload(f, kind="image", max_mb=10)
        assert data == _TINY_PNG

    async def test_pdf_with_wrong_magic_rejected(self):
        f = _mock_upload("a.pdf", "application/pdf", b"NOTPDF" + b"x" * 100)
        with pytest.raises(BadRequestError, match="magic bytes"):
            await validate_upload(f, kind="pdf", max_mb=10)

    async def test_pdf_real_passes(self):
        f = _mock_upload("a.pdf", "application/pdf", b"%PDF-1.4\n" + b"x" * 100)
        data = await validate_upload(f, kind="pdf", max_mb=10)
        assert data.startswith(b"%PDF-")


class TestSize:
    async def test_oversize_rejected(self):
        # 12 MB 超過 max_mb=10
        body = b"\xff\xd8\xff" + b"\x00" * (12 * 1024 * 1024)
        f = _mock_upload("a.jpg", "image/jpeg", body)
        with pytest.raises(BadRequestError, match="檔案過大"):
            await validate_upload(f, kind="image", max_mb=10)

    async def test_empty_rejected(self):
        f = _mock_upload("a.jpg", "image/jpeg", b"")
        with pytest.raises(BadRequestError, match="空檔案"):
            await validate_upload(f, kind="image", max_mb=10)


class TestImageDimensions:
    async def test_normal_image_ok(self):
        # 1x1 PNG ok
        f = _mock_upload("a.png", "image/png", _TINY_PNG)
        await validate_upload(f, kind="image", max_mb=10)

    async def test_pixel_constant_sanity(self):
        # 確認常數 100MP 沒被改錯
        assert MAX_IMAGE_PIXELS == 100_000_000
