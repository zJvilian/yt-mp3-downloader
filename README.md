# yt-mp3-downloader

A modern web interface for downloading YouTube videos as MP3 (audio) or MP4 (video) with built-in media players.  
Built with Flask and yt-dlp, featuring a responsive design and packaged with Docker for easy deployment.

---

## Features

- **Multi-format downloads**: Download YouTube URLs as MP3 (audio-only) or MP4 (video + audio)  
- **Organized storage**: Automatically organizes MP3s in `mp3s/` and MP4s in `mp4s/` directories  
- **Built-in media players**: 
  - Audio player for MP3 files with playback controls
  - Video modal player for MP4 files with responsive sizing
- **File management**: Lists all downloaded files with direct download links
- **Cookie support**: Handles authenticated/premium videos using `cookies.txt`
- **Responsive design**: Mobile-friendly interface that works on all devices
- **Progress tracking**: Real-time download progress updates
- **Error handling**: User-friendly error messages and validation
- **Docker ready**: One-command deployment with Docker

---

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/yt-mp3-downloader.git
cd yt-mp3-downloader

# Build and run with Docker
docker build -t yt-mp3-downloader .
docker run -p 5000:5000 -v $(pwd)/downloads:/app/downloads yt-mp3-downloader
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/yt-mp3-downloader.git
cd yt-mp3-downloader

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Visit `http://localhost:5000` in your browser.

---

## Repository Structure

```
yt-mp3-downloader/
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css          # Main application styles
│   │   │   └── video.css          # Video player modal styles
│   │   └── js/
│   │       └── main.js            # Frontend JavaScript functionality
│   ├── templates/
│   │   └── index.html             # Main application template
│   └── __init__.py
├── downloads/
│   ├── mp3s/                      # Downloaded MP3 files
│   └── mp4s/                      # Downloaded MP4 files
├── app.py                         # Main Flask application
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker configuration
├── cookies.txt                    # YouTube authentication cookies (optional)
└── README.md                      # This file
```

---

## Usage

1. **Enter a YouTube URL** in the input field
2. **Select format**: Choose between MP3 (audio) or MP4 (video)
3. **Click Download** to start the process
4. **Monitor progress** with the real-time progress bar
5. **Access files** from the downloaded files list below
6. **Play media** using the built-in players:
   - Click MP3 files to play in the audio player
   - Click MP4 files to open in the video modal player

---

## Configuration

### Cookie Support
For downloading age-restricted or premium content, add your YouTube cookies to `cookies.txt`:

```bash
# Export cookies from your browser (Chrome/Firefox extension recommended)
# Save as cookies.txt in the project root directory
```

### Environment Variables
- `FLASK_ENV`: Set to `development` for debug mode
- `PORT`: Server port (default: 5000)

---

## Technical Details

- **Backend**: Flask (Python web framework)
- **Downloader**: yt-dlp (YouTube download library)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Media Players**: HTML5 audio/video with custom controls
- **Styling**: Responsive CSS with modal overlays
- **File Handling**: Organized directory structure with metadata

---

## Browser Compatibility

- Chrome/Chromium 60+
- Firefox 55+
- Safari 12+
- Edge 79+

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

This tool is for educational purposes only. Please respect YouTube's Terms of Service and copyright laws. Only download content you have permission to download.

