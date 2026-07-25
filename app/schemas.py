from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BotResponse(BaseModel):
    """Final JSON response format required by evaluation pipeline."""
    answer: Any = Field(description="The structured answer extracted or calculated for the user question.")
    log_url: str = Field(description="Public URL where the execution JSONL log can be downloaded.")


class LogEvent(BaseModel):
    """Structured log entry stored in JSONL log files."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    execution_id: str
    user_id: Optional[int] = None
    chat_id: Optional[int] = None
    event: str
    details: Dict[str, Any] = Field(default_factory=dict)


class DatasetInfo(BaseModel):
    """Metadata describing a loaded dataset."""
    source: str
    file_type: str
    row_count: int
    column_count: int
    columns: List[str]
    sample_data: List[Dict[str, Any]]
    dtypes: Dict[str, str]
    summary_stats: Optional[Dict[str, Any]] = None


class ConversationMessage(BaseModel):
    """Single message in multi-turn conversation memory."""
    role: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    has_dataset: bool = False
    dataset_urls: List[str] = Field(default_factory=list)
