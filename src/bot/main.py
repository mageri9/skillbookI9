"""Точка входа Telegram-бота."""

from telegram.ext import CommandHandler
from src.bot.app import create_app
from src.bot.handlers.analyze import analyze_command


async def start(update, context) -> None:
    """Приветствие на /start."""
    await update.message.reply_text("Commit Chronicle готов.")


def main():
    app = create_app()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.run_polling()


if __name__ == "__main__":
    main()