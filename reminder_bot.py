"""Pengingat presensi harian pukul 16.30 WIB (Senin-Jumat).

Cara pakai:
1. Isi BOT_TOKEN dan CHAT_ID lewat environment variable / file .env
2. pip install -r requirements.txt
3. python reminder_bot.py
"""

import datetime as dt
import logging
import os
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])
WIB = ZoneInfo("Asia/Jakarta")  # UTC+7

PESAN = (
    "⏰ Pengingat presensi 16.30 WIB\n"
    "\n"
    "Sudah presensi hari ini?\n"
    "• Istri — MAN 2 Cilegon\n"
    "• Saya — Universitas Telkom\n"
    "\n"
    "Jangan lupa ya ✅"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Balas /start dengan chat ID supaya mudah disalin ke .env."""
    await update.message.reply_text(
        "Bot pengingat presensi aktif.\n"
        f"Chat ID: {update.effective_chat.id}\n"
        "Kirim /test untuk mencoba isi pengingat."
    )


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kirim contoh pengingat ke chat tempat perintah diketik."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=PESAN)


async def kirim_pengingat(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dijalankan otomatis oleh JobQueue sesuai jadwal."""
    logger.info("Mengirim pengingat ke chat %s", CHAT_ID)
    await context.bot.send_message(chat_id=CHAT_ID, text=PESAN)


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))

    # 0 = Senin ... 4 = Jumat. WIB = Asia/Jakarta (UTC+7).
    app.job_queue.run_daily(
        kirim_pengingat,
        time=dt.time(hour=16, minute=30, tzinfo=WIB),
        days=(0, 1, 2, 3, 4),
        name="pengingat-presensi",
    )

    logger.info("Bot berjalan. Pengingat: Senin-Jumat 16.30 WIB.")
    app.run_polling()


if __name__ == "__main__":
    main()
