import yt_dlp
import sys

COOKIE_FILE = 'cookies.txt'
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

def list_formats(url: str):
    """Print available formats and exit."""
    yt_dlp.YoutubeDL({'cookiefile': COOKIE_FILE, 'http_headers': HTTP_HEADERS}).list_formats(url)
    sys.exit(0)

def download_youtube(url: str, to_mp3: bool = True):
    """Download a YouTube URL as MP3 or MP4, with fallbacks."""
    if to_mp3:
        fmt = 'bestaudio/best'
        postp = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        # try separate MP4 video + M4A audio, then MP4 combined, then any best
        fmt = 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b'
        postp = []  # merging is automatic

    ydl_opts = {
        'format': fmt,
        'cookiefile': COOKIE_FILE,
        'http_headers': HTTP_HEADERS,
        'postprocessors': postp,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        print(f"[ERROR] Download failed: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

def main():
    while True:
        choice = input("Enter 1=MP3, 2=MP4, f=list formats, q=quit: ").strip().lower()
        if choice == 'q':
            print("Goodbye!")
            break
        elif choice == 'f':
            url = input("Enter the YouTube URL to inspect: ").strip()
            list_formats(url)
        elif choice in {'1', '2'}:
            url = input("Enter the YouTube URL: ").strip()
            download_youtube(url, to_mp3=(choice == '1'))
        else:
            print("Invalid choice, please enter 1, 2, f, or q.")

if __name__ == '__main__':
    main()
