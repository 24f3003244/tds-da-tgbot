# Production-Ready AI Data Analyst Telegram Bot 🤖📊

An autonomous, production-ready AI Data Analyst Telegram Bot built with Python 3.12+, FastAPI, `python-telegram-bot`, Pandas, DuckDB, and OpenAI.

The bot receives Telegram messages containing data analysis questions, datasets (inline text/tables, files, or public/government URLs), performs deterministic calculations using Pandas and DuckDB, and responds with **EXACTLY ONE JSON OBJECT**.

---

## 🌟 Key Features

- **Multi-Turn Memory**: Remembers prior datasets and context in multi-turn conversations.
- **Auto Dataset Detection**: Supports CSV, TSV, JSON, Excel (.xlsx, .xls), Parquet, ZIP files, GitHub raw URLs, Google Sheets, MOSPI, and government dataset links.
- **Dual Data Engine**: Combines Pandas vector manipulation and DuckDB in-memory SQL queries.
- **Strict Response Guarantee**: Always outputs pure JSON format matching requested schemas without markdown codeblocks or extra text.
- **Execution JSONL Logging**: Generates public, downloadable JSONL execution logs for every query run.
- **Railway Ready**: Includes Dockerfile, health endpoints (`/` and `/health`), and auto-polling service.

---

## 🏗️ Project Architecture

```
                                  +-----------------------+
                                  |     Telegram User     |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  | python-telegram-bot  |
                                  +-----------+-----------+
                                              |
                                              v
+------------------------+        +-----------+-----------+        +------------------------+
|   ConversationMemory   | <----> |   DataAnalystAgent    | <----> |      LLMService        |
|  (In-Memory / Redis)   |        +-----------+-----------+        |  (OpenAI GPT-4o-mini)  |
+------------------------+                    |                    +------------------------+
                                              v
                                  +-----------+-----------+
                                  |  DatasetDownloader    |
                                  |   & DatasetLoader     |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |      DataAnalyzer     |
                                  |  (Pandas / DuckDB)    |
                                  +-----------+-----------+
                                              |
                                              v
+------------------------+        +-----------+-----------+
|  FastAPI /logs Service | <----- |    ExecutionLogger    |
| (GET /logs/run_xxx)    |        | (logs/run_xxx.jsonl)  |
+------------------------+        +-----------------------+
```

---

## 📁 Folder Structure

```
telegram-data-analyst-bot/
├── app/
│   ├── __init__.py
│   ├── agent.py          # DataAnalystAgent orchestrator
│   ├── analyzer.py       # DataAnalyzer (Pandas + DuckDB)
│   ├── bot.py            # Telegram Bot polling manager
│   ├── config.py         # Pydantic Settings & Env configuration
│   ├── dataset.py        # DatasetLoader & Summary generator
│   ├── downloader.py     # DatasetDownloader (retries, caching, ZIPs)
│   ├── handlers.py       # Telegram Command & Message handlers
│   ├── logger.py         # ExecutionLogger for JSONL audit logs
│   ├── memory.py         # Multi-turn ConversationMemory
│   ├── prompts.py        # System & LLM prompt templates
│   ├── schemas.py        # Pydantic validation models
│   ├── storage.py        # Pluggable storage abstraction
│   └── utils.py          # Utility helpers
├── services/
│   ├── __init__.py
│   ├── llm.py            # Async OpenAI client wrapper
│   ├── logging_service.py# FastAPI log server helper
│   └── telegram_service.py # JSON response formatter
├── tests/
│   ├── test_agent.py
│   ├── test_analyzer.py
│   ├── test_downloader.py
│   ├── test_handlers.py
│   ├── test_logging.py
│   └── test_memory.py
├── logs/                 # Execution JSONL logs directory
├── cache/                # Downloaded dataset cache directory
├── main.py               # Application entry point (FastAPI + Bot)
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container build specification
├── Procfile              # Deployment process configuration
├── railway.json          # Railway deployment settings
├── .env.example          # Environment variables template
├── .env                  # Secrets configuration
└── README.md
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```ini
# Telegram Bot API Token from @BotFather
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE

# OpenAI API Key
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE

# OpenAI Model
OPENAI_MODEL=gpt-4o-mini

# Web Server Port
PORT=8000

# Base URL for public log retrieval
BASE_URL=http://localhost:8000
PUBLIC_LOG_BASE_URL=https://your-app.up.railway.app
```

---

## 🚀 Running Locally

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/telegram-data-analyst-bot.git
cd telegram-data-analyst-bot

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Application

```bash
python main.py
```

The FastAPI web server will listen on `http://localhost:8000`, and Telegram Bot polling will automatically launch in the background.

---

## 🧪 Testing

Run the full pytest suite with offline mocks:

```bash
pytest tests/ -v
```

---

## 🚂 Railway Deployment

1. Create a new project on [Railway](https://railway.app).
2. Connect your GitHub repository.
3. Add the following Environment Variables in Railway Dashboard:
   - `BOT_TOKEN`
   - `OPENAI_API_KEY`
   - `PUBLIC_LOG_BASE_URL` = `https://${RAILWAY_PUBLIC_DOMAIN}`
4. Deploy! Railway will automatically detect the `Dockerfile` and build the container.

---

## 📩 Example Requests & Responses

### Request (Inline CSV)
```
state,income
Assam,1000
Goa,5000

Which state has the highest income?
```

### Response
```json
{
  "answer": {
    "state": "Goa"
  },
  "log_url": "https://your-app.up.railway.app/logs/run_9f8a3c2b1e.jsonl"
}
```

---

## 📸 Screenshots

*(Placeholders for deployment dashboard & Telegram interaction screenshots)*

- Telegram Bot Interface: `docs/telegram_sample.png`
- Downloadable Log Endpoint: `docs/log_sample.png`

---

## ❓ Troubleshooting

- **Telegram Bot not responding?**
  Verify `BOT_TOKEN` in `.env` and check log output for `starting_telegram_bot_polling`.
- **404 Log File Not Found?**
  Ensure `PUBLIC_LOG_BASE_URL` matches your deployed domain without a trailing slash.

---

## 🔮 Future Improvements

- Add Redis memory backend for horizontal scaling across multiple instances.
- Support multi-modal chart and graph generation returned as media attachments.
