# =========================================
#   PEXELS MEDIA SELECTOR (VIDEO + IMAGE 4K MAX)
# =========================================
import os
import time
import requests
from utility.utils import log_response, LOG_TYPE_PEXEL

# ================================
# PEXELS CONFIG
# ================================
PEXELS_API_KEY = os.environ.get("PEXELS_KEY")
if not PEXELS_API_KEY:
    raise RuntimeError("Missing PEXELS_KEY environment variable")


# ================================
# SAFE REQUEST
# ================================
def safe_request(url, headers, params=None, retries=3):
    for _ in range(retries):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=8)
            if r.status_code == 429:  # rate limit
                time.sleep(1.2)
                continue
            if r.status_code >= 500:  # server error
                time.sleep(1)
                continue
            return r
        except Exception:
            time.sleep(1)
    return None


# ================================
# CHECK RATIO 9:16
# ================================
def is_tiktok_ratio(w, h):
    if not w or not h:
        return False
    ratio = h / w
    return 1.70 <= ratio <= 1.90


# ================================
# PEXELS VIDEO SEARCH
# ================================
def pexels_video_search(query):
    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": PEXELS_API_KEY,
        "User-Agent": "Mozilla/5.0"
    }
    params = {
        "query": query,
        "orientation": "portrait",
        "per_page": 30
    }

    r = safe_request(url, headers, params)
    if not r:
        return None

    data = r.json()
    log_response(LOG_TYPE_PEXEL, query, data)
    return data


# ================================
# PEXELS IMAGE SEARCH (4K MAX)
# ================================
def pexels_image_search(query):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "orientation": "portrait",
        "per_page": 20,
        "size": "large"
    }

    r = safe_request(url, headers, params)
    if not r:
        return None

    data = r.json()
    log_response(LOG_TYPE_PEXEL, query, data)
    return data


# ================================
# GET BEST VIDEO (QUALITY FIRST)
# ================================
def getBestVideo(query_list, used=None, target_duration=5):
    if used is None:
        used = set()
    else:
        used = set(used)

    if not isinstance(query_list, list):
        query_list = [query_list]

    for query in query_list:
        data = pexels_video_search(query)
        if not data or "videos" not in data:
            continue

        candidates = []
        for v in data["videos"]:
            duration = int(v.get("duration", 0))
            for f in v.get("video_files", []):
                w, h = f.get("width"), f.get("height")
                if not is_tiktok_ratio(w, h):
                    continue
                link = f.get("link")
                if not link:
                    continue
                base = link.split("?")[0]
                if base in used:
                    continue
                candidates.append({
                    "link": link,
                    "base": base,
                    "pixels": (w or 0) * (h or 0),
                    "fps": f.get("fps", 0),
                    "size": f.get("file_size", 0),
                    "duration_diff": abs(duration - target_duration)
                })

        if not candidates:
            continue

        # SORT: chất lượng cao nhất, fps, size, duration
        candidates.sort(
            key=lambda x: (
                -x["pixels"],
                -x["size"],
                -x["fps"],
                x["duration_diff"]
            )
        )

        best = candidates[0]
        used.add(best["base"])
        return {
            "type": "video",
            "url": best["link"],
            "resolution": f"{int((best['pixels']**0.5))}x{int((best['pixels']**0.5*16/9))}"
        }

    return None


# ================================
# GET BEST IMAGE (ULTRA QUALITY)
# ================================
def getUltraQualityImage(query_list, used=None):
    if used is None:
        used = set()
    else:
        used = set(used)

    if not isinstance(query_list, list):
        query_list = [query_list]

    for query in query_list:
        data = pexels_image_search(query)
        if not data or "photos" not in data:
            continue

        candidates = []
        for p in data["photos"]:
            src = p.get("src", {})
            url = src.get("original")  # max quality
            if not url:
                continue
            base = url.split("?")[0]
            if base in used:
                continue
            w = p.get("width", 0)
            h = p.get("height", 0)
            candidates.append({
                "url": url,
                "base": base,
                "pixels": w * h,
                "width": w,
                "height": h
            })

        if not candidates:
            continue

        # sort theo độ phân giải + ưu tiên dọc
        candidates.sort(
            key=lambda x: (
                -x["pixels"],
                -x["height"],
                -x["width"]
            )
        )

        best = candidates[0]
        used.add(best["base"])
        return {
            "type": "image",
            "url": best["url"],
            "resolution": f"{best['width']}x{best['height']}"
        }

    return None


# ================================
# FINAL MEDIA GENERATOR
# ================================
def generate_video_url(timed_video_searches):
    """
    timed_video_searches = [
        {"start": 0, "end": 3.3, "keywords": ["space", "universe"]},
        ...
    ]
    """

    results = []
    used_assets = set()

    for item in timed_video_searches:
        t1 = float(item.get("start", 0))
        t2 = float(item.get("end", 0))
        keywords = item.get("keywords", [])

        duration = max(1.0, t2 - t1)

        # 1️⃣ Try high-quality video
        media = getBestVideo(keywords, used=used_assets, target_duration=duration)

        # 2️⃣ Fallback → Ultra quality image
        if not media:
            media = getUltraQualityImage(keywords, used=used_assets)

        results.append({
            "time": [t1, t2],
            "media": media
        })

    return results
