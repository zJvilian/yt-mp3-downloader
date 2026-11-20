# Universal Media Downloader

A Flask app powered by yt-dlp and FFmpeg, with MP3/MP4 downloads, playlist support, a local media library, audio/video playback, and live job updates.

## Run

Use Python 3.11+ and install FFmpeg on the host:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/flask --app app run
```

Or run `docker compose up --build -d`, then open http://localhost:5000.
Docker binds to localhost by default. This is a trusted local application, without authentication; do not expose it directly to the internet. Use one Gunicorn worker because jobs are held in memory.

## Settings

Expand **Download settings** for 128/192/320 kbps audio, maximum 720p/1080p/4K video resolution, and entire-playlist downloads. Preferences and the selected format are remembered in this browser. Quality cannot exceed the source. The header switch controls light/dark appearance.

Cookies are optional for local use. Docker mounts the root `cookies.txt`; supply a Netscape-format cookie file there if required. Cookies are copied into a job's private temporary directory so the original can stay read-only. Never commit account cookies.

## Reliability and limitations

Downloads use separate temporary folders and absolute output paths. Errors, completion, and cancellation appear in the page. Cancellation is cooperative: it takes effect at the next downloader/postprocessor hook and may wait for network requests or FFmpeg. Finished files are retained. Jobs and their status history are lost on restart. Video selection requires an MP4-compatible source at the chosen resolution.

Some YouTube videos require a supported JavaScript runtime (such as Deno), authentication, or additional yt-dlp configuration; these are not bundled here. Live provider downloads need an integration check on the deployment host.

## Verification

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Tests cover page rendering, settings propagation, invalid URLs, safe deletion, event streaming, and failure reporting with mocked downloads.

## Suggested next functionality

1. A persistent queue with retry and a concurrency limit, so large playlists and restarts are manageable.
2. Library search, sorting, and storage usage.
3. A pre-download preview showing title, duration, available quality, and estimated size.
4. Authentication and request/network restrictions before any shared or remote deployment.

