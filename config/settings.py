from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database — swap this one line to go from DuckDB to PostgreSQL
    database_url: str = Field(default="duckdb:///./data/fundlens.duckdb")

    # API Keys
    tiingo_api_key: str = Field(default="")

    # Pipeline schedule
    daily_update_hour: int = Field(default=18)
    daily_update_minute: int = Field(default=0)

    # Paths
    data_dir: Path = Field(default=Path("./data"))
    exports_dir: Path = Field(default=Path("./data/exports"))
    funds_config: Path = Field(default=Path("./config/funds.yaml"))

    # Logging
    log_level: str = Field(default="INFO")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
