import os
import json
import re
from datetime import datetime
from google import genai
from google.genai import types
from google.genai.errors import APIError

# --- GEMINI CLIENT SETUP ---
try:
    client = genai.Client()  # Lấy key từ biến môi trường GEMINI_API_KEY
    model = "gemini-3-pro-preview"
except Exception as e:
    print(f"Lỗi khởi tạo Gemini Client: {e}")
    client = None
    model = None

log_directory = ".logs/gpt_logs"

# --- PROMPT SYSTEM ---
prompt = """# Instructions

Given the following video script and timed captions, extract three visually concrete and specific keywords for each time segment that can be used to search for background videos. The keywords should be short and capture the main essence of the sentence. They can be synonyms or related terms. If a caption is vague or general, consider the next timed caption for more context. If a keyword is a single word, try to return a two-word keyword that is visually concrete. If a time frame contains two or more important pieces of information, divide it into shorter time frames with one keyword each. Ensure that the time periods are strictly consecutive and cover the entire length of the video. Each keyword should cover between 2-4 seconds. The output should be in JSON format, like this: [[[t1, t2], ["keyword1", "keyword2", "keyword3"]], [[t2, t3], ["keyword4", "keyword5", "keyword6"]], ...]. Please handle all edge cases, such as overlapping time segments, vague or general captions, and single-word keywords.

Return ONLY valid JSON with no comments, no trailing commas, no backticks. Escape all internal quotes properly.
"""

# -----------------------------
# GEMINI CALL
# -----------------------------
def call_Gemini(script, captions_timed):
    user_content = f"Script: {script}\nTimed Captions:{''.join(map(str, captions_timed))}"
    try:
        response = client.models.generate_content(
            model=model,
            contents=[types.Content(role="user", parts=[types.Part(text=user_content)])],
            config=types.GenerateContentConfig(
                temperature=1.0,
                system_instruction=prompt,
                response_mime_type="application/json",
                response_schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "number"},
                            "end": {"type": "number"},
                            "keywords": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["start", "end", "keywords"]
                    }
                }
            )
        )
    except APIError as e:
        print(f"Lỗi API Gemini: {e}")
        return ""
    except Exception as e:
        print(f"Lỗi không xác định trong Gemini call: {e}")
        return ""

    if hasattr(response, "text") and response.text.strip():
        return response.text.strip()
    else:
        try:
            return response.candidates[0].content.parts[0].text.strip()
        except:
            print("Không thể lấy nội dung từ Gemini response.")
            return ""

# -----------------------------
# PARSE TIMED CAPTIONS + PEXELS KEYWORDS
# -----------------------------
def getVideoSearchQueriesTimed(script_json, timed_captions, use_gemini=False):
    """
    Map từng timed caption sang keywords Pexels.
    Nếu use_gemini=True thì refine bằng Gemini.
    """
    if not timed_captions:
        print("Lỗi: timed_captions rỗng.")
        return None

    search_terms = []
    parts = script_json.get("script_parts", [])
    part_idx = 0

    for (start, end), caption_text in timed_captions:
        if part_idx >= len(parts):
            break
        keywords = parts[part_idx].get("pexels_keywords", "")

        if use_gemini and client:
            gemini_out = call_Gemini(script_json, [[(start, end), caption_text]])
            try:
                gemini_json = json.loads(gemini_out)
                if gemini_json and "keywords" in gemini_json[0]:
                    keywords = ", ".join(gemini_json[0]["keywords"])
            except:
                pass

        search_terms.append({
            "start": start,
            "end": end,
            "keywords": [k.strip() for k in keywords.split(",") if k.strip()]
        })
        part_idx += 1

    return search_terms

# -----------------------------
# MAP SCRIPT -> PEXELS VIDEO
# -----------------------------
def map_script_to_pexels(script_json, timed_captions, use_gemini=False):
    """
    Map từng segment sang video Pexels dựa trên keywords.
    Trả về dạng: [{'time':[start,end], 'media':{'type':'video','url':...}}, ...]
    """
    search_terms = getVideoSearchQueriesTimed(script_json, timed_captions, use_gemini)
    mapped_videos = []
    for seg in search_terms:
        keywords = " ".join(seg["keywords"])
        video_url = search_pexels_video(keywords)  # Placeholder
        mapped_videos.append({
            "time": [seg["start"], seg["end"]],
            "media": {"type": "video", "url": video_url}
        })
    return mapped_videos

# -----------------------------
# PEXELS SEARCH PLACEHOLDER
# -----------------------------
def search_pexels_video(keywords):
    """
    Placeholder: tìm video Pexels theo từ khóa.
    TODO: Gọi API Pexels thật với API Key.
    """
    # Ví dụ demo trả về None
    return None

# -----------------------------
# MERGE EMPTY INTERVALS
# -----------------------------
def merge_empty_intervals(segments):
    """
    Merge consecutive segments where 'media' is None.
    Input: segments = [
        {'time': [0,1], 'media': {...}}, 
        {'time': [1,2], 'media': None}, 
        ...
    ]
    Output: segments merged without consecutive None intervals.
    """
    merged = []
    for seg in segments:
        if seg['media'] is None:
            if merged and merged[-1]['media'] is not None:
                # mở rộng thời gian của segment trước
                merged[-1]['time'][1] = seg['time'][1]
            else:
                merged.append(seg)
        else:
            merged.append(seg)
    return merged
