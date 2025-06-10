import os
import uuid
import threading
from flask import (
    current_app, render_template, request, jsonify, Response,
    redirect, url_for, flash, send_from_directory
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

            if not url:
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
            active_downloads[download_id] = {
                "url": url,
                "format": fmt,
                "status": "downloading"
            }
            
            # Run download in background thread
            def download_task():
                try:
                    cwd = os.getcwd()
                    os.chdir(output_dir)
                    download_youtube(url, to_mp3=to_mp3, download_id=download_id)
                    flash(f"✅ {fmt.upper()} download complete!")
                except Exception as e:
                    flash(f"⚠️ Download failed: {e}")
                finally:
                    os.chdir(cwd)
                    if download_id in active_downloads:
                        active_downloads[download_id]["status"] = "completed"
                    # Notify clients of the change
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
            handle_event_stream(active_downloads), 
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
        
        # Build the full path and ensure it's within the expected directory
        filepath = os.path.abspath(os.path.join(directory, filename))
        directory_abs = os.path.abspath(directory)

        # Prevent path traversal attacks
        if os.path.commonpath([filepath, directory_abs]) != directory_abs:
            return jsonify({"success": False, "error": "Invalid file path"}), 400
        
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

    @app.route("/api/file-list")
    def file_list():
        """API endpoint to get file lists for polling"""
        return jsonify(get_files_response(active_downloads))
