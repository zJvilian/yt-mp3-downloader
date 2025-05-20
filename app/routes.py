import os
from flask import (
    current_app, render_template, request,
    redirect, url_for, flash, send_from_directory
)
from .downloader import download_youtube

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

            try:
                cwd = os.getcwd()
                os.chdir(output_dir)

                download_youtube(url, to_mp3=to_mp3)
                flash(f"✅ {fmt.upper()} download complete!")
            except Exception as e:
                flash(f"⚠️ Download failed: {e}")
            finally:
                os.chdir(cwd)

            return redirect(url_for("index"))

        # list existing files
        mp3_files = sorted(os.listdir(current_app.config["OUTPUT_DIR_MP3"]))
        mp4_files = sorted(os.listdir(current_app.config["OUTPUT_DIR_MP4"]))
        return render_template("index.html", mp3_files=mp3_files, mp4_files=mp4_files)

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
