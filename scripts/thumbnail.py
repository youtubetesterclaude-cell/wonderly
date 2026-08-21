"""
Generate a thumbnail by grabbing a frame from the assembled video and
overlaying bold title text. Simple and free -- no image-gen API needed.
For more distinctive thumbnails later, swap this for an image-gen API call.
"""
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _get_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _extract_frame(video_path: str, out_path: str, timestamp: str = "00:00:01"):
    subprocess.run([
        "ffmpeg", "-y", "-ss", timestamp, "-i", video_path,
        "-frames:v", "1", "-q:v", "2", out_path,
    ], check=True, capture_output=True)


def _wrap_text(text, font, max_width, draw):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def generate_thumbnail(video_path: str, title_text: str, output_path: str,
                        work_dir: str, orientation: str = "landscape"):
    """
    Only meaningful for "landscape" (standard) videos -- YouTube Shorts don't
    use the regular thumbnail picker the same way, so main_pipeline.py skips
    calling this for shorts entirely.
    """
    os.makedirs(work_dir, exist_ok=True)
    frame_path = os.path.join(work_dir, "thumb_frame.jpg")
    _extract_frame(video_path, frame_path)

    img = Image.open(frame_path).convert("RGB")
    img = img.resize((1280, 720))
    draw = ImageDraw.Draw(img)

    # darken bottom third for text legibility
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([0, 460, 1280, 720], fill=(0, 0, 0, 160))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    font = _get_font(64)
    lines = _wrap_text(title_text.upper(), font, max_width=1180, draw=draw)[:3]
    y = 480
    for line in lines:
        draw.text((50, y), line, font=font, fill="white",
                   stroke_width=3, stroke_fill="black")
        y += 74

    img.save(output_path, quality=92)
    return output_path


if __name__ == "__main__":
    print("Run via main_pipeline.py -- this module expects an assembled video.")
