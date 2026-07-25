import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, FileResponse
import uvicorn
import structlog
from app.bot import bot_app_instance
from app.config import settings
from services.logging_service import logging_service

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for starting and stopping background services (Telegram bot polling)."""
    logger.info("application_starting", port=settings.PORT, base_url=settings.BASE_URL)

    # Ensure log & cache directories exist
    Path(settings.LOG_DIRECTORY).mkdir(parents=True, exist_ok=True)
    Path(settings.DATA_CACHE_DIR).mkdir(parents=True, exist_ok=True)

    # Start Telegram polling task if token provided
    polling_task = asyncio.create_task(bot_app_instance.start_polling_async())

    yield

    logger.info("application_shutting_down")
    await bot_app_instance.stop_polling_async()
    polling_task.cancel()


fastapi_app = FastAPI(
    title="Telegram AI Data Analyst Bot",
    description="Production-ready Telegram Data Analyst Bot API with Railway deployment support.",
    version="1.0.0",
    lifespan=lifespan
)


@fastapi_app.get("/", response_class=PlainTextResponse)
async def root():
    """Root endpoint returning OK as required by Railway health checks."""
    return "OK"


@fastapi_app.get("/health", response_class=PlainTextResponse)
async def health_check():
    """Health check endpoint returning healthy."""
    return "healthy"


@fastapi_app.get("/logs/{filename}")
async def get_log_file(filename: str):
    """
    Downloads execution JSONL log file.
    Publicly accessible URL: GET /logs/{execution_id}.jsonl
    """
    return logging_service.get_log_file_response(filename)


if __name__ == "__main__":
    port = int(os.getenv("PORT", settings.PORT))
    uvicorn.run("main:fastapi_app", host="0.0.0.0", port=port, reload=False)
