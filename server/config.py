from functools import lru_cache
from pydantic import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    UNIFAI_AGENT_API_KEY: str
    DEFAULT_MODEL: str = "gpt-4o-mini"
    DB_URL: str = "sqlite:///./ai.sqlite3"
    STREAM_CHUNK_SIZE: int = 1024
    LOG_SQL: bool = False

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
