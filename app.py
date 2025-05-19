import os
from flask import (
    Flask, request, render_template, send_from_directory,
    flash, redirect, url_for
)
from main import download_youtube, list_formats

# ─── Configuration ────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")  # change for prod

BASE_DIR   = os.path.abspath(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "mp3s")

# ensure download directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Routes ────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url    = request.form.get("url", "").strip()
        action = request.form.get("action")

        if not url:
            flash("⚠️ Please enter a valid YouTube URL")
            return redirect(url_for("index"))

        if action == "formats":
            # prints available formats to your console/terminal
            try:
                list_formats(url)
                flash("✅ Formats printed to console. Check your terminal.")
            except Exception as e:
                flash(f"⚠️ Error listing formats: {e}")
        else:
            # download MP3
            try:
                # switch into OUTPUT_DIR so files land there
                cwd = os.getcwd()
                os.chdir(OUTPUT_DIR)

                download_youtube(url, to_mp3=True)
                flash("✅ Download complete!")
            except Exception as e:
                flash(f"⚠️ Download failed: {e}")
            finally:
                os.chdir(cwd)

        return redirect(url_for("index"))

    # GET: show existing MP3s
    files = sorted(os.listdir(OUTPUT_DIR))
    return render_template("index.html", files=files)


@app.route("/mp3s/<path:filename>")
def serve_mp3(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


# ─── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # bind to 0.0.0.0 so Docker can forward host port → container port
    app.run(host="0.0.0.0", port=5000, debug=True)
