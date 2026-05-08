"""
行照 OCR 辨識 — Gemini Vision（免費）+ Anthropic Claude（備用）
"""
import json
import time
import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

REG_PROMPT = """你是台灣行照（車輛牌照登記書）辨識專家。分析這張圖片，擷取所有欄位。
注意：圖片可能旋轉或橫放，請自行判斷正確方向。
民國年轉西元年：民國年 + 1911 = 西元年。

只回傳 JSON，不加任何說明：
{
  "plate_number": "車牌號碼",
  "owner_name": "車主姓名",
  "brand": "廠牌（如 TOYOTA、BMW）",
  "model": "車型（如 COROLLA CROSS、K1200R）",
  "year": 出廠年份西元年整數,
  "color": "顏色",
  "engine_cc": 排氣量cc整數,
  "vin": "車身號碼",
  "registration_date": "發照日期 YYYY-MM-DD",
  "registration_expiry": "指定檢驗日期 YYYY-MM-DD",
  "vehicle_type": "車輛種類（如自用小客車、大型重機）",
  "fuel_type": "燃料（汽油/柴油/電動）"
}
無法辨識填 null。"""

# Gemini 上次呼叫時間（全域限速：至少間隔 5 秒）
_last_gemini_call = 0.0


def _gemini_call(image_path: str, prompt: str) -> dict:
    """Gemini Vision OCR（含限速和重試）"""
    import os
    global _last_gemini_call

    api_key = getattr(settings, "GEMINI_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return {"error": "未設定 GEMINI_API_KEY"}

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        img_bytes = Path(image_path).read_bytes()
        suffix = Path(image_path).suffix.lower()
        mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".webp": "image/webp"}.get(suffix, "image/jpeg")

        content = types.Content(parts=[
            types.Part(inline_data=types.Blob(mime_type=mime, data=img_bytes)),
            types.Part(text=prompt),
        ])

        # 限速：距上次呼叫至少 5 秒(用 await asyncio.sleep,不阻塞 event loop)
        import asyncio as _asyncio
        elapsed = time.time() - _last_gemini_call
        if elapsed < 5:
            await _asyncio.sleep(5 - elapsed)

        models = ["gemini-2.5-flash", "gemini-2.0-flash-lite", "gemini-2.0-flash"]
        last_err = ""
        for model_name in models:
            try:
                _last_gemini_call = time.time()
                response = client.models.generate_content(
                    model=model_name,
                    contents=content,
                )
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                result = json.loads(text.strip())
                result["_ocr_engine"] = f"gemini ({model_name})"
                logger.info(f"Gemini OCR ({model_name}) 完成")
                return result
            except Exception as e:
                last_err = str(e)
                logger.warning(f"Gemini {model_name}: {last_err[:80]}")
                continue

        raise Exception(last_err)

    except json.JSONDecodeError as e:
        return {"error": f"辨識結果格式錯誤: {e}"}
    except Exception as e:
        return {"error": f"Gemini: {str(e)}"}


def _anthropic_call(image_path: str, prompt: str) -> dict:
    """Anthropic Claude Vision（備用）"""
    import os, base64
    api_key = getattr(settings, "ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"error": "未設定 ANTHROPIC_API_KEY"}

    path = Path(image_path)
    image_data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    suffix = path.suffix.lower()
    media_type = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                  ".png": "image/png", ".webp": "image/webp"}.get(suffix, "image/jpeg")

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=2048,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                {"type": "text", "text": prompt},
            ]}],
        )
        text = message.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        result = json.loads(text.strip())
        result["_ocr_engine"] = "claude"
        return result
    except Exception as e:
        return {"error": f"Anthropic: {str(e)}"}


async def analyze_registration(image_path: str) -> dict:
    """分析行照。Gemini（免費）→ Anthropic（備用）"""
    if not Path(image_path).exists():
        return {"error": f"圖片不存在: {image_path}"}

    result = _gemini_call(image_path, REG_PROMPT)
    if "error" not in result:
        return result
    gemini_err = result["error"]
    logger.info(f"Gemini 失敗: {gemini_err}，嘗試 Anthropic...")

    result = _anthropic_call(image_path, REG_PROMPT)
    if "error" not in result:
        return result

    return {"error": f"Gemini: {gemini_err}"}
