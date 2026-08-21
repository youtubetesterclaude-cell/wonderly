"""Generate a specific video topic within a chosen niche, using Gemini (free tier)."""
import os
import json
from feedback import load_feedback
from gemini_client import generate_with_retry

RECENT_TOPICS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "recent_topics.json")


def _load_recent_topics(niche_id, limit=15):
    if not os.path.exists(RECENT_TOPICS_PATH):
        return []
    with open(RECENT_TOPICS_PATH) as f:
        all_topics = json.load(f)
    return [t["topic"] for t in all_topics if t["niche_id"] == niche_id][-limit:]


def _save_topic(niche_id, topic):
    all_topics = []
    if os.path.exists(RECENT_TOPICS_PATH):
        with open(RECENT_TOPICS_PATH) as f:
            all_topics = json.load(f)
    all_topics.append({"niche_id": niche_id, "topic": topic})
    with open(RECENT_TOPICS_PATH, "w") as f:
        json.dump(all_topics, f, indent=2)


def generate_topic(niche: dict) -> str:
    recent = _load_recent_topics(niche["id"])
    avoid_clause = ""
    if recent:
        avoid_clause = "\n\nAvoid repeating or closely resembling these already-used topics:\n- " + "\n- ".join(recent)

    feedback = load_feedback()
    feedback_clause = f"\n\nAlso factor in this feedback from the channel owner:\n{feedback}" if feedback else ""

    prompt = f"""Give me one specific, attention-grabbing video topic about {niche['topic_prompt']}.

Respond with ONLY the topic as a single sentence, no preamble, no quotes, no numbering.
It should be specific enough to write a 60-second script about, and phrased in a way
that would make someone stop scrolling (curiosity gap, surprising claim, etc.) without
being clickbait/false.{avoid_clause}{feedback_clause}"""

    topic = generate_with_retry(prompt)
    _save_topic(niche["id"], topic)
    return topic


if __name__ == "__main__":
    import sys
    from allocator import load_niches
    niche = load_niches()[0]
    print(generate_topic(niche))
