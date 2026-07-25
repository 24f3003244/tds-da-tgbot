"""
Utility functions for Telegram Data Analyst Bot.
"""

import json
from typing import Any


def safe_json_dumps(data: Any) -> str:
    """Safely converts Python data structure to JSON string."""
    try:
        return json.dumps(data, default=str, ensure_ascii=False)
    except Exception:
        return str(data)
