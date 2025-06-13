import os
import logging
import datetime
import pytz
from dotenv import load_dotenv
import aiohttp
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram import Update

load_dotenv("C:\\Users\\Pc\\Desktop\\TelegramBot\\script_dati.env")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

ITALY_TZ = pytz.timezone("Europe/Rome")
POST_HOUR = 14
POST_MINUTE = 0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_latest_video():
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={CHANNEL_ID}&type=video&order=date&key={YOUTUBE_API_KEY}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

        logger.info(f"API Response: {data}")

        if "items" in data and data["items"]:
            video_id = data["items"][0]["id"]["videoId"]
            video_title = data["items"][0]["snippet"]["title"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            logger.info(f"Found latest video: {video_title} ({video_url})")
            return video_title, video_url
        else:
            logger.info("No videos found.")
        return None, None
    except Exception as e:
        logger.error(f"Error fetching video: {e}")
        return None, None

async def post_latest_video(app):
    title, url = await get_latest_video()
    if title and url:
        message = f"🎥 Ultimo video: {title}\n🔴 Guarda qui: {url}"
    else:
        message = "Nessun video recente trovato."
    try:
        await app.bot.send_message(chat_id=CHAT_ID, text=message)
        logger.info("Messaggio video inviato su Telegram")
    except Exception as e:
        logger.error(f"Errore invio messaggio Telegram: {e}")

async def scheduled_post(app):
    while True:
        now_utc = datetime.datetime.now(pytz.utc)
        now_italy = now_utc.astimezone(ITALY_TZ)
        logger.info(f"Orario italiano attuale: {now_italy.strftime('%A %H:%M:%S')}")
        if now_italy.weekday() == 5 and now_italy.hour == POST_HOUR and now_italy.minute == POST_MINUTE:
            await post_latest_video(app)
            await asyncio.sleep(60)
        await asyncio.sleep(1)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text == "ciao":
        await update.message.reply_text("attivo")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    # Avvia la task schedulata in parallelo
    app.create_task(scheduled_post(app))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
