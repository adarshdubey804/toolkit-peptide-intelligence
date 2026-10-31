from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    app_env: str = "development"
    app_secret_key: str
    frontend_origin: str = "http://localhost:3000"
    ncbi_email: str | None = None
    ncbi_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
