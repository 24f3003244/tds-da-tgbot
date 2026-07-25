# Build a Production-Ready AI Data Analyst Telegram Bot

## Role

You are a senior Python AI engineer, AI agent architect, and backend developer.

Your goal is to build an entire production-ready Telegram Data Analyst Bot for the assignment below.

Do **not** produce a prototype or MVP.

Build a clean, modular, maintainable project that is ready to deploy and pass grading.

If the output exceeds your context window, continue automatically until every file has been generated.

---

# IMPORTANT

Before writing any code, first inspect this repository:

https://github.com/Jivraj-18/tds-p1-t2-2026-telegram-bot

Study it carefully to understand:

- Project architecture
- Folder structure
- Evaluation pipeline
- Expected Telegram message format
- Expected response format
- Testing flow
- How grading works
- How questions are structured

Use it **only as inspiration**.

Do NOT copy code.

Instead:

- Follow a similar folder organization.
- Keep compatible project structure where appropriate.
- Improve engineering quality wherever possible.
- Write original code.

---

# Assignment

Build an AI-powered Telegram bot.

The bot acts like a Data Analyst.

It receives Telegram messages containing data-analysis questions.

Messages may contain:

- Inline datasets
- CSV data
- JSON data
- Tables
- Public dataset URLs
- Government dataset URLs
- MOSPI datasets
- Statistical questions
- Multi-turn conversations

The bot must determine the answer.

Finally it must reply with exactly ONE JSON object.

Example:

```json
{
  "answer": {
    "state": "Assam"
  },
  "log_url": "https://example.com/logs/run_123.jsonl"
}
```

The bot must NEVER output:

- Markdown
- Explanation
- Extra text
- Code block
- Notes

Only the JSON object.

---

# LLM

Use

**OpenAI GPT-4.1 Mini**

Use the official OpenAI Python SDK.

Read the API key from environment variables.

Environment variable:

```
OPENAI_API_KEY
```

Default model:

```
gpt-4.1-mini
```

Model should be configurable.

---

# Deployment

Deploy to

## Railway

The project must be Railway-ready.

Include:

- railway.json (if useful)
- Procfile (if needed)
- Dockerfile
- health endpoint
- automatic startup
- polling mode

README must include Railway deployment instructions.

---

# Folder Structure

Use the repository above as inspiration.

Follow approximately the same layout.

Improve it where appropriate.

Example:

```
telegram-data-analyst-bot/

app/
    agent.py
    analyzer.py
    bot.py
    config.py
    dataset.py
    downloader.py
    handlers.py
    logger.py
    memory.py
    prompts.py
    schemas.py
    storage.py
    utils.py

services/
    llm.py
    telegram_service.py
    logging_service.py

tests/

logs/

main.py

requirements.txt

Dockerfile

README.md

.env.example
```

Keep it modular.

Avoid putting everything in one file.

---

# Tech Stack

Python 3.12+

Libraries:

- python-telegram-bot
- openai
- pandas
- polars
- duckdb
- numpy
- requests
- httpx
- pydantic
- python-dotenv
- tenacity
- aiofiles
- uvicorn
- fastapi
- structlog

Prefer async code.

---

# Functional Requirements

## Telegram Bot

The bot must:

- Receive Telegram messages
- Support multiple users
- Maintain conversation history
- Support polling
- Make webhook optional

---

## Multi-turn Conversations

Example

User:

```
Use this dataset.
```

Later

```
Now compute the average income.
```

The agent must remember previous conversation.

Answer ONLY the latest message.

---

## Memory

Maintain conversation memory.

Store:

- role
- message
- timestamp

Implement pluggable memory.

Initially:

In-memory

Design so Redis can later replace it.

---

## LLM Agent

Create an Agent class.

Responsibilities:

- Read conversation
- Understand task
- Detect datasets
- Detect URLs
- Plan analysis
- Execute tools
- Produce answer

Keep agent logic isolated.

---

# Prompt Engineering

Write a strong system prompt.

The prompt should enforce:

- Never hallucinate.
- Never invent numbers.
- Always inspect datasets.
- Always verify calculations.
- Never output markdown.
- Never output explanations.
- Follow requested JSON schema exactly.
- Use available tools.
- Be deterministic whenever possible.

---

# Tool System

Implement tools.

Examples:

```
download_dataset()

load_dataframe()

run_duckdb()

execute_analysis()

describe_dataframe()

find_columns()

summarize_data()

```

The agent should decide which tools to call.

---

# Dataset Support

Automatically detect:

CSV

Excel

JSON

TSV

ZIP containing CSV

Parquet

GitHub raw URLs

Google Sheets

Government datasets

MOSPI

Download automatically.

Retry failures.

Cache downloads.

Validate file size.

Validate MIME type.

---

# Analysis Engine

Support

- filtering
- sorting
- joins
- merges
- groupby
- aggregation
- top-k
- ranking
- median
- average
- mode
- standard deviation
- variance
- correlation
- regression
- percentages
- pivot tables
- date parsing
- missing values
- duplicate detection
- DuckDB SQL

Prefer Pandas.

Use DuckDB where useful.

---

# JSON Schema Extraction

Questions may request:

```
{
    "state":"..."
}
```

or

```
{
    "top_5":[]
}
```

or

```
{
    "average":0
}
```

Never hardcode.

Detect requested schema automatically.

Return:

```json
{
    "answer": {
        ...
    },
    "log_url": "..."
}
```

---

# Logging

Every execution must generate JSONL logs.

Each line:

```json
{"event":"message_received"}
```

```json
{"event":"dataset_downloaded"}
```

```json
{"event":"analysis_completed"}
```

```json
{"event":"response_generated"}
```

Include:

- timestamp
- execution id
- user id
- tool calls
- downloaded URLs
- errors
- final response

---

# Log Storage

Implement LogService.

Initially:

Store locally.

Expose via FastAPI.

For example

```
https://your-app.up.railway.app/logs/run123.jsonl
```

The URL must be publicly downloadable.

Design abstraction so cloud storage can later replace local storage.

---

# FastAPI

Add FastAPI.

Endpoints:

```
GET /
```

returns

```
OK
```

---

```
GET /health
```

returns

```
healthy
```

---

```
GET /logs/{filename}
```

Downloads JSONL.

---

# Configuration

Use .env

Variables

```
BOT_TOKEN=

OPENAI_API_KEY=

OPENAI_MODEL=gpt-4.1-mini

BASE_URL=

LOG_DIRECTORY=

PUBLIC_LOG_BASE_URL=
```

Never hardcode secrets.

---

# Error Handling

Gracefully handle:

- invalid CSV
- invalid JSON
- bad URLs
- 404
- timeout
- OpenAI errors
- Telegram errors
- malformed data
- unsupported formats

Retry network requests.

Use exponential backoff.

---

# Performance

Reuse HTTP clients.

Use async.

Cache downloaded datasets.

Avoid duplicate downloads.

Avoid unnecessary memory usage.

---

# Security

Validate URLs.

Restrict file size.

Prevent path traversal.

Never execute arbitrary Python code.

Sanitize filenames.

---

# Testing

Write tests for:

- Telegram handlers
- Memory
- Dataset download
- JSON schema generation
- Agent
- Conversation flow
- Logging
- Error handling

---

# Code Quality

Use

- type hints
- docstrings
- Pydantic models
- logging
- dependency injection where useful
- clean architecture
- modular design

Avoid duplicated code.

Follow PEP8.

---

# README

Write a complete README.

Include:

- Project overview
- Architecture diagram
- Folder structure
- Installation
- Railway deployment
- Environment variables
- Running locally
- Testing
- Example requests
- Example responses
- Screenshots placeholders
- Troubleshooting
- Future improvements

---

# Docker

Generate:

Dockerfile

Requirements

Startup command

Suitable for Railway deployment.

---

# Railway

The application must automatically start on Railway.

Use PORT from environment variables.

Health endpoint must work.

Telegram polling should start automatically.

---

# Final Deliverables

Generate every required file.

Including:

- Source code
- README
- Dockerfile
- requirements.txt
- .env.example
- Tests
- Logging system
- Railway deployment configuration
- Example logs

Do not stop until the entire project has been generated.

If interrupted because of context length, continue automatically from the last generated file.

---

# Final Self Review

Before finishing:

Perform a complete review of the generated project.

Verify:

- Every assignment requirement has been implemented.
- Folder structure follows the reference repository where appropriate.
- The bot returns exactly one JSON object.
- Multi-turn conversations work.
- Logging works.
- Public log URLs work.
- Railway deployment is ready.
- GPT-4.1 Mini integration is complete.
- No placeholder implementations remain.

If any requirement is missing, implement it before ending the response.