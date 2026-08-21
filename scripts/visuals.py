"""Fetch matching stock video clips from Pexels (free API) for the b-roll."""
import os
import random
import requests

PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]
HEADERS = {"Authorization": PEXELS_API_KEY}


def fetch_clips(keywords: list[str], count: int, out_dir: str, orientation: str = "landscape") -> list[str]:
    """Downloads `count` short clips matching the keywords.
    orientation: "landscape" or "portrait" -- matches this to Pexels' own
    orientation filter so Shorts get footage framed for vertical instead of
    landscape clips getting aggressively center-cropped later."""
    os.makedirs(out_dir, exist_ok=True)
    saved_paths = []
    tried_urls = set()
    pexels_orientation = "portrait" if orientation == "portrait" else "landscape"

    attempts = 0
    while len(saved_paths) < count and attempts < count * 4:
        attempts += 1
        keyword = random.choice(keywords)
        resp = requests.get(
            "https://api.pexels.com/videos/search",
            headers=HEADERS,
            params={"query": keyword, "per_page": 10, "orientation": pexels_orientation},
        )
        resp.raise_for_status()
        results = resp.json().get("videos", [])
        if not results:
            continue
        # Pexels already ranks by relevance -- sample from the top few results
        # rather than the whole page, so clips stay on-topic instead of drifting
        # into loosely-related matches further down the list.
        top_results = results[:5]
        video = random.choice(top_results)
        # pick a moderate-resolution file (avoid 4K to keep downloads/processing fast)
        files = sorted(video["video_files"], key=lambda f: f.get("width", 0))
        candidates = [f for f in files if 1000 <= f.get("width", 0) <= 1920] or files
        file_info = candidates[len(candidates) // 2]
        url = file_info["link"]
        if url in tried_urls:
            continue
        tried_urls.add(url)

        video_resp = requests.get(url)
        path = os.path.join(out_dir, f"clip_{len(saved_paths)}.mp4")
        with open(path, "wb") as f:
            f.write(video_resp.content)
        saved_paths.append(path)

    return saved_paths


if __name__ == "__main__":
    paths = fetch_clips(["space", "galaxy"], count=3, out_dir="/tmp/clips")
    print(paths)
