import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.handlers import start_handler, help_handler, clear_handler


@pytest.mark.asyncio
async def test_start_handler():
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await start_handler(update, context)
    update.message.reply_text.assert_called_once()
    reply_arg = update.message.reply_text.call_args[0][0]
    parsed = json.loads(reply_arg)
    assert "answer" in parsed
    assert "log_url" in parsed


@pytest.mark.asyncio
async def test_clear_handler():
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = 12345
    context = MagicMock()

    await clear_handler(update, context)
    update.message.reply_text.assert_called_once()
    reply_arg = update.message.reply_text.call_args[0][0]
    parsed = json.loads(reply_arg)
    assert parsed["answer"]["status"] == "Conversation context cleared successfully."
