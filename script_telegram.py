from flask import Flask
from dotenv import load_dotenv
import os
import aiohttp
import datetime
import logging
import pytz
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import asyncio
import threading

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, World!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Carica variabili d'ambiente
load_dotenv("C:\\Users\\Pc\\Desktop\\TelegramBot\\script_dati.env")

# Configurazioni
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ITALY_TZ = pytz.timezone("Europe/Rome")
POST_HOUR = 14
POST_MINUTE = 0

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Ottiene l'ultimo video caricato (normale, non live)
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
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching video: {e}")
        return None, None

# Ottiene l'ultima diretta
async def get_latest_live():
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={CHANNEL_ID}&eventType=live&type=video&key={YOUTUBE_API_KEY}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

        logger.info(f"Live API Response: {data}")

        if "items" in data and data["items"]:
            video_id = data["items"][0]["id"]["videoId"]
            title = data["items"][0]["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"
            return title, url
        else:
            return None, None
    except Exception as e:
        logger.error(f"Errore ottenendo la diretta: {e}")
        return None, None

# Posta l’ultimo video su Telegram
async def post_to_telegram():
    title, url = await get_latest_video()
    if title and url:
        message = f"🎥 Ultimo video: {title}\n🔴 Guarda qui: {url}"
    else:
        message = "Nessun video recente trovato."
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
        logger.info("Messaggio inviato su Telegram.")
    except Exception as e:
        logger.error(f"Errore nell'invio del messaggio su Telegram: {e}")

# Loop per il post automatico
async def telegram_loop():
    while True:
        now_utc = datetime.datetime.now(pytz.utc)
        now_italy = now_utc.astimezone(ITALY_TZ)

        logger.info(f"Orario italiano attuale: {now_italy.strftime('%A %H:%M:%S')}")

        if now_italy.weekday() == 5 and now_italy.hour == POST_HOUR and now_italy.minute == POST_MINUTE and now_italy.second == 0:
            await post_to_telegram()
            await asyncio.sleep(60)
        await asyncio.sleep(1)

# Comando !ultima via Telegram
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip().lower() == "!ultima":
        title, url = await get_latest_live()
        if title and url:
            message = f"📺 Ultima diretta: {title}\n🔴 Guarda qui: {url}"
        else:
            message = "⚠️ Nessuna diretta trovata recentemente."
        await update.message.reply_text(message)

# Listener dei messaggi Telegram
async def telegram_listener():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    await application.run_polling()

# Avvia entrambi i processi
def run_telegram():
    asyncio.run(asyncio.gather(
        telegram_loop(),
        telegram_listener()
    ))

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    telegram_thread = threading.Thread(target=run_telegram)

    flask_thread.start()
    telegram_thread.start()

    flask_thread.join()
    telegram_thread.join()
