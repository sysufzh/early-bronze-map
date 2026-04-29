import os
from pathlib import Path

from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parent.parent  # backend/


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "early_bronze"
    DB_USER: str = "bronze_user"
    DB_PASSWORD: str = "bronze_pass_2024"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:5173"]
    STATIC_DIR: str = str(BACKEND_DIR / "static")

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = {"env_prefix": "BRONZE_"}


settings = Settings()
