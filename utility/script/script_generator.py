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
    """Khởi tạo Gemini Client."""
    try:
        # Giả định GEMINI_API_KEY đã được đặt trong biến môi trường
        return genai.Client()
    except Exception as e:
        print(f"Lỗi khởi tạo Gemini client: {e}")
        return None

client = init_gemini_client()
MODEL_NAME = "gemini-3-pro-preview" # Hoặc "gemini-2.5-flash" để tối ưu tốc độ/chi phí


# =======================
# PROMPT TỐI ƯU CHO TÍNH CHÂN THẬT, Ý NGHĨA VÀ HÌNH ẢNH
# =======================

# Sử dụng chuỗi Python đa dòng cho PROMPT_SYSTEM
PROMPT_SYSTEM = """
Bạn là nhà văn kiêm biên kịch TikTok chuyên nghiệp, người hiểu rõ thuật toán và tâm lý người xem. Nhiệm vụ của bạn là tạo ra kịch bản CÓ CHIỀU SÂU VÀ Ý NGHĨA, mang tính truyền cảm hứng cao, được tối ưu hóa cho giọng đọc AI TTS (FPT AI) nghe CHÂN THẬT, NHƯ NGƯỜI THẬT đang tâm sự. Kịch bản phải bao gồm chi tiết từ khóa hình ảnh/video cho Pexels.

MỤC TIÊU:
- Tạo kịch bản cảm xúc, sâu sắc, truyền tải thông điệp ý nghĩa, dễ chạm tới trái tim người xem.
- Tối ưu hóa nhịp điệu nói để tạo cảm giác TRÔI CHẢY, tự nhiên, không bị cứng nhắc khi đọc bằng AI TTS (FPT AI).
- Đưa ra các từ khóa hình ảnh CHI TIẾT (Pexels Keywords) mô tả cảm xúc và bối cảnh cho từng phần thoại.

QUY TẮC BẮT BUỘC:
- Độ dài câu: Câu có thể dài hơn một chút (tối đa mười lăm từ) để tăng tính trôi chảy.
- Dùng dấu chấm phẩy (;): Để ngắt câu dài hơn một chút, duy trì luồng thông tin liên tục.
- Dùng dấu chấm (.): Để ngắt hơi ở những điểm nhấn mạnh, hoặc khi muốn người nghe suy ngẫm.
- Dùng dấu phẩy (,): Ngắt hơi nhẹ, tạo sự liền mạch trong câu.
- KHÔNG dùng dấu "..."
- KHÔNG dùng emoji.
- Viết số bằng chữ (một, hai, ba).
- Tổng độ dài tối đa một trăm ba mươi từ (cho toàn bộ phần thoại).
- KHÔNG xuống dòng giữa câu.

PHONG CÁCH:
- HOOK mạnh bằng câu hỏi tu từ hoặc tuyên bố mang tính triết lý.
- Nhịp điệu: Khởi đầu chậm rãi, tăng dần cảm xúc, rồi lắng đọng ở phần kết.
- Ngôn ngữ: Gần gũi, truyền cảm hứng, sử dụng từ ngữ gợi hình ảnh và cảm xúc.
- Sử dụng từ NHẤN MẠNH (VIẾT HOA) để tạo điểm nhấn cảm xúc quan trọng.

BẮT BUỘNG trả về DUY NHẤT dạng JSON theo cấu trúc CẤU TRÚC JSON bên dưới.
"""


# =======================
# SCRIPT NORMALIZER (CHO TTS)
# =======================

def normalize_script_for_tts(script_data: dict) -> dict:
    """
    Làm sạch & tối ưu từng phần text trong script cho FPT TTS + Whisper.
    Giữ nguyên cấu trúc JSON.
    """
    normalized_data = {"title": script_data.get("title", ""), "script_parts": []}
    
    for part in script_data.get("script_parts", []):
        text = part.get("text", "")
        if not text:
            continue
            
        # Làm sạch & tối ưu script
        text = unicodedata.normalize("NFC", text)
        text = text.replace("...", ".") # Xóa ...
        text = re.sub(r"\.{2,}", ".", text) # Gộp nhiều dấu chấm
        text = re.sub(r",{2,}", ",", text) # Gộp nhiều dấu phẩy
        text = text.strip()

        normalized_data["script_parts"].append({
            "text": text,
            "pexels_keywords": part.get("pexels_keywords", "")
        })
        
    normalized_data["call_to_action"] = script_data.get("call_to_action", "").strip()
    return normalized_data


# =======================
# GENERATE SCRIPT
# =======================

def generate_script(topic: str) -> dict | None:
    """Gọi Gemini để tạo kịch bản theo cấu trúc JSON mới."""
    if client is None:
        print("❌ Không khởi tạo được Gemini client. Kiểm tra GEMINI_API_KEY.")
        return None

    user_content = f"{PROMPT_SYSTEM}\n\nCHỦ ĐỀ CẦN TẠO: {topic}"
    
    # Định nghĩa Schema JSON mới
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Tên chủ đề có chiều sâu, ngắn gọn."},
            "script_parts": {
                "type": "array",
                "description": "Danh sách các phần thoại, mỗi phần có text và từ khóa hình ảnh.",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Nội dung câu nói (Tối đa 15 từ)."},
                        "pexels_keywords": {"type": "string", "description": "Từ khóa tìm kiếm hình ảnh/video trên Pexels mô tả cảm xúc và bối cảnh."}
                    },
                    "required": ["text", "pexels_keywords"]
                }
            },
            "call_to_action": {"type": "string", "description": "Lời kêu gọi hành động ngắn gọn ở cuối (ví dụ: Bình luận 'TÔI' nếu bạn muốn biết thêm.)."}
        },
        "required": ["title", "script_parts", "call_to_action"]
    }

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
                response_schema=RESPONSE_SCHEMA
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
        # Response đã được định dạng JSON theo schema
        script_data = json.loads(raw_text)
    except json.JSONDecodeError:
        print("❌ Không parse được JSON hợp lệ từ Gemini.")
        # Thử trích xuất JSON nếu Gemini trả về thêm văn bản
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
             try:
                script_data = json.loads(match.group(0))
             except Exception:
                print("❌ Không thể trích xuất JSON.")
                return None
        else:
            return None
    except Exception:
        print("❌ Lỗi xử lý JSON.")
        return None

    return normalize_script_for_tts(script_data)

def extract_text_for_tts(script_data: dict) -> str:
    """
    Trích xuất và nối toàn bộ nội dung text từ cấu trúc script_parts 
    của Gemini thành một chuỗi duy nhất cho FPT AI TTS.

    Args:
        script_data (dict): JSON script đã normalize, có cấu trúc:
            {
                "title": "Tiêu đề",
                "script_parts": [
                    {"text": "Nội dung câu 1", "pexels_keywords": "..."},
                    {"text": "Nội dung câu 2", "pexels_keywords": "..."},
                    ...
                ],
                "call_to_action": "Lời kêu gọi hành động"
            }

    Returns:
        str: Toàn bộ text nối liền, có thêm call_to_action ở cuối (nếu có)
    """
    # Nối các phần thoại
    all_text = " ".join([
        part.get("text", "").strip()
        for part in script_data.get("script_parts", [])
        if part.get("text")
    ])

    # Thêm Call to Action vào cuối
    call_to_action = script_data.get("call_to_action", "").strip()
    if call_to_action:
        all_text += f". {call_to_action}"

    return all_text.strip()
