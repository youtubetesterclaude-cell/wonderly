"""Loads data/feedback.md so topic_gen.py and script_gen.py can factor in
human notes edited directly on GitHub (no code changes needed to steer output)."""
import os

FEEDBACK_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "feedback.md")


def load_feedback() -> str:
    """Returns the person's feedback notes (everything after the '---' divider
    in data/feedback.md, minus the placeholder line), or '' if nothing is set."""
    if not os.path.exists(FEEDBACK_PATH):
        return ""
    with open(FEEDBACK_PATH) as f:
        content = f.read()

    if "---" not in content:
        return ""

    notes = content.split("---", 1)[1]
    notes = notes.replace("(no feedback yet -- add your notes above this line)", "")
    notes = notes.strip()
    return notes


if __name__ == "__main__":
    fb = load_feedback()
    print(f"Loaded feedback ({len(fb)} chars):\n{fb}" if fb else "No feedback set.")
