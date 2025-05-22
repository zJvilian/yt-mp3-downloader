import os
import glob
import yt_dlp
from .config import Config

# Track active yt-dlp instances by download_id
_active_ydl = {}

def cancel_download(download_id):
    """Cancel a download in progress"""
    if download_id in _active_ydl:
        ydl = _active_ydl[download_id]
        if hasattr(ydl, '_finish_multiline_status'):
            ydl._finish_multiline_status()
        ydl.interrupt = True
        return True
    return False

def download_youtube(url: str, to_mp3: bool = True, download_id: str = None):
    """
    Download a YouTube URL as MP3 (with embedded cover & metadata)
    or MP4 (video). Filenames use only the title + ext, no IDs or literals.
    
    Args:
        url: YouTube URL to download
        to_mp3: Whether to convert to MP3 (True) or keep as MP4 (False)
        download_id: Optional ID to track this download for cancellation
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
        # Track this download if an ID was provided
        if download_id:
            _active_ydl[download_id] = ydl
            
        try:
            ydl.download([url])
        finally:
            # Clean up tracking
            if download_id and download_id in _active_ydl:
                del _active_ydl[download_id]

    # cleanup any standalone thumbnail files
    for ext in ("jpg", "webp"):
        for thumb in glob.glob(f"*.{ext}"):
            try:
                os.remove(thumb)
            except OSError:
                pass
