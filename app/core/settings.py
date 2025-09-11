from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/chat_service"
    secret_key: str = "changeme"
    
    # Recommendations system
    enable_vacancy_recommendations: bool = False  # Feature flag - по умолчанию выключено
    openai_api_key: str = "" 
    yandex_gpt_api_key: str = ""
    yandex_gpt_folder_id: str = ""
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "vacancies_tasks"

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False


settings = Settings()  # singleton-style simple settings loading



