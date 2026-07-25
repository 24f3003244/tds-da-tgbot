import pytest
from app.memory import ConversationMemory
from app.storage import InMemoryStorage


@pytest.mark.asyncio
async def test_conversation_memory():
    storage = InMemoryStorage()
    memory = ConversationMemory(storage=storage)
    chat_id = 12345

    await memory.add_user_message(chat_id, "Use https://example.com/data.csv", has_dataset=True, dataset_urls=["https://example.com/data.csv"])
    await memory.add_assistant_message(chat_id, '{"answer": {"status": "ok"}, "log_url": "http://localhost/logs/run1.jsonl"}')
    await memory.add_user_message(chat_id, "Compute average income")

    history = await memory.get_history(chat_id)
    assert len(history) == 3
    assert history[0].role == "user"
    assert history[1].role == "assistant"
    assert history[2].role == "user"

    urls = await memory.get_all_dataset_urls(chat_id)
    assert urls == ["https://example.com/data.csv"]

    await memory.clear_memory(chat_id)
    cleared_history = await memory.get_history(chat_id)
    assert len(cleared_history) == 0
