import requests
import time
import json # Import thư viện json để xử lý dữ liệu từ Gemini

# =======================
# CẤU HÌNH FPT AI
# =======================
API_KEY = "7zE1Fuq1p0bKESXNy3WFwIGWsQWQF23I"  # API key FPT AI của bạn
VOICE = "banmai"                             # giọng đọc

# =======================
# HÀM NỐI TEXT TỪ JSON
# =======================
def extract_text_for_tts(script_data: dict) -> str:
    """
    Trích xuất và nối toàn bộ nội dung text từ cấu trúc script_parts 
    của Gemini thành một chuỗi duy nhất cho FPT AI TTS.
    """
    all_text = " ".join([
        part.get("text", "") 
        for part in script_data.get("script_parts", []) 
        if part.get("text")
    ])
    
    # Thêm Call to Action vào cuối (nếu cần đọc)
    call_to_action = script_data.get("call_to_action", "")
    if call_to_action:
         all_text += f". {call_to_action}"
         
    return all_text.strip()


# =======================
# HÀM TẠO AUDIO (TTS)
# =======================
def generate_audio(text: str, outputFilename: str):
    """
    Gửi request đến FPT AI TTS và tải về file audio.
    """
    if not text:
        print("Cảnh báo: Không có nội dung text để tạo audio.")
        return

    url = "https://api.fpt.ai/hmi/tts/v5"

    headers = {
        "api_key": API_KEY,
        "voice": VOICE,
        "Cache-Control": "no-cache"
    }

    # 1. Gửi request tạo audio
    print(f"Bắt đầu tạo audio (dài {len(text)} ký tự)...")
    try:
        response = requests.post(
            url,
            headers=headers,
            data=text.encode("utf-8")
        )
    except requests.exceptions.RequestException as e:
        raise Exception(f"Lỗi kết nối FPT TTS: {e}")

    if response.status_code != 200:
        raise Exception(f"TTS request failed (Mã {response.status_code}): {response.text}")

    # FPT trả về link file audio
    result = response.json()
    audio_url = result.get("async")
    
    if not audio_url:
        raise Exception("Không nhận được link audio từ FPT")
        
    print(f"Link audio tạm thời: {audio_url}")

    # 2. Tải về file audio
    download_headers = {
        "User-Agent": "Mozilla/5.0"
    }

    # Retry tối đa 10 lần (~10–15 giây)
    audio_data = None
    max_retries = 10
    for i in range(max_retries):
        r = requests.get(audio_url, headers=download_headers)
        if r.status_code == 200:
            audio_data = r.content
            print(f"✅ Audio sẵn sàng sau {i+1} lần thử")
            break
        elif i < max_retries - 1:
            print(f"Chưa xong (Mã {r.status_code}), chờ thêm 1.5 giây...")
            time.sleep(1.5)

    if audio_data is None:
        raise Exception(f"Audio chưa sẵn sàng sau {max_retries} lần thử")

    with open(outputFilename, "wb") as f:
        f.write(audio_data)

    print(f"✅ Đã lưu audio thành công: {outputFilename}")