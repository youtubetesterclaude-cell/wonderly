"""Generate a narration script + title + description + tags for a given topic."""
import os
import json
from feedback import load_feedback
from gemini_client import generate_with_retry


def generate_script(topic: str, niche: dict) -> dict:
    feedback = load_feedback()
    feedback_clause = f"\n\nAlso factor in this feedback from the channel owner:\n{feedback}" if feedback else ""

    prompt = f"""Write a short-form YouTube video script (~{niche['video_length_seconds']} seconds
when read aloud at a natural pace, roughly {niche['video_length_seconds'] * 2.5:.0f} words) on this topic:

"{topic}"

Requirements:
- Hook in the first sentence -- no throat-clearing intro
- Conversational, punchy, short sentences -- written to be read aloud by TTS
- End with a soft call-to-action (follow for more / what do you think, comment below)
- Factually accurate -- do not invent statistics or facts you're not confident about

Also generate a YouTube title (under 70 characters, curiosity-driving but not
false/clickbait), a 2-3 sentence description, and 8-10 relevant tags.{feedback_clause}

Respond ONLY with valid JSON in this exact shape, no markdown fences, no preamble:
{{
  "script": "...",
  "title": "...",
  "description": "...",
  "tags": ["...", "..."]
}}"""

    raw = generate_with_retry(prompt)
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)


if __name__ == "__main__":
    from allocator import load_niches
    niche = load_niches()[0]
    result = generate_script("A surprising fact about black holes", niche)
    print(json.dumps(result, indent=2))
