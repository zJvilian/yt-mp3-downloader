# yt-mp3-downloader

A simple web interface for downloading YouTube videos as MP3 (audio) or MP4 (video).  
Built with Flask and yt-dlp, and packaged into Docker for easy deployment on any host or NAS.

---

## Features

- Download YouTube URLs as MP3 (audio-only) or MP4 (video + audio)  
- Keeps MP3s in `mp3s/` and MP4s in `mp4s/` directories  
- Simple HTML form with dropdown to choose format
- Lists all downloaded files with links to download
- Built-in audio player for MP3s and video player for MP4s
- Cookie support for authenticated/premium videos (`cookies.txt`)
- Dockerized for one-command deployment

---

## Repository layout

