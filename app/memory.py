from typing import List, Optional
from app.config import settings
from app.schemas import ConversationMessage
from app.storage import BaseStorage, InMemoryStorage


class ConversationMemory:
    """Manages multi-turn conversation memory for Telegram users."""

    def __init__(self, storage: Optional[BaseStorage] = None):
        self.storage = storage or InMemoryStorage()
        self.max_history = settings.MAX_CONVERSATION_HISTORY

    def _get_key(self, chat_id: int) -> str:
        return f"chat:{chat_id}"

    async def add_user_message(
        self,
        chat_id: int,
        content: str,
        has_dataset: bool = False,
        dataset_urls: Optional[List[str]] = None
    ) -> ConversationMessage:
        msg = ConversationMessage(
            role="user",
            content=content,
            has_dataset=has_dataset,
            dataset_urls=dataset_urls or []
        )
        await self.storage.add_message(self._get_key(chat_id), msg)
        return msg

    async def add_assistant_message(self, chat_id: int, content: str) -> ConversationMessage:
        msg = ConversationMessage(
            role="assistant",
            content=content
        )
        await self.storage.add_message(self._get_key(chat_id), msg)
        return msg

    async def get_history(self, chat_id: int) -> List[ConversationMessage]:
        return await self.storage.get_messages(self._get_key(chat_id), limit=self.max_history)

    async def get_all_dataset_urls(self, chat_id: int) -> List[str]:
        """Extracts all dataset URLs referenced across prior turns in the conversation."""
        history = await self.get_history(chat_id)
        urls = []
        for msg in history:
            urls.extend(msg.dataset_urls)
        # Deduplicate while maintaining order
        seen = set()
        deduped = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                deduped.append(url)
        return deduped

    async def clear_memory(self, chat_id: int) -> None:
        await self.storage.clear(self._get_key(chat_id))


# Global default instance
memory_manager = ConversationMemory()
