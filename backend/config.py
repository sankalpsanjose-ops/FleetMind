from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    database_url: str = "sqlite:///./fleetmind.db"
    debug: bool = False

    model_config = {"env_file": ".env"}

settings = Settings()
