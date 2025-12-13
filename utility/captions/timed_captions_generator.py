import re
import unicodedata
import difflib
from whisper_timestamped import load_model, transcribe_timestamped


# =======================
# MAIN
# =======================

def generate_timed_captions(
    audio_filename,
    script_text,
    model_size="medium"
):
    model = load_model(model_size)

    whisper_result = transcribe_timestamped(
        model,
        audio_filename,
        verbose=False,
        fp16=False
    )

    whisper_words = extract_whisper_words(whisper_result)
    script_phrases = split_script_to_phrases(script_text)

    return align_script_phrases_with_time(
        script_phrases,
        whisper_words
    )


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
