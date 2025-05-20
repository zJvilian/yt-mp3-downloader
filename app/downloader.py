import os
import glob
import yt_dlp
from .config import Config

def download_youtube(url: str, to_mp3: bool = True):
    """
    Download a YouTube URL as MP3 (with embedded cover & metadata)
    or MP4 (video). Filenames use only the title + ext, no IDs or literals.
    """
    # template: just title + extension
    outtmpl = "%(title)s.%(ext)s"

    # common options for both mp3 and mp4
    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bestaudio/best" if to_mp3 else "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "cookiefile": Config.COOKIE_FILE,
        "http_headers": Config.HTTP_HEADERS,

        # write and embed thumbnail
        "writethumbnail": True,
        "embedthumbnail": True,

        # add default metadata (title, uploader, upload_date, etc)
        "add_metadata": True,

        # prefer ffmpeg for all processing
        "prefer_ffmpeg": True,
    }

    # build postprocessors list
    postprocessors = []
    if to_mp3:
        # extract audio to mp3
        postprocessors.append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        })

        # embed the thumbnail as cover art
        postprocessors.append({"key": "EmbedThumbnail"})

        # write metadata tags into the mp3
        postprocessors.append({"key": "FFmpegMetadata"})
    else:
        # for mp4 we can still embed metadata, but no audio extraction
        postprocessors.append({"key": "EmbedThumbnail"})
        postprocessors.append({"key": "FFmpegMetadata"})

    ydl_opts["postprocessors"] = postprocessors

    # run the download
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # cleanup any standalone thumbnail files
    for ext in ("jpg", "webp"):
        for thumb in glob.glob(f"*.{ext}"):
            try:
                os.remove(thumb)
            except OSError:
                pass
