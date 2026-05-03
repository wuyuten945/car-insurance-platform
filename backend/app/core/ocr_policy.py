"""
保單 OCR 辨識 — Gemini Vision（免費）+ Anthropic Claude（備用）
"""
import logging
from pathlib import Path

from app.core.ocr_registration import _gemini_call, _anthropic_call

logger = logging.getLogger(__name__)

POLICY_PROMPT = """你是台灣車險保單辨識專家。分析這張保單圖片，擷取所有資訊。
注意：圖片可能旋轉、多頁、或為掃描件。
民國年 + 1911 = 西元年。

只回傳 JSON，不加說明：
{
  "insurer_name": "保險公司名稱",
  "policy_number": "保單號碼",
  "insured_name": "被保險人姓名",
  "plate_number": "車牌號碼",
  "start_date": "起保日 YYYY-MM-DD",
  "end_date": "到期日 YYYY-MM-DD",
  "total_premium": 總保費整數,
  "items": [
    {"item_name": "保障項目名稱", "coverage_limit": 保額整數, "deductible": 自負額整數, "premium": 該項保費整數}
  ]
}
items 請列出所有保障項目（強制險、第三人責任險體傷/財損、車體損失險、竊盜險、超額責任險等）。
無法辨識填 null。只回傳 JSON。"""


async def analyze_policy(image_path: str) -> dict:
    """分析保單。Gemini（免費）→ Anthropic（備用）"""
    if not Path(image_path).exists():
        return {"error": f"圖片不存在: {image_path}"}

    result = _gemini_call(image_path, POLICY_PROMPT)
    if "error" not in result:
        return result
    gemini_err = result["error"]
    logger.info(f"保單 Gemini 失敗: {gemini_err}，嘗試 Anthropic...")

    result = _anthropic_call(image_path, POLICY_PROMPT)
    if "error" not in result:
        return result

    return {"error": f"Gemini: {gemini_err}"}
