# Use official Python slim image
FROM python:3.11-slim

# Set working dir
WORKDIR /app

# Install system deps for ffmpeg (needed by yt-dlp postprocessor) 
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code, cookies, templates, etc.
COPY . .

# Ensure mp3s folder exists
RUN mkdir -p /app/mp3s

# Expose Flask port
EXPOSE 5000

# Launch the app
CMD ["python", "app.py"]
