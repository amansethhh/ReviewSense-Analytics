from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
# This points to ReviewSense-Analytics/ (project root)
# so that src/ and models/ resolve correctly regardless
# of where uvicorn is launched from.


class Settings(BaseSettings):
    app_name: str = "ReviewSense Analytics API"
    app_version: str = "10.0.0"
    debug: bool = False

    # CORS — explicit origins, never wildcard in prod
    allowed_origins: list[str] = [
        "http://localhost:5173",    # Vite dev server
        "http://localhost:5174",    # Vite fallback port
        "http://localhost:5175",    # Vite fallback port
        "http://localhost:5176",    # Vite fallback port
        "http://localhost:3000",    # fallback CRA
        "http://localhost:8080",    # fallback
    ]

    # Model paths — relative to project root
    model_dir: Path = ROOT_DIR / "models"
    src_dir:   Path = ROOT_DIR / "src"
    data_dir:  Path = ROOT_DIR / "data"

    # Performance
    max_bulk_rows: int = 5000
    prediction_timeout_seconds: int = 30
    bulk_chunk_size: int = 50

    # Job store TTL (seconds)
    job_ttl: int = 3600

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()

