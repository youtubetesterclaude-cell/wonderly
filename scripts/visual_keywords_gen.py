"""
Generates specific, topic-relevant stock-footage search terms via Gemini, so
background visuals actually match what the video is about instead of just
falling back to the niche's generic keywords (e.g. "space", "galaxy") for
every single video in that niche regardless of the actual topic.
"""
from gemini_client import generate_with_retry


def generate_visual_keywords(topic: str, fallback: list[str]) -> list[str]:
    prompt = f"""Given this video topic: "{topic}"

List 5 short, concrete search terms (2-4 words each) for finding matching
stock video footage. Focus on specific, visually filmable subjects, objects,
scenes, actions, or locations mentioned or implied by the topic -- not
abstract ideas that can't be filmed.

Respond with ONLY a comma-separated list, no numbering, no explanation, no quotes."""

    try:
        raw = generate_with_retry(prompt)
        keywords = [k.strip() for k in raw.split(",") if k.strip()]
        if len(keywords) >= 3:
            return keywords
        print(f"[visual_keywords_gen] Only got {len(keywords)} usable keywords, "
              f"falling back to niche defaults.")
    except Exception as e:
        print(f"[visual_keywords_gen] Failed to generate topic-specific keywords, "
              f"falling back to niche defaults: {e}")
    return fallback


if __name__ == "__main__":
    result = generate_visual_keywords(
        "In 1942, a U.S. Navy blimp crash-landed with its two pilots vanished without a trace",
        fallback=["ancient ruins", "old map"],
    )
    print(result)
