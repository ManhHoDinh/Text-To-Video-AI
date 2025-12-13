import re
import unicodedata
import difflib
from whisper_timestamped import load_model, transcribe_timestamped

# =======================
# MAIN
# =======================

def generate_timed_captions(audio_filename, script_json, model_size="medium"):
    """
    Tạo caption có timestamp dựa trên audio và script mới dạng JSON.
    
    Args:
        audio_filename (str): File audio cần tạo captions.
        script_json (dict): Script dạng mới {title, script_parts, call_to_action}.
        model_size (str): Kích thước model Whisper.
    
    Returns:
        list: [(start_end_tuple, phrase), ...]
    """
    model = load_model(model_size)

    # Transcribe audio với Whisper
    whisper_result = transcribe_timestamped(
        model,
        audio_filename,
        verbose=False,
        fp16=False
    )

    # 1️⃣ Trích xuất từ JSON script → chuỗi text
    script_text = extract_text_from_json(script_json)

    # 2️⃣ Tách script thành các câu/phrases
    script_phrases = split_script_to_phrases(script_text)

    # 3️⃣ Lấy danh sách words từ Whisper
    whisper_words = extract_whisper_words(whisper_result)

    # 4️⃣ Align script phrases với thời gian
    return align_script_phrases_with_time(script_phrases, whisper_words)


# =======================
# CHUYỂN JSON → CHUỖI
# =======================

def extract_text_from_json(script_json: dict) -> str:
    """
    Nối toàn bộ text từ script JSON (script_parts + call_to_action)
    thành chuỗi duy nhất.
    """
    all_text = " ".join([
        part.get("text", "").strip()
        for part in script_json.get("script_parts", [])
        if part.get("text")
    ])

    call_to_action = script_json.get("call_to_action", "").strip()
    if call_to_action:
        all_text += f". {call_to_action}"

    return all_text.strip()


# =======================
# SCRIPT → PHRASES
# =======================

def split_script_to_phrases(script_text):
    """
    Cắt script theo đúng nhịp đã viết cho TTS
    """
    script_text = unicodedata.normalize("NFC", script_text)

    lines = []
    for line in script_text.split("\n"):
        parts = re.split(r"[.!?]", line)
        for p in parts:
            p = p.strip()
            if p:
                lines.append(p)

    return lines


def tokenize(text):
    return re.findall(
        r"[0-9A-Za-zÀ-ỹăâđêôơưĂÂÊÔƠƯĐà-ỹ]+",
        text.lower()
    )


# =======================
# WHISPER WORDS
# =======================

def extract_whisper_words(analysis):
    words = []
    for seg in analysis.get("segments", []):
        for w in seg.get("words", []):
            if "start" in w and "end" in w:
                words.append({
                    "text": normalize_word(w["text"]),
                    "start": w["start"],
                    "end": w["end"]
                })
    return words


# =======================
# NORMALIZE
# =======================

WORD_FIX = {
    "hách": "hack",
    "trùng": "trùm",
    "lau": "lao",
    "hát": "hạt"
}


def normalize_word(word):
    word = unicodedata.normalize("NFC", word)
    word = re.sub(
        r"[^0-9A-Za-zÀ-ỹăâđêôơưĂÂÊÔƠƯĐà-ỹ]",
        "",
        word
    )
    return WORD_FIX.get(word.lower(), word.lower())


# =======================
# ALIGN SCRIPT ↔ TIME
# =======================

def align_script_phrases_with_time(script_phrases, whisper_words):
    captions = []
    w_idx = 0

    for phrase in script_phrases:
        tokens = tokenize(phrase)
        if not tokens:
            continue

        start_time = None
        end_time = None
        matched = 0

        for i in range(w_idx, len(whisper_words)):
            score = difflib.SequenceMatcher(
                None,
                whisper_words[i]["text"],
                tokens[matched]
            ).ratio()

            if score > 0.7:
                if start_time is None:
                    start_time = whisper_words[i]["start"]
                end_time = whisper_words[i]["end"]
                matched += 1
                w_idx = i + 1

                if matched >= len(tokens):
                    break

        if start_time is None:
            continue

        captions.append((
            (round(start_time, 2), round(end_time, 2)),
            phrase
        ))

    return captions
