import os
from flask import Flask
from .routes import register_routes
from .config import Config

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def create_app():
    # tell Flask exactly where static and templates live:
    app = Flask(
        __name__,
        static_folder=os.path.join(BASE_DIR, "static"),
        static_url_path="/static",
        template_folder=os.path.join(BASE_DIR, "templates")
    )
    app.config.from_object(Config)

    # ensure output dirs exist (you already had this)
    os.makedirs(app.config["OUTPUT_DIR_MP3"], exist_ok=True)
    os.makedirs(app.config["OUTPUT_DIR_MP4"], exist_ok=True)

    register_routes(app)
    return app

# so `flask run` or `gunicorn app:create_app` picks it up:
app = create_app()
