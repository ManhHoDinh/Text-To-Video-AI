from google import genai
from google.genai import types
from google.genai.errors import APIError
import os
import json
import re
from datetime import datetime
# Giả định các hàm utility.utils.log_response, LOG_TYPE_GPT đã được định nghĩa và có sẵn.
# import utility.utils # Bỏ comment nếu bạn cần sử dụng các hàm utility

# --- THIẾT LẬP GEMINI API ---
# Tự động lấy key từ biến môi trường GEMINI_API_KEY
try:
    client = genai.Client() 
    # Chọn mô hình Pro cho tác vụ suy luận phức tạp và định dạng JSON nghiêm ngặt
    model = "gemini-3-pro-preview" 
except Exception as e:
    # Xử lý trường hợp Client không thể khởi tạo (ví dụ: thiếu API Key)
    print(f"Lỗi khởi tạo Gemini Client: {e}")
    client = None
    model = None

log_directory = ".logs/gpt_logs"

# Prompt giữ nguyên, nhưng sẽ được truyền qua system_instruction
prompt = """# Instructions

Given the following video script and timed captions, extract three visually concrete and specific keywords for each time segment that can be used to search for background videos. The keywords should be short and capture the main essence of the sentence. They can be synonyms or related terms. If a caption is vague or general, consider the next timed caption for more context. If a keyword is a single word, try to return a two-word keyword that is visually concrete. If a time frame contains two or more important pieces of information, divide it into shorter time frames with one keyword each. Ensure that the time periods are strictly consecutive and cover the entire length of the video. Each keyword should cover between 2-4 seconds. The output should be in JSON format, like this: [[[t1, t2], ["keyword1", "keyword2", "keyword3"]], [[t2, t3], ["keyword4", "keyword5", "keyword6"]], ...]. Please handle all edge cases, such as overlapping time segments, vague or general captions, and single-word keywords.

For example, if the caption is 'The cheetah is the fastest land animal, capable of running at speeds up to 75 mph', the keywords should include 'cheetah running', 'fastest animal', and '75 mph'. Similarly, for 'The Great Wall of China is one of the most iconic landmarks in the world', the keywords should be 'Great Wall of China', 'iconic landmark', and 'China landmark'.

Important Guidelines:

Use only English in your text queries.
Each search string must depict something visual.
The depictions have to be extremely visually concrete, like rainy street, or cat sleeping.
'emotional moment' <= BAD, because it doesn't depict something visually.
'crying child' <= GOOD, because it depicts something visual.
The list must always contain the most relevant and appropriate query searches.
['Car', 'Car driving', 'Car racing', 'Car parked'] <= BAD, because it's 4 strings.
['Fast car'] <= GOOD, because it's 1 string.
['Un chien', 'une voiture rapide', 'une maison rouge'] <= BAD, because the text query is NOT in English.

Return ONLY valid JSON with no comments, no trailing commas, no backticks. 
Escape all internal quotes properly.
If a string contains quotes, replace them with safer wording instead of escaping.
"""

def call_Gemini(script, captions_timed):
    user_content = f"Script: {script}\nTimed Captions:{''.join(map(str, captions_timed))}"
    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=user_content)]
                )
            ],
            config=types.GenerateContentConfig(
                temperature=1.0,
                system_instruction=prompt,
                response_mime_type="application/json",
                response_schema = {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "number"},
                            "end": {"type": "number"},
                            "keywords": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
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

    # ---- FIX QUAN TRỌNG NHẤT ----
    if hasattr(response, "text") and response.text.strip():
        text = response.text.strip()
    else:
        try:
            text = response.candidates[0].content.parts[0].text.strip()
        except:
            print("Không thể lấy nội dung từ Gemini response.")
            return ""

    # //text = re.sub(r"\s+", " ", text)
    return text

def getVideoSearchQueriesTimed(script, captions_timed):
    """Gọi Gemini và parse JSON trả về dạng:
    [
      {
        "start": 0,
        "end": 2.6,
        "keywords": ["a", "b"]
      },
      ...
    ]
    """
    if not client:
        print("Gemini Client chưa được khởi tạo. Không thể gọi API.")
        return None
    
    if not captions_timed:
        print("Lỗi: captions_timed rỗng.")
        return None
        
    expected_end = captions_timed[-1][0][1]
    out = None
    
    try:
        # 1. Gọi Gemini API
        content = call_Gemini(script, captions_timed)
        if not content:
            print("Lỗi: Gemini API trả về nội dung rỗng.")
            return None
        
        # ============================================
        #  FIX LỖI: content có thể là list, không replace được
        # ============================================
        if isinstance(content, list):
            # Chuyển list thành JSON string
            content = json.dumps(content)

        elif not isinstance(content, str):
            # Các kiểu khác cũng convert về string
            content = str(content)

        # chuẩn hóa JSON (xóa code block và quote)
        content = (
            content.replace("```json", "")
                   .replace("```", "")
                   .replace("'", '"')
        )

        # 2. Parse JSON
        try:
            out = json.loads(content)
        except Exception as e:
            print("Lỗi JSON decode lần 1:", e)
            cleaned = fix_json(content)
            try:
                out = json.loads(cleaned)
            except Exception as e2:
                print("Lỗi JSON sau khi làm sạch:", e2)
                return None

        # 3. Kiểm tra cấu trúc JSON
        if not isinstance(out, list):
            print("JSON không phải danh sách array.")
            return out
        
        for item in out:
            if not isinstance(item, dict):
                print("Lỗi: phần tử JSON không phải object:", item)
                return out
            
            if "start" not in item or "end" not in item or "keywords" not in item:
                print("Lỗi: thiếu key trong object:", item)
                return out
        
        # 4. Kiểm tra end time khớp
        if abs(out[-1]["end"] - expected_end) < 0.05:
            return out
        else:
            print("Cảnh báo: end time cuối không khớp:", out[-1]["end"], "vs", expected_end)
            return out

    except Exception as e:
        print(f"Unhandled error: {e}")
    
    return None



def merge_empty_intervals(segments):
    """Hàm merge giữ nguyên, dùng để xử lý dữ liệu sau API."""
    # Hàm này có logic xử lý danh sách phức tạp. 
    # Nếu lỗi pop vẫn xảy ra, nó có thể là do segments không phải là list, 
    # hoặc một hàm bên ngoài đang gọi pop(a, b) trên kết quả của hàm này.
    merged = []
    i = 0
    while i < len(segments):
        interval, url = segments[i]
        if url is None:
            # Find consecutive None intervals
            j = i + 1
            while j < len(segments) and segments[j][1] is None:
                j += 1
            
            # Merge consecutive None intervals with the previous valid URL
            if i > 0:
                prev_interval, prev_url = merged[-1]
                if prev_url is not None and prev_interval[1] == interval[0]:
                    merged[-1] = [[prev_interval[0], segments[j-1][0][1]], prev_url]
                else:
                    merged.append([interval, prev_url])
            else:
                merged.append([interval, None])
            
            i = j
        else:
            merged.append([interval, url])
            i += 1
    
    return merged