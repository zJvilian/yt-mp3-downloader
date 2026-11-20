import os
import threading
import tempfile
import yt_dlp
from .config import Config

_cancelled = set()
_lock = threading.Lock()


def cancel_download(download_id):
    with _lock:
        _cancelled.add(download_id)
    return True


def download_youtube(url, to_mp3=True, download_id=None, progress_callback=None,
                     output_dir=None, quality="192", height="1080", playlist=False):
    output_dir = output_dir or (Config.OUTPUT_DIR_MP3 if to_mp3 else Config.OUTPUT_DIR_MP4)
    def hook(data):
        with _lock:
            cancelled = download_id in _cancelled
        if cancelled:
            raise RuntimeError("Download cancelled")
        if data.get("status") == "finished" and data.get("postprocessor") == "MoveFiles" and progress_callback:
            progress_callback(download_id, data)

    # Each job owns its temporary files; cancellation cannot erase another job.
    try:
        with tempfile.TemporaryDirectory(prefix="download-", dir=output_dir) as temporary:
            opts = {
                "paths": {"home": output_dir, "temp": temporary},
                "outtmpl": "%(title)s [%(id)s].%(ext)s",
                "format": "bestaudio/best" if to_mp3 else f"bv*[ext=mp4][height<={height}]+ba[ext=m4a]/b[ext=mp4][height<={height}]",
                "merge_output_format": "mp4",
                "noplaylist": not playlist,
                "writethumbnail": True,
                "socket_timeout": 30, "retries": 3,
                "progress_hooks": [hook],
                "postprocessor_hooks": [hook],
                "postprocessors": ([{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": quality}] if to_mp3 else []) + [{"key": "FFmpegMetadata"}, {"key": "EmbedThumbnail"}],
            }
            if os.path.isfile(Config.COOKIE_FILE):
                # yt-dlp writes its cookie jar on exit, so copy read-only mounts.
                import shutil
                cookie_copy = os.path.join(temporary, "cookies.txt")
                shutil.copyfile(Config.COOKIE_FILE, cookie_copy)
                opts["cookiefile"] = cookie_copy
            hook({})
            with yt_dlp.YoutubeDL(opts) as ydl:
                result = ydl.download([url])
                if result:
                    raise RuntimeError("Download failed; check the URL and try again.")
    finally:
        with _lock:
            _cancelled.discard(download_id)
