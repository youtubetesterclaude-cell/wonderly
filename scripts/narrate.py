"""
Builds a short, plain-English explanation of what the pipeline is doing and
why -- the "this isn't working so I'm gonna try this next" narration. Uses
templates (not another API call) so it's fast, free, and can't hallucinate
about its own decision.

Logs each entry to data/narration_log.json (rolling cap) so the dashboard
can display a running feed of these.
"""
import json
import os
import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
NARRATION_LOG_PATH = os.path.join(DATA_DIR, "narration_log.json")
MAX_LOG_ENTRIES = 100


def describe_choice(niche: dict, scores: dict, was_exploration: bool) -> str:
    chosen_score = scores.get(niche["id"], 0.5)
    format_label = "as a Short" if niche.get("format") == "shorts" else "as a standard video"

    if was_exploration:
        return (f"Trying {niche['label']} {format_label} this run -- giving it a look "
                f"regardless of past performance, just to keep the data fresh and make "
                f"sure nothing gets written off too early.")

    # find the worst-performing niche with enough data to judge, for contrast
    scored_with_data = {k: v for k, v in scores.items() if v != 0.5}
    worst_id = min(scored_with_data, key=scored_with_data.get) if scored_with_data else None

    if chosen_score >= 0.6:
        base = (f"Going with {niche['label']} {format_label} -- it's been one of the "
                f"stronger performers (score {chosen_score:.2f}), so leaning into what's working.")
    elif chosen_score <= 0.35 and len(scored_with_data) > 1:
        base = (f"Giving {niche['label']} {format_label} another shot even though it's "
                f"been underperforming (score {chosen_score:.2f}) -- still within the "
                f"exploration budget, not written off yet.")
    else:
        base = (f"Going with {niche['label']} {format_label} -- score {chosen_score:.2f}, "
                f"roughly middle of the pack.")

    if worst_id and worst_id != niche["id"] and scored_with_data[worst_id] < 0.35:
        base += f" Meanwhile pulling back on the lowest performer for now."

    return base


def log_narration(text: str, niche_id: str = None):
    log = {"entries": []}
    if os.path.exists(NARRATION_LOG_PATH):
        with open(NARRATION_LOG_PATH) as f:
            log = json.load(f)

    log["entries"].append({
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "text": text,
        "niche_id": niche_id,
    })
    log["entries"] = log["entries"][-MAX_LOG_ENTRIES:]  # keep it capped, most recent last

    with open(NARRATION_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


if __name__ == "__main__":
    from allocator import choose_next_niche
    niche, scores, was_exploration = choose_next_niche(return_details=True)
    text = describe_choice(niche, scores, was_exploration)
    print(text)
    log_narration(text, niche["id"])
