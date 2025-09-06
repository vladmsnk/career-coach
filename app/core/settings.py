from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/chat_service"
    secret_key: str = "changeme"

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False


settings = Settings()  # singleton-style simple settings loading



