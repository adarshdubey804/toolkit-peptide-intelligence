from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    app_env: str = "development"
    app_secret_key: str
    frontend_origin: str = "http://localhost:3000"
    rate_limit_window_seconds: int = 60
    login_rate_limit_per_window: int = 10
    registration_rate_limit_per_window: int = 5
    agent_rate_limit_per_window: int = 10
    ncbi_email: str | None = None
    ncbi_api_key: str | None = None
    ai_synthesis_enabled: bool = False
    ai_api_key: str | None = None
    ai_api_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4.1-mini"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
