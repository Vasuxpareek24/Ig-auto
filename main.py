import os
import time
import json
from pytube import Playlist, YouTube
from instagrapi import Client
from dotenv import load_dotenv

# Load credentials
load_dotenv()
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

# Setup
PLAYLIST_URL = "https://youtube.com/playlist?list=PLzlOHuvgTpSY4_88tPkqV9BKMt-J2Ivnm&si=zXefeH20MrI7dN6f"
DOWNLOAD_DIR = "downloads"
POSTED_FILE = "posted.json"

# Ensure folders and files exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
if not os.path.exists(POSTED_FILE):
    with open(POSTED_FILE, "w") as f:
        json.dump([], f)

def load_posted():
    with open(POSTED_FILE) as f:
        return set(json.load(f))

def save_posted(posted_ids):
    with open(POSTED_FILE, "w") as f:
        json.dump(list(posted_ids), f)

def download_video(video):
    try:
        yt = YouTube(video.watch_url)
        stream = yt.streams.filter(file_extension="mp4", progressive=True).order_by("resolution").desc().first()
        output_path = os.path.join(DOWNLOAD_DIR, yt.title + ".mp4")
        stream.download(output_path=DOWNLOAD_DIR, filename=yt.title + ".mp4")
        return output_path, yt.title
    except Exception as e:
        print("❌ Download failed:", e)
        return None, None

def login_instagram():
    cl = Client()
    cl.login(USERNAME, PASSWORD)
    return cl

def upload_reel(cl, video_path, caption):
    try:
        cl.clip_upload(video_path, caption)
        print(f"✅ Uploaded: {caption}")
        os.remove(video_path)
    except Exception as e:
        print("❌ Upload failed:", e)

# Start
client = login_instagram()
posted_ids = load_posted()
playlist = Playlist(PLAYLIST_URL)

print(f"🔁 Total videos in playlist: {len(playlist.video_urls)}")

while True:
    for video in playlist.videos:
        video_id = video.video_id
        if video_id in posted_ids:
            print(f"⏭️ Skipping already posted: {video.title}")
            continue

        print(f"📥 Downloading: {video.title}")
        video_path, title = download_video(video)

        if video_path:
            print(f"🚀 Uploading: {title}")
            upload_reel(client, video_path, title)
            posted_ids.add(video_id)
            save_posted(posted_ids)

            print("⏳ Sleeping 5 hours...")
            time.sleep(5 * 60 * 60)
        else:
            print("❌ Skipping due to download error.")

    print("✅ All videos checked. Restarting in 30 minutes.")
    time.sleep(30 * 60)
