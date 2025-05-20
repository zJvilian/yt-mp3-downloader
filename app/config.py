import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET", "dev-secret")

    # Project paths
    PROJECT_ROOT   = os.path.dirname(BASE_DIR)
    OUTPUT_DIR_MP3 = os.path.join(PROJECT_ROOT, "mp3s")
    OUTPUT_DIR_MP4 = os.path.join(PROJECT_ROOT, "mp4s")
    COOKIE_FILE    = os.path.join(PROJECT_ROOT, "cookies.txt")

    # yt-dlp HTTP headers
    HTTP_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
