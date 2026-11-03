from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    scheduler_database_url: str | None = None
    app_env: str = "development"
    app_secret_key: str
    frontend_origin: str = "http://localhost:3000"
    rate_limit_window_seconds: int = Field(default=60, ge=1)
    login_rate_limit_per_window: int = Field(default=10, ge=1)
    registration_rate_limit_per_window: int = Field(default=5, ge=1)
    agent_rate_limit_per_window: int = Field(default=10, ge=1)
    public_research_rate_limit_per_window: int = Field(default=30, ge=1)
    sensitive_write_rate_limit_per_window: int = Field(default=20, ge=1)
    enrichment_rate_limit_per_window: int = Field(default=10, ge=1)
    ncbi_email: str | None = None
    ncbi_api_key: str | None = None
    openfda_api_key: str | None = None
    gtopdb_api_key: str | None = None
    ai_synthesis_enabled: bool = False
    ai_api_key: str | None = None
    ai_api_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4.1-mini"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
