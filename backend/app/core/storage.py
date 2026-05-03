import os
import shutil
from pathlib import Path
from fastapi import UploadFile
from app.config import settings
from app.database import generate_uuid


class LocalStorage:
    """開發用本地檔案儲存，生產環境替換為 S3。"""

    def __init__(self):
        self.base_dir = Path(settings.UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def upload(self, file: UploadFile, subfolder: str = "") -> str:
        folder = self.base_dir / subfolder
        folder.mkdir(parents=True, exist_ok=True)

        ext = Path(file.filename).suffix if file.filename else ".bin"
        filename = f"{generate_uuid()}{ext}"
        file_path = folder / filename

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        return f"/uploads/{subfolder}/{filename}" if subfolder else f"/uploads/{filename}"

    async def delete(self, file_path: str) -> bool:
        full_path = self.base_dir / file_path.lstrip("/uploads/")
        if full_path.exists():
            os.remove(full_path)
            return True
        return False

    def get_full_path(self, relative_url: str) -> Path:
        return self.base_dir / relative_url.lstrip("/uploads/")


storage = LocalStorage()
