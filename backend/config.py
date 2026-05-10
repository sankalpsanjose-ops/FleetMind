from pathlib import Path
from pydantic_settings import BaseSettings

_HERE = Path(__file__).parent  # backend/

class Settings(BaseSettings):
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    database_url: str = f"sqlite:///{_HERE}/../fleetmind.db"
    debug: bool = False

    model_config = {"env_file": [str(_HERE / ".env"), ".env"]}

settings = Settings()
