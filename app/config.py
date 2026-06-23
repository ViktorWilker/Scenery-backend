from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_uri: str
    gemini_api_key: str
    freesound_api_key: str

    chroma_api_key: str
    chroma_tenant: str
    chroma_database: str

    db_name: str = "scenery"

    class Config:
        env_file = ".env"


settings = Settings()