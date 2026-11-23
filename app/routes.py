import os
import uuid
import threading
import tempfile
import zipfile
from urllib.parse import urlsplit
from werkzeug.utils import safe_join
from flask import (
    current_app, render_template, request, jsonify, Response,
    redirect, url_for, flash, send_from_directory, send_file, stream_with_context
)
from .downloader import download_youtube, cancel_download
from .auto_reload import (
    get_filtered_files, notify_clients, handle_event_stream, get_files_response
)

# Track active downloads
active_downloads = {}

def register_routes(app):

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            url    = request.form.get("url", "").strip()
            fmt    = request.form.get("format", "mp3")

            quality = request.form.get("quality", "192")
            height = request.form.get("height", "1080")
            playlist = request.form.get("playlist") == "on"
            parsed = urlsplit(url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or fmt not in {"mp3", "mp4"} or quality not in {"128", "192", "320"} or height not in {"720", "1080", "2160"}:
                flash("⚠️ Please enter a valid YouTube URL")
                return redirect(url_for("index"))

            # choose directory & download mode
            if fmt == "mp4":
                output_dir = app.config["OUTPUT_DIR_MP4"]
                to_mp3 = False
            else:
                output_dir = app.config["OUTPUT_DIR_MP3"]
                to_mp3 = True

            # Generate a unique ID for this download
            download_id = str(uuid.uuid4())
            total = "?" if playlist else 1
            active_downloads[download_id] = {
                "url": url,
                "format": fmt,
                "status": "downloading",
                "current": 0,
                "total": total,
            }
            
            # Run download in background thread
            def download_task():
                def progress_cb(d_id, _info):
                    if d_id in active_downloads:
                        active_downloads[d_id]["current"] += 1
                        notify_clients()

                try:
                    download_youtube(
                        url,
                        to_mp3=to_mp3,
                        download_id=download_id,
                        progress_callback=progress_cb,
                        output_dir=output_dir, quality=quality, height=height, playlist=playlist,
                    )
                    if active_downloads[download_id]["status"] != "cancelled":
                        active_downloads[download_id]["status"] = "completed"
                except Exception as e:
                    if active_downloads[download_id]["status"] != "cancelled":
                        active_downloads[download_id].update(status="failed", error=str(e))
                finally:
                    notify_clients()
            
            thread = threading.Thread(target=download_task)
            thread.daemon = True
            thread.start()
            
            return redirect(url_for("index"))

        # Get filtered files for display
        mp3_files, mp4_files = get_filtered_files()
        return render_template("index.html", 
                              mp3_files=mp3_files, 
                              mp4_files=mp4_files,
                              active_downloads=active_downloads)

    @app.route("/events")
    def events():
        """Server-sent events endpoint for real-time updates"""
        return Response(
            stream_with_context(handle_event_stream(active_downloads)), 
            mimetype="text/event-stream"
        )

    @app.route("/cancel/<download_id>", methods=["POST"])
    def cancel_download_route(download_id):
        if download_id in active_downloads:
            cancel_download(download_id)
            active_downloads[download_id]["status"] = "cancelled"
            # Notify clients of change
            notify_clients()
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Download not found"}), 404
        
    @app.route("/mp3s/<path:filename>")
    def serve_mp3(filename):
        return send_from_directory(
            current_app.config["OUTPUT_DIR_MP3"],
            filename,
            as_attachment=True
        )

    @app.route("/mp4s/<path:filename>")
    def serve_mp4(filename):
        return send_from_directory(
            current_app.config["OUTPUT_DIR_MP4"],
            filename,
            as_attachment=True
        )

    @app.route("/delete/<filetype>/<path:filename>", methods=["POST"])
    def delete_file(filetype, filename):
        """Delete a file from the server"""
        if filetype not in ["mp3", "mp4"]:
            return jsonify({"success": False, "error": "Invalid file type"}), 400
            
        # Get the directory based on file type
        directory = current_app.config["OUTPUT_DIR_MP3"] if filetype == "mp3" else current_app.config["OUTPUT_DIR_MP4"]
        
        # Build the full path
        filepath = safe_join(directory, filename)
        if not filepath or os.path.islink(filepath):
            return jsonify(success=False, error="Invalid filename"), 400
        
        # Check if file exists and delete it
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                # Notify clients of change
                notify_clients()
                return jsonify({"success": True})
            except OSError as e:
                return jsonify({"success": False, "error": str(e)}), 500
        else:
            return jsonify({"success": False, "error": "File not found"}), 404

    @app.route("/clear", methods=["POST"])
    def clear_all():
        """Delete every listed file and forget finished jobs; running jobs are kept."""
        mp3_files, mp4_files = get_filtered_files()
        failed = []
        for directory, names in ((current_app.config["OUTPUT_DIR_MP3"], mp3_files), (current_app.config["OUTPUT_DIR_MP4"], mp4_files)):
            for name in names:
                path = os.path.join(directory, name)
                try:
                    os.remove(path)  # removes a symlink itself, never its target
                except OSError:
                    failed.append(name)
        for key in [k for k, v in active_downloads.items() if v["status"] != "downloading"]:
            del active_downloads[key]
        notify_clients()
        if failed:
            return jsonify(success=False, error=f"Could not delete: {', '.join(failed)}"), 500
        return jsonify(success=True)

    @app.route("/download-all/<filetype>")
    def download_all(filetype):
        """Send every listed file of one type as a single zip."""
        if filetype not in ("mp3", "mp4"):
            return jsonify(success=False, error="Invalid file type"), 400
        directory = current_app.config["OUTPUT_DIR_MP3" if filetype == "mp3" else "OUTPUT_DIR_MP4"]
        names = get_filtered_files()[0 if filetype == "mp3" else 1]
        archive = tempfile.TemporaryFile()  # on disk: libraries can be larger than RAM
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_STORED) as zf:  # media is already compressed
            for name in names:
                path = os.path.join(directory, name)
                if not os.path.islink(path):  # never ship a symlink's target
                    zf.write(path, name)
        archive.seek(0)
        return send_file(archive, mimetype="application/zip", as_attachment=True, download_name=f"{filetype}s.zip")

    @app.route("/api/file-list")
    def file_list():
        """API endpoint to get file lists for polling"""
        return jsonify(get_files_response(active_downloads))
