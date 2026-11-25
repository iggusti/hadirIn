"""Simple daily attendance reminder at 16:30 WIB, Monday to Friday.

Usage:
1. Set BOT_TOKEN and CHAT_ID as environment variables / in .env
2. pip install -r requirements.txt
3. python simple_reminder_bot.py

This is the legacy one-shot version. The active bot with hourly escalation
is attendance_bot.py.
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

MESSAGE = (
    "⏰ Attendance reminder 16:30 WIB\n"
    "\n"
    "Have you checked in today?\n"
    "• Nia — MAN 2 Cilegon\n"
    "• Ilham — Universitas Telkom\n"
    "\n"
    "Don't forget ✅"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply to /start with the chat ID so it can be copied into .env."""
    await update.message.reply_text(
        "Attendance reminder bot is active.\n"
        f"Chat ID: {update.effective_chat.id}\n"
        "Send /test to preview the reminder."
    )


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a sample reminder to the chat where the command was typed."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=MESSAGE)


async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Triggered automatically by the JobQueue."""
    logger.info("Sending reminder to chat %s", CHAT_ID)
    await context.bot.send_message(chat_id=CHAT_ID, text=MESSAGE)


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))

    # 0 = Monday ... 4 = Friday. WIB = Asia/Jakarta (UTC+7).
    app.job_queue.run_daily(
        send_reminder,
        time=dt.time(hour=16, minute=30, tzinfo=WIB),
        days=(0, 1, 2, 3, 4),
        name="attendance-reminder",
    )

    logger.info("Bot is running. Reminder: Mon-Fri 16:30 WIB.")
    app.run_polling()


if __name__ == "__main__":
    main()
