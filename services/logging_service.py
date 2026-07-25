from pathlib import Path
from typing import Optional
from fastapi import HTTPException
from fastapi.responses import FileResponse
from app.config import settings
from app.logger import ExecutionLogger


class LoggingService:
    """Service for creating loggers and serving JSONL log files."""

    @staticmethod
    def create_logger(execution_id: Optional[str] = None, user_id: Optional[int] = None, chat_id: Optional[int] = None) -> ExecutionLogger:
        return ExecutionLogger(execution_id=execution_id, user_id=user_id, chat_id=chat_id)

    @staticmethod
    def get_log_file_response(filename: str) -> FileResponse:
        """Returns FileResponse for requested JSONL log file or raises 404 HTTP Exception."""
        log_dir = Path(settings.LOG_DIRECTORY)
        filepath = (log_dir / filename).resolve()

        # Security check: prevent path traversal attacks
        if not str(filepath).startswith(str(log_dir.resolve())):
            raise HTTPException(status_code=400, detail="Invalid log filename.")

        if not filepath.exists() or not filepath.is_file():
            raise HTTPException(status_code=404, detail="Log file not found.")

        return FileResponse(
            path=filepath,
            media_type="application/x-ndjson",
            filename=filename
        )


logging_service = LoggingService()
