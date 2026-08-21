"""
Run by .github/workflows/process_feedback.yml when a GitHub issue labeled
"feedback" is opened (from tapping "Give feedback" on the phone dashboard).
Takes the issue title/body (passed in as env vars by the workflow) and
inserts them into data/feedback.md, above the placeholder line, so the next
pipeline run picks them up automatically.
"""
import os
import datetime

FEEDBACK_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "feedback.md")
PLACEHOLDER = "(no feedback yet -- add your notes above this line)"


def append_issue_feedback(issue_title: str, issue_body: str, issue_number: int):
    with open(FEEDBACK_PATH) as f:
        content = f.read()

    date = datetime.date.today().isoformat()
    note = f"- [{date}, via issue #{issue_number}] {issue_body.strip() or issue_title.strip()}"

    if PLACEHOLDER in content:
        content = content.replace(PLACEHOLDER, f"{note}\n\n{PLACEHOLDER}")
    else:
        # placeholder line got removed at some point -- just append to the end
        content = content.rstrip() + f"\n\n{note}\n"

    with open(FEEDBACK_PATH, "w") as f:
        f.write(content)

    print(f"Added feedback from issue #{issue_number} to {FEEDBACK_PATH}")


if __name__ == "__main__":
    title = os.environ["ISSUE_TITLE"]
    body = os.environ.get("ISSUE_BODY", "")
    number = int(os.environ["ISSUE_NUMBER"])
    append_issue_feedback(title, body, number)
