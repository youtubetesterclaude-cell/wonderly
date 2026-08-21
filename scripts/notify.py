"""
Sends push notifications to your phone via ntfy.sh (free, no account needed).

Setup (one-time):
1. Install the ntfy app: apps.apple.com or Google Play, search "ntfy"
2. Pick a topic name -- this is like a private channel name. Make it long and
   random (e.g. "wonderly-pipeline-7f3k9x2") since anyone who knows your exact
   topic name on the public ntfy.sh server could subscribe to it too. This is
   "secret by obscurity," not real auth -- fine for personal notifications,
   not for anything sensitive.
3. In the app, tap + and subscribe to that exact topic name.
4. Add it as a GitHub secret: NTFY_TOPIC = your topic name
"""
import os
import requests

NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
NTFY_URL = "https://ntfy.sh"


def notify(title: str, message: str, priority: str = "default", tags: list[str] = None):
    """priority: 'min', 'low', 'default', 'high', 'urgent'.
    tags: ntfy emoji shortcodes, e.g. ['tada'], ['warning'], ['x']."""
    if not NTFY_TOPIC:
        print(f"[notify] NTFY_TOPIC not set -- skipping push notification. "
              f"Would have sent: {title} -- {message}")
        return

    try:
        requests.post(
            f"{NTFY_URL}/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": priority,
                "Tags": ",".join(tags) if tags else "",
            },
            timeout=10,
        )
    except Exception as e:
        # Never let a failed notification take down the actual pipeline run
        print(f"[notify] Failed to send push notification: {e}")


if __name__ == "__main__":
    notify("Test", "This is a test notification from the Wonderly pipeline.", tags=["wave"])
