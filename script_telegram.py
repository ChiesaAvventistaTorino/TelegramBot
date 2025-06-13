import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask
import pytz
import aiohttp
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)

# Flask app solo per status
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot attivo!"

# Carica variabili d'ambiente
load_dotenv("C:\\Users\\Pc\\Desktop\\TelegramBot\\script_dati.env")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ITALY_TZ = pytz.timezone("Europe/Rome")

# Configura logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Funzione per prendere l'ultimo video dal canale YouTube
async def get_latest_video():
    url = (
        f"https://www.googleapis.com/youtube/v3/search?"
        f"part=snippet&channelId={CHANNEL_ID}&type=video&order=date&key={YOUTUBE_API_KEY}&maxResults=1"
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
        if "items" in data and data["items"]:
            video = data["items"][0]
            video_id = video["id"]["videoId"]
            video_title = video["snippet"]["title"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            return video_title, video_url
        else:
            return None, None
    except Exception as e:
        logger.error(f"Errore fetching video: {e}")
        return None, None

# Handler per comando /ultima
async def ultima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Ricevuto comando /ultima da {update.effective_user.id}")
    title, url = await get_latest_video()
    if title and url:
        msg = f"🎥 Ultimo video: {title}\n🔴 Guarda qui: {url}"
    else:
        msg = "Nessun video recente trovato."
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

# Funzione per invio programmato (esempio: tutti i sabati alle 14:00)
async def scheduled_post(application):
    while True:
        now = datetime.now(ITALY_TZ)
        if now.weekday() == 5 and now.hour == 14 and now.minute == 0:
            title, url = await get_latest_video()
            if title and url:
                message = f"🎥 Ultimo video (post automatico): {title}\n🔴 Guarda qui: {url}"
            else:
                message = "Nessun video recente trovato."
            try:
                await application.bot.send_message(chat_id=CHAT_ID, text=message)
                logger.info("Post automatico inviato.")
            except Exception as e:
                logger.error(f"Errore invio post automatico: {e}")
            await asyncio.sleep(60)  # evita doppi invii nel minuto
        await asyncio.sleep(10)  # check ogni 10 secondi

async def main():
    # Crea applicazione telegram bot
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Aggiungi handler comando /ultima
    application.add_handler(CommandHandler("ultima", ultima))

    # Avvia Flask in thread separato
    import threading
    def run_flask():
        port = int(os.getenv("PORT", 5000))
        app.run(host="0.0.0.0", port=port)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Avvia task per post programmato
    asyncio.create_task(scheduled_post(application))

    # Avvia bot telegram
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
