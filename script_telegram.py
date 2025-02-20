from dotenv import load_dotenv
import os
import aiohttp
import datetime
import logging
from telegram import Bot
import asyncio

# Load environment variables
load_dotenv("C:\\Users\\Pc\\Desktop\\TelegramBot\\script_dati.env")

# Configurations
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
POST_HOUR = 14  # Set the hour (24-hour format)
POST_MINUTE = 20  # Set the minute

# Initialize bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def get_latest_video():
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={CHANNEL_ID}&type=video&order=date&key={YOUTUBE_API_KEY}"
    try:
        # Making an asynchronous request to the YouTube API
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

        logger.info(f"API Response: {data}")  # Debugging line

        # Check if we have videos
        if "items" in data and data["items"]:
            video_id = data["items"][0]["id"]["videoId"]
            video_title = data["items"][0]["snippet"]["title"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            logger.info(f"Found latest video: {video_title} ({video_url})")
            return video_title, video_url
        else:
            logger.info("No videos found.")
        return None, None
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching video: {e}")
        return None, None

async def post_to_telegram():
    title, url = await get_latest_video()
    if title and url:
        message = f"🎥 Latest Video: {title}\n🔴 Watch here: {url}"
        try:
            response = await bot.send_message(chat_id=CHAT_ID, text=message)
            logger.info("Latest video posted to Telegram.")
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
    else:
        message = "No recent video found."
        try:
            await bot.send_message(chat_id=CHAT_ID, text=message)
            logger.info("No video message sent.")
        except Exception as e:
            logger.error(f"Error sending no-video message to Telegram: {e}")

async def main():
    while True:
        now = datetime.datetime.now()
        logger.info(f"Current time: {now.hour}:{now.minute}:{now.second}")  # Logging current time for debugging

        # Check if it's the exact second when we want to post
        if now.hour == POST_HOUR and now.minute == POST_MINUTE and now.second == 0:
            await post_to_telegram()
            break
        await asyncio.sleep(1)  # Check every second

if __name__ == "__main__":
    asyncio.run(main())