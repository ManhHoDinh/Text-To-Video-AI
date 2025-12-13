import os
import json
import re
import unicodedata

from google import genai
from google.genai import types
from google.genai.errors import APIError


# =======================
# GEMINI CLIENT SETUP
# =======================

def init_gemini_client():
    try:
        return genai.Client()
    except Exception:
        return None


client = init_gemini_client()
MODEL_NAME = "gemini-3-pro-preview"


# =======================
# PROMPT TỐI ƯU CHO TTS + CAPTION
# =======================

PROMPT_SYSTEM = """
Bạn là một biên kịch TikTok chuyên nghiệp, đồng thời là chuyên gia viết kịch bản cho AI Text-to-Speech.

MỤC TIÊU:
- Kịch bản phải NGHE HAY khi đọc bằng AI TTS (đặc biệt là FPT AI)
- Kịch bản giúp hệ thống tạo caption tự động chính xác

QUY TẮC BẮT BUỘC:
- Mỗi câu KHÔNG quá 12 từ
- Câu ngắn, nhịp nhanh, giống lời nói
- Dùng dấu chấm (.) để ngắt hơi mạnh
- Dùng dấu phẩy (,) để ngắt hơi nhẹ
- KHÔNG dùng dấu "..."
- KHÔNG dùng emoji
- KHÔNG dùng số dạng chữ số (1, 2, 3)
- Viết số bằng chữ (một, hai, ba)
- Tối đa 120 từ
- Không xuống dòng giữa câu

PHONG CÁCH:
- Hook mạnh ngay câu đầu
- Tăng dần cao trào
- Có twist hoặc kết bất ngờ
- Có một vài từ NHẤN MẠNH (viết HOA, rất ít)

BẮT BUỘC trả về DUY NHẤT dạng JSON:
{"script": "nội dung kịch bản ở đây"}
"""


# =======================
# SCRIPT NORMALIZER (CHO TTS)
# =======================

def normalize_script_for_tts(script: str) -> str:
    """
    Làm sạch & tối ưu script cho FPT TTS + Whisper
    """
    script = unicodedata.normalize("NFC", script)

    # Xóa ...
    script = script.replace("...", ".")

    # Gộp nhiều dấu chấm
    script = re.sub(r"\.{2,}", ".", script)

    # Gộp nhiều dấu phẩy
    script = re.sub(r",{2,}", ",", script)

    # Mỗi câu một dòng để tạo nhịp đọc rõ
    script = script.replace(". ", ".\n")

    return script.strip()


# =======================
# GENERATE SCRIPT
# =======================

def generate_script(topic: str) -> str | None:
    if client is None:
        print("❌ Không khởi tạo được Gemini client. Kiểm tra GEMINI_API_KEY.")
        return None

    user_content = f"{PROMPT_SYSTEM}\n\nCHỦ ĐỀ: {topic}"

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=user_content)]
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "script": {
                            "type": "string",
                            "description": "Kịch bản TikTok tối ưu cho AI TTS"
                        }
                    },
                    "required": ["script"]
                }
            )
        )
    except APIError as e:
        print(f"❌ Lỗi Gemini API: {e}")
        return None
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")
        return None

    raw_text = response.text.strip()

    # Parse JSON an toàn
    try:
        script = json.loads(raw_text)["script"]
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        if start != -1 and end != -1:
            try:
                script = json.loads(raw_text[start:end])["script"]
            except Exception:
                print("❌ Không parse được JSON từ Gemini")
                return None
        else:
            print("❌ Không tìm thấy JSON hợp lệ")
            return None

    return normalize_script_for_tts(script)

