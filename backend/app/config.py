"""Application configuration from environment variables with sensible defaults."""

from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "Product Intelligence Dashboard API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: Optional[str] = None

    # Gemini (kept as secondary fallback for title enhancement only)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_VISION_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    CORS_ORIGINS: str = "*"

    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_VIDEO_EXTENSIONS: str = ".mp4,.avi,.mov,.mkv,.webm"
    ALLOWED_CSV_EXTENSIONS: str = ".csv"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
