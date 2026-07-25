from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from app.schemas import ConversationMessage


class BaseStorage(ABC):
    """Abstract interface for storing conversation messages per user/chat."""

    @abstractmethod
    async def add_message(self, key: str, message: ConversationMessage) -> None:
        pass

    @abstractmethod
    async def get_messages(self, key: str, limit: Optional[int] = None) -> List[ConversationMessage]:
        pass

    @abstractmethod
    async def clear(self, key: str) -> None:
        pass


class InMemoryStorage(BaseStorage):
    """Thread-safe in-memory message store for local or single-instance deployment."""

    def __init__(self):
        self._store: Dict[str, List[ConversationMessage]] = {}

    async def add_message(self, key: str, message: ConversationMessage) -> None:
        if key not in self._store:
            self._store[key] = []
        self._store[key].append(message)

    async def get_messages(self, key: str, limit: Optional[int] = None) -> List[ConversationMessage]:
        messages = self._store.get(key, [])
        if limit and len(messages) > limit:
            return messages[-limit:]
        return messages

    async def clear(self, key: str) -> None:
        if key in self._store:
            self._store[key] = []
