import asyncio
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
import structlog
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
from app.agent import agent_instance
from app.config import settings
from app.dataset import dataset_loader
from app.memory import memory_manager

logger = structlog.get_logger()


@asynccontextmanager
async def typing_action(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Periodically sends typing chat action to Telegram while processing request."""
    async def _send_typing_loop():
        try:
            while True:
                await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning("typing_action_error", error=str(e))

    typing_task = asyncio.create_task(_send_typing_loop())
    try:
        yield
    finally:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /start command."""
    if update.message:
        welcome_msg = (
            '{"answer": {"message": "Telegram AI Data Analyst Bot initialized. Send dataset link, text, or file with your question."}, '
            f'"log_url": "{settings.get_public_log_base_url()}/logs/system.jsonl"}}'
        )
        await update.message.reply_text(welcome_msg)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /help command."""
    if update.message:
        help_msg = (
            '{"answer": {"info": "Send dataset URLs (CSV, JSON, Google Sheets, GitHub) or inline data tables with your question. Use /clear to reset context."}, '
            f'"log_url": "{settings.get_public_log_base_url()}/logs/system.jsonl"}}'
        )
        await update.message.reply_text(help_msg)


async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /clear or /reset command to wipe conversation history."""
    if update.message and update.effective_chat:
        chat_id = update.effective_chat.id
        await memory_manager.clear_memory(chat_id)
        clear_msg = (
            '{"answer": {"status": "Conversation context cleared successfully."}, '
            f'"log_url": "{settings.get_public_log_base_url()}/logs/system.jsonl"}}'
        )
        await update.message.reply_text(clear_msg)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming text messages with dataset analysis questions."""
    if not update.message or not update.message.text or not update.effective_chat or not update.effective_user:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message_text = update.message.text

    # Show typing indicator while agent processes query
    async with typing_action(context, chat_id):
        bot_json_response = await agent_instance.process_message(
            chat_id=chat_id,
            user_id=user_id,
            message_text=message_text
        )

    # Reply with exact JSON output
    await update.message.reply_text(bot_json_response)


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles document attachments (e.g. CSV, JSON, Excel files sent directly to the Telegram bot)."""
    if not update.message or not update.message.document or not update.effective_chat or not update.effective_user:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    doc = update.message.document
    caption = update.message.caption or f"Analyze attached dataset file: {doc.file_name}"

    try:
        async with typing_action(context, chat_id):
            telegram_file = await context.bot.get_file(doc.file_id)
            file_ext = Path(doc.file_name or "data.csv").suffix or ".csv"
            cache_file_path = Path(settings.DATA_CACHE_DIR) / f"doc_{doc.file_id}{file_ext}"

            await telegram_file.download_to_drive(custom_path=str(cache_file_path))

            # Append file local path url or instruction to message caption
            full_prompt = f"{caption}\nDataset file downloaded locally at: {cache_file_path.name}"

            bot_json_response = await agent_instance.process_message(
                chat_id=chat_id,
                user_id=user_id,
                message_text=full_prompt
            )
        await update.message.reply_text(bot_json_response)
    except Exception as e:
        logger.error("telegram_document_download_error", error=str(e))
        error_msg = (
            f'{{"answer": {{"error": "Failed to process document: {str(e)}"}}, '
            f'"log_url": "{settings.get_public_log_base_url()}/logs/system.jsonl"}}'
        )
        await update.message.reply_text(error_msg)
