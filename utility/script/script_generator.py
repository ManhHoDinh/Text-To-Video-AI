import os
import json
from google import genai
from google.genai import types
from google.genai.errors import APIError

# --- THIẾT LẬP GEMINI API (Lấy từ đoạn mã trước) ---
# Đảm bảo bạn đã đặt biến môi trường GEMINI_API_KEY
try:
    client = genai.Client()
except Exception:
    client = None

model = "gemini-3-pro-preview" 
# ---------------------------------------------------

def generate_script(topic):
    if client is None:
        print("Lỗi: Không thể khởi tạo Gemini client. Hãy kiểm tra GEMINI_API_KEY.")
        return None
        
    prompt_system = """
    Bạn là một biên kịch TikTok chuyên nghiệp, chuyên tạo ra những video ngắn VIRAL, thu hút người xem ngay từ 2 giây đầu.
    Phong cách viết phải:
    - Hook cực mạnh mở đầu (gây sốc / bất ngờ / tò mò)
    - Câu ngắn, tiết tấu nhanh, dễ nghe, dễ hiểu
    - Tăng dần độ hấp dẫn, luôn giữ người xem “muốn nghe tiếp”
    - Có twist hoặc thông tin gây ngạc nhiên
    - Không vòng vo, không lan man
    - Ngôn ngữ đời thường, đậm chất TikTok
    - Dưới 140 từ (tương ứng video ~50 giây)

    Bắt buộc trả về DUY NHẤT dạng JSON:
    {"script": "nội dung kịch bản ở đây"}
    """
    
    full_user_content = f"{prompt_system}\n\nCHỦ ĐỀ: {topic}"

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Content(
                    role="user", 
                    parts=[types.Part(text=full_user_content)] # Đã sửa lỗi Part.from_text()
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "script": {"type": "string", "description": "Nội dung kịch bản TikTok dưới 140 từ."}
                    },
                    "required": ["script"]
                }
            )
        )
    except APIError as e:
        print(f"Lỗi API: {e}")
        return None
    except Exception as e:
        print(f"Lỗi không xác định: {e}")
        return None

    content = response.text.strip()

    try:
        # Tách JSON hợp lệ
        return json.loads(content)["script"].strip()
    except (json.JSONDecodeError, KeyError):
        # Fallback: Xử lý lỗi JSON
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start != -1 and json_end != -1 and json_end > json_start:
            cleaned = content[json_start:json_end]
            try:
                return json.loads(cleaned)["script"].strip()
            except json.JSONDecodeError:
                return f"Lỗi phân tích JSON sau khi làm sạch: {content}"
        else:
            return f"Lỗi không tìm thấy JSON: {content}"
