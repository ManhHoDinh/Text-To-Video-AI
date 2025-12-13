import requests
import time

API_KEY = "7zE1Fuq1p0bKESXNy3WFwIGWsQWQF23I"        # API key FPT AI của bạn
VOICE = "banmai"                 # giọng đọc

def generate_audio(text, outputFilename):
    url = "https://api.fpt.ai/hmi/tts/v5"

    headers = {
        "api_key": API_KEY,
        "voice": VOICE,
        "Cache-Control": "no-cache"
    }

    response = requests.post(
        url,
        headers=headers,
        data=text.encode("utf-8")
    )

    if response.status_code != 200:
        raise Exception("TTS request failed:", response.text)

    # FPT trả về link file audio

    result = response.json()
    audio_url = result.get("async")
    print("Audio URL:", audio_url)

    if not audio_url:
        raise Exception("Không nhận được link audio từ FPT")

    download_headers = {
        "User-Agent": "Mozilla/5.0"
    }

    # Retry tối đa 10 lần (~10–15 giây)
    audio_data = None
    for i in range(10):
        r = requests.get(audio_url, headers=download_headers)
        if r.status_code == 200:
            audio_data = r.content
            print(f"Audio sẵn sàng sau {i+1} lần thử")
            break
        else:
            print(f"Chưa xong ({r.status_code}), chờ thêm...")
            time.sleep(1.5)

    if audio_data is None:
        raise Exception("Audio chưa sẵn sàng sau nhiều lần thử")

    with open(outputFilename, "wb") as f:
        f.write(audio_data)

    print("Đã tạo audio:", outputFilename)
