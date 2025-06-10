import os
import glob
import threading
import signal
import ctypes
import yt_dlp
import time
from .config import Config
from flask import current_app

# Track active yt-dlp instances by download_id
_active_ydl = {}
# Track active download threads and their file paths
_active_threads = {}
# Track temporary files for each download_id
_download_files = {}

def _terminate_thread(thread):
    """Force terminate a thread (Windows-specific approach)"""
    if not thread.is_alive():
        return
        
    # This is a bit aggressive but necessary for stubborn download threads
    exc_type = SystemExit
    try:
        # For Windows
        if hasattr(ctypes, 'pythonapi'):
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(thread.ident), ctypes.py_object(exc_type))
            if res == 0:
                print("Invalid thread ID")
            elif res != 1:
                # If more than one thread affected, reset the effect
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
                print("PyThreadState_SetAsyncExc failed")
    except Exception as e:
        print(f"Error terminating thread: {e}")

def cancel_download(download_id):
    """Cancel a download in progress and delete any partial files"""
    cancelled = False
    
    # Try to cancel via yt-dlp's internal mechanism
    if download_id in _active_ydl:
        ydl = _active_ydl[download_id]
        if hasattr(ydl, '_finish_multiline_status'):
            ydl._finish_multiline_status()
        ydl.interrupt = True
        cancelled = True
    
    # Mark the thread for cancellation
    if download_id in _active_threads:
        thread_info = _active_threads[download_id]
        thread_info['cancel'] = True
        
        # Force terminate the thread if it exists and is alive
        if 'thread' in thread_info and thread_info['thread'] is not None:
            _terminate_thread(thread_info['thread'])
        
        cancelled = True
    print(f"Download {download_id} cancel status: {cancelled}")
    # Also remove the tracking entries
    _active_ydl.pop(download_id, None)
    
    # Delete any partial files
    cleanup_partial_files(download_id)
    
    return cancelled

def cleanup_partial_files(download_id):
    """Delete any partial download files"""
    if download_id in _download_files:
        files_to_delete = _download_files[download_id]
        for file_path in files_to_delete:
            try:
                if os.path.exists(file_path):
                    print(f"Deleting partial file: {file_path}")
                    os.remove(file_path)
            except OSError as e:
                print(f"Error deleting file {file_path}: {e}")
        
        # Also check for any temp or part files with similar names
        for file_path in files_to_delete:
            try:
                base_dir = os.path.dirname(file_path)
                base_name = os.path.basename(file_path)
                # Look for .part files, .temp files, etc.
                for pattern in [f"{base_name}.*", "*.part", "*.temp"]:
                    pattern_path = os.path.join(base_dir if base_dir else ".", pattern)
                    for matched_file in glob.glob(pattern_path):
                        if os.path.exists(matched_file):
                            print(f"Deleting additional temp file: {matched_file}")
                            os.remove(matched_file)
            except Exception as e:
                print(f"Error cleaning up additional files: {e}")
        
        # Clear the file list
        _download_files[download_id] = []

def progress_hook(d, download_id=None, progress_cb=None):
    """Track file paths during download and report playlist progress"""
    # Allow passing download_id/progress_cb via wrapper for convenience
    if download_id is None:
        if not d.get('download_id') and 'ctx' in d and 'download_id' in d['ctx']:
            download_id = d['ctx']['download_id']
            progress_cb = progress_cb or d['ctx'].get('progress_callback')
        else:
            download_id = d.get('download_id')
            progress_cb = progress_cb or d.get('progress_callback')
        
    if not download_id:
        return
    
    # Initialize the file list if not exists
    if download_id not in _download_files:
        _download_files[download_id] = []
    
    # Check if download has been cancelled
    if download_id in _active_threads and _active_threads[download_id]['cancel']:
        # Raise an exception to abort the download
        raise Exception("Download cancelled by user")
    
    # Track filename when it becomes available
    if d.get('filename') and d['filename'] not in _download_files[download_id]:
        print(f"Tracking file for {download_id}: {d['filename']}")
        _download_files[download_id].append(d['filename'])
    
    # Also track any temporary files from the postprocessors
    if d.get('info_dict') and d['info_dict'].get('__files_to_move'):
        for _, filepath in d['info_dict']['__files_to_move'].items():
            if filepath not in _download_files[download_id]:
                print(f"Tracking postprocess file for {download_id}: {filepath}")
                _download_files[download_id].append(filepath)

    # When a video/entry is finished, trigger progress callback
    if d.get('status') == 'finished' and progress_cb:
        try:
            progress_cb(download_id, d)
        except Exception as e:
            print(f"Progress callback error: {e}")

def download_youtube(url: str, to_mp3: bool = True, download_id: str = None, progress_callback=None):
    """
    Download a YouTube URL as MP3 (with embedded cover & metadata)
    or MP4 (video). Filenames use only the title + ext, no IDs or literals.
    
    Args:
        url: YouTube URL to download
        to_mp3: Whether to convert to MP3 (True) or keep as MP4 (False)
        download_id: Optional ID to track this download for cancellation
        progress_callback: Optional callback invoked when each playlist entry is
            finished. It receives ``(download_id, info_dict)``.
    """
    # Track this download thread if an ID was provided
    if download_id:
        _active_threads[download_id] = {'thread': threading.current_thread(), 'cancel': False}
        _download_files[download_id] = []
    
    try:
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
            
            # progress hook to track files
            "progress_hooks": [
                lambda d, dl_id=download_id, cb=progress_callback: progress_hook(d, dl_id, cb)
            ],
            
            # Make sure we can interrupt
            "noprogress": False,
            "nopart": True  # Don't use .part files which are harder to clean up
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
                # Before starting download, check if already cancelled
                if download_id and download_id in _active_threads and _active_threads[download_id]['cancel']:
                    print(f"Download {download_id} was cancelled before starting")
                    cleanup_partial_files(download_id)
                    return
                
                ydl.download([url])
                
                # Notify clients of the new file if in app context
                try:
                    from flask import current_app
                    if current_app:
                        from .auto_reload import notify_clients
                        notify_clients()
                        print("Notified clients of new file")
                except (RuntimeError, ImportError):
                    # Not in Flask context or auto_reload not available
                    pass
                    
            except Exception as e:
                # Check if this was a cancellation
                if download_id and download_id in _active_threads and _active_threads[download_id]['cancel']:
                    print(f"Download {download_id} was cancelled during download")
                    cleanup_partial_files(download_id)
                    return
                else:
                    # Re-raise other errors
                    raise
            finally:
                # Clean up tracking
                if download_id:
                    _active_ydl.pop(download_id, None)
                    
    finally:
        # Clean up thread tracking
        if download_id:
            _active_threads.pop(download_id, None)
            _download_files.pop(download_id, None)
            
        # cleanup any standalone thumbnail files
        for ext in ("jpg", "webp", "png"):
            for thumb in glob.glob(f"*.{ext}"):
                try:
                    os.remove(thumb)
                except OSError:
                    pass
