import os 
import requests
from utility.utils import log_response,LOG_TYPE_PEXEL

PEXELS_API_KEY = os.environ.get("PEXELS_KEY")

def search_videos(query_string, orientation_landscape=True):
   
    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": PEXELS_API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    params = {
        "query": query_string,
        "orientation": "landscape" if orientation_landscape else "portrait",
        "per_page": 15
    }

    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()
    log_response(LOG_TYPE_PEXEL,query_string,response.json())
   
    return json_data
def getBestVideo(query_string, orientation_landscape=True, used_vids=None):
    if used_vids is None:
        used_vids = set()
    else:
        used_vids = set(used_vids)  # ensure it's always a set

    vids = search_videos(query_string, orientation_landscape)
    print(vids)

    if not isinstance(vids, dict) or "videos" not in vids:
        return None

    videos = vids.get("videos", [])
    if not videos:
        return None

    def is_landscape(video):
        w = video.get("width", 0)
        h = video.get("height", 0)
        return w >= 1920 and h >= 1080 and abs(w/h - 16/9) < 0.01

    def is_portrait(video):
        w = video.get("width", 0)
        h = video.get("height", 0)
        return h >= 1920 and w >= 1080 and abs(h/w - 16/9) < 0.01

    if orientation_landscape:
        filtered_videos = [v for v in videos if is_landscape(v)]
    else:
        filtered_videos = [v for v in videos if is_portrait(v)]

    if not filtered_videos:
        return None

    sorted_videos = sorted(filtered_videos, key=lambda x: abs(15 - int(x.get("duration", 0))))

    for video in sorted_videos:
        for f in video.get("video_files", []):
            link = f.get("link")
            if not link:
                continue

            w, h = f.get("width"), f.get("height")
            base = link.split(".hd")[0]

            if base in used_vids:
                continue

            if orientation_landscape and w == 1920 and h == 1080:
                used_vids.add(base)
                return link

            if not orientation_landscape and w == 1080 and h == 1920:
                used_vids.add(base)
                return link

    return None


def generate_video_url(timed_video_searches,video_server):
        timed_video_urls = []
        if video_server == "pexel":
            used_links = []
            for (t1, t2), search_terms in timed_video_searches:
                url = ""
                for query in search_terms:
                  
                    url = getBestVideo(query, orientation_landscape=True, used_vids=used_links)
                    if url:
                        used_links.append(url.split('.hd')[0])
                        break
                timed_video_urls.append([[t1, t2], url])
        elif video_server == "stable_diffusion":
            timed_video_urls = get_images_for_video(timed_video_searches)

        return timed_video_urls
