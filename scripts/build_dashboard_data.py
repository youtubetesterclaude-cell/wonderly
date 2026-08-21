"""
Aggregates data/upload_log.json + performance_log.json + narration_log.json
into docs/data.json -- the single file the dashboard (docs/index.html) fetches.

Run this after main_pipeline.py and after track.py so the dashboard always
reflects the latest state. Both workflows call this and commit docs/data.json
alongside the data/ files.
"""
import json
import os
import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")

UPLOAD_LOG_PATH = os.path.join(DATA_DIR, "upload_log.json")
PERF_LOG_PATH = os.path.join(DATA_DIR, "performance_log.json")
NARRATION_LOG_PATH = os.path.join(DATA_DIR, "narration_log.json")
NICHES_PATH = os.path.join(DATA_DIR, "niches.json")
OUTPUT_PATH = os.path.join(DOCS_DIR, "data.json")


def _load(path, default):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def build():
    uploads = _load(UPLOAD_LOG_PATH, {"videos": []})["videos"]
    perf = _load(PERF_LOG_PATH, {"videos": []})["videos"]
    narration = _load(NARRATION_LOG_PATH, {"entries": []})["entries"]
    niches = _load(NICHES_PATH, {"niches": []})["niches"]

    niche_labels = {n["id"]: n["label"] for n in niches}
    perf_by_id = {v["video_id"]: v for v in perf}

    videos = []
    for u in sorted(uploads, key=lambda x: x["published_date"], reverse=True)[:30]:
        stats = perf_by_id.get(u["video_id"])
        videos.append({
            "video_id": u["video_id"],
            "title": u["title"],
            "niche_label": niche_labels.get(u["niche_id"], u["niche_id"]),
            "published_date": u["published_date"],
            "url": f"https://youtube.com/watch?v={u['video_id']}",
            "views": stats["views"] if stats else None,
            "likes": stats["likes"] if stats else None,
        })

    # simple per-niche summary for the stats section
    niche_summary = []
    for n in niches:
        tracked = [v for v in perf if v["niche_id"] == n["id"]]
        if tracked:
            avg_views = sum(v["views"] for v in tracked) / len(tracked)
        else:
            avg_views = None
        niche_summary.append({
            "id": n["id"],
            "label": n["label"],
            "format": n.get("format", "standard"),
            "video_count": len([u for u in uploads if u["niche_id"] == n["id"]]),
            "avg_views": round(avg_views) if avg_views is not None else None,
        })

    output = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "videos": videos,
        "narration": list(reversed(narration[-25:])),  # most recent first for the feed
        "niche_summary": niche_summary,
    }

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {OUTPUT_PATH} ({len(videos)} videos, {len(narration)} narration entries)")


if __name__ == "__main__":
    build()
