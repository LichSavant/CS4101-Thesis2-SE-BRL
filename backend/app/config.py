from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    database_url: str = "sqlite:///./database/phishing_defense.db"
    email_open_deduplication_seconds: int = Field(default=5, ge=1, le=60)
    artifact_payload_max_bytes: int = Field(default=1_000_000, ge=1024, le=16_000_000)
    artifact_timeout_seconds: float = Field(default=10., gt=0, le=60)
    artifact_bundle_max_bytes: int = Field(default=20_000_000, ge=1024, le=500_000_000)
    artifact_email_bundle: str | None = None
    artifact_email_bundle_sha256: str | None = None
    artifact_web_bundle: str | None = None
    artifact_web_bundle_sha256: str | None = None
    artifact_uci_bundle: str | None = None
    artifact_uci_bundle_sha256: str | None = None
    artifact_phiusiil_bundle: str | None = None
    artifact_phiusiil_bundle_sha256: str | None = None
    artifact_metadata_retention_enabled: bool = False
    supabase_url: str | None = None
    supabase_service_role_key: str | None = Field(default=None, repr=False)

    model_config = SettingsConfigDict(env_file="backend/.env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
