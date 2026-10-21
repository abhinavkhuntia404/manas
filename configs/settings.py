from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "MANAS"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # Database (Supabase PostgreSQL or local SQLite)
    database_url: str = "sqlite:///./data/manas.db"
    supabase_url: str = ""
    supabase_key: str = ""

    # Upstash / Redis Caching & Queue
    redis_url: str = ""
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    # Paths
    data_dir: Path = Path("./data")
    raw_data_dir: Path = Path("./data/raw")
    processed_data_dir: Path = Path("./data/processed")

    # Rate limiting
    api_rate_limit: str = "100/minute"
    max_concurrent_jobs: int = 4

    # Logging
    log_level: str = "INFO"

    # Allen Institute
    allen_aging_base_url: str = "https://aging.brain-map.org"
    allen_atlas_base_url: str = "https://human.brain-map.org"

    # Analysis defaults
    min_group_size: int = 5           # Minimum per-group n to run a test
    fdr_alpha: float = 0.05           # FDR significance threshold
    bootstrap_n: int = 1000           # Bootstrap iterations for CI
    default_random_seed: int = 42


@lru_cache()
def get_settings() -> Settings:
    return Settings()
