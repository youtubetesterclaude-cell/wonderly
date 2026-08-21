"""
RUN THIS ONCE, LOCALLY (needs a browser -- won't work in CI/GitHub Actions).

Generates a refresh token you'll store as a GitHub secret (YT_REFRESH_TOKEN)
so the automated pipeline can upload without re-authenticating each time.

Prereqs:
1. Google Cloud Console -> new project -> enable "YouTube Data API v3" and
   "YouTube Analytics API"
2. Create OAuth 2.0 credentials, type = "Desktop app"
3. Download the JSON, save it as client_secret.json in this scripts/ folder
   (do NOT commit this file -- it's in .gitignore)
"""
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

CLIENT_SECRET_PATH = os.path.join(os.path.dirname(__file__), "client_secret.json")


def main():
    if not os.path.exists(CLIENT_SECRET_PATH):
        print(f"ERROR: put your downloaded OAuth client JSON at {CLIENT_SECRET_PATH}")
        return

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n=== SUCCESS ===")
    print("Save these as GitHub repo secrets (Settings -> Secrets and variables -> Actions):\n")
    print(f"YT_CLIENT_ID={creds.client_id}")
    print(f"YT_CLIENT_SECRET={creds.client_secret}")
    print(f"YT_REFRESH_TOKEN={creds.refresh_token}")
    print("\nDo NOT commit these anywhere. Paste them directly into GitHub's secret UI.")


if __name__ == "__main__":
    main()
