import yt_dlp
import time
import os
import logging
from instagrapi import Client
from flask import Flask
import threading
import subprocess

# ========== Configuration ==========
playlist_url = "https://youtube.com/playlist?list=PLzlOHuvgTpSY4_88tPkqV9BKMt-J2Ivnm&si=zXefeH20MrI7dN6f"
wait_seconds = 5 * 60 * 60  # 5 hours
output_folder = "downloads"
video_path = os.path.join(output_folder, "reel.mp4")
uploaded_file = "uploaded_titles.txt"
session_file = "insta_session.json"
caption = "Follow For Such Amazing Content 😋 #Viral #Like #Follow #Meme... This Reel Is Uploaded Via Automation If You Wanna Learn Then Dm Me Asap"

# ========== Setup ==========
app = Flask(__name__)
os.makedirs(output_folder, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Load credentials from environment variables
username = os.getenv("INSTA_USERNAME", "cricko.fun")
password = os.getenv("INSTA_PASSWORD", "@Vasu2412")

cl = Client()

# Check for ffmpeg
def check_ffmpeg():
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        logging.info(f"FFmpeg version: {result.stdout.splitlines()[0]}")
        return True
    except Exception as e:
        logging.error(f"FFmpeg not found: {e}")
        return False

ffmpeg_available = check_ffmpeg()

# Instagram login with session handling
if os.path.exists(session_file):
    cl.load_settings(session_file)
    try:
        cl.login(username, password)
        logging.info("✅ Session restored.")
    except Exception as e:
        logging.error(f"Session restore failed: {e}")
        cl.login(username, password)
        cl.dump_settings(session_file)
else:
    cl.login(username, password)
    cl.dump_settings(session_file)

def get_uploaded_titles():
    if not os.path.exists(uploaded_file):
        return set()
    with open(uploaded_file, "r", encoding='utf-8') as f:
        return set(line.strip() for line in f)

def mark_as_uploaded(title):
    with open(uploaded_file, "a", encoding='utf-8') as f:
        f.write(title + "\n")

def cleanup_downloads():
    for file in os.listdir(output_folder):
        file_path = os.path.join(output_folder, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
            logging.info(f"🧹 Cleaned up: {file_path}")

def is_video_available(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {'quiet': True, 'simulate': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=False)
        return True
    except Exception as e:
        logging.info(f"Video {video_id} unavailable: {e}")
        return False

def download_video(url):
    cleanup_downloads()
    ydl_opts = {
        'outtmpl': video_path,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' if ffmpeg_available else 'best[ext=mp4]',
        'merge_output_format': 'mp4' if ffmpeg_available else None,
        'quiet': False,  # Verbose output for debugging
        'noplaylist': True,
        'retries': 3,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return ydl.extract_info(url, download=False)
    except Exception as e:
        logging.error(f"Failed to download {url}: {str(e)}")
        raise

def background_job():
    extract_opts = {
        'extract_flat': True,
        'quiet': False,  # Verbose output for debugging
        'skip_download': True,
    }

    while True:
        uploaded_titles = get_uploaded_titles()

        try:
            with yt_dlp.YoutubeDL(extract_opts) as ydl:
                playlist = ydl.extract_info(playlist_url, download=False)
                videos = playlist.get('entries', [])
        except Exception as e:
            logging.error(f"Failed to fetch playlist: {e}")
            time.sleep(60)  # Wait 1 minute before retrying
            continue

        if not videos:
            logging.info("No videos found in playlist. Sleeping...")
            time.sleep(wait_seconds)
            continue

        for entry in videos:
            title = entry.get('title')
            video_id = entry.get('id')

            if not title or not video_id or title in uploaded_titles:
                logging.info(f"Skipping {title or video_id}: Already uploaded or invalid")
                continue

            if not is_video_available(video_id):
                logging.info(f"Skipping {title}: Video unavailable")
                continue

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            try:
                logging.info(f"📥 Downloading: {title}")
                info = download_video(video_url)

                logging.info("🚀 Uploading to Instagram...")
                cl.clip_upload(video_path, caption=caption)
                logging.info(f"✅ Uploaded: {title}")

                mark_as_uploaded(title)
                break  # Upload one video, then wait

            except Exception as e:
                logging.error(f"❌ Error processing {title}: {e}")
                continue  # Skip to next video on error

        logging.info(f"⏳ Sleeping {wait_seconds // 3600}h...")
        time.sleep(wait_seconds)

@app.route("/")
def home():
    return "🤖 Instagram Auto Upload Bot Running!"

@app.route("/test-download/<video_id>")
def test_download(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        download_video(video_url)
        return f"Downloaded {video_id}"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    threading.Thread(target=background_job, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
