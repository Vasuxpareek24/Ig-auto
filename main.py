import os
import time
import json
import shutil
from pytube import Playlist
from instagrapi import Client
import yt_dlp

# === SETTINGS ===
USERNAME = os.environ.get("INSTA_USER")
PASSWORD = os.environ.get("INSTA_PASS")
PLAYLIST_URL = os.environ.get("YT_PLAYLIST") or "https://youtube.com/playlist?list=PLzlOHuvgTpSY4_88tPkqV9BKMt-J2Ivnm&si=zXefeH20MrI7dN6f"  # replace with actual default if needed
SESSION_FILE = "insta_session.json"
VIDEO_FILE = "reel.mp4"
THUMBNAIL_FILE = VIDEO_FILE + ".jpg"
DELAY_MINUTES = 5

# === UTILS ===
def clean_old_files():
    for file in [VIDEO_FILE, THUMBNAIL_FILE]:
        if os.path.exists(file):
            os.remove(file)


def download_video(url, output_path=VIDEO_FILE):
    ydl_opts = {
        'outtmpl': output_path,
        'quiet': True,
        'format': 'mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
        return False


def upload_to_instagram(video_path, caption, cl):
    try:
        print(f"\n🚀 Uploading to Instagram...")
        cl.clip_upload(video_path, caption=caption)
        print("✅ Uploaded")
        return True
    except Exception as e:
        print(f"❌ Failed: {caption} — {e}")
        return False


# === MAIN ===
def main():
    cl = Client()
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(USERNAME, PASSWORD)
        except:
            print("🔐 Session invalid, re-login required")
            cl.login(USERNAME, PASSWORD)
            cl.dump_settings(SESSION_FILE)
    else:
        cl.login(USERNAME, PASSWORD)
        cl.dump_settings(SESSION_FILE)

    uploaded = set()

    while True:
        print("\n🔁 Checking playlist...")
        playlist = Playlist(PLAYLIST_URL)

        for video in playlist.videos:
            title = video.title
            url = video.watch_url

            if url in uploaded:
                continue

            print(f"\n📥 Downloading: {title}")
            clean_old_files()
            success = download_video(url)

            if success:
                uploaded.add(url)
                uploaded.add(video.video_id)
                upload_to_instagram(VIDEO_FILE, title, cl)
                clean_old_files()
            else:
                print(f"⏩ Skipping due to download failure: {title}")

        print(f"⏳ Waiting {DELAY_MINUTES} minutes before checking again...")
        time.sleep(DELAY_MINUTES * 60)


if __name__ == '__main__':
    main()
