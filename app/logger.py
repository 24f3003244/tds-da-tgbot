import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import structlog
from app.config import settings
from app.schemas import LogEvent

try:
    import structlog
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )
    console_logger = structlog.get_logger()
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    console_logger = logging.getLogger("telegram_bot")


class ExecutionLogger:
    """Manages execution-scoped JSONL log files for evaluation & audit compliance."""

    def __init__(self, execution_id: Optional[str] = None, user_id: Optional[int] = None, chat_id: Optional[int] = None):
        self.execution_id = execution_id or f"run_{uuid.uuid4().hex[:12]}"
        self.user_id = user_id
        self.chat_id = chat_id
        self.filename = f"{self.execution_id}.jsonl"
        self.filepath = Path(settings.LOG_DIRECTORY) / self.filename
        self.events: list[LogEvent] = []

    def log_event(self, event_name: str, **kwargs: Any) -> LogEvent:
        """Appends a structured event to memory and syncs to JSONL log file."""
        log_event = LogEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            execution_id=self.execution_id,
            user_id=self.user_id,
            chat_id=self.chat_id,
            event=event_name,
            details=kwargs
        )
        self.events.append(log_event)

        # Write to JSONL file
        try:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_event.model_dump(), default=str) + "\n")
        except Exception as e:
            console_logger.error(f"failed_to_write_log_event: {str(e)}")

        # Also emit to console
        console_logger.info(f"{event_name}: {kwargs}")
        return log_event

    def get_log_url(self) -> str:
        """Constructs the public URL where this JSONL file can be fetched."""
        base_url = settings.get_public_log_base_url()
        return f"{base_url}/logs/{self.filename}"

