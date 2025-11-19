import asyncio
import os
import re
import telegram
import yt_dlp
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, YOUTUBE_CHANNEL_URL

# --- Bot Configuration ---
# Directory to store downloaded videos
DOWNLOAD_DIR = "downloads"
# File to keep track of processed video URLs
PROCESSED_VIDEOS_FILE = "processed_videos.txt"
# Time to wait between checking for new videos (in seconds)
CHECK_INTERVAL = 300  # 5 minutes

async def download_short(video_url: str) -> str | None:
    """
    Downloads a YouTube short if it's less than 61 seconds long.

    Args:
        video_url: The URL of the YouTube video.

    Returns:
        The file path of the downloaded video, or None if download fails or the video is too long.
    """
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "match_filter": lambda info: None if info.get("duration", 0) < 61 else "The video is not a short (too long).",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            return ydl.prepare_filename(info)
    except yt_dlp.utils.DownloadError as e:
        print(f"Error downloading {video_url}: {e}")
        return None

async def get_latest_shorts(channel_url: str, limit: int = 5) -> list[str]:
    """
    Fetches the latest video URLs from a YouTube channel.
    Args:
        channel_url: The URL of the YouTube channel.
        limit: The maximum number of recent videos to check.
    Returns:
        A list of video URLs.
    """
    ydl_opts = {
        # "extract_flat": True, # Removed to fetch full metadata for reliability
        "playlistend": limit,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        return [
            entry.get("webpage_url")
            for entry in info.get("entries", [])
            if entry and entry.get("webpage_url")
        ]

async def main():
    """
    The main function to run the bot.
    """
    # --- Initialization ---
    # Create downloads directory if it doesn't exist
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    # Load processed video IDs
    processed_videos = set()
    if os.path.exists(PROCESSED_VIDEOS_FILE):
        with open(PROCESSED_VIDEOS_FILE, "r") as f:
            processed_videos = set(line.strip() for line in f)

    # Initialize Telegram bot
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    # --- Main Loop ---
    while True:
        print("Checking for new shorts...")
        # Append /shorts to the channel URL to specifically fetch from the shorts feed
        shorts_feed_url = YOUTUBE_CHANNEL_URL.rstrip('/') + "/shorts"
        latest_shorts = await get_latest_shorts(shorts_feed_url)

        for short_url in latest_shorts:
            if not short_url:
                continue

            # Extract video ID using regex for robustness
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", short_url)
            if not match:
                print(f"Could not extract video ID from {short_url}. Skipping.")
                continue
            video_id = match.group(1)

            if video_id not in processed_videos:
                print(f"New short found: {short_url}")
                video_path = await download_short(short_url)

                if video_path:
                    try:
                        with open(video_path, "rb") as video_file:
                            await bot.send_video(
                                chat_id=TELEGRAM_CHANNEL_ID,
                                video=video_file,
                                caption=f"New short from {YOUTUBE_CHANNEL_URL}"
                            )
                        print(f"Successfully sent {video_path} to Telegram.")

                        # Add to processed list and file
                        processed_videos.add(video_id)
                        with open(PROCESSED_VIDEOS_FILE, "a") as f:
                            f.write(f"{video_id}\n")

                    except Exception as e:
                        print(f"Failed to send video to Telegram: {e}")
                    finally:
                        # Clean up the downloaded file
                        if os.path.exists(video_path):
                            os.remove(video_path)
                else:
                    print(f"Skipping {short_url} (either too long or download failed).")
                    # Mark as processed to avoid re-checking
                    processed_videos.add(video_id)
                    with open(PROCESSED_VIDEOS_FILE, "a") as f:
                        f.write(f"{video_id}\n")

        print(f"Waiting for {CHECK_INTERVAL} seconds before next check.")
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())