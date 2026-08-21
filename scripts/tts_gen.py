"""
Convert script text to voiceover audio using edge-tts (free, uses Microsoft
Edge's neural voices, no API key required).
"""
import asyncio
import os
import edge_tts

# Browse more voices with: `edge-tts --list-voices`
DEFAULT_VOICE = "en-US-GuyNeural"
MAX_RETRIES = 3


async def _generate(text: str, output_path: str, voice: str = DEFAULT_VOICE, rate: str = "+0%"):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)


def generate_voiceover(text: str, output_path: str, voice: str = DEFAULT_VOICE):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            asyncio.run(_generate(text, output_path, voice))
        except Exception as e:
            last_error = e
            print(f"[tts_gen] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            continue

        # edge-tts can exit "successfully" but write a 0-byte or missing file
        # if the connection dropped mid-stream -- verify before trusting it.
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path

        last_error = RuntimeError(
            f"edge-tts produced an empty or missing file at {output_path} "
            f"(attempt {attempt}/{MAX_RETRIES})"
        )
        print(f"[tts_gen] {last_error}")

    raise RuntimeError(
        f"Voiceover generation failed after {MAX_RETRIES} attempts. "
        f"Last error: {last_error}. This is usually a transient network issue "
        f"reaching Microsoft's TTS endpoint from the CI runner -- re-running "
        f"the workflow often fixes it. If it keeps failing, edge-tts's API may "
        f"have changed; check https://github.com/rany2/edge-tts for known issues."
    )


if __name__ == "__main__":
    generate_voiceover(
        "This is a test of the voiceover pipeline.",
        "/tmp/test_voiceover.mp3",
    )
    print("Saved /tmp/test_voiceover.mp3")
