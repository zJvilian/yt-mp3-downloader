FROM python:3.11-slim
WORKDIR /app

# Install ffmpeg for yt-dlp postprocessing
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir --upgrade yt-dlp

COPY . .

EXPOSE 5000
ENV FLASK_APP=app

CMD ["sh", "-c", "mkdir -p /app/mp3s /app/mp4s && flask run --host=0.0.0.0 --port=5000"]
