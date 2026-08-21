"""
Weighted-random bandit allocator.

Reads data/niches.json (base config) and data/performance_log.json (history),
computes a performance score per niche, and picks the next niche to produce a
video for -- weighted toward better performers, but never fully abandoning
weaker ones (epsilon-greedy style exploration so a niche can recover if the
first few videos were unlucky).
"""
import json
import random
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
NICHES_PATH = os.path.join(DATA_DIR, "niches.json")
PERF_LOG_PATH = os.path.join(DATA_DIR, "performance_log.json")

EXPLORATION_RATE = 0.20  # 20% of the time, pick a random niche regardless of performance
MIN_VIDEOS_FOR_TRUST = 3  # need at least this many data points before trusting a score


def load_niches():
    with open(NICHES_PATH) as f:
        return json.load(f)["niches"]


def load_performance():
    if not os.path.exists(PERF_LOG_PATH):
        return {"videos": []}
    with open(PERF_LOG_PATH) as f:
        return json.load(f)


def compute_scores(niches, perf):
    """
    Score = weighted combo of normalized views, like ratio, and avg view duration.
    Niches with fewer than MIN_VIDEOS_FOR_TRUST get a neutral default score so
    they aren't judged on too little data.
    """
    scores = {}
    videos_by_niche = {}
    for v in perf["videos"]:
        videos_by_niche.setdefault(v["niche_id"], []).append(v)

    all_views = [v["views"] for v in perf["videos"] if "views" in v]
    max_views = max(all_views) if all_views else 1

    for niche in niches:
        nid = niche["id"]
        vids = videos_by_niche.get(nid, [])
        tracked = [v for v in vids if "views" in v]
        if len(tracked) < MIN_VIDEOS_FOR_TRUST:
            scores[nid] = 0.5  # neutral, unproven
            continue
        avg_views_norm = sum(v["views"] for v in tracked) / len(tracked) / max_views
        avg_like_ratio = sum(v.get("like_ratio", 0) for v in tracked) / len(tracked)
        avg_retention = sum(v.get("avg_view_pct", 0) for v in tracked) / len(tracked)
        scores[nid] = (0.5 * avg_views_norm) + (0.25 * avg_like_ratio) + (0.25 * avg_retention)
    return scores


def choose_next_niche(return_details: bool = False):
    """
    By default returns just the chosen niche dict (backward compatible).
    If return_details=True, returns (chosen_niche, scores_dict, was_exploration)
    so callers (like narrate.py) can explain the decision.
    """
    niches = load_niches()
    perf = load_performance()
    scores = compute_scores(niches, perf)

    if random.random() < EXPLORATION_RATE:
        chosen = random.choice(niches)
        print(f"[allocator] Exploration pick: {chosen['label']}")
        return (chosen, scores, True) if return_details else chosen

    # weighted choice proportional to score (add small epsilon so score=0 niches
    # still have a nonzero chance)
    weighted = [(n, scores.get(n["id"], 0.5) + 0.05) for n in niches]
    total = sum(w for _, w in weighted)
    r = random.uniform(0, total)
    upto = 0
    for n, w in weighted:
        upto += w
        if upto >= r:
            print(f"[allocator] Performance-weighted pick: {n['label']} (score={scores.get(n['id'], 0.5):.3f})")
            return (n, scores, False) if return_details else n
    fallback = weighted[-1][0]
    return (fallback, scores, False) if return_details else fallback


if __name__ == "__main__":
    chosen = choose_next_niche()
    print(json.dumps(chosen, indent=2))
