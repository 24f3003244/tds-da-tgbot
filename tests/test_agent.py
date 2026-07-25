import json
import pytest
from app.agent import DataAnalystAgent


@pytest.mark.asyncio
async def test_agent_inline_dataset_processing():
    agent = DataAnalystAgent()
    chat_id = 99999
    user_id = 88888

    msg = """Here is the dataset:
state,income
Assam,1000
Goa,5000

Which state has the highest income?"""

    response_json_str = await agent.process_message(
        chat_id=chat_id,
        user_id=user_id,
        message_text=msg,
        execution_id="test_run_agent_1"
    )

    parsed = json.loads(response_json_str)
    assert "answer" in parsed
    assert "log_url" in parsed
    assert parsed["log_url"].endswith("test_run_agent_1.jsonl")


@pytest.mark.asyncio
async def test_agent_json_array_with_trailing_question():
    agent = DataAnalystAgent()
    chat_id = 88888
    user_id = 77777

    msg = """[
  {"product": "Laptop", "price": 1200, "units_sold": 15},
  {"product": "Phone", "price": 800, "units_sold": 40},
  {"product": "Tablet", "price": 500, "units_sold": 25},
  {"product": "Monitor", "price": 300, "units_sold": 30}
]

What is the total revenue generated across all products?"""

    response_json_str = await agent.process_message(
        chat_id=chat_id,
        user_id=user_id,
        message_text=msg,
        execution_id="test_run_agent_json_revenue"
    )

    parsed = json.loads(response_json_str)
    assert "answer" in parsed
    assert parsed["answer"] == {"total_revenue": 71500}


@pytest.mark.asyncio
async def test_agent_json_array_with_nbsp():
    agent = DataAnalystAgent()
    chat_id = 88887
    user_id = 77776

    msg = "[\n\u00a0 {\"product\": \"Laptop\", \"price\": 1200, \"units_sold\": 15},\n\u00a0 {\"product\": \"Phone\", \"price\": 800, \"units_sold\": 40},\n\u00a0 {\"product\": \"Tablet\", \"price\": 500, \"units_sold\": 25},\n\u00a0 {\"product\": \"Monitor\", \"price\": 300, \"units_sold\": 30}\n]\n\nWhat is the total revenue generated across all products?"

    response_json_str = await agent.process_message(
        chat_id=chat_id,
        user_id=user_id,
        message_text=msg,
        execution_id="test_run_agent_nbsp"
    )

    parsed = json.loads(response_json_str)
    assert "answer" in parsed
    assert parsed["answer"] == {"total_revenue": 71500}

