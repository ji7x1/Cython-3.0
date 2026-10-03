"""إعدادات السيرفر، تنقرا من متغيرات البيئة (او من ملف .env بجذر المشروع)."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

# ملف .env اختياري؛ متغيرات البيئة الموجودة اصلاً ما تنكتب فوكها
load_dotenv(ROOT_DIR / ".env", override=False)

DEFAULT_CORS_ORIGINS = (
    "http://localhost:8000,http://127.0.0.1:8000,"
    "http://localhost:5500,http://127.0.0.1:5500"
)


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from None
    if value < 1:
        raise ValueError(f"{name} must be >= 1, got {value}")
    return value


@dataclass(frozen=True)
class Settings:
    model: str
    temperature: float
    max_tokens: int
    request_timeout: int
    max_history_messages: int
    max_conversations: int
    cors_origins: tuple


def load_settings() -> Settings:
    origins = os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    return Settings(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0.6,  # حرارة متوسطة للابداع والالتزام
        max_tokens=1024,
        request_timeout=_int_env("LLM_TIMEOUT_SECONDS", 30),
        max_history_messages=_int_env("MAX_HISTORY_MESSAGES", 20),
        max_conversations=_int_env("MAX_CONVERSATIONS", 1000),
        cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
    )


def get_api_key() -> str | None:
    """يرجع GROQ_API_KEY وقت الطلب (مو وقت الـ import) حتى السيرفر ما يوكع اذا ناقص."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    return key or None
