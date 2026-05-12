from telegram import (
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)
from functools import wraps
from asyncio import sleep
import time
import shutil
import datetime as dt
import json
import logging, sys, os
import html
import traceback
from telegram.constants import ParseMode
# logger = logging.getLogger(__name__)

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

from warnings import filterwarnings
from telegram.warnings import PTBUserWarning
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

import ytube_down, bcamp_down

from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("TOKEN") # os.environ["TOKEN"]
ADMINS = list(map(int, os.getenv("ADMINS", "").split(",")))
DEVELOPER = os.getenv("DEVELOPER")
DOWNFOLDER = "down-music"
LENGHT = 61


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "При обработке update возникла ошибка: \n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n"
        f"<pre>context.user_data = {html.escape(str(context.bot_data))}</pre>\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    await context.bot.send_message(
        chat_id=DEVELOPER, text=message, parse_mode=ParseMode.HTML
    )

def detect_error(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except BaseException as err:
            await update.message.reply_text(
                "Извините, произошла непредвиденная ошибка. Попробуйте снова.")
            text = f'Ошибка в функции {func.__name__}: {err}'
            await context.bot.send_message(479917441, text)
            logging.info(text)
            return
    return wrapped

def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMINS:
            await update.effective_message.reply_text('Извините, доступ к боту закрыт.')
            logging.info(f"Неавторизованный доступ запрещен для {user_id}.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped


# @detect_error
@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Добро пожаловать!\n" \
        "Отправьте название песни или ссылку.\n"
        "Пример принимаемых ссылок.\n"
        "YOUTUBE\n"
        "Скачивание первого попавшего в ссылке трека:\n"
        "`music.youtube.com/watch?v=abc-123`\n"
        "Скачать 10 первых треков по ссылке:\n"
        "`music.youtube.com/watch?v=abc-123 10`\n"
        "Скачать весь плейлист:\n"
        "`music.youtube.com/playlist?list=abc123`\n"
        "Скачать 10 первых треков из плейлиста:\n"
        "`music.youtube.com/playlist?list=abc123 10`\n"
        "BANDCAMP\n"
        "Скачать плейлист:\n"
        "`artist.bandcamp.com/album/name-album`\n"
        "Скачать конкретный трек:\n"
        "`artist.bandcamp.com/track/name-track`\n"
    )
    await update.message.reply_text(text=text, parse_mode="Markdown")

async def set_commands(context: ContextTypes.DEFAULT_TYPE):
    commands = [
        ("start", "info"),
    ]
    await context.bot.set_my_commands(commands)

# async def identify_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     pass

@restricted
async def youtube_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text.split()
    link = message[0]
    count = None if len(message) == 1 else int(message[1])
    uniq_time = str(time.time()).replace(".", "")
    uniq_path = os.path.join(DOWNFOLDER, uniq_time)

    if "youtube.com/watch" in link:
        items = "1" if not count else ",".join(map(str, range(1, count+1)))
    elif "youtube.com/playlist" in link:
        items = None if not count else ",".join(map(str, range(1, count+1)))
    else:
        await update.message.reply_text("Некорректный ввод ссылки.")
        return
    
    ytube_down.download(url=link, playlist_items=items, path=uniq_path)

    track_list = os.listdir(uniq_path)
    track_list = sorted(track_list, key=lambda t: os.path.getmtime(os.path.join(uniq_path, t)))
    if not track_list:
        await update.message.reply_text("Не удалось найти.")
        return
    for track in track_list:
        if len(track) > LENGHT:
            name = track.replace(".mp3", "")[:LENGHT+1] + "...mp3"
        else:
            name = track
        try:
            await update.message.reply_audio(os.path.join(uniq_path, track), title=name) 
            await sleep(1)
        except:
            print("ERROR DOWNLOAD")

    shutil.rmtree(uniq_path)

@restricted
async def song_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    song = update.message.text
    link = ytube_down.get_track_url(song_name=song)

    uniq_time = str(time.time()).replace(".", "")
    uniq_path = os.path.join(DOWNFOLDER, uniq_time)

    if link:
        ytube_down.download(url=link, path=uniq_path)
        track = os.listdir(uniq_path)[0]

        if len(track) > LENGHT:
            name = track.replace(".mp3", "")[:LENGHT+1] + "...mp3"
        else:
            name = track

        try:
            await update.message.reply_audio(os.path.join(uniq_path, track), title=name) 
            await sleep(1)
        except:
            print("ERROR DOWNLOAD")
            
    else:
        await update.message.reply_text("Трек не найден.")

    shutil.rmtree(uniq_path)

@restricted
async def bandcamp_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    link = update.message.text
    uniq_time = str(time.time()).replace(".", "")
    uniq_path = os.path.join(DOWNFOLDER, uniq_time)

    bcamp_down.download(link=link, path=uniq_path)

    track_list = os.listdir(uniq_path)
    track_list = sorted(track_list, key=lambda t: os.path.getmtime(os.path.join(uniq_path, t)))
    if not track_list:
        await update.message.reply_text("Не удалось найти песни.")
        return
    for track in track_list:
        if len(track) > LENGHT:
            name = track.replace(".mp3", "")[:LENGHT+1] + "...mp3"
        else:
            name = track
        try:
            await update.message.reply_audio(os.path.join(uniq_path, track), title=name) 
            await sleep(1)
        except:
            print("ERROR DOWNLOAD")

    shutil.rmtree(uniq_path)

    # await update.message.reply_text("Некорректный ввод ссылки.")

def main() -> None:
    app = ApplicationBuilder().token(TOKEN).arbitrary_callback_data(True).build()

    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.Regex("(youtube.com/)"), youtube_link))
    app.add_handler(MessageHandler(filters.Regex("(bandcamp.com/)"), bandcamp_link))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, song_name))
    
    app.job_queue.run_once(set_commands, 0)
    app.run_polling(poll_interval=2.0,
                    bootstrap_retries=5,
                    allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()