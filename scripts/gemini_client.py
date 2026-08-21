"""
Shared wrapper around the Gemini API call used by topic_gen.py and
script_gen.py. Adds automatic retries with backoff for transient server
errors (503 UNAVAILABLE, 429 rate limits, etc.) -- these happen occasionally
on the free tier under high demand and are almost always resolved by waiting
a bit and retrying, not a real problem with your code or prompt.
"""
import os
import time
from google import genai
from google.genai import errors as genai_errors

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.6-flash"  # free-tier model as of Aug 2026; Google deprecates these fast -- check ai.google.dev/gemini-api/docs/pricing if you hit a 404

MAX_RETRIES = 4
BASE_DELAY_SECONDS = 15  # doubles each retry: 15s, 30s, 60s, 120s


def generate_with_retry(prompt: str) -> str:
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.models.generate_content(model=MODEL, contents=prompt)
            return resp.text.strip()
        except genai_errors.ServerError as e:
            last_error = e
            delay = BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            print(f"[gemini_client] Attempt {attempt}/{MAX_RETRIES} hit a server error "
                  f"({e}). Retrying in {delay}s...")
            if attempt < MAX_RETRIES:
                time.sleep(delay)
        except genai_errors.ClientError as e:
            # Client errors (bad request, 404 model not found, auth issues) won't
            # be fixed by retrying -- fail fast with a clear message instead of
            # burning 4 retries on something that will never succeed.
            raise RuntimeError(
                f"Gemini API rejected the request (not a transient issue -- "
                f"retrying won't help): {e}"
            ) from e

    raise RuntimeError(
        f"Gemini API still unavailable after {MAX_RETRIES} attempts over "
        f"~{sum(BASE_DELAY_SECONDS * (2**i) for i in range(MAX_RETRIES-1))}s. "
        f"Last error: {last_error}. This usually means genuinely high demand on "
        f"Google's end -- the next scheduled run will likely succeed on its own."
    )
