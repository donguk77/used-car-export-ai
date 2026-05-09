from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/used_car_export"
    database_echo: bool = False

    llm_provider: str = "stub"  # anthropic | gemini | stub

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    nhtsa_vpic_base: str = "https://vpic.nhtsa.dot.gov/api"
    ofac_sdn_url: str = "https://www.treasury.gov/ofac/downloads/sdn.xml"
    yestrade_base: str = "https://www.yestrade.go.kr"

    rules_dir: Path = Field(default=Path("configs/rules"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
