"""
PDF 轉圖片工具 — 將 PDF 每頁轉為高解析度 JPG 供 OCR 辨識
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


MAX_PDF_PAGES = 20             # 防解壓炸彈:超過 20 頁直接拒絕
MAX_TOTAL_PIXELS = 60_000_000  # 60 MP 渲染上限,超過動態降 dpi


def pdf_to_images(pdf_path: str, output_dir: str = None, dpi: int = 300) -> list[str]:
    """
    將 PDF 每頁轉為 JPG 圖片。回傳圖片路徑列表。

    安全防護:
      - 超過 MAX_PDF_PAGES 頁直接拒絕(防解壓炸彈)
      - 單頁渲染後若總像素超過上限自動降 dpi 重渲(防超大頁面 OOM)
    """
    import fitz  # PyMuPDF

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return []

    if output_dir is None:
        output_dir = str(pdf_path.parent)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    image_paths = []
    doc = None
    try:
        doc = fitz.open(str(pdf_path))
        # 防解壓炸彈:過多頁直接拒絕
        if len(doc) > MAX_PDF_PAGES:
            logger.warning(f"PDF 頁數 {len(doc)} 超過上限 {MAX_PDF_PAGES},拒絕處理: {pdf_path}")
            return []

        for i, page in enumerate(doc):
            zoom = dpi / 72  # 72 is default DPI
            # 預估渲染後像素,若超過上限就動態降 dpi
            rect = page.rect
            est_pixels = (rect.width * zoom) * (rect.height * zoom)
            if est_pixels > MAX_TOTAL_PIXELS:
                # 重新算一個剛好不超過上限的 zoom
                import math
                zoom = math.sqrt(MAX_TOTAL_PIXELS / (rect.width * rect.height))
                logger.warning(f"PDF 第 {i+1} 頁太大,降 zoom 為 {zoom:.2f}")
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            img_name = f"{pdf_path.stem}_page{i+1}.jpg"
            img_path = str(Path(output_dir) / img_name)
            pix.save(img_path)
            image_paths.append(img_path)
            logger.info(f"PDF 第 {i+1} 頁轉為圖片: {img_path} ({pix.width}x{pix.height})")
    except Exception as e:
        logger.error(f"PDF 轉圖片失敗: {e}")
    finally:
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass

    return image_paths


def is_pdf(content_type: str, filename: str = "") -> bool:
    """判斷是否為 PDF 檔案"""
    if content_type == "application/pdf":
        return True
    if filename and filename.lower().endswith(".pdf"):
        return True
    return False
