"""
Orchestrates one full run of the pipeline:
allocate niche -> topic -> script -> voiceover -> visuals -> assemble ->
thumbnail -> upload -> log it for future tracking.

Usage:
    python main_pipeline.py --once          # run one video, exit
    python main_pipeline.py --dry-run       # do everything except upload
"""
import argparse
import os
import json
import datetime
import shutil
import sys
from dotenv import load_dotenv

load_dotenv()  # reads .env in the project root when running locally; no-op on GitHub Actions (secrets are injected as real env vars there)

sys.path.insert(0, os.path.dirname(__file__))

from allocator import choose_next_niche
from topic_gen import generate_topic
from script_gen import generate_script
from tts_gen import generate_voiceover
from visuals import fetch_clips
from assemble import assemble_video
from thumbnail import generate_thumbnail
from upload import upload_video
from notify import notify
from narrate import describe_choice, log_narration
from visual_keywords_gen import generate_visual_keywords

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
UPLOAD_LOG_PATH = os.path.join(DATA_DIR, "upload_log.json")
WORK_ROOT = "/tmp/pipeline_run"


def log_upload(video_id, niche_id, title):
    log = {"videos": []}
    if os.path.exists(UPLOAD_LOG_PATH):
        with open(UPLOAD_LOG_PATH) as f:
            log = json.load(f)
    log["videos"].append({
        "video_id": video_id,
        "niche_id": niche_id,
        "title": title,
        "published_date": datetime.date.today().isoformat(),
    })
    with open(UPLOAD_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def run_once(dry_run: bool = False):
    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = os.path.join(WORK_ROOT, run_id)
    os.makedirs(work_dir, exist_ok=True)

    print("== 1. Choosing niche ==")
    niche, scores, was_exploration = choose_next_niche(return_details=True)
    is_short = niche.get("format") == "shorts"
    orientation = "portrait" if is_short else "landscape"
    print(f"   -> {niche['label']} ({'Shorts' if is_short else 'standard'})")

    narration = describe_choice(niche, scores, was_exploration)
    print(f"   -> {narration}")
    log_narration(narration, niche["id"])
    notify("Wonderly: starting a new video", narration, tags=["thinking_face"])

    print("== 2. Generating topic ==")
    topic = generate_topic(niche)
    print(f"   -> {topic}")

    print("== 3. Generating script + metadata ==")
    content = generate_script(topic, niche)
    print(f"   -> Title: {content['title']}")

    print("== 4. Generating voiceover ==")
    voice_path = os.path.join(work_dir, "voiceover.mp3")
    generate_voiceover(content["script"], voice_path)

    print("== 5. Fetching visuals ==")
    print("   -> Generating topic-specific search keywords...")
    visual_keywords = generate_visual_keywords(topic, fallback=niche["visual_keywords"])
    print(f"   -> {visual_keywords}")
    clips_dir = os.path.join(work_dir, "clips")
    num_clips = max(3, niche["video_length_seconds"] // 8)
    clip_paths = fetch_clips(visual_keywords, count=num_clips, out_dir=clips_dir, orientation=orientation)
    if not clip_paths:
        raise RuntimeError("No stock clips found -- check Pexels API key / keywords")

    print("== 6. Assembling video ==")
    video_path = os.path.join(work_dir, "final.mp4")
    assemble_video(voice_path, clip_paths, video_path,
                    work_dir=os.path.join(work_dir, "assembly"), orientation=orientation)

    thumb_path = os.path.join(work_dir, "thumbnail.jpg")
    if not is_short:
        print("== 7. Generating thumbnail ==")
        generate_thumbnail(video_path, content["title"], thumb_path, work_dir=work_dir, orientation=orientation)
    else:
        print("== 7. Skipping custom thumbnail (not applicable to Shorts) ==")

    if dry_run:
        print(f"\nDRY RUN complete. Output at: {video_path}")
        return

    print("== 8. Uploading to YouTube ==")
    video_id = upload_video(
        video_path=video_path,
        thumbnail_path=thumb_path,
        title=content["title"],
        description=content["description"],
        tags=content["tags"],
        is_short=is_short,
    )

    log_upload(video_id, niche["id"], content["title"])
    video_url = f"https://youtube.com/watch?v={video_id}"
    print(f"\nDone. {video_url}")

    notify(
        "Wonderly: new video posted",
        f"{content['title']}\n{niche['label']} ({'Short' if is_short else 'standard'})\n{video_url}",
        tags=["tada"],
    )

    # clean up temp working directory
    shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run a single video through the pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Do everything except upload")
    args = parser.parse_args()

    if args.once or args.dry_run:
        try:
            run_once(dry_run=args.dry_run)
        except Exception as e:
            notify(
                "Wonderly: run failed",
                f"{type(e).__name__}: {e}",
                priority="high",
                tags=["x"],
            )
            raise  # still fail the GitHub Actions run so it shows red in the Actions tab
    else:
        print("Specify --once or --dry-run")
