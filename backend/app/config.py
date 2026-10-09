from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Loan Risk MVP"
    debug: bool = True
    database_url: str = "sqlite+aiosqlite:///./risk.db"
    datasource_mode: str = "mock"  # mock | live


settings = Settings()
