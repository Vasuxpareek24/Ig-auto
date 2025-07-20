import yt_dlp
import time
import os
import logging
from instagrapi import Client
from getpass import getpass

# Configurations
playlist_url = "https://youtube.com/playlist?list=PLGMAm7BxCkldg1axtD4HdzJtjBnWpqE51"
wait_seconds = 5 * 60 * 60  # 5 hours
output_folder = "downloads"
video_path = os.path.join(output_folder, "reel.mp4")
file_name = "shorts_data.txt"
uploaded_file = "uploaded_titles.txt"

caption = "Follow For Such Amazing Content 😋 #Viral #Like #Follow #Meme #Tend #Py................. This Reel Is Posted By Automation If You Wanna Try This Automation Then Dm me asap"

# Setup
os.makedirs(output_folder, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')

# Login to Instagram

username = "cricko.fun"
password = "@Vasu2412"
session_file = "insta_session.json"

cl = Client()

# Try loading session first
if os.path.exists(session_file):
    cl.load_settings(session_file)
    try:
        cl.login(username, password)
        logging.info("✅ Session restored and logged in.")
    except Exception as e:
        logging.warning(f"⚠️ Failed with saved session: {e}, retrying login...")
        cl.login(username, password)
        cl.dump_settings(session_file)
else:
    cl.login(username, password)
    cl.dump_settings(session_file)

def download_video(url):
    # Delete old video if exists
    if os.path.exists(video_path):
        os.remove(video_path)

    if os.path.exists("reel.mp4.jpg"):
        os.remove("reel.mp4.jpg")

    ydl_opts = {
        'outtmpl': video_path,
        'quiet': True,
        'format': 'mp4/best',
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=True)

def save_info(info):
    with open(file_name, 'a', encoding='utf-8') as f:
        f.write(f"Title     : {info.get('title')}\n")
        f.write(f"Link      : https://www.youtube.com/watch?v={info.get('id')}\n")
        f.write(f"Duration  : {info.get('duration')} seconds\n")
        f.write(f"Views     : {info.get('view_count')}\n")
        f.write("-" * 40 + "\n")

def get_uploaded_titles():
    if not os.path.exists(uploaded_file):
        return set()
    with open(uploaded_file, "r", encoding='utf-8') as f:
        return set(line.strip() for line in f)

def mark_as_uploaded(title):
    with open(uploaded_file, "a", encoding='utf-8') as f:
        f.write(title + "\n")

def main():
    extract_opts = {
        'extract_flat': True,
        'quiet': True,
        'skip_download': True
    }

    while True:
        uploaded_titles = get_uploaded_titles()

        with yt_dlp.YoutubeDL(extract_opts) as ydl:
            playlist = ydl.extract_info(playlist_url, download=False)
            videos = playlist.get('entries', [])

        success = False

        for entry in videos:
            title = entry.get('title')
            video_id = entry.get('id')

            if not title or not video_id:
                continue

            if title in uploaded_titles:
                logging.info(f"⏩ Already uploaded: {title}")
                continue

            video_url = f"https://www.youtube.com/watch?v={video_id}"
            try:
                logging.info(f"📥 Downloading: {title}")
                info = download_video(video_url)
                save_info(info)

                logging.info("🚀 Uploading to Instagram...")
                cl.clip_upload(video_path, caption=caption)
                logging.info(f"✅ Uploaded: {title}")

                mark_as_uploaded(title)
                success = True
                break  # Stop loop after successful upload

            except Exception as e:
                logging.error(f"❌ Failed: {title} — {e}")
                continue  # Try next video

        if success:
            logging.info(f"⏳ Waiting {wait_seconds//3600} hours before next upload...\n")
            time.sleep(wait_seconds)
        else:
            logging.info("⚠️ No valid video found. Retrying in 10 minutes...")
            time.sleep(600)

if __name__ == "__main__":
    main()
