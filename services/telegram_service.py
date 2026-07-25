import json
from typing import Any, Dict
from app.schemas import BotResponse


class TelegramService:
    """Telegram message formatting and output helper."""

    @staticmethod
    def format_bot_response(answer: Any, log_url: str) -> str:
        """
        Formats the output strictly as a single unformatted raw JSON string.
        No Markdown block, no explanations, no surrounding text.
        """
        response_model = BotResponse(answer=answer, log_url=log_url)
        # Dump compact or clean JSON string
        return json.dumps(response_model.model_dump(), ensure_ascii=False)


telegram_service = TelegramService()
