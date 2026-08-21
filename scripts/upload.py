"""Upload the finished video + thumbnail to YouTube via the Data API."""
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def _get_credentials():
    return Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )


def upload_video(video_path: str, thumbnail_path: str, title: str,
                  description: str, tags: list[str], category_id: str = "27",
                  privacy_status: str = "public", is_short: bool = False) -> str:
    """category_id 27 = Education. See YouTube API docs for the full list.

    is_short: if True, appends #Shorts to the title/description, which is
    what tells YouTube to route the video into the Shorts shelf -- this only
    works correctly if the video itself is also vertical (9:16) and under
    ~3 minutes, which assemble.py handles via orientation="portrait".
    """
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    final_title = title[:95] + " #Shorts" if is_short else title[:100]
    final_description = f"{description}\n\n#Shorts" if is_short else description

    body = {
        "snippet": {
            "title": final_title[:100],
            "description": final_description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]

    if os.path.exists(thumbnail_path) and not is_short:
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg"),
            ).execute()
        except Exception as e:
            # Don't let a thumbnail failure take down the whole upload -- the
            # video itself is already live at this point. Common cause: the
            # channel isn't phone-verified yet (youtube.com/verify), which
            # YouTube requires before allowing custom thumbnails.
            print(f"[upload] WARNING: video uploaded, but setting thumbnail failed: {e}")
            print("[upload] If this is a 403 'forbidden' error, verify your channel "
                  "at https://youtube.com/verify -- custom thumbnails require phone "
                  "verification. The video is still live with YouTube's auto-generated "
                  "thumbnail in the meantime.")

    print(f"Uploaded: https://youtube.com/watch?v={video_id}")
    return video_id


if __name__ == "__main__":
    print("Run via main_pipeline.py -- this module expects a finished video.")
