"""
PDF 轉圖片工具 — 將 PDF 每頁轉為高解析度 JPG 供 OCR 辨識
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def pdf_to_images(pdf_path: str, output_dir: str = None, dpi: int = 300) -> list[str]:
    """
    將 PDF 每頁轉為 JPG 圖片。
    回傳圖片路徑列表。
    """
    import fitz  # PyMuPDF

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return []

    if output_dir is None:
        output_dir = str(pdf_path.parent)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    image_paths = []
    try:
        doc = fitz.open(str(pdf_path))
        for i, page in enumerate(doc):
            # 高解析度渲染
            zoom = dpi / 72  # 72 is default DPI
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            img_name = f"{pdf_path.stem}_page{i+1}.jpg"
            img_path = str(Path(output_dir) / img_name)
            pix.save(img_path)
            image_paths.append(img_path)
            logger.info(f"PDF 第 {i+1} 頁轉為圖片: {img_path} ({pix.width}x{pix.height})")

        doc.close()
    except Exception as e:
        logger.error(f"PDF 轉圖片失敗: {e}")

    return image_paths


def is_pdf(content_type: str, filename: str = "") -> bool:
    """判斷是否為 PDF 檔案"""
    if content_type == "application/pdf":
        return True
    if filename and filename.lower().endswith(".pdf"):
        return True
    return False
