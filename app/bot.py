import asyncio
from typing import Optional
import structlog
from telegram import BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from app.config import settings
from app.handlers import (
    start_handler,
    help_handler,
    clear_handler,
    message_handler,
    document_handler
)

logger = structlog.get_logger()


class TelegramBotApp:
    """Telegram Bot application lifecycle manager."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.BOT_TOKEN
        self.application: Optional[Application] = None

    def build_application(self) -> Application:
        """Constructs python-telegram-bot Application instance with registered handlers."""
        if not self.token or self.token.startswith("YOUR_"):
            logger.warning("telegram_bot_token_not_configured_polling_disabled")

        app = Application.builder().token(self.token or "123456789:AAA_dummy_token_for_init").build()

        # Register handlers
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CommandHandler("help", help_handler))
        app.add_handler(CommandHandler("clear", clear_handler))
        app.add_handler(CommandHandler("reset", clear_handler))

        # Register document handler
        app.add_handler(MessageHandler(filters.Document.ALL, document_handler))

        # Register text message handler
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

        self.application = app
        return app

    async def start_polling_async(self) -> None:
        """Starts telegram bot polling asynchronously and sets command menu in Telegram UI."""
        if not self.token or self.token.startswith("YOUR_"):
            logger.warning("skipping_telegram_polling_no_valid_token")
            return

        if self.application is None:
            self.build_application()

        assert self.application is not None
        logger.info("starting_telegram_bot_polling")
        await self.application.initialize()
        await self.application.start()

        # Set Telegram command autocomplete list (menu pop-up when user types /)
        try:
            await self.application.bot.set_my_commands([
                BotCommand("start", "Initialize the Telegram Data Analyst Bot"),
                BotCommand("help", "Show help and usage guidelines"),
                BotCommand("clear", "Clear conversation context and memory"),
                BotCommand("reset", "Reset conversation context"),
            ])
            logger.info("telegram_bot_commands_registered_successfully")
        except Exception as e:
            logger.warning("failed_to_set_bot_commands", error=str(e))

        await self.application.updater.start_polling(drop_pending_updates=True)

    async def stop_polling_async(self) -> None:
        """Gracefully stops telegram bot polling."""
        if self.application and self.application.updater and self.application.updater.running:
            logger.info("stopping_telegram_bot")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()


bot_app_instance = TelegramBotApp()
