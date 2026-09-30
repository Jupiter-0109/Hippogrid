"""Core configuration settings for HippoGrid."""
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Union
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    PROJECT_NAME: str = "HippoGrid"
    TAGLINE: str = "Don't just predict the shortage. Guarantee the service."
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    RANDOM_SEED: int = 42

    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:3000",
    ]

    # Database & Supabase credentials
    SUPABASE_URL: str = "https://ucihhursqublehkxpqqm.supabase.co"
    SUPABASE_PUBLISHABLE_KEY: str = ""
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/postgres"

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            if self.CORS_ORIGINS.startswith("[") and self.CORS_ORIGINS.endswith("]"):
                import json
                try:
                    return json.loads(self.CORS_ORIGINS)
                except Exception:
                    pass
            return [i.strip() for i in self.CORS_ORIGINS.split(",") if i.strip()]
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()


def load_yaml_config(filename: str) -> Dict[str, Any]:
    """Load configuration from config/ directory."""
    config_path = PROJECT_ROOT / "config" / filename
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
