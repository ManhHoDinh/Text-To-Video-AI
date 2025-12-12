import os
import time
import requests
from utility.utils import log_response, LOG_TYPE_PEXEL


# ================================
#   PEXELS CONFIG
# ================================
PEXELS_API_KEY = os.environ.get("PEXELS_KEY")


# ================================
#   REQUEST WITH RETRY
# ================================
def pexels_search(query, retries=3):
    """Call Pexels API with retry for TikTok portrait videos."""
    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": PEXELS_API_KEY,
        "User-Agent": "Mozilla/5.0"
    }
    params = {
        "query": query,
        "orientation": "portrait",
        "per_page": 20
    }

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=8)

            if response.status_code == 429:  # rate limit
                time.sleep(1.3)
                continue

            if response.status_code >= 500:  # server error
                time.sleep(1)
                continue

            json_data = response.json()
            log_response(LOG_TYPE_PEXEL, query, json_data)
            return json_data

        except Exception:
            time.sleep(1)

    return None


# ================================
#   CHECK RATIO 9:16
# ================================
def is_tiktok_ratio(w, h):
    """Check if width/height ≈ 9:16."""
    if not w or not h:
        return False
    ratio = h / w
    return 1.70 <= ratio <= 1.90  # khoảng xấp xỉ 9:16


# ================================
#   GET BEST VIDEO (ONLY PEXELS)
# ================================
def getBestVideo(query_list, used_vids=None, target_duration=5):
    """
    Select best TikTok 9:16 video:
        - correct ratio (9:16)
        - avoid duplicate videos
        - prefer full HD 1080x1920
        - duration closest to target_duration
    """

    if used_vids is None:
        used_vids = set()
    else:
        used_vids = set(used_vids)

    if not isinstance(query_list, list):
        query_list = [query_list]

    for query in query_list:

        data = pexels_search(query)
        if not data or "videos" not in data:
            continue

        videos = data.get("videos", [])
        if not videos:
            continue

        # Lọc các video đúng tỷ lệ 9:16
        valid = []
        for v in videos:
            w = v.get("width", 0)
            h = v.get("height", 0)

            if is_tiktok_ratio(w, h):
                valid.append(v)

        if not valid:
            continue

        # Sắp xếp theo độ gần target duration nhất
        valid.sort(key=lambda x: abs(target_duration - int(x.get("duration", 0))))

        # Lấy video phù hợp nhất
        for v in valid:
            for f in v.get("video_files", []):
                link = f.get("link")
                if not link:
                    continue

                w = f.get("width")
                h = f.get("height")
                base = link.split(".hd")[0]  # loại bỏ biến thể URL để nhận diện duplicate

                if base in used_vids:
                    continue

                # Ưu tiên 1080x1920
                if w == 1080 and h == 1920:
                    used_vids.add(base)
                    return link

                # Chấp nhận bất kỳ 9:16 video nào
                if is_tiktok_ratio(w, h):
                    used_vids.add(base)
                    return link

    return None


# ================================
#   GENERATE FINAL RESULT
# ================================
import os
import time
import requests
from utility.utils import log_response, LOG_TYPE_PEXEL


# ================================
#   PEXELS CONFIG
# ================================
PEXELS_API_KEY = os.environ.get("PEXELS_KEY")


# ================================
#   REQUEST WITH RETRY
# ================================
def pexels_search(query, retries=3):
    """Call Pexels API with retry for TikTok portrait videos."""
    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": PEXELS_API_KEY,
        "User-Agent": "Mozilla/5.0"
    }
    params = {
        "query": query,
        "orientation": "portrait",
        "per_page": 20
    }

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=8)

            if response.status_code == 429:  # rate limit
                time.sleep(1.3)
                continue

            if response.status_code >= 500:  # server error
                time.sleep(1)
                continue

            json_data = response.json()
            log_response(LOG_TYPE_PEXEL, query, json_data)
            return json_data

        except Exception:
            time.sleep(1)

    return None


# ================================
#   CHECK RATIO 9:16
# ================================
def is_tiktok_ratio(w, h):
    """Check if width/height ≈ 9:16."""
    if not w or not h:
        return False
    ratio = h / w
    return 1.70 <= ratio <= 1.90  # khoảng xấp xỉ 9:16


# ================================
#   GET BEST VIDEO (ONLY PEXELS)
# ================================
def getBestVideo(query_list, used_vids=None, target_duration=5):
    """
    Select best TikTok 9:16 video:
        - correct ratio (9:16)
        - avoid duplicate videos
        - prefer full HD 1080x1920
        - duration closest to target_duration
    """

    if used_vids is None:
        used_vids = set()
    else:
        used_vids = set(used_vids)

    if not isinstance(query_list, list):
        query_list = [query_list]

    for query in query_list:

        data = pexels_search(query)
        if not data or "videos" not in data:
            continue

        videos = data.get("videos", [])
        if not videos:
            continue

        # Lọc các video đúng tỷ lệ 9:16
        valid = []
        for v in videos:
            w = v.get("width", 0)
            h = v.get("height", 0)

            if is_tiktok_ratio(w, h):
                valid.append(v)

        if not valid:
            continue

        # Sắp xếp theo độ gần target duration nhất
        valid.sort(key=lambda x: abs(target_duration - int(x.get("duration", 0))))

        # Lấy video phù hợp nhất
        for v in valid:
            for f in v.get("video_files", []):
                link = f.get("link")
                if not link:
                    continue

                w = f.get("width")
                h = f.get("height")
                base = link.split(".hd")[0]  # loại bỏ biến thể URL để nhận diện duplicate

                if base in used_vids:
                    continue

                # Ưu tiên 1080x1920
                if w == 1080 and h == 1920:
                    used_vids.add(base)
                    return link

                # Chấp nhận bất kỳ 9:16 video nào
                if is_tiktok_ratio(w, h):
                    used_vids.add(base)
                    return link

    return None


# ================================
#   GENERATE FINAL RESULT
# ================================
def generate_video_url(timed_video_searches):
    """
    timed_video_searches = [
      {
        "start": 0,
        "end": 3.3,
        "keywords": ["beer", "belly"]
      },
      ...
    ]
    """

    timed_video_urls = []
    used = set()  # tránh duplicate video

    for item in timed_video_searches:

        # --- Lấy thông số ---
        t1 = float(item.get("start", 0))
        t2 = float(item.get("end", 0))
        keywords = item.get("keywords", [])

        duration = t2 - t1

        # --- Gọi Pexels ---
        url = getBestVideo(
            query_list=keywords,
            used_vids=used,
            target_duration=duration
        )

        # --- Ghi vào danh sách ---
        timed_video_urls.append([[t1, t2], url])

    return timed_video_urls
