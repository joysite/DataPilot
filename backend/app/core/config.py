"""DataPilot 全局配置。"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """应用配置。"""

    model_config = SettingsConfigDict(
        env_prefix="DATAPILOT_",
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'data' / 'datapilot.db'}"
    checkpointer_path: Path = PROJECT_ROOT / "data" / "checkpointer.db"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    ollama_temperature: float = 0.0


settings = Settings()
