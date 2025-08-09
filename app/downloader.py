import os
import glob
import threading
import ctypes
import yt_dlp
from yt_dlp.update import Updater
from .config import Config
from flask import current_app


class DownloadManager:
    """Manage yt-dlp download threads and auto-update the backend."""

    def __init__(self) -> None:
        self._active_ydl: dict[str, yt_dlp.YoutubeDL] = {}
        self._active_threads: dict[str, dict] = {}
        self._download_files: dict[str, list[str]] = {}
        self._ensure_latest_yt_dlp()

    def _ensure_latest_yt_dlp(self) -> None:
        """Attempt to update yt-dlp to the latest version."""
        try:
            Updater(yt_dlp.YoutubeDL({"quiet": True})).update()
        except Exception as exc:
            print(f"yt-dlp auto-update failed: {exc}")

    @staticmethod
    def _terminate_thread(thread: threading.Thread) -> None:
        """Force terminate a thread (Windows-specific approach)."""
        if not thread.is_alive():
            return
        exc_type = SystemExit
        try:
            if hasattr(ctypes, "pythonapi"):
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_long(thread.ident), ctypes.py_object(exc_type)
                )
                if res == 0:
                    print("Invalid thread ID")
                elif res != 1:
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
                    print("PyThreadState_SetAsyncExc failed")
        except Exception as e:
            print(f"Error terminating thread: {e}")

    def cancel_download(self, download_id: str) -> bool:
        """Cancel a download in progress and delete any partial files."""
        cancelled = False
        if download_id in self._active_ydl:
            ydl = self._active_ydl[download_id]
            if hasattr(ydl, "_finish_multiline_status"):
                ydl._finish_multiline_status()
            ydl.interrupt = True
            cancelled = True

        if download_id in self._active_threads:
            thread_info = self._active_threads[download_id]
            thread_info["cancel"] = True
            if thread_info.get("thread") is not None:
                self._terminate_thread(thread_info["thread"])
            cancelled = True
        print(f"Download {download_id} cancel status: {cancelled}")
        self._active_ydl.pop(download_id, None)
        self.cleanup_partial_files(download_id)
        return cancelled

    def cleanup_partial_files(self, download_id: str) -> None:
        """Delete any partial download files."""
        if download_id not in self._download_files:
            return
        files_to_delete = self._download_files[download_id]
        for file_path in files_to_delete:
            try:
                if os.path.exists(file_path):
                    print(f"Deleting partial file: {file_path}")
                    os.remove(file_path)
            except OSError as e:
                print(f"Error deleting file {file_path}: {e}")

        for file_path in files_to_delete:
            try:
                base_dir = os.path.dirname(file_path)
                base_name = os.path.basename(file_path)
                for pattern in [f"{base_name}.*", "*.part", "*.temp"]:
                    pattern_path = os.path.join(base_dir or ".", pattern)
                    for matched_file in glob.glob(pattern_path):
                        if os.path.exists(matched_file):
                            print(f"Deleting additional temp file: {matched_file}")
                            os.remove(matched_file)
            except Exception as e:
                print(f"Error cleaning up additional files: {e}")

        self._download_files[download_id] = []

    def _progress_hook(self, d, download_id=None, progress_cb=None):
        """Track file paths during download and report playlist progress."""
        if download_id is None:
            if not d.get("download_id") and "ctx" in d and "download_id" in d["ctx"]:
                download_id = d["ctx"]["download_id"]
                progress_cb = progress_cb or d["ctx"].get("progress_callback")
            else:
                download_id = d.get("download_id")
                progress_cb = progress_cb or d.get("progress_callback")
        if not download_id:
            return
        if download_id not in self._download_files:
            self._download_files[download_id] = []
        if (
            download_id in self._active_threads
            and self._active_threads[download_id]["cancel"]
        ):
            raise Exception("Download cancelled by user")
        if d.get("filename") and d["filename"] not in self._download_files[download_id]:
            print(f"Tracking file for {download_id}: {d['filename']}")
            self._download_files[download_id].append(d["filename"])
        if d.get("info_dict") and d["info_dict"].get("__files_to_move"):
            for _, filepath in d["info_dict"]["__files_to_move"].items():
                if filepath not in self._download_files[download_id]:
                    print(f"Tracking postprocess file for {download_id}: {filepath}")
                    self._download_files[download_id].append(filepath)
        if d.get("status") == "finished" and progress_cb:
            try:
                progress_cb(download_id, d)
            except Exception as e:
                print(f"Progress callback error: {e}")

    def download_youtube(
        self,
        url: str,
        to_mp3: bool = True,
        download_id: str | None = None,
        progress_callback=None,
    ) -> None:
        """Download a YouTube URL as MP3 or MP4."""
        if download_id:
            self._active_threads[download_id] = {
                "thread": threading.current_thread(),
                "cancel": False,
            }
            self._download_files[download_id] = []
        try:
            outtmpl = "%(title)s.%(ext)s"
            ydl_opts = {
                "outtmpl": outtmpl,
                "format": "bestaudio/best"
                if to_mp3
                else "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
                "cookiefile": Config.COOKIE_FILE,
                "http_headers": Config.HTTP_HEADERS,
                "writethumbnail": True,
                "embedthumbnail": True,
                "add_metadata": True,
                "prefer_ffmpeg": True,
                "progress_hooks": [
                    lambda d, dl_id=download_id, cb=progress_callback: self._progress_hook(
                        d, dl_id, cb
                    )
                ],
                "noprogress": False,
                "nopart": True,
            }
            postprocessors = []
            if to_mp3:
                postprocessors.append(
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                )
                postprocessors.append({"key": "EmbedThumbnail"})
                postprocessors.append({"key": "FFmpegMetadata"})
            else:
                postprocessors.append({"key": "EmbedThumbnail"})
                postprocessors.append({"key": "FFmpegMetadata"})
            ydl_opts["postprocessors"] = postprocessors
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if download_id:
                    self._active_ydl[download_id] = ydl
                try:
                    if (
                        download_id
                        and download_id in self._active_threads
                        and self._active_threads[download_id]["cancel"]
                    ):
                        print(f"Download {download_id} was cancelled before starting")
                        self.cleanup_partial_files(download_id)
                        return
                    ydl.download([url])
                    try:
                        if current_app:
                            from .auto_reload import notify_clients

                            notify_clients()
                            print("Notified clients of new file")
                    except (RuntimeError, ImportError):
                        pass
                except Exception:
                    if (
                        download_id
                        and download_id in self._active_threads
                        and self._active_threads[download_id]["cancel"]
                    ):
                        print(f"Download {download_id} was cancelled during download")
                        self.cleanup_partial_files(download_id)
                        return
                    raise
                finally:
                    if download_id:
                        self._active_ydl.pop(download_id, None)
        finally:
            if download_id:
                self._active_threads.pop(download_id, None)
                self._download_files.pop(download_id, None)
            for ext in ("jpg", "webp", "png"):
                for thumb in glob.glob(f"*.{ext}"):
                    try:
                        os.remove(thumb)
                    except OSError:
                        pass


# expose default manager functions for backwards compatibility
_default_manager = DownloadManager()
cancel_download = _default_manager.cancel_download
cleanup_partial_files = _default_manager.cleanup_partial_files
download_youtube = _default_manager.download_youtube
