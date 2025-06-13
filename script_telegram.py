from flask import Flask
from dotenv import load_dotenv
import os
import aiohttp
import datetime
import logging
import pytz  # Libreria per il fuso orario
from telegram import Bot
import asyncio
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, World!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))  # Usa la porta di Render o default 5000
    app.run(host="0.0.0.0", port=port)

# Carica le variabili d'ambiente
load_dotenv("C:\\Users\\Pc\\Desktop\\TelegramBot\\script_dati.env")

# Configurazioni
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Imposta il fuso orario italiano (CET/CEST)
ITALY_TZ = pytz.timezone("Europe/Rome")

# Orario del post in formato 24h (ora italiana)
POST_HOUR = 14  # Ora italiana (CET/CEST)
POST_MINUTE = 00  # Minuto

# Inizializza il bot Telegram
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Configurazione logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def get_latest_video():
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={CHANNEL_ID}&type=video&order=date&key={YOUTUBE_API_KEY}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

        logger.info(f"API Response: {data}")  # Debugging

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
        message = f"🎥 Ultimo video: {title}\n🔴 Guarda qui: {url}"
        try:
            await bot.send_message(chat_id=CHAT_ID, text=message)
            logger.info("Ultimo video pubblicato su Telegram.")
        except Exception as e:
            logger.error(f"Errore nell'invio del messaggio su Telegram: {e}")
    else:
        message = "Nessun video recente trovato."
        try:
            await bot.send_message(chat_id=CHAT_ID, text=message)
            logger.info("Messaggio 'nessun video' inviato.")
        except Exception as e:
            logger.error(f"Errore nell'invio del messaggio su Telegram: {e}")
async def telegram_loop():
    while True:
        now_utc = datetime.datetime.now(pytz.utc)  # Ottieni l'orario UTC
        now_italy = now_utc.astimezone(ITALY_TZ)  # Converti all'orario italiano

        logger.info(f"Orario italiano attuale: {now_italy.strftime('%A %H:%M:%S')}")  # Formato 24 ore

        if now_italy.weekday() == 5 and now_italy.hour == POST_HOUR and now_italy.minute == POST_MINUTE and now_italy.second == 0:
            await post_to_telegram()
            await asyncio.sleep(60)  # Evita duplicati nello stesso minuto
        await asyncio.sleep(1)

def run_telegram():
    asyncio.run(telegram_loop())

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    telegram_thread = threading.Thread(target=run_telegram)

    flask_thread.start()
    telegram_thread.start()

    flask_thread.join()
    telegram_thread.join()