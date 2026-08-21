"""
Pull performance data for previously-uploaded videos via YouTube Analytics
API, and update data/performance_log.json so allocator.py can use it.

Run this daily via workflows/track_performance.yml. Videos are tracked once
they're at least 48 hours old (early view counts are noisy/misleading).
"""
import os
import json
import datetime
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly"]
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
UPLOAD_LOG_PATH = os.path.join(DATA_DIR, "upload_log.json")
PERF_LOG_PATH = os.path.join(DATA_DIR, "performance_log.json")


def _get_credentials():
    return Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _fetch_stats(youtube_analytics, video_id: str, published_date: str):
    end_date = datetime.date.today().isoformat()
    resp = youtube_analytics.reports().query(
        ids="channel==MINE",
        startDate=published_date,
        endDate=end_date,
        metrics="views,likes,dislikes,averageViewPercentage,comments",
        filters=f"video=={video_id}",
    ).execute()
    rows = resp.get("rows")
    if not rows:
        return None
    views, likes, dislikes, avg_view_pct, comments = rows[0]
    like_ratio = likes / max(views, 1)
    return {
        "views": views,
        "likes": likes,
        "like_ratio": round(like_ratio, 4),
        "avg_view_pct": round(avg_view_pct / 100, 4),
        "comments": comments,
    }


def update_performance_log():
    upload_log = _load_json(UPLOAD_LOG_PATH, {"videos": []})
    perf_log = _load_json(PERF_LOG_PATH, {"videos": []})
    tracked_ids = {v["video_id"] for v in perf_log["videos"]}

    creds = _get_credentials()
    yt_analytics = build("youtubeAnalytics", "v2", credentials=creds)

    today = datetime.date.today()
    updated = 0

    for entry in upload_log["videos"]:
        video_id = entry["video_id"]
        published = datetime.date.fromisoformat(entry["published_date"])
        age_hours = (datetime.datetime.now() - datetime.datetime.combine(published, datetime.time())).total_seconds() / 3600

        if age_hours < 48:
            continue  # too early, skip -- will pick it up on a later run

        stats = _fetch_stats(yt_analytics, video_id, entry["published_date"])
        if stats is None:
            continue

        record = {
            "video_id": video_id,
            "niche_id": entry["niche_id"],
            "title": entry["title"],
            "published_date": entry["published_date"],
            **stats,
        }

        if video_id in tracked_ids:
            # update existing record
            perf_log["videos"] = [record if v["video_id"] == video_id else v for v in perf_log["videos"]]
        else:
            perf_log["videos"].append(record)
        updated += 1

    _save_json(PERF_LOG_PATH, perf_log)
    print(f"Updated performance data for {updated} video(s).")


if __name__ == "__main__":
    update_performance_log()
