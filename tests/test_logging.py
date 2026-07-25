import json
from pathlib import Path
import pytest
from app.logger import ExecutionLogger
from services.logging_service import logging_service


def test_execution_logger_events(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.LOG_DIRECTORY", str(tmp_path))

    exec_logger = ExecutionLogger(execution_id="test_run_123", user_id=999, chat_id=888)
    exec_logger.log_event("message_received", text="Hello data analyst")
    exec_logger.log_event("response_generated", answer={"value": 100})

    log_path = tmp_path / "test_run_123.jsonl"
    assert log_path.exists()

    with open(log_path, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f.readlines()]

    assert len(lines) == 2
    assert lines[0]["event"] == "message_received"
    assert lines[0]["user_id"] == 999
    assert lines[1]["event"] == "response_generated"
    assert lines[1]["details"]["answer"] == {"value": 100}
