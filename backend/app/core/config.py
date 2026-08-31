from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "NeuraLearn AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Database (defaults to SQLite for local dev)
    # In production set DATABASE_URL to your PostgreSQL connection string.
    # Both postgresql:// and postgresql+asyncpg:// are accepted — the async
    # driver prefix is added automatically if missing.
    DATABASE_URL: str = "sqlite+aiosqlite:///./neuralearn.db"
    SYNC_DATABASE_URL: str = "sqlite:///./neuralearn.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Keys
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_COLLECTION: str = "neuralearn_resources"

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ALGORITHM: str = "HS256"

    # CORS — comma-separated list of allowed origins, e.g.:
    # FRONTEND_URL=https://neuralearn.vercel.app,https://neuralearn-preview.vercel.app
    FRONTEND_URL: str = "http://localhost:5173"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10

    @property
    def async_database_url(self) -> str:
        """Return DATABASE_URL with the correct async driver prefix.

        Render's managed PostgreSQL injects a plain 'postgresql://' URL.
        SQLAlchemy's async engine requires 'postgresql+asyncpg://'.
        This property normalises the URL so both formats work.
        """
        url = self.DATABASE_URL
        if url.startswith("postgresql://") and not url.startswith("postgresql+"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            # Heroku-style shorthand also sometimes appears
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
