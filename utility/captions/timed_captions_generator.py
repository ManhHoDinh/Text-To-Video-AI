import whisper_timestamped as whisper
from whisper_timestamped import load_model, transcribe_timestamped
import re
import unicodedata


# =======================
# Load + Transcribe
# =======================
def generate_timed_captions(audio_filename, model_size="medium"):
    model = load_model(model_size)

    gen = transcribe_timestamped(
        model,
        audio_filename,
        verbose=False,
        fp16=False
    )

    return getCaptionsWithTime(gen)



# =======================
# UTILS TỐI ƯU TIẾNG VIỆT
# =======================

# giữ lại toàn bộ chữ tiếng Việt
def clean_word_vi(word):
    word = unicodedata.normalize("NFC", word)
    word = word.strip()
    # giữ chữ cái tiếng Việt / dấu / số
    word = re.sub(r"[^0-9A-Za-zÀ-ỹăâđêôơưÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯĂẠ-ỹ\-\"']", "", word)
    return word


# Danh sách từ "ngắt caption" tự nhiên cho tiếng Việt
VI_BREAK_WORDS = {
    "và", "nhưng", "rồi", "thì", "là", "để", "vì", "do", "nếu", "khi",
    "vậy", "cho", "còn", "cũng", "nên"
}


def split_vietnamese_phrases(words, max_len=20):
    """
    Chia câu tiếng Việt thành các cụm có nghĩa.
    Ưu tiên ngắt ở các từ nối / từ phụ / giới từ.
    """
    chunks = []
    current = []

    for w in words:
        w_clean = clean_word_vi(w)
        if not w_clean:
            continue

        # Nếu đang quá dài → tách luôn
        if sum(len(x) + 1 for x in current) + len(w_clean) > max_len:
            chunks.append(" ".join(current))
            current = [w_clean]
            continue

        current.append(w_clean)

        # Nếu từ thuộc nhóm "điểm ngắt tự nhiên" → tách cụm
        if w_clean.lower() in VI_BREAK_WORDS and len(current) >= 3:
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return chunks



# =======================
# TIMESTAMP MAPPING
# =======================

def getTimestampMapping(whisper_analysis):
    index = 0
    mapping = {}

    for seg in whisper_analysis.get("segments", []):
        for word in seg.get("words", []):
            text = word.get("text", "").strip()
            if not text:
                continue

            end_time = word.get("end", None)
            if end_time is None:
                continue

            new_index = index + len(text) + 1
            mapping[(index, new_index)] = end_time
            index = new_index

    return mapping


def interpolateTime(pos, mapping):
    best = None
    for (start, end), ts in mapping.items():
        if start <= pos <= end:
            return ts
        if end < pos:
            best = ts
    return best



# =======================
# FINALLY — FI NÊU TIẾNG VIỆT
# =======================

def getCaptionsWithTime(whisper_analysis, maxCaptionSize=20):

    mapping = getTimestampMapping(whisper_analysis)
    text = whisper_analysis.get("text", "").strip()
    if not text:
        return []

    raw_words = text.split()
    phrases = split_vietnamese_phrases(raw_words, max_len=maxCaptionSize)

    captions = []
    start_time = 0
    pos = 0

    for phrase in phrases:
        pos += len(phrase) + 1
        end_time = interpolateTime(pos, mapping)

        if end_time is None:
            end_time = start_time + 0.8  # fallback nhỏ

        captions.append(((start_time, end_time), phrase))
        start_time = end_time

    return captions
