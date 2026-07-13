"""Environment-backed settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql://fp:fp@localhost:15432/factorypulse"
    mqtt_broker: str = "localhost"
    mqtt_port: int = 11883
    fp_log_level: str = "INFO"
    fp_seed: int = 42
    anthropic_api_key: str | None = None
    groq_api_key: str | None = None
    langfuse_host: str = "http://localhost:13001"
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    audio_chunk_dir: str = "data/audio_chunks"
    config_dir: str = "config"
    fp_offline_llm: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
